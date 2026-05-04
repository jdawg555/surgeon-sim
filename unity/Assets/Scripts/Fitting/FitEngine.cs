using System;
using System.Collections.Generic;
using System.Linq;
using Dragonfly.XR.Domain;

namespace Dragonfly.XR.Fitting
{
    // Deterministic implant ranking — port of dragonfly/fitting/fit_engine.py.
    // Pure math; no Unity, no I/O. Safe to unit-test outside the player.
    public static class FitEngine
    {
        const float WeightFootprint = 0.40f;
        const float WeightHeight = 0.35f;
        const float WeightLordosis = 0.25f;

        public static FitScore Score(ImplantSpec implant, DiscSpaceMeasurement meas)
        {
            if (!implant.Indications.Contains(meas.Level))
            {
                return new FitScore
                {
                    Implant = implant, Measurement = meas,
                    Warnings = { "Implant not indicated for this spinal level" },
                };
            }

            var (fp, overhang, coverage) = FootprintScore(implant, meas);
            var h = HeightScore(implant, meas);
            var l = LordosisScore(implant, meas);

            float composite = WeightFootprint * fp + WeightHeight * h + WeightLordosis * l;

            return new FitScore
            {
                Implant = implant,
                Measurement = meas,
                FootprintScore = (float)Math.Round(fp, 3),
                HeightScore = (float)Math.Round(h, 3),
                LordosisScore = (float)Math.Round(l, 3),
                OverhangMm = (float)Math.Round(overhang, 2),
                CoverageFraction = (float)Math.Round(coverage, 3),
                TotalScore = (float)Math.Round(composite * 100f, 1),
                Warnings = BuildWarnings(implant, meas, overhang, coverage),
            };
        }

        public static List<FitScore> Rank(
            DiscSpaceMeasurement meas, IEnumerable<ImplantSpec> catalog, int topN = 10)
        {
            var implantType = meas.Level.IsCervical()
                ? ImplantType.CervicalTDR : ImplantType.LumbarTDR;

            var scored = catalog
                .Where(i => i.ImplantType == implantType)
                .Select(i => Score(i, meas))
                .OrderByDescending(s => s.TotalScore)
                .Take(topN)
                .ToList();

            for (int i = 0; i < scored.Count; i++) scored[i].Rank = i + 1;
            return scored;
        }

        public static FitScore BestFit(DiscSpaceMeasurement meas, IEnumerable<ImplantSpec> catalog) =>
            Rank(meas, catalog, 1).FirstOrDefault();

        // --- internal scoring functions ------------------------------------

        static (float score, float overhangMm, float coverage)
            FootprintScore(ImplantSpec implant, DiscSpaceMeasurement meas)
        {
            float endplateA = meas.ApDepthMm / 2f;
            float endplateB = meas.MlWidthMm / 2f;
            float endplateArea = (float)Math.PI * endplateA * endplateB;

            float impA = implant.ApDepthMm / 2f;
            float impB = implant.MlWidthMm / 2f;

            float intersectArea = (float)Math.PI * Math.Min(endplateA, impA) * Math.Min(endplateB, impB);
            float coverage = endplateArea > 0 ? intersectArea / endplateArea : 0f;

            float overhangAp = Math.Max(0, impA - endplateA);
            float overhangMl = Math.Max(0, impB - endplateB);
            float overhangMm = (float)Math.Sqrt(overhangAp * overhangAp + overhangMl * overhangMl);

            float covScore;
            if (coverage >= 0.80f && coverage <= 0.95f) covScore = 1f;
            else if (coverage < 0.80f) covScore = coverage / 0.80f;
            else covScore = Math.Max(0f, 1f - (coverage - 0.95f) * 3f);

            float overhangPenalty = Math.Min(1f, overhangMm / 5f);
            float score = covScore * (1f - overhangPenalty * 0.8f);
            return (Math.Max(0f, score), overhangMm, coverage);
        }

        static float HeightScore(ImplantSpec implant, DiscSpaceMeasurement meas)
        {
            float target = meas.DiscHeightMeanMm + 1f;
            float actual = implant.HeightMm;

            if (actual < implant.HeightMinMm || actual > implant.HeightMaxMm) return 0f;

            float dev = Math.Abs(actual - target);
            if (dev <= 2f) return 1f;
            if (dev <= 5f) return 1f - (dev - 2f) / 3f;
            if (dev <= 8f) return Math.Max(0f, 0.1f - (dev - 5f) / 30f);
            return 0f;
        }

        static float LordosisScore(ImplantSpec implant, DiscSpaceMeasurement meas)
        {
            float natural = meas.NaturalLordosisDeg;
            if (implant.AvailableAnglesDeg == null || implant.AvailableAnglesDeg.Count == 0)
                return 0f;

            float bestAngle = implant.AvailableAnglesDeg
                .OrderBy(a => Math.Abs(a - natural))
                .First();
            float dev = Math.Abs(bestAngle - natural);

            if (dev <= 2f) return 1f;
            if (dev <= 5f) return 1f - (dev - 2f) / 3f * 0.5f;
            if (dev <= 10f) return 0.5f - (dev - 5f) / 5f * 0.4f;
            return Math.Max(0f, 0.1f - (dev - 10f) / 50f);
        }

        static List<string> BuildWarnings(
            ImplantSpec implant, DiscSpaceMeasurement meas, float overhangMm, float coverage)
        {
            var w = new List<string>();
            if (overhangMm > 2f)
                w.Add($"Implant overhangs endplate by {overhangMm:F1} mm — subsidence risk elevated");
            if (coverage < 0.60f)
                w.Add($"Endplate coverage {coverage * 100f:F0}% — implant undersized; consider larger footprint");
            if (implant.HeightMm > meas.DiscHeightMeanMm + 5f)
                w.Add("Implant height significantly exceeds disc space — distraction may be excessive");
            if (implant.HeightMm < meas.DiscHeightMeanMm - 2f)
                w.Add("Implant height below disc space — may not restore adequate foraminal height");
            if (!implant.FdaCleared)
                w.Add("Not FDA cleared — CE marked only; verify regulatory status for jurisdiction");
            if (meas.Confidence < 0.5f)
                w.Add("Measurement confidence low — manual verification of dimensions recommended");
            return w;
        }
    }
}
