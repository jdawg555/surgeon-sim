using System.Collections.Generic;
using System.Linq;
using Dragonfly.XR.Domain;
using UnityEngine;

namespace Dragonfly.XR.Catalog
{
    // Loads implant_catalog.json from Resources at first access.
    // Indications are stored as int indices into the SpineLevel enum to keep
    // the JSON small and resilient against JsonUtility's lack of enum-string support.
    public static class ImplantCatalog
    {
        static List<ImplantSpec> _all;
        public static IReadOnlyList<ImplantSpec> All => _all ??= Load();

        public static IEnumerable<ImplantSpec> ForType(ImplantType type) =>
            All.Where(i => i.ImplantType == type);

        public static IEnumerable<ImplantSpec> ForLevel(SpineLevel level) =>
            All.Where(i => i.Indications.Contains(level));

        public static ImplantSpec ById(string id) =>
            All.FirstOrDefault(i => i.ImplantId == id);

        static List<ImplantSpec> Load()
        {
            var asset = Resources.Load<TextAsset>("implant_catalog");
            if (asset == null)
            {
                Debug.LogError("Dragonfly.XR: implant_catalog.json missing from Resources/");
                return new List<ImplantSpec>();
            }
            var wrapper = JsonUtility.FromJson<CatalogFile>(asset.text);
            return wrapper?.implants?.Select(j => j.ToSpec()).ToList() ?? new List<ImplantSpec>();
        }

        [System.Serializable]
        class CatalogFile
        {
            public List<JsonImplant> implants;
        }

        [System.Serializable]
        class JsonImplant
        {
            public string ImplantId;
            public string Manufacturer;
            public string ProductName;
            public int ImplantType;
            public float ApDepthMm, MlWidthMm, HeightMm, HeightMinMm, HeightMaxMm;
            public float LordoticAngleDeg;
            public List<float> AvailableAnglesDeg;
            public string MaterialEndplate, MaterialCore;
            public bool HasKeel;
            public float KeelHeightMm;
            public bool FdaCleared, CeMarked;
            public List<int> Indications;

            public ImplantSpec ToSpec() => new()
            {
                ImplantId = ImplantId,
                Manufacturer = Manufacturer,
                ProductName = ProductName,
                ImplantType = (ImplantType)ImplantType,
                ApDepthMm = ApDepthMm,
                MlWidthMm = MlWidthMm,
                HeightMm = HeightMm,
                HeightMinMm = HeightMinMm,
                HeightMaxMm = HeightMaxMm,
                LordoticAngleDeg = LordoticAngleDeg,
                AvailableAnglesDeg = AvailableAnglesDeg ?? new List<float>(),
                MaterialEndplate = MaterialEndplate,
                MaterialCore = MaterialCore,
                HasKeel = HasKeel,
                KeelHeightMm = KeelHeightMm,
                FdaCleared = FdaCleared,
                CeMarked = CeMarked,
                Indications = (Indications ?? new List<int>())
                    .Select(i => (SpineLevel)i).ToList(),
            };
        }
    }
}
