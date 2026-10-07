"""Isolated, verified FBX export. The interactive scene is never cleaned or baked.

Maya: import AutoRigForHumanoid.unity_fbx_export as exporter; exporter.show()
The worker runs in a separate mayapy process against an immutable snapshot.
"""

import json
import math
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import uuid


def _maya():
    from maya import cmds, mel
    from maya.api import OpenMaya as om, OpenMayaAnim as oma

    return cmds, mel, om, oma


def _publish(source, output):
    """Publish a fully copied file atomically, without replacing existing output."""
    source, output = Path(source), Path(output)
    temporary = output.with_name(
        "." + output.name + "." + uuid.uuid4().hex + ".partial"
    )
    try:
        with source.open("rb") as reader, temporary.open("xb") as writer:
            shutil.copyfileobj(reader, writer, 8 * 1024 * 1024)
        if temporary.stat().st_size != source.stat().st_size:
            raise IOError("FBX output copy is incomplete")
        if os.name == "nt":
            os.rename(temporary, output)  # Windows refuses an existing destination.
        else:
            os.link(temporary, output)  # Exclusive create on POSIX.
            temporary.unlink()
    finally:
        if temporary.exists():
            temporary.unlink()


def _points(mesh):
    cmds, mel, om, oma = _maya()
    selection = om.MSelectionList()
    selection.add(mesh)
    return [
        (p.x, p.y, p.z)
        for p in om.MFnMesh(selection.getDagPath(0)).getPoints(om.MSpace.kWorld)
    ]


def _error(a, b):
    if len(a) != len(b):
        raise RuntimeError("Vertex count changed during export validation")
    return max((math.dist(x, y) for x, y in zip(a, b)), default=0.0)


def _capture(meshes, frames):
    cmds, _, _, _ = _maya()
    result = {}
    for frame in frames:
        cmds.currentTime(frame)
        result[frame] = {m: _points(m) for m in meshes}
    return result


def _check_capture(reference, meshes, tolerance, offset=0.0):
    """offset: where the reference frames are after moving the clip in time."""
    cmds, _, _, _ = _maya()
    worst = 0.0
    for frame, expected in reference.items():
        cmds.currentTime(frame + offset)
        for original, actual in meshes.items():
            error = _error(expected[original], _points(actual))
            worst = max(worst, error)
            if error > tolerance:
                raise RuntimeError(
                    "Deformation validation failed at frame %s: %s, error %g"
                    % (frame, original, error)
                )
    return worst


def _clean_deleted_topology(mesh):
    """Bake deletion history, then restore the exact surviving skin weights.

    Maya's default post-deformer baking interpolates skin weights. On deletion-only
    history the surviving vertices have an exact correspondence; use that instead.
    Ambiguous positions with different weights are refused rather than guessed.
    """
    cmds, _, om, oma = _maya()
    history = cmds.listHistory(mesh, pruneDagObjects=True) or []
    skins = [n for n in history if cmds.nodeType(n) == "skinCluster"]
    deletions = [n for n in history if cmds.nodeType(n) == "deleteComponent"]
    if not deletions:
        return False
    if len(skins) != 1:
        raise RuntimeError(
            "Deletion-history repair requires exactly one skinCluster: " + mesh
        )
    skin_name = skins[0]
    post = history[: history.index(skin_name)]
    unsupported = [
        n
        for n in post
        if cmds.nodeType(n) not in ("mesh", "transform", "deleteComponent", "groupId")
    ]
    if unsupported:
        raise RuntimeError("Unsupported post-skin history: " + ", ".join(unsupported))
    selection = om.MSelectionList()
    selection.add(skin_name)
    skin = oma.MFnSkinCluster(selection.getDependNode(0))
    selection = om.MSelectionList()
    selection.add(mesh)
    dag = selection.getDagPath(0)
    geometry_index = skin.indexForOutputShape(dag.node())
    output = "%s.outputGeometry[%d]" % (skin_name, geometry_index)
    node = om.MFnDependencyNode(skin.object())
    old_points = om.MFnMesh(
        node.findPlug("outputGeometry", False)
        .elementByLogicalIndex(geometry_index)
        .asMObject()
    ).getPoints()
    new_points = om.MFnMesh(dag).getPoints()
    component = om.MFnSingleIndexedComponent()
    vertices = component.create(om.MFn.kMeshVertComponent)
    component.addElements(range(len(old_points)))
    original_input = cmds.connectionInfo(mesh + ".inMesh", sourceFromDestination=True)
    try:
        cmds.connectAttr(output, mesh + ".inMesh", force=True)
        weights, influence_count = skin.getWeights(dag, vertices)
        blend_weights = skin.getBlendWeights(dag, vertices)
    finally:
        cmds.connectAttr(original_input, mesh + ".inMesh", force=True)

    def key(point):
        return tuple(round(v, 5) for v in (point.x, point.y, point.z))

    lookup = {}
    for index, point in enumerate(old_points):
        lookup.setdefault(key(point), []).append(index)
    mapping = []
    for point in new_points:
        candidates = lookup.get(key(point), [])
        if not candidates:
            raise RuntimeError(
                "History changes vertex positions, not just topology: " + mesh
            )
        chosen = candidates[0]
        for other in candidates[1:]:
            if any(
                abs(
                    weights[chosen * influence_count + j]
                    - weights[other * influence_count + j]
                )
                > 1e-10
                for j in range(influence_count)
            ):
                raise RuntimeError(
                    "Coincident vertices have different skin weights: " + mesh
                )
        mapping.append(chosen)
    exact = om.MDoubleArray(
        [
            weights[i * influence_count + j]
            for i in mapping
            for j in range(influence_count)
        ]
    )
    cmds.bakePartialHistory(mesh, prePostDeformers=True)
    component = om.MFnSingleIndexedComponent()
    vertices = component.create(om.MFn.kMeshVertComponent)
    component.addElements(range(len(mapping)))
    skin.setWeights(dag, vertices, om.MIntArray(range(influence_count)), exact, False)
    if len(blend_weights):
        skin.setBlendWeights(
            dag, vertices, om.MDoubleArray([blend_weights[i] for i in mapping])
        )
    return True


