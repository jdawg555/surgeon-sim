using System;
using System.Collections.Generic;
using Dragonfly.XR.Domain;

namespace Dragonfly.XR.Fusion
{
    // Pedicle screw + rod predictor for lumbar fusion. C# port of
    // python/core/implant_predictor.py. Pure logic; no Unity APIs beyond
    // the Vector3-based LandmarkSet helpers. Headset-free testable.
    //
    // Statistical prior: Zindrick et al. 1987 (Spine), Mirkovic et al. 1997.
    public static class ImplantPredictor
    {
        // Normative pedicle isthmus width (mm). Source: Zindrick, Mirkovic.
        static readonly Dictionary<VertebraLevel, (float male, float female)> NormativePedicleWidth = new()
        {
            { VertebraLevel.L1, (8.7f,  7.8f) },
            { VertebraLevel.L2, (8.9f,  7.9f) },
            { VertebraLevel.L3, (10.2f, 9.0f) },
            { VertebraLevel.L4, (12.6f, 11.2f) },
            { VertebraLevel.L5, (15.4f, 13.8f) },
        };

        // Normative AP vertebral body depth (mm). Source: Panjabi 1992.
        static readonly Dictionary<VertebraLevel, float> NormativeVbDepth = new()
        {
            { VertebraLevel.L1, 38.0f },
            { VertebraLevel.L2, 38.5f },
            { VertebraLevel.L3, 39.0f },
            { VertebraLevel.L4, 40.0f },
            { VertebraLevel.L5, 40.5f },
            { VertebraLevel.S1, 38.0f },
        };

        public static readonly float[] StandardDiameters = { 4.5f, 5.5f, 6.5f, 7.5f };
        public static readonly int[] StandardLengths = { 35, 40, 45, 50, 55 };

        public const float MaxScrewDiameterMm = 8.5f;
        public const int MaxScrewLengthMm = 55;
        const float SafetyMarginFactor = 0.80f;
        const float LengthTargetFactor = 0.80f;
        const float RodOverhangMm = 20.0f;
        const float CdiCobaltCrThreshold = 600.0f;
        const float NormativeInterCentroidMm = 35.0f;

