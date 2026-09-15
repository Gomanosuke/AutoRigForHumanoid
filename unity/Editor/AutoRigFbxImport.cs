using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

// Put this file in an Editor folder. The menu applies only to selected FBX assets.
public static class AutoRigFbxImport
{
    private const string Menu = "Assets/AutoRig/Use Source Animation (Generic)";

    [MenuItem(Menu, true)]
    private static bool CanApply()
    {
        return Selection.objects.Any(o => AssetImporter.GetAtPath(
            AssetDatabase.GetAssetPath(o)) is ModelImporter);
    }

    [MenuItem(Menu)]
    private static void Apply()
    {
        var folder = Path.Combine("Library", "AutoRigFbxBackups",
            DateTime.Now.ToString("yyyyMMdd_HHmmss") + "_" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(folder);
        foreach (var path in Selection.objects.Select(AssetDatabase.GetAssetPath).Distinct())
        {
            var importer = AssetImporter.GetAtPath(path) as ModelImporter;
            if (importer == null) continue;
            var meta = path + ".meta";
            var backup = Path.Combine(folder, AssetDatabase.AssetPathToGUID(path) + ".meta");
            File.Copy(meta, backup, false);
            if (new FileInfo(meta).Length != new FileInfo(backup).Length)
                throw new IOException("Importer backup verification failed");

            importer.animationType = ModelImporterAnimationType.Generic;
            importer.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
            importer.importAnimation = true;
            importer.importBlendShapes = true;
            importer.importConstraints = false;
            importer.importCameras = false;
            importer.importLights = false;
            importer.animationCompression = ModelImporterAnimationCompression.Off;
            importer.resampleCurves = false;
            importer.optimizeGameObjects = false;
            importer.preserveHierarchy = true;
            importer.skinWeights = ModelImporterSkinWeights.Custom;
            importer.maxBonesPerVertex = 255;
            importer.minBoneWeight = 0;
            importer.SaveAndReimport();
            Debug.Log("Applied source-animation FBX settings: " + path +
                      "\nPrevious importer settings: " + backup);
        }
    }
}