def _source(plug):
    cmds, _, _, _ = _maya()
    destination = cmds.connectionInfo(plug, getExactDestination=True)
    return (
        cmds.connectionInfo(destination, sourceFromDestination=True)
        if destination
        else ""
    )


def _sample(plugs, frames):
    """Evaluate plugs on each frame; returns one row of internal values per frame."""
    cmds, _, om, oma = _maya()
    selection = om.MSelectionList()
    for plug in plugs:
        selection.add(plug)
    mplugs = [selection.getPlug(i) for i in range(len(plugs))]
    unit = om.MTime.uiUnit()
    control = oma.MAnimControl
    # Parallel evaluation is faster on large rigs once unrelated characters are
    # removed (_prune_unrelated); _bake re-reads frames in DG mode to confirm it.
    mode = cmds.evaluationManager(query=True, mode=True)[0]
    cmds.evaluationManager(mode="parallel")
    try:
        rows = []
        for frame in frames:
            control.setCurrentTime(om.MTime(frame, unit))
            rows.append([plug.asDouble() for plug in mplugs])
    finally:
        cmds.evaluationManager(mode=mode)
    return rows


def _open_snapshot(path):
    cmds, _, _, _ = _maya()
    for plugin in ("matrixNodes", "quatNodes", "lookdevKit", "fbxmaya"):
        cmds.loadPlugin(plugin, quiet=True)
    cmds.file(path, open=True, force=True, prompt=False, executeScriptNodes=False)
    cmds.undoInfo(stateWithoutFlush=False)


def sample_task(task_path):
    """Helper-process entry point: sample one part of the clip from the snapshot."""
    import numpy

    task = json.loads(Path(task_path).read_text(encoding="utf-8"))
    _open_snapshot(task["snapshot"])
    _prune_unrelated(task["target"], task["plugs"], task["meshes"])
    rows = _sample(task["plugs"], range(task["first"], task["last"] + 1))
    numpy.save(task["output"], numpy.array(rows))


