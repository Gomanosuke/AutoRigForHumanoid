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


def _key_rest_pose(pose, curves, offset):
    """Move the clip by offset frames and key the rest pose at frame 0.

    Unity builds a model's default pose (the base of a Humanoid Avatar) from the
    animation at FBX time 0 when the take covers it, otherwise at the take's first
    frame; the static FBX transforms of animated nodes are ignored (Unity 2022.3).
    The clip is moved to start at frame 1 and the take is extended to frame 0.
    """
    cmds, _, _, _ = _maya()

    def edge_samples(curve, shift):
        # The segments next to the clip ends are the only ones a new key at
        # frame 0 can influence (through recomputed auto/spline tangents).
        times = cmds.keyframe(curve, query=True, timeChange=True)
        spans = [(times[0], times[min(1, len(times) - 1)]),
                 (times[max(len(times) - 2, 0)], times[-1])]
        return [
            cmds.keyframe(curve, query=True, eval=True, time=(t + shift, t + shift))[0]
            for a, b in spans
            for t in [a + (b - a) * i / 8 for i in range(9)]
        ], times

    before = {c: edge_samples(c, 0.0) for c in curves}
    if offset:
        cmds.keyframe(curves, edit=True, relative=True, timeChange=offset)
    for curve in curves:
        count = cmds.keyframe(curve, query=True, keyframeCount=True)
        for index in {0, count - 1}:
            angles = {
                flag: cmds.keyTangent(
                    curve, index=(index, index), query=True, **{flag: True}
                )[0]
                for flag in ("inAngle", "outAngle")
            }
            cmds.keyTangent(curve, index=(index, index), lock=False)
            cmds.keyTangent(
                curve,
                index=(index, index),
                inTangentType="fixed",
                outTangentType="fixed",
            )
            cmds.keyTangent(curve, index=(index, index), **angles)
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
    for curve, (values, times) in before.items():
        after = [
            cmds.keyframe(curve, query=True, eval=True, time=(t, t))[0]
            for a, b in [(times[0], times[min(1, len(times) - 1)]),
                         (times[max(len(times) - 2, 0)], times[-1])]
            for t in [a + offset + (b - a) * i / 8 for i in range(9)]
        ]
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
        offset = 0.0
        if "rest_frame" in job:
            # Unity reads the default pose at frame 0; see _key_rest_pose.
            offset = 1 - start
            curves = sorted(
                set(_source(p).split(".")[0] for p in plugs if _source(p))
            )
            report["clip_offset_frames"] = offset
            report["exported_clip"] = [start + offset, end + offset]
            report["rest_keys"] = _key_rest_pose(rest_pose, curves, offset)
            cmds.playbackOptions(
                minTime=0,
                maxTime=end + offset,
                animationStartTime=0,
                animationEndTime=end + offset,
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
        run_job(sys.argv[1])
    finally:
        maya.standalone.uninitialize()
