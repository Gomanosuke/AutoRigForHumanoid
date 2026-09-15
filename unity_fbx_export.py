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


def _check_capture(reference, meshes, tolerance):
    cmds, _, _, _ = _maya()
    worst = 0.0
    for frame, expected in reference.items():
        cmds.currentTime(frame)
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

    def stage(name, **values):
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
        started = time.time()
        if unsupported:
            cmds.bakeResults(
                unsupported,
                time=(start, end),
                sampleBy=1,
                simulation=True,
                preserveOutsideKeys=False,
                sparseAnimCurveBake=False,
                disableImplicitControl=True,
                minimizeRotation=True,
            )
        report["bake_seconds"] = time.time() - started
        max_shear = 0.0
        for plug in shear_plugs:
            values = cmds.keyframe(plug, query=True, valueChange=True) or [
                cmds.getAttr(plug)
            ]
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
        report["bake_max_error"] = _check_capture(
            reference, {m: m for m in meshes}, tolerance
        )
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
        animated = [p for p in plugs if _source(p)]
        for boundary in (start, end):
            cmds.currentTime(boundary)
            for plug in animated:
                cmds.setKeyframe(plug, time=boundary, insert=True)
        if animated:
            cmds.cutKey(animated, time=(-1e10, start - 0.0001), clear=True)
            cmds.cutKey(animated, time=(end + 0.0001, 1e10), clear=True)
        constant_count = 0
        for plug in animated:
            source = _source(plug)
            if not source:
                continue
            values = cmds.keyframe(plug, query=True, valueChange=True) or []
            if values and max(values) - min(values) <= 1e-10:
                cmds.cutKey(
                    source.split(".")[0], time=(start + 0.0001, 1e10), clear=True
                )
                constant_count += 1
        report["constant_channels_reduced"] = constant_count
        report["prepared_max_error_cm"] = _check_capture(
            reference, {m: m for m in meshes}, tolerance
        )
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
            reference, mesh_map, report["roundtrip_tolerance_cm"]
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


def launch(root, output, start, end):
    """Snapshot the current scene and launch a separate worker; return job folder."""
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
    job_path = folder / "job.json"
    job_path.write_text(json.dumps(job, indent=2), encoding="utf-8")
    mayapy = (
        Path(os.environ["MAYA_LOCATION"])
        / "bin"
        / ("mayapy.exe" if os.name == "nt" else "mayapy")
    )
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
    return folder


def show():
    cmds, _, _, _ = _maya()
    name = "ARFHUnityFbxExport"
    if cmds.window(name, exists=True):
        cmds.deleteUI(name)
    window = cmds.window(
        name, title="Unity FBX Export (isolated copy)", widthHeight=(560, 240)
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
    status = cmds.text(label="Ready", align="left", wordWrap=True)

    def export(*_):
        paths = cmds.fileDialog2(
            fileMode=0, caption="New FBX output", fileFilter="FBX (*.fbx)"
        )
        if not paths:
            return
        folder = launch(
            cmds.textFieldButtonGrp(root_field, query=True, text=True),
            paths[0],
            cmds.floatFieldGrp(range_field, query=True, value1=True),
            cmds.floatFieldGrp(range_field, query=True, value2=True),
        )
        cmds.text(
            status,
            edit=True,
            label="Export running. Backup, status and log:\n" + str(folder),
        )
        print("Unity FBX export job: " + str(folder))
        from PySide6 import QtCore

        timer = QtCore.QTimer()

        def poll():
            report_file = folder / "report.json"
            if not report_file.exists():
                return
            try:
                report = json.loads(report_file.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                return
            if cmds.control(status, exists=True):
                cmds.text(
                    status,
                    edit=True,
                    label=report.get("stage", "running") + "\n" + str(folder),
                )
            if report.get("status") in ("complete", "failed"):
                timer.stop()
                if report["status"] == "complete":
                    cmds.confirmDialog(
                        title="FBX export complete", message=report["output"]
                    )
                else:
                    cmds.warning("FBX export failed. See " + str(report_file))

        timer.timeout.connect(poll)
        timer.start(2000)
        _timers.append(timer)

    cmds.button(label="Export and verify on a copy", command=export, height=35)
    cmds.showWindow(window)
    return window


_timers = []

if __name__ == "__main__":
    import maya.standalone

    maya.standalone.initialize(name="python")
    try:
        run_job(sys.argv[1])
    finally:
        maya.standalone.uninitialize()
