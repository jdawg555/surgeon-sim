using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using GLTFast;
using UnityEngine;
using Dragonfly.XR.Domain;

namespace Dragonfly.XR.Cases
{
    // Loads a case directory produced by python/case_pipeline into the
    // current scene. Each structure becomes a child GameObject named after
    // its manifest entry, parented to this MonoBehaviour's transform.
    //
    // Loading is async because glTFast is async; callers should await
    // LoadCaseAsync before assuming geometry is in the hierarchy. The
    // Quest runtime will eventually wrap this in an Addressables flow but
    // for development and editor verification a directory path is enough.
    public class CaseLoader : MonoBehaviour
    {
        [Tooltip("Optional. If unset, glTFast's default material stays.")]
        public CaseMaterialMap MaterialMap;

        [Tooltip("Log per-structure AABB after load. Useful for sanity " +
                 "checking pathology variants without inspecting meshes by hand.")]
        public bool LogStructureBounds;

        public CaseManifest LoadedManifest { get; private set; }

        readonly List<GameObject> _loaded = new();
        public IReadOnlyList<GameObject> LoadedStructures => _loaded;

        public async Task<bool> LoadCaseAsync(string caseDirAbsolute)
        {
            ClearLoaded();

            var manifestPath = Path.Combine(caseDirAbsolute, "manifest.json");
            if (!File.Exists(manifestPath))
            {
                Debug.LogError($"[CaseLoader] manifest.json missing at {manifestPath}");
                return false;
            }

            var json = await File.ReadAllTextAsync(manifestPath);
            LoadedManifest = JsonUtility.FromJson<CaseManifest>(json);
            if (LoadedManifest == null || LoadedManifest.structures == null)
            {
                Debug.LogError($"[CaseLoader] failed to parse {manifestPath}");
                return false;
            }

            Debug.Log(
                $"[CaseLoader] case={LoadedManifest.case_id} " +
                $"hash={LoadedManifest.spec_hash} " +
                $"structures={LoadedManifest.structures.Count}");

            foreach (var entry in LoadedManifest.structures)
            {
                var glbAbs = Path.Combine(caseDirAbsolute, entry.mesh_path);
                var go = await LoadStructureAsync(entry, glbAbs);
                if (go != null) _loaded.Add(go);
            }

            return _loaded.Count == LoadedManifest.structures.Count;
        }

        async Task<GameObject> LoadStructureAsync(StructureManifest entry, string glbAbs)
        {
            if (!File.Exists(glbAbs))
            {
                Debug.LogError($"[CaseLoader] mesh missing: {glbAbs}");
                return null;
            }

            var data = await File.ReadAllBytesAsync(glbAbs);
            // glTFast holds internal buffers until disposed; per its docs the
            // loaded scene's meshes are owned by Unity after Instantiate, so
            // disposing afterward is the recommended pattern.
            var gltf = new GltfImport();
            GameObject go;
            try
            {
                var ok = await gltf.LoadGltfBinary(data);
                if (!ok)
                {
                    Debug.LogError($"[CaseLoader] glTFast failed to load {glbAbs}");
                    return null;
                }

                go = new GameObject(entry.name);
                go.transform.SetParent(transform, worldPositionStays: false);

                var instantiated = await gltf.InstantiateMainSceneAsync(go.transform);
                if (!instantiated)
                {
                    Debug.LogError($"[CaseLoader] InstantiateMainSceneAsync failed for {entry.name}");
                    Object.DestroyImmediate(go);
                    return null;
                }
            }
            finally
            {
                gltf.Dispose();
            }

            ApplyMaterial(go, entry);

            if (LogStructureBounds)
            {
                var renderers = go.GetComponentsInChildren<Renderer>();
                if (renderers.Length > 0)
                {
                    var b = renderers[0].bounds;
                    for (int i = 1; i < renderers.Length; i++) b.Encapsulate(renderers[i].bounds);
                    Debug.Log(
                        $"[CaseLoader]   {entry.name}: " +
                        $"center={b.center.ToString("F1")} size={b.size.ToString("F1")} " +
                        $"({entry.triangle_count} tris)");
                }
            }

            return go;
        }

        void ApplyMaterial(GameObject root, StructureManifest entry)
        {
            if (MaterialMap == null) return;
            var mat = MaterialMap.Resolve(entry.material_hint);
            if (mat == null) return;
            foreach (var r in root.GetComponentsInChildren<Renderer>())
                r.sharedMaterial = mat;
        }

        public void ClearLoaded()
        {
            for (int i = _loaded.Count - 1; i >= 0; i--)
            {
                if (_loaded[i] != null)
                {
                    if (Application.isPlaying) Destroy(_loaded[i]);
                    else DestroyImmediate(_loaded[i]);
                }
            }
            _loaded.Clear();
            LoadedManifest = null;
        }
    }
}
