using UnityEngine;

namespace Dragonfly.XR.Cases
{
    // Maps a structure's `material_hint` to a Material the project supplies.
    // Lives as a ScriptableObject so the surgeon (or whoever skins the
    // project) can swap shaders/materials per case archetype without
    // touching code. If the project ships no map, CaseLoader leaves
    // glTFast's default material in place.
    [CreateAssetMenu(fileName = "CaseMaterialMap", menuName = "Dragonfly/Case Material Map")]
    public class CaseMaterialMap : ScriptableObject
    {
        public Material Skin;
        public Material SoftTissue;
        public Material Bone;
        public Material Disc;
        public Material Cord;
        public Material Fallback;

        public Material Resolve(string hint)
        {
            switch (hint)
            {
                case "skin":         return Skin;
                case "soft_tissue":  return SoftTissue;
                case "bone":         return Bone;
                case "disc":         return Disc;
                case "cord":         return Cord;
                default:             return Fallback;
            }
        }
    }
}