def _available_memory():
    """Bytes of physical memory currently available, or None if unknown."""
    if os.name != "nt":
        return None
    import ctypes

    class Status(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = Status()
    status.dwLength = ctypes.sizeof(Status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return None
    return status.ullAvailPhys


def _sample_split(plugs, frames, context):
    """Sample frames, sharing long clips across helper mayapy processes.

    Rig evaluation dominates long exports and runs mostly on one core. Each
    helper opens the same snapshot (about 15 s and several GB for a large scene)
    and samples a contiguous part; this process samples the first part.
    """
    import numpy

    count = min(8, max(1, (os.cpu_count() or 1) // 4), len(frames) // 5000)
    if count >= 2 and context:
        # A helper holding a 2 GB scene used about 4.7 GB; keep a margin so
        # several exports running at once cannot exhaust memory.
        per_helper = 3 * Path(context["snapshot"]).stat().st_size
        available = _available_memory()
        if available is not None:
            count = min(count, 1 + int(available * 0.7 // max(per_helper, 1)))
    if count < 2 or not context:
        return _sample(plugs, frames), 1
    bounds = [round(len(frames) * i / count) for i in range(count + 1)]
    folder = Path(context["folder"])
    helpers = []
    try:
        for index in range(1, count):
            task = {
                "snapshot": context["snapshot"],
                "target": context["target"],
                "meshes": context["meshes"],
                "plugs": plugs,
                "first": frames[bounds[index]],
                "last": frames[bounds[index + 1] - 1],
                "output": str(folder / ("samples_%d.npy" % index)),
            }
            task_path = folder / ("sample_task_%d.json" % index)
            task_path.write_text(json.dumps(task), encoding="utf-8")
            environment = os.environ.copy()
            environment["MAYA_APP_DIR"] = str(folder / ("profile_sampler_%d" % index))
            environment["MAYA_SKIP_USERSETUP_PY"] = "1"
            log = (folder / ("sampler_%d.log" % index)).open("wb")
            process = subprocess.Popen(
                [_mayapy(), str(Path(__file__).resolve()), "--sample", str(task_path)],
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            helpers.append((process, log, task))
        rows = _sample(plugs, frames[bounds[0] : bounds[1]])
    finally:
        for process, log, _ in helpers:
            process.wait()
            log.close()
    for index, (process, _, task) in enumerate(helpers, 1):
        part = Path(task["output"])
        if process.returncode != 0 or not part.is_file():
            raise RuntimeError(
                "Sampling process %d failed (exit %s); see sampler_%d.log"
                % (index, process.returncode, index)
            )
        values = numpy.load(part)
        if values.shape != (task["last"] - task["first"] + 1, len(plugs)):
            raise RuntimeError("Sampling process %d returned wrong data" % index)
        rows.extend(values.tolist())
        part.unlink()
    return rows, count


def _bake(plugs, start, end, offset=0.0, context=None):
    """Replace each plug's input with a curve keyed on every frame.

    Equivalent to bakeResults(simulation=True, preserveOutsideKeys=False,
    disableImplicitControl=True, minimizeRotation=True) for a time-driven rig,
    but bakeResults slows down more than linearly on long ranges (220 s for
    67,685 frames vs 7 s for 10,000). Values are sampled per frame in the normal
    context and every curve is created with one addKeys call, with its keys moved
    by offset frames. Returns the sampled (min, max) per plug in internal units
    and the number of sampling processes.
    """
    import numpy

    cmds, _, om, oma = _maya()
    selection = om.MSelectionList()
    for plug in plugs:
        selection.add(plug)
    mplugs = [selection.getPlug(i) for i in range(len(plugs))]
    unit = om.MTime.uiUnit()
    frames = range(int(math.floor(start)), int(math.ceil(end)) + 1)
    if frames[0] != start or frames[-1] != end:
        raise RuntimeError("Start and end frames must be whole frames")
    rows, processes = _sample_split(plugs, frames, context)
    if len(rows) != len(frames):
        raise RuntimeError("Sampled frame count does not match the clip")
    # Re-read frames here in DG mode: confirms parallel evaluation and the helper
    # processes (including each part boundary) evaluated this rig identically.
    control = oma.MAnimControl
    checks = set(round(i * (len(frames) - 1) / 8) for i in range(9))
    checks.update(round(len(frames) * i / processes) for i in range(1, processes))
    for index in sorted(checks):
        control.setCurrentTime(om.MTime(frames[index], unit))
        error = max(
            (abs(p.asDouble() - v) for p, v in zip(mplugs, rows[index])),
            default=0.0,
        )
        if error > 1e-6:
            raise RuntimeError(
                "Sampled values differ from DG evaluation at frame %s (%g)"
                % (frames[index], error)
            )
    columns = numpy.array(rows).T
    times = om.MTimeArray([om.MTime(f + offset, unit) for f in frames])
    # Drivers may be connected to a compound (translate, shear) rather than the
    # child plug; every child of such a compound must be in the baked set.
    names = set(p.name() for p in mplugs)
    disconnected = set()
    modifier = om.MDGModifier()
    for plug in mplugs:
        for target in [plug] + ([plug.parent()] if plug.isChild else []):
            source = target.source()
            if source.isNull or target.name() in disconnected:
                continue
            disconnected.add(target.name())
            if target.isCompound:
                missing = [
                    target.child(i).name()
                    for i in range(target.numChildren())
                    if target.child(i).name() not in names
                ]
                if missing:
                    raise RuntimeError(
                        "Cannot bake part of a driven compound: " + ", ".join(missing)
                    )
            modifier.disconnect(source, target)
    modifier.doIt()
    ranges = {}
    for name, plug, column in zip(plugs, mplugs, columns):
        curve = oma.MFnAnimCurve()
        curve.create(plug)
        if curve.animCurveType == oma.MFnAnimCurve.kAnimCurveTA:
            # minimizeRotation: remove 360-degree jumps between frames, per channel.
            column = numpy.unwrap(column)
        ranges[name] = (float(column.min()), float(column.max()))
        if not all(map(math.isfinite, ranges[name])):
            raise RuntimeError("Non-finite sampled value: " + name)
        if ranges[name][1] - ranges[name][0] <= 1e-10:
            # Same result as keying every frame and reducing it afterwards.
            curve.addKey(times[0], float(column[0]))
            continue
        curve.addKeys(
            times,
            column.tolist(),
            oma.MFnAnimCurve.kTangentAuto,
            oma.MFnAnimCurve.kTangentAuto,
        )
    return ranges, processes


def _prune_unrelated(target, plugs, meshes):
    """Delete top-level hierarchies the export does not depend on.

    Only the disposable copy is changed. Other characters in the same scene cost
    evaluation time on every baked frame, especially in parallel evaluation.
    """
    cmds, _, _, _ = _maya()
    upstream = cmds.listHistory(
        list(set(p.split(".")[0] for p in plugs)) + meshes + [target]
    ) or []
    keep = set(
        n.split("|")[1] for n in cmds.ls(upstream, long=True, dag=True) + [target]
    )
    removed = []
    for top in cmds.ls(assemblies=True, long=True):
        name = top.split("|")[1]
        cameras = cmds.listRelatives(top, shapes=True, type="camera") or []
        if name in keep or (
            cameras and cmds.camera(top, query=True, startupCamera=True)
        ):
            continue
        if cmds.referenceQuery(top, isNodeReferenced=True):
            continue
        try:
            cmds.lockNode(top, lock=False)
            cmds.delete(top)
            removed.append(name)
        except RuntimeError:
            pass  # Locked or protected content simply stays.
    return removed


def _mayapy():
    return str(
        Path(os.environ["MAYA_LOCATION"])
        / "bin"
        / ("mayapy.exe" if os.name == "nt" else "mayapy")
    )


def _curve(plug_or_node):
    """MFnAnimCurve for an anim curve node name."""
    _, _, om, oma = _maya()
    selection = om.MSelectionList()
    selection.add(plug_or_node)
    return oma.MFnAnimCurve(selection.getDependNode(0))


def _curve_values(curve):
    return [curve.value(i) for i in range(curve.numKeys)]


def _export_nodes(target):
    cmds, _, _, _ = _maya()
    nodes = [target] + [
        n
        for n in (cmds.listRelatives(target, allDescendents=True, fullPath=True) or [])
        if cmds.nodeType(n) in ("transform", "joint")
    ]
    parent = cmds.listRelatives(target, parent=True, fullPath=True)
    while parent:
        nodes += parent
        parent = cmds.listRelatives(parent[0], parent=True, fullPath=True)
    return list(dict.fromkeys(nodes))


def _export_fbx(target, path):
    cmds, mel, _, _ = _maya()
    commands = [
        "FBXResetExport",
        "FBXExportAnimationOnly -v false",
        "FBXExportSkins -v true",
        "FBXExportShapes -v true",
        "FBXExportConstraints -v false",
        "FBXExportCameras -v false",
        "FBXExportLights -v false",
        "FBXExportInputConnections -v false",
        "FBXExportBakeComplexAnimation -v false",
        "FBXExportBakeResampleAnimation -v false",
        "FBXExportEmbeddedTextures -v false",
        "FBXExportInAscii -v false",
    ]
    for command in commands:
        mel.eval(command + ";")
    cmds.select(target, replace=True)
    mel.eval("FBXExport -f " + json.dumps(str(path).replace("\\", "/")) + " -s;")


def _key_rest_pose(pose, curves):
    """Key the rest pose at frame 0 without changing the clip.

    Unity builds a model's default pose (the base of a Humanoid Avatar) from the
    animation at FBX time 0 when the take covers it, otherwise at the take's first
    frame; the static FBX transforms of animated nodes are ignored (Unity 2022.3).
    The caller moves the clip to start at frame 1 and extends the take to 0.
    """
    cmds, _, om, oma = _maya()
    unit = om.MTime.uiUnit()

    def edge_times(fn):
        # The segments next to the clip ends are the only ones a new key at
        # frame 0 can influence (through recomputed auto/spline tangents).
        last = fn.numKeys - 1
        spans = [(0, min(1, last)), (max(last - 1, 0), last)]
        return [
            a + (b - a) * i / 8
            for a, b in [
                (fn.input(x).asUnits(unit), fn.input(y).asUnits(unit)) for x, y in spans
            ]
            for i in range(9)
        ]

    def sample(fn, times, shift):
        return [fn.evaluate(om.MTime(t + shift, unit)) for t in times]

    functions = {c: _curve(c) for c in curves}
    before = {}
    for curve, fn in functions.items():
        times = edge_times(fn)
        before[curve] = (times, sample(fn, times, 0.0))
    for fn in functions.values():
        for index in {0, fn.numKeys - 1}:
            angles = [fn.getTangentAngleWeight(index, side)[0] for side in (True, False)]
            fn.setTangentsLocked(index, False)
            fn.setInTangentType(index, oma.MFnAnimCurve.kTangentFixed)
            fn.setOutTangentType(index, oma.MFnAnimCurve.kTangentFixed)
            fn.setAngle(index, angles[0], True)
            fn.setAngle(index, angles[1], False)
    keyed = 0
    for plug, value in pose.items():
        source = _source(plug)
        if source:
            cmds.setKeyframe(
                source.split(".")[0],
                time=0,
                value=value,
                inTangentType="linear",
                outTangentType="step",
            )
            keyed += 1
    for curve, (times, values) in before.items():
        after = sample(functions[curve], times, 0.0)
        if max(abs(x - y) for x, y in zip(values, after)) > 1e-9:
            raise RuntimeError("Keying the rest pose changed the clip: " + curve)
    return keyed


def _repair_bind_poses(skins, nodes):
    """Add grouping transforms to pose metadata without changing joint binds."""
    cmds, _, _, _ = _maya()
    poses = set(
        p
        for skin in skins
        for p in (
            cmds.listConnections(skin + ".bindPose", source=True, destination=False)
            or []
        )
    )
    if not poses:
        raise RuntimeError(
            "Missing skin bind pose; bind-pose reconstruction is required"
        )
    added = 0
    for pose in poses:
        members = cmds.ls(cmds.dagPose(pose, query=True, members=True), long=True)
        missing = [node for node in nodes if node not in members]
        if missing:
            cmds.dagPose(missing, addToPose=True, name=pose)
            added += len(missing)
    return added


def run_job(job_path):
    """Worker entry point. Only call in a disposable Maya process."""
    cmds, mel, om, oma = _maya()
    job_path = Path(job_path)
    job = json.loads(job_path.read_text(encoding="utf-8"))
    report_path = job_path.parent / "report.json"
    report = {"status": "running"}

    clock = [time.time()]

    def stage(name, **values):
        # Seconds spent in each finished stage, to find what dominates a job.
        if "stage" in report:
            report.setdefault("stage_seconds", {})[report["stage"]] = round(
                time.time() - clock[0], 2
            )
        clock[0] = time.time()
        report["stage"] = name
        report.update(values)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("FBX_EXPORT_STAGE " + name, flush=True)

    try:
        output = Path(job["output"])
        if output.exists():
            raise RuntimeError("Output already exists; choose a new filename")
        stage("opening_snapshot")
        for plugin in ("matrixNodes", "quatNodes", "lookdevKit", "fbxmaya"):
            cmds.loadPlugin(plugin, quiet=True)
        cmds.file(
            job["snapshot"],
            open=True,
            force=True,
            prompt=False,
            executeScriptNodes=False,
        )
        cmds.undoInfo(stateWithoutFlush=False)
        targets = cmds.ls(job["root"], long=True, type="transform") or []
        if len(targets) != 1:
            raise RuntimeError("Export root must resolve to exactly one transform")
        target = targets[0]
        meshes = [
            m
            for m in (
                cmds.listRelatives(
                    target, allDescendents=True, fullPath=True, type="mesh"
                )
                or []
            )
            if not cmds.getAttr(m + ".intermediateObject")
        ]
        if not meshes:
            raise RuntimeError("Export root contains no meshes")
        start, end = float(job["start"]), float(job["end"])
        if end < start:
            raise ValueError("End frame precedes start frame")
        frames = sorted(
            set(
                [start, end]
                + [round(start + (end - start) * i / 8) for i in range(1, 8)]
            )
        )
        tolerance = float(job.get("tolerance", 0.001))
        stage(
            "capturing_reference",
            meshes=len(meshes),
            frames=[start, end],
            sample_frames=frames,
            time_unit=cmds.currentUnit(query=True, time=True),
        )
        if job.get("reference_file"):
            reference = {
                float(t): v
                for t, v in json.loads(
                    Path(job["reference_file"]).read_text(encoding="utf-8")
                ).items()
            }
            if set(reference) != set(frames):
                raise RuntimeError("Reference frames do not match the requested clip")
        else:
            reference = _capture(meshes, frames)
        if job.get("save_reference"):
            (job_path.parent / "reference.json").write_text(
                json.dumps(reference), encoding="utf-8"
            )
        # The FBX default pose (what Unity builds a Humanoid Avatar from). Record
        # it from the untouched rig: keys outside the clip are removed later.
        rest_frame = float(job.get("rest_frame", start))
        report["rest_frame"] = rest_frame
        cmds.currentTime(rest_frame)
        rest_matrices = {n: cmds.getAttr(n + ".matrix") for n in _export_nodes(target)}
        rest_pose = {
            n + "." + a: cmds.getAttr(n + "." + a)
            for n in rest_matrices
            for a in ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz")
        }
        rest_pose.update(
            {
                n + "." + a: cmds.getAttr(n + "." + a)
                for n in set(
                    h
                    for m in meshes
                    for h in (cmds.listHistory(m) or [])
                    if cmds.nodeType(h) == "blendShape"
                )
                for a in (cmds.aliasAttr(n, query=True) or [])[::2]
            }
        )
        cmds.currentTime(start)
        stage("cleaning_topology")
        repaired = [m for m in meshes if _clean_deleted_topology(m)]
        report["repaired_meshes"] = repaired
        report["history_max_error"] = _check_capture(
            reference, {m: m for m in meshes}, tolerance
        )
        nodes = _export_nodes(target)
        skins = sorted(
            set(
                n
                for m in meshes
                for n in (cmds.listHistory(m) or [])
                if cmds.nodeType(n) == "skinCluster"
            )
        )
        shapes = sorted(
            set(
                n
                for m in meshes
                for n in (cmds.listHistory(m) or [])
                if cmds.nodeType(n) == "blendShape"
            )
        )
        for skin in skins:
            for influence in cmds.ls(
                cmds.skinCluster(skin, query=True, influence=True), long=True
            ):
                if influence not in nodes:
                    raise RuntimeError(
                        "Select a root containing every skin influence: " + influence
                    )
        identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        for node in nodes:
            if (
                _source(node + ".offsetParentMatrix")
                or max(
                    abs(a - b)
                    for a, b in zip(
                        cmds.getAttr(node + ".offsetParentMatrix"), identity
                    )
                )
                > 1e-9
            ):
                raise RuntimeError(
                    "Export transform uses offsetParentMatrix; conversion is required: "
                    + node
                )
        plugs = [
            n + "." + a
            for n in nodes
            for a in ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz")
        ]
        shape_aliases = {n: (cmds.aliasAttr(n, query=True) or [])[::2] for n in shapes}
        plugs += [
            n + "." + a
            for n in shapes
            for a in (cmds.aliasAttr(n, query=True) or [])[1::2]
        ]
        shear_plugs = [
            n + "." + a
            for n in nodes
            for a in ("shearXY", "shearXZ", "shearYZ")
            if _source(n + "." + a) or cmds.getAttr(n + "." + a) != 0
        ]
        plugs += shear_plugs
        unsupported = [
            p
            for p in plugs
            if _source(p)
            and not cmds.nodeType(_source(p).split(".")[0]).startswith("animCurveT")
        ]
        # Sample driven shear even when directly keyed: FBX cannot retain shear.
        unsupported += [p for p in shear_plugs if _source(p) and p not in unsupported]
        stage(
            "baking_animation",
            baked_attributes=len(unsupported),
            joints=sum(cmds.nodeType(n) == "joint" for n in nodes),
            blendshape_targets=sum(map(len, shape_aliases.values())),
        )
        report["pruned_hierarchies"] = _prune_unrelated(target, plugs, meshes)
        started = time.time()
        # Sampled (min, max) per baked plug, in internal units.
        # With a rest pose, Unity reads it at frame 0 (see _key_rest_pose), so the
        # clip is moved to start at frame 1 while baking.
        offset = 1 - start if "rest_frame" in job else 0.0
        baked_ranges, processes = (
            _bake(
                unsupported,
                start,
                end,
                offset,
                {
                    "folder": str(job_path.parent),
                    "snapshot": job["snapshot"],
                    "target": target,
                    "meshes": meshes,
                },
            )
            if unsupported
            else ({}, 0)
        )
        report["sampling_processes"] = processes
        report["bake_seconds"] = time.time() - started
        max_shear = 0.0
        for plug in shear_plugs:
            values = baked_ranges.get(plug) or [cmds.getAttr(plug)]
            if not all(math.isfinite(value) for value in values):
                raise RuntimeError("Non-finite shear animation: " + plug)
            magnitude = max(abs(value) for value in values)
            max_shear = max(max_shear, magnitude)
            if magnitude > 1e-5:
                raise RuntimeError(
                    "FBX cannot preserve shear above numerical noise: " + plug
                )
        # A baked child can override a still-connected compound. Disconnect the
        # compound first so removing a child curve cannot expose that old driver.
        for compound in {p.rsplit(".", 1)[0] + ".shear" for p in shear_plugs}:
            cmds.setAttr(compound, lock=False)
            if cmds.connectionInfo(compound, isExactDestination=True):
                source = cmds.connectionInfo(compound, sourceFromDestination=True)
                if source:
                    cmds.disconnectAttr(source, compound)
        for plug in shear_plugs:
            # Only the disposable copy is changed; the deformation checks below
            # independently limit the effect of clearing this numerical noise.
            destination = cmds.connectionInfo(plug, getExactDestination=True)
            source = _source(plug)
            cmds.setAttr(plug, lock=False)
            if source:
                cmds.disconnectAttr(source, destination)
            cmds.setAttr(plug, 0)
        report["cleared_shear_channels"] = len(shear_plugs)
        report["max_sampled_shear"] = max_shear
        # The FBX plug-in warns about constraints anywhere in the scene, even
        # outside the selection. They are obsolete in this disposable baked scene.
        obsolete = (cmds.ls(type="constraint") or []) + (cmds.ls(type="ikHandle") or [])
        if obsolete:
            cmds.delete(obsolete)
        # Move directly keyed channels with the baked ones.
        keyed_curves = sorted(
            set(
                _source(p).split(".")[0]
                for p in plugs
                if _source(p) and p not in baked_ranges
            )
        )
        if offset and keyed_curves:
            cmds.keyframe(keyed_curves, edit=True, relative=True, timeChange=offset)
        report["bake_max_error"] = _check_capture(
            reference, {m: m for m in meshes}, tolerance, offset
        )
        start, end = start + offset, end + offset
        remaining = [
            p
            for p in plugs
            if _source(p)
            and not cmds.nodeType(_source(p).split(".")[0]).startswith("animCurveT")
        ]
        if remaining:
            raise RuntimeError(
                "Unsupported animation remains after bake: " + ", ".join(remaining[:10])
            )
        cmds.currentTime(start)
        report["added_pose_entries"] = _repair_bind_poses(skins, nodes)
        cmds.playbackOptions(
            minTime=start, maxTime=end, animationStartTime=start, animationEndTime=end
        )
        # Restrict directly keyed channels too: FBX otherwise includes keys outside
        # the requested clip even when the playback range has been changed.
        # Baked channels already hold exactly the clip; only keyed ones need it.
        baked = set(unsupported)
        animated = [p for p in plugs if _source(p) and p not in baked]
        for boundary in (start, end):
            cmds.currentTime(boundary)
            for plug in animated:
                cmds.setKeyframe(plug, time=boundary, insert=True)
        if animated:
            cmds.cutKey(animated, time=(-1e10, start - 0.0001), clear=True)
            cmds.cutKey(animated, time=(end + 0.0001, 1e10), clear=True)
        constant_count = sum(hi - lo <= 1e-10 for lo, hi in baked_ranges.values())
        for plug in animated:
            source = _source(plug)
            if not source:
                continue
            values = _curve_values(_curve(source.split(".")[0]))
            if values and max(values) - min(values) <= 1e-10:
                cmds.cutKey(
                    source.split(".")[0], time=(start + 0.0001, 1e10), clear=True
                )
                constant_count += 1
        report["constant_channels_reduced"] = constant_count
        if "rest_frame" in job:
            curves = sorted(
                set(_source(p).split(".")[0] for p in plugs if _source(p))
            )
            report["clip_offset_frames"] = offset
            report["exported_clip"] = [start, end]
            report["rest_keys"] = _key_rest_pose(rest_pose, curves)
            cmds.playbackOptions(
                minTime=0, maxTime=end, animationStartTime=0, animationEndTime=end
            )
        report["prepared_max_error_cm"] = _check_capture(
            reference, {m: m for m in meshes}, tolerance, offset
        )
        if "rest_frame" in job:
            # Compare matrices: baking may choose equivalent Euler values (+360).
            cmds.currentTime(0)
            rest_error = max(
                [
                    abs(a - b)
                    for n, m in rest_matrices.items()
                    for a, b in zip(cmds.getAttr(n + ".matrix"), m)
                ]
                + [
                    abs(cmds.getAttr(p) - v)
                    for p, v in rest_pose.items()
                    if p.split(".")[0] not in rest_matrices
                ]
            )
            report["rest_pose_max_error"] = rest_error
            if rest_error > 1e-5:
                raise RuntimeError(
                    "Rest pose could not be reproduced at frame 0 (error %g)"
                    % rest_error
                )
        else:
            cmds.currentTime(start)
        stage("writing_fbx")
        temporary_fbx = job_path.parent / "candidate.fbx"
        _export_fbx(target, temporary_fbx)
        # Reimport in a fresh scene before publishing the candidate file.
        stage("roundtrip_validation")
        cmds.file(new=True, force=True)
        mel.eval("FBXResetImport;")
        mel.eval(
            "FBXImport -f " + json.dumps(str(temporary_fbx).replace("\\", "/")) + ";"
        )
        mesh_map = {}
        import_renames = {}
        for mesh in meshes:
            transform_name = mesh.rsplit("|", 2)[-2]
            transforms = cmds.ls(transform_name, long=True, type="transform") or []
            candidates = [
                m
                for t in transforms
                for m in (
                    cmds.listRelatives(
                        t, shapes=True, fullPath=True, noIntermediate=True, type="mesh"
                    )
                    or []
                )
            ]
            if not candidates:
                # Maya can append a numeric suffix when an FBX material already
                # claimed a mesh transform's name. Require matching parent and
                # vertex count, then verify the actual deformation as usual.
                parent = mesh.rsplit("|", 2)[0]
                expected_count = len(reference[frames[0]][mesh])
                renamed = [
                    t
                    for t in (
                        cmds.ls(transform_name + "*", long=True, type="transform") or []
                    )
                    if t.rsplit("|", 1)[0] == parent
                    and re.fullmatch(
                        re.escape(transform_name) + r"\d+", t.rsplit("|", 1)[-1]
                    )
                ]
                candidates = [
                    m
                    for t in renamed
                    for m in (
                        cmds.listRelatives(
                            t,
                            shapes=True,
                            fullPath=True,
                            noIntermediate=True,
                            type="mesh",
                        )
                        or []
                    )
                    if cmds.polyEvaluate(m, vertex=True) == expected_count
                ]
                if len(candidates) == 1:
                    import_renames[mesh] = candidates[0]
            if len(candidates) != 1:
                raise RuntimeError(
                    "Missing or ambiguous mesh after FBX import: " + transform_name
                )
            mesh_map[mesh] = candidates[0]
        if len(set(mesh_map.values())) != len(mesh_map):
            raise RuntimeError("Multiple source meshes mapped to one imported mesh")
        report["import_mesh_renames"] = import_renames
        report["roundtrip_tolerance_cm"] = float(job.get("roundtrip_tolerance_cm", 0.1))
        report["roundtrip_max_error_cm"] = _check_capture(
            reference, mesh_map, report["roundtrip_tolerance_cm"], offset
        )
        if "rest_frame" in job:
            # The pose Unity will see: the imported animation at frame 0.
            # Names imported from FBX keep characters Maya cannot use as
            # FBXASCnnn in both scenes, so short names still correspond.
            cmds.currentTime(0)
            rest_error = 0.0
            for node, matrix in rest_matrices.items():
                if cmds.nodeType(node) != "joint":
                    continue
                imported = cmds.ls(node.rsplit("|", 1)[-1], long=True, type="joint")
                if len(imported) != 1:
                    raise RuntimeError(
                        "Joint missing or ambiguous after FBX import: " + node
                    )
                rest_error = max(
                    [rest_error]
                    + [
                        abs(a - b)
                        for a, b in zip(cmds.getAttr(imported[0] + ".matrix"), matrix)
                    ]
                )
            report["rest_pose_fbx_max_error"] = rest_error
            if rest_error > 1e-3:
                raise RuntimeError(
                    "FBX pose at frame 0 differs from the rest pose (error %g)"
                    % rest_error
                )
        actual_aliases = [
            (cmds.aliasAttr(n, query=True) or [])[::2]
            for n in cmds.ls(type="blendShape")
        ]
        if sorted(sum(shape_aliases.values(), [])) != sorted(sum(actual_aliases, [])):
            raise RuntimeError("Blendshape target names changed during FBX roundtrip")
        output.parent.mkdir(parents=True, exist_ok=True)
        _publish(temporary_fbx, output)
        report["status"] = "complete"
        stage("complete", output=str(output), bytes=output.stat().st_size)
    except Exception:
        report["status"] = "failed"
        stage("failed", error=traceback.format_exc())
        raise
    return report


def launch(root, output, start, end, rest_frame=None):
    """Snapshot the current scene and launch a separate worker; return job folder.

    rest_frame: the frame whose pose Unity should use as the default pose (the
    base of a Humanoid Avatar). It is keyed at frame 0 and the clip is moved to
    start at frame 1. It may lie outside the clip. None keeps the clip's frames.
    """
    cmds, _, _, _ = _maya()
    output = Path(output).resolve()
    if output.exists():
        raise RuntimeError(
            "Choose a new FBX filename; existing exports are never overwritten"
        )
    roots = cmds.ls(root, long=True, type="transform") or []
    if len(roots) != 1:
        raise RuntimeError("Choose one geometry/skeleton root")
    folder = Path(tempfile.gettempdir()) / (
        "maya_unity_fbx_" + time.strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
    )
    folder.mkdir()
    snapshot = folder / "source_snapshot.mb"
    original_name = cmds.file(query=True, sceneName=True)
    if original_name and Path(original_name).is_file():
        backup = folder / ("saved_original" + Path(original_name).suffix)
        shutil.copy2(original_name, backup)
        if backup.stat().st_size != Path(original_name).stat().st_size:
            raise RuntimeError("Saved-scene backup size mismatch")
    cmds.file(
        str(snapshot),
        exportAll=True,
        type="mayaBinary",
        preserveReferences=True,
        force=False,
    )
    if not snapshot.is_file() or snapshot.stat().st_size == 0:
        raise RuntimeError("Current-scene snapshot failed")
    job = {
        "snapshot": str(snapshot),
        "root": roots[0],
        "output": str(output),
        "start": float(start),
        "end": float(end),
    }
    if rest_frame is not None:
        job["rest_frame"] = float(rest_frame)
    job_path = folder / "job.json"
    job_path.write_text(json.dumps(job, indent=2), encoding="utf-8")
    mayapy = _mayapy()
    environment = os.environ.copy()
    environment["MAYA_APP_DIR"] = str(folder / "profile")
    environment["MAYA_SKIP_USERSETUP_PY"] = "1"
    with (folder / "worker.log").open("wb") as log:
        process = subprocess.Popen(
            [str(mayapy), str(Path(__file__).resolve()), str(job_path)],
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    (folder / "pid.txt").write_text(str(process.pid))
    _jobs[str(folder)] = {
        "folder": folder,
        "output": str(output),
        "root": roots[0],
        "started": time.monotonic(),
        "process": process,
        "report": {"status": "running", "stage": "starting"},
    }
    return folder


def _refresh_jobs():
    """Poll every worker without opening modal UI or changing the source scene."""
    for job in _jobs.values():
        if job["report"].get("status") in ("complete", "failed"):
            continue
        report_file = job["folder"] / "report.json"
        try:
            job["report"] = json.loads(report_file.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            pass  # The worker may be starting or replacing its report.
        process = job.get("process")
        if (
            process is not None
            and process.poll() is not None
            and job["report"].get("status") not in ("complete", "failed")
        ):
            job["report"] = {
                "status": "failed",
                "stage": "failed",
                "error": "Worker exited without a final report (exit code %s). See worker.log."
                % process.returncode,
            }
        if job["report"].get("status") in ("complete", "failed"):
            job["finished"] = time.monotonic()
    if _job_window is not None:
        _job_window.refresh()
    if _job_timer is not None and all(
        j["report"].get("status") in ("complete", "failed") for j in _jobs.values()
    ):
        _job_timer.stop()


def show_jobs(*_):
    """A persistent, non-modal overview for concurrent exports."""
    global _job_window, _job_timer
    from maya import OpenMayaUI
    from PySide6 import QtCore, QtWidgets
    from shiboken6 import wrapInstance

    if _job_window is None:

        class JobWindow(QtWidgets.QDialog):
            def __init__(self):
                parent = wrapInstance(
                    int(OpenMayaUI.MQtUtil.mainWindow()), QtWidgets.QWidget
                )
                super().__init__(parent)
                self.setWindowTitle("Unity FBX - 書き出し状況")
                self.resize(900, 400)
                layout = QtWidgets.QVBoxLayout(self)
                layout.addWidget(
                    QtWidgets.QLabel(
                        "各ジョブの処理段階と経過時間を表示します。全体の完了率ではありません。"
                    )
                )
                self.table = QtWidgets.QTableWidget(0, 4)
                self.table.setHorizontalHeaderLabels(
                    ["出力ファイル", "対象", "処理段階", "経過時間"]
                )
                self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
                self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
                self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
                self.table.horizontalHeader().setSectionResizeMode(
                    QtWidgets.QHeaderView.Stretch
                )
                layout.addWidget(self.table)
                self.details = QtWidgets.QPlainTextEdit()
                self.details.setReadOnly(True)
                self.details.setMaximumHeight(120)
                layout.addWidget(self.details)
                row = QtWidgets.QHBoxLayout()
                for label, filename in [
                    ("ジョブフォルダを開く", None),
                    ("ログを開く", "worker.log"),
                ]:
                    button = QtWidgets.QPushButton(label)
                    button.clicked.connect(
                        lambda checked=False, f=filename: self.open_path(f)
                    )
                    row.addWidget(button)
                layout.addLayout(row)
                self.table.itemSelectionChanged.connect(self.update_details)

            def selected_job(self):
                row = self.table.currentRow()
                return list(_jobs.values())[row] if 0 <= row < len(_jobs) else None

            def update_details(self):
                job = self.selected_job()
                if job:
                    self.details.setPlainText(
                        "出力: "
                        + job["output"]
                        + "\nジョブ: "
                        + str(job["folder"])
                        + "\n"
                        + job["report"].get("error", "")
                    )

            def open_path(self, filename):
                from PySide6 import QtGui

                job = self.selected_job()
                if job:
                    path = job["folder"] / filename if filename else job["folder"]
                    QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path)))

            def refresh(self):
                labels = {
                    "starting": "ワーカー起動中",
                    "opening_snapshot": "シーン読み込み中",
                    "capturing_reference": "元の変形を記録中",
                    "cleaning_topology": "履歴整理中",
                    "baking_animation": "アニメーションのベイク中",
                    "writing_fbx": "FBX出力中",
                    "roundtrip_validation": "再読み込み・検証中",
                    "complete": "完了",
                    "failed": "失敗",
                }
                self.table.setRowCount(len(_jobs))
                for row, job in enumerate(_jobs.values()):
                    elapsed = max(
                        0, int(job.get("finished", time.monotonic()) - job["started"])
                    )
                    stage = job["report"].get("stage", "starting")
                    values = [
                        Path(job["output"]).name,
                        job["root"],
                        labels.get(stage, stage),
                        "%02d:%02d:%02d"
                        % (elapsed // 3600, elapsed // 60 % 60, elapsed % 60),
                    ]
                    for column, value in enumerate(values):
                        item = self.table.item(row, column)
                        if item is None:
                            item = QtWidgets.QTableWidgetItem()
                            self.table.setItem(row, column, item)
                        item.setText(value)
                        item.setToolTip(value)
                if self.table.currentRow() < 0 and _jobs:
                    self.table.selectRow(len(_jobs) - 1)
                self.update_details()

        _job_window = JobWindow()
    if _job_timer is None:
        _job_timer = QtCore.QTimer(_job_window)
        _job_timer.timeout.connect(_refresh_jobs)
    _job_timer.start(1000)
    _refresh_jobs()
    _job_window.show()
    _job_window.raise_()
    return _job_window


def show():
    cmds, _, _, _ = _maya()
    name = "ARFHUnityFbxExport"
    if cmds.window(name, exists=True):
        cmds.deleteUI(name)
    window = cmds.window(
        name, title="Unity FBX Export (isolated copy)", widthHeight=(560, 280)
    )
    cmds.columnLayout(adjustableColumn=True, rowSpacing=10)
    cmds.text(
        label="Select a root containing geometry and its skin skeleton.\nThe source scene is preserved; baking runs in a separate process.",
        align="left",
    )
    cmds.text(
        label="FBX roundtrip: maximum allowed position difference 1 mm (sampled).",
        align="left",
    )
    selected = cmds.ls(selection=True, long=True, type="transform") or []
    root_field = cmds.textFieldButtonGrp(
        label="Export root",
        text=selected[0] if selected else "",
        buttonLabel="Use selection",
    )

    def use_selection(*_):
        selected = cmds.ls(selection=True, long=True, type="transform") or []
        if len(selected) != 1:
            raise RuntimeError("Select one root transform")
        cmds.textFieldButtonGrp(root_field, edit=True, text=selected[0])

    cmds.textFieldButtonGrp(root_field, edit=True, buttonCommand=use_selection)
    range_field = cmds.floatFieldGrp(
        numberOfFields=2,
        label="Start / End",
        value1=cmds.playbackOptions(query=True, minTime=True),
        value2=cmds.playbackOptions(query=True, maxTime=True),
    )
    # Remembered across sessions: the rest pose frame is usually fixed per project.
    rest_enabled = bool(cmds.optionVar(query="ARFHUnityFbxRestFrameEnabled"))
    rest_field = cmds.floatFieldGrp(
        numberOfFields=1,
        label="Rest pose frame",
        value1=(
            cmds.optionVar(query="ARFHUnityFbxRestFrame")
            if cmds.optionVar(exists="ARFHUnityFbxRestFrame")
            else 0.0
        ),
        enable=rest_enabled,
        annotation="このフレームのポーズを0フレームに置き、アニメーションを1フレーム"
        "から始まるように移動します(UnityのHumanoid設定の基準)。範囲外も指定できます。",
    )
    cmds.checkBox(
        label="Specify rest pose frame (off: start frame)",
        value=rest_enabled,
        changeCommand=lambda value: cmds.floatFieldGrp(
            rest_field, edit=True, enable=value
        ),
    )
    status = cmds.text(label="Ready", align="left", wordWrap=True)

    def export(*_):
        paths = cmds.fileDialog2(
            fileMode=0, caption="New FBX output", fileFilter="FBX (*.fbx)"
        )
        if not paths:
            return
        use_rest = cmds.floatFieldGrp(rest_field, query=True, enable=True)
        rest_frame = cmds.floatFieldGrp(rest_field, query=True, value1=True)
        cmds.optionVar(intValue=("ARFHUnityFbxRestFrameEnabled", int(use_rest)))
        cmds.optionVar(floatValue=("ARFHUnityFbxRestFrame", rest_frame))
        folder = launch(
            cmds.textFieldButtonGrp(root_field, query=True, text=True),
            paths[0],
            cmds.floatFieldGrp(range_field, query=True, value1=True),
            cmds.floatFieldGrp(range_field, query=True, value2=True),
            rest_frame if use_rest else None,
        )
        cmds.text(
            status,
            edit=True,
            label="Export running. Backup, status and log:\n" + str(folder),
        )
        print("Unity FBX export job: " + str(folder))
        show_jobs()

    cmds.button(label="Export and verify on a copy", command=export, height=35)
    cmds.button(label="書き出し状況を表示", command=show_jobs, height=30)
    cmds.showWindow(window)
    return window


# Keep active jobs when this module is reloaded in a running Maya session.
_jobs = globals().get("_jobs", {})
_job_window = globals().get("_job_window")
_job_timer = globals().get("_job_timer")

if __name__ == "__main__":
    import maya.standalone

    maya.standalone.initialize(name="python")
    try:
        if sys.argv[1] == "--sample":
            sample_task(sys.argv[2])
        else:
            run_job(sys.argv[1])
        code = 0
    except Exception:
        traceback.print_exc()
        code = 1
    # The report is final. maya.standalone.uninitialize() and even os._exit can
    # crash in plug-in unload handlers (Maya 2026, large scenes), which starts
    # Maya's crash handler; leave without any shutdown sequence.
    sys.stdout.flush()
    sys.stderr.flush()
    if os.name == "nt":
        # os._exit still runs DLL unload handlers, where the crash occurs.
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.windll.kernel32
        # Without these, the 64-bit pseudo handle is truncated and the call fails.
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        kernel.TerminateProcess.argtypes = (wintypes.HANDLE, wintypes.UINT)
        kernel.TerminateProcess(kernel.GetCurrentProcess(), code)
    os._exit(code)
