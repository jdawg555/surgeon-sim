#if UNITY_EDITOR
using UnityEditor;
using UnityEngine;
using Dragonfly.XR.Cases;

namespace Dragonfly.XR.EditorTools
{
    // Tools > Dragonfly > Load Case from Disk...
    // Picks a case directory (containing manifest.json + meshes/) and
    // loads it into the active scene under a host GameObject. Useful to
    // confirm glTFast + the manifest schema work end-to-end without
    // launching the headset.
    public static class CaseLoaderEditorTest
    {
        const string HostName = "__case_loader_test";

        [MenuItem("Tools/Dragonfly/Load Case from Disk...")]
        public static async void LoadCaseFromDisk()
        {
            var dir = EditorUtility.OpenFolderPanel(
                "Pick a case directory (must contain manifest.json)", "", "");
            if (string.IsNullOrEmpty(dir)) return;

            var host = GameObject.Find(HostName);
            if (host == null) host = new GameObject(HostName);
            var loader = host.GetComponent<CaseLoader>();
            if (loader == null) loader = host.AddComponent<CaseLoader>();
            loader.LogStructureBounds = true;

            var ok = await loader.LoadCaseAsync(dir);
            if (ok)
            {
                Debug.Log($"[CaseLoader] OK loaded case from {dir}");
                Selection.activeGameObject = host;
                EditorGUIUtility.PingObject(host);
            }
            else
            {
                Debug.LogError($"[CaseLoader] failed to load case from {dir}");
            }
        }

        [MenuItem("Tools/Dragonfly/Clear Loaded Case")]
        public static void ClearLoadedCase()
        {
            var host = GameObject.Find(HostName);
            if (host == null) return;
            var loader = host.GetComponent<CaseLoader>();
            if (loader != null) loader.ClearLoaded();
            Object.DestroyImmediate(host);
            Debug.Log("[CaseLoader] cleared");
        }
    }
}
#endif
