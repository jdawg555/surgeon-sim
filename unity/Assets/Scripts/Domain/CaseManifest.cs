using System;
using System.Collections.Generic;

namespace Dragonfly.XR.Domain
{
    // Mirror of python/case_pipeline manifest.json. Field names use snake_case
    // so Unity's JsonUtility deserializes the file directly without a custom
    // converter. C# style convention bends here for interop reasons; the rest
    // of the project is PascalCase.
    [Serializable]
    public class CaseManifest
    {
        public string case_id;
        public string description;
        public string spec_hash;
        public string generated_at;
        public string pipeline_version;
        public List<StructureManifest> structures = new();
    }

    [Serializable]
    public class StructureManifest
    {
        public string name;          // 'skin', 'vertebral_body', ...
        public string mesh_path;     // relative to the case dir, e.g. 'meshes/skin.glb'
        public int vertex_count;
        public int triangle_count;
        public string material_hint; // 'skin' | 'soft_tissue' | 'bone' | 'disc' | 'cord'
    }
}