        public static ImplantPlan Predict(
            LandmarkSet landmarks,
            SpinopelvicParams spinopelvic,
            float densityHu,
            IReadOnlyList<SpineLevel> fusedLevels,
            Sex sex = Sex.Male,
            int age = 50)
        {
            landmarks ??= new LandmarkSet();
            var warnings = new List<string>();

            var vertOrder = VertebraLevelExtensions.SpannedVertebrae(fusedLevels);

            var screws = new Dictionary<string, ScrewSpec>();
            var backups = new Dictionary<string, List<ScrewSpec>>();
            var confidence = new Dictionary<VertebraLevel, float>();

            foreach (var vert in vertOrder)
            {
                float vertConf = 1.0f;

                foreach (ScrewSide side in new[] { ScrewSide.Left, ScrewSide.Right })
                {
                    var (pedicleWidth, basis, pedicleConfMul) =
                        ResolvePedicleWidth(landmarks, vert, side, sex, warnings);
                    vertConf *= pedicleConfMul;

                    float chosenDia = SelectDiameter(pedicleWidth);
                    string key = $"{vert.Display()}-{(side == ScrewSide.Left ? "left" : "right")}";
                    if (chosenDia > MaxScrewDiameterMm)
                    {
                        chosenDia = MaxScrewDiameterMm;
                        warnings.Add($"{key}: diameter capped at safety ceiling {MaxScrewDiameterMm}mm");
                    }

                    var (vbDepth, vbBasis, vbConfMul) = ResolveVbDepth(landmarks, vert);
                    vertConf *= vbConfMul;
                    if (vbBasis == SizingBasis.Normative) basis = SizingBasis.Normative;

                    int chosenLen = SelectLength(vbDepth);

                    var spec = new ScrewSpec
                    {
                        DiameterMm = chosenDia,
                        LengthMm = chosenLen,
                        Vertebra = vert,
                        Side = side,
                        Basis = basis,
                    };
                    screws[key] = spec;
                    backups[key] = BuildBackups(chosenDia, chosenLen, vert, side, basis);
                }

                confidence[vert] = (float)Math.Round(Math.Clamp(vertConf, 0f, 1f), 3);
            }

            if (age > 70)
            {
                warnings.Add(
                    "Patient age > 70: cortical thinning may reduce effective pedicle width; " +
                    "consider intraoperative pedicle sounding.");
                var keys = new List<VertebraLevel>(confidence.Keys);
                foreach (var k in keys)
                    confidence[k] = (float)Math.Round(confidence[k] * 0.92f, 3);
            }
            else if (age < 25)
            {
                warnings.Add(
                    "Patient age < 25: pedicle dimensions may exceed normative adult range; " +
                    "confirm with direct measurement.");
            }

            float rodLength = EstimateRodLength(vertOrder, landmarks) + 2f * RodOverhangMm;
            float ll = spinopelvic.LumbarLordosisDeg;
            float rodCurvature = ll * 0.75f;

            var rodMaterial = densityHu > CdiCobaltCrThreshold ? RodMaterial.CoCr : RodMaterial.Ti;

            if (fusedLevels.Count >= 3)
            {
                warnings.Add(
                    $"{fusedLevels.Count}-level construct: consider staged surgery or " +
                    "supplemental anterior support.");
            }

            float pi = spinopelvic.PelvicIncidenceDeg;
            float piLl = pi - ll;
            if (Math.Abs(piLl) > 20f)
            {
                warnings.Add(
                    $"PI-LL mismatch {piLl:+0.0;-0.0}° (>20°): sagittal imbalance risk — " +
                    "adjust rod curvature intraoperatively.");
            }

            return new ImplantPlan
            {
                FusedLevels = fusedLevels,
                Screws = screws,
                RodLengthMm = (float)Math.Round(rodLength, 1),
                RodCurvatureDeg = (float)Math.Round(rodCurvature, 1),
                RodMaterial = rodMaterial,
                BackupScrews = backups,
                Confidence = confidence,
                Warnings = warnings,
            };
        }

        public static ValidationResult Validate(ImplantPlan plan)
        {
            var issues = new List<string>();

            foreach (var (key, screw) in plan.Screws)
            {
                if (Array.IndexOf(StandardDiameters, screw.DiameterMm) < 0)
                {
                    issues.Add(
                        $"{key}: diameter {screw.DiameterMm}mm not in standard catalogue " +
                        $"[{string.Join(", ", StandardDiameters)}]");
                }
                if (screw.DiameterMm > MaxScrewDiameterMm)
                {
                    issues.Add(
                        $"{key}: diameter {screw.DiameterMm}mm exceeds safety ceiling {MaxScrewDiameterMm}mm");
                }
                if (screw.LengthMm > MaxScrewLengthMm)
                {
                    issues.Add($"{key}: length {screw.LengthMm}mm exceeds maximum {MaxScrewLengthMm}mm");
                }
            }

            if (plan.RodLengthMm <= 0f)
                issues.Add("RodLengthMm must be positive");

            if (!VertebraLevelExtensions.IsContiguous(plan.FusedLevels))
            {
                var names = string.Join(", ", FusedLevelNames(plan.FusedLevels));
                issues.Add(
                    $"Fused levels [{names}] are not contiguous — " +
                    "non-contiguous fusion constructs are not supported");
            }

            return new ValidationResult { Valid = issues.Count == 0, Warnings = issues };
        }

        // --- helpers --------------------------------------------------------

