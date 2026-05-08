using System;
using System.Collections.Generic;
using Dragonfly.XR.Domain;

namespace Dragonfly.XR.Fusion
{
    // Reduces a 120-implant standard spine tray to the minimum viable set
    // for a single case. C# port of python/core/tray_optimizer.py.
    public static class TrayOptimizer
    {
        const float SterilizationCostPerUnitUsd = 2.50f;
        const int StandardTrayBaseline = 120;

        public static TrayConfiguration Optimize(ImplantPlan plan, int safetyMargin = 2)
        {
            var warnings = new List<string>();

            var primaryCounts = new Dictionary<(float dia, int len), int>();
            foreach (var screw in plan.Screws.Values)
            {
                var k = (screw.DiameterMm, screw.LengthMm);
                primaryCounts.TryGetValue(k, out int n);
                primaryCounts[k] = n + 1;
            }

            var backupCounts = new Dictionary<(float dia, int len), int>();
            foreach (var list in plan.BackupScrews.Values)
            {
                foreach (var screw in list)
                {
                    var k = (screw.DiameterMm, screw.LengthMm);
                    backupCounts.TryGetValue(k, out int n);
                    backupCounts[k] = n + 1;
                }
            }

            var allSizes = new HashSet<(float dia, int len)>(primaryCounts.Keys);
            foreach (var k in backupCounts.Keys) allSizes.Add(k);

            var sizes = new List<(float dia, int len)>(allSizes);
            sizes.Sort((a, b) =>
            {
                int c = a.dia.CompareTo(b.dia);
                return c != 0 ? c : a.len.CompareTo(b.len);
            });

            var items = new List<TrayItem>();
            foreach (var k in sizes)
            {
                primaryCounts.TryGetValue(k, out int p);
                backupCounts.TryGetValue(k, out int b);
                int buf = safetyMargin * p;
                int qty = p + b + buf;
                if (qty == 0) continue;

                string role = p > 0
                    ? (b == 0 ? "primary" : "primary+backup")
                    : "backup";

                items.Add(new TrayItem
                {
                    DiameterMm = k.dia,
                    LengthMm = k.len,
                    Quantity = qty,
                    Role = role,
                });
            }

            int total = 0;
            foreach (var i in items) total += i.Quantity;

            float reductionPct = Math.Max(0f, (1f - (float)total / StandardTrayBaseline) * 100f);
            if (total > StandardTrayBaseline)
            {
                warnings.Add(
                    $"Optimized tray ({total} units) exceeds standard baseline " +
                    $"({StandardTrayBaseline}); consider splitting into two trays.");
                reductionPct = 0f;
            }

            return new TrayConfiguration
            {
                Items = items,
                TotalImplants = total,
                StandardBaseline = StandardTrayBaseline,
                ReductionPct = (float)Math.Round(reductionPct, 1),
                RodSpecs = BuildRodSpecs(plan),
                EstimatedSterilizationCostUsd =
                    (float)Math.Round(total * SterilizationCostPerUnitUsd, 2),
                Warnings = warnings,
            };
        }

        static List<string> BuildRodSpecs(ImplantPlan plan)
        {
            string spec =
                $"{plan.RodMaterial}  {plan.RodLengthMm:F0} mm  " +
                $"{plan.RodCurvatureDeg:F1}° pre-bend";
            return new List<string>
            {
                $"Left rod:  {spec}",
                $"Right rod: {spec}",
            };
        }
    }
}
