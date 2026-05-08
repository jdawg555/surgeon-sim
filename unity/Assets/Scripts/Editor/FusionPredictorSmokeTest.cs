#if UNITY_EDITOR
using System.Collections.Generic;
using Dragonfly.XR.Domain;
using Dragonfly.XR.Fusion;
using UnityEditor;
using UnityEngine;

namespace Dragonfly.XR.EditorTools
{
    // Tools > Dragonfly > Run Fusion Predictor Smoke Test.
    // Runs the C# fusion port against a literature-default L4-L5 + L5-S1
    // construct and prints screws, rod, and tray summary. Useful to confirm
    // the port matches the Python reference without launching XR.
    public static class FusionPredictorSmokeTest
    {
        [MenuItem("Tools/Dragonfly/Run Fusion Predictor Smoke Test")]
        public static void Run()
        {
            var fused = new List<SpineLevel> { SpineLevel.L4_L5, SpineLevel.L5_S1 };
            var plan = ImplantPredictor.Predict(
                landmarks: new LandmarkSet(),
                spinopelvic: new SpinopelvicParams { LumbarLordosisDeg = 48f, PelvicIncidenceDeg = 55f },
                densityHu: 540f,
                fusedLevels: fused,
                sex: Sex.Male,
                age: 58);

            Debug.Log($"[Dragonfly.Fusion] Construct: {string.Join(", ", FormatLevels(fused))}");
            Debug.Log($"[Dragonfly.Fusion] Rod: {plan.RodMaterial} {plan.RodLengthMm}mm @ {plan.RodCurvatureDeg}°");
            foreach (var (key, screw) in plan.Screws)
            {
                Debug.Log($"  {key,-10} ⌀{screw.DiameterMm}mm × {screw.LengthMm}mm  [{screw.Basis}]");
            }
            foreach (var (vert, conf) in plan.Confidence)
                Debug.Log($"  confidence {vert.Display()}: {conf:F2}");
            foreach (var w in plan.Warnings)
                Debug.LogWarning($"  warning: {w}");

            var validation = ImplantPredictor.Validate(plan);
            if (!validation.Valid)
            {
                foreach (var w in validation.Warnings)
                    Debug.LogError($"  validation: {w}");
            }
            else
            {
                Debug.Log("[Dragonfly.Fusion] Validation: ok");
            }

            var tray = TrayOptimizer.Optimize(plan);
            Debug.Log(
                $"[Dragonfly.Fusion] Tray: {tray.TotalImplants}/{tray.StandardBaseline} units " +
                $"({tray.ReductionPct}% reduction, ~${tray.EstimatedSterilizationCostUsd} sterilization)");
            foreach (var item in tray.Items)
                Debug.Log($"  {item.Label()}");
            foreach (var spec in tray.RodSpecs)
                Debug.Log($"  {spec}");
        }

        static IEnumerable<string> FormatLevels(IEnumerable<SpineLevel> levels)
        {
            foreach (var l in levels) yield return l.Display();
        }
    }
}
#endif
