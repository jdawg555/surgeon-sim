#if UNITY_EDITOR
using Dragonfly.XR.Catalog;
using Dragonfly.XR.Domain;
using Dragonfly.XR.Fitting;
using UnityEditor;
using UnityEngine;

namespace Dragonfly.XR.EditorTools
{
    // Quick sanity-check menu item: Tools > Dragonfly > Run Fit Engine Smoke Test.
    // Walks every spine level, prints the top fit. Useful to confirm the
    // catalog JSON parses and the engine ports cleanly without launching XR.
    public static class FitEngineSmokeTest
    {
        [MenuItem("Tools/Dragonfly/Run Fit Engine Smoke Test")]
        public static void Run()
        {
            Debug.Log($"[Dragonfly.XR] Catalog loaded: {ImplantCatalog.All.Count} implants");
            foreach (SpineLevel level in System.Enum.GetValues(typeof(SpineLevel)))
            {
                var meas = DiscSpaceMeasurement.FromLiterature(level);
                var top = FitEngine.Rank(meas, ImplantCatalog.All, 3);
                if (top.Count == 0) { Debug.LogWarning($"  {level.Display()}: no candidates"); continue; }
                Debug.Log($"  {level.Display()}: " + string.Join(" | ",
                    top.ConvertAll(s => $"{s.Implant.ProductName} ({s.TotalScore:F1})")));
            }
        }
    }
}
#endif