        static (float widthMm, SizingBasis basis, float confMul) ResolvePedicleWidth(
            LandmarkSet landmarks, VertebraLevel vert, ScrewSide side, Sex sex, List<string> warnings)
        {
            var measured = landmarks.PedicleWidthMm(vert, side);
            if (measured.HasValue) return (measured.Value, SizingBasis.Measured, 1f);

            string key = $"{vert.Display()}-{(side == ScrewSide.Left ? "left" : "right")}";
            if (!NormativePedicleWidth.TryGetValue(vert, out var norm))
            {
                // S1 is not in the normative table — fall back to L5 values.
                norm = NormativePedicleWidth[VertebraLevel.L5];
                warnings.Add(
                    $"{vert.Display()} not in normative table; using L5 values as proxy for {key}");
            }
            float w = sex == Sex.Female ? norm.female : norm.male;
            return (w, SizingBasis.Normative, 0.75f);
        }

        static (float vbDepthMm, SizingBasis basis, float confMul) ResolveVbDepth(
            LandmarkSet landmarks, VertebraLevel vert)
        {
            var measured = landmarks.VbDepthMm(vert);
            if (measured.HasValue) return (measured.Value, SizingBasis.Measured, 1f);

            float depth = NormativeVbDepth.TryGetValue(vert, out var d) ? d : 39.0f;
            return (depth, SizingBasis.Normative, 0.90f);
        }

        static float SelectDiameter(float pedicleWidthMm)
        {
            float target = pedicleWidthMm * SafetyMarginFactor;
            float chosen = StandardDiameters[0];
            bool found = false;
            foreach (var s in StandardDiameters)
            {
                if (s <= target && s > chosen) { chosen = s; found = true; }
                else if (s <= target && !found) { chosen = s; found = true; }
            }
            return chosen;
        }

        static int SelectLength(float vbDepthMm)
        {
            float target = vbDepthMm * LengthTargetFactor;
            int chosen = StandardLengths[0];
            float bestDelta = Math.Abs(chosen - target);
            foreach (var l in StandardLengths)
            {
                float d = Math.Abs(l - target);
                if (d < bestDelta) { bestDelta = d; chosen = l; }
            }
            return chosen;
        }

        static List<ScrewSpec> BuildBackups(
            float chosenDia, int chosenLen, VertebraLevel vert, ScrewSide side, SizingBasis basis)
        {
            var dias = BackupDiameters(chosenDia);
            var lens = BackupLengths(chosenLen);
            var list = new List<ScrewSpec>();
            foreach (var d in dias)
                foreach (var l in lens)
                    list.Add(new ScrewSpec
                    {
                        DiameterMm = d,
                        LengthMm = l,
                        Vertebra = vert,
                        Side = side,
                        Basis = basis,
                    });
            return list;
        }

        static List<float> BackupDiameters(float chosen)
        {
            int idx = Array.IndexOf(StandardDiameters, chosen);
            if (idx < 0) idx = 0;
            var r = new List<float>();
            if (idx > 0) r.Add(StandardDiameters[idx - 1]);
            if (idx < StandardDiameters.Length - 1) r.Add(StandardDiameters[idx + 1]);
            return r;
        }

        static List<int> BackupLengths(int chosen)
        {
            int idx = Array.IndexOf(StandardLengths, chosen);
            if (idx < 0) idx = 0;
            var r = new List<int>();
            if (idx > 0) r.Add(StandardLengths[idx - 1]);
            if (idx < StandardLengths.Length - 1) r.Add(StandardLengths[idx + 1]);
            return r;
        }

        static float EstimateRodLength(IReadOnlyList<VertebraLevel> vertOrder, LandmarkSet landmarks)
        {
            float total = 0f;
            for (int i = 0; i < vertOrder.Count - 1; i++)
            {
                var d = landmarks.CentroidDistanceMm(vertOrder[i], vertOrder[i + 1]);
                total += d ?? NormativeInterCentroidMm;
            }
            return total;
        }

        static IEnumerable<string> FusedLevelNames(IReadOnlyList<SpineLevel> levels)
        {
            foreach (var l in levels) yield return l.Display();
        }

        public class ValidationResult
        {
            public bool Valid;
            public List<string> Warnings = new();
        }
    }
}
