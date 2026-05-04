using System.Collections.Generic;
using UnityEngine;

namespace Dragonfly.XR.Domain
{
    public class DiscSpaceMeasurement
    {
        public SpineLevel Level;
        public float ApDepthMm;
        public float MlWidthMm;
        public float DiscHeightAnteriorMm;
        public float DiscHeightPosteriorMm;
        public float DiscHeightMeanMm;
        public float NaturalLordosisDeg;
        public float EndplateAreaMm2;

        public Vector3 SuperiorCentroid;
        public Vector3 InferiorCentroid;
        public Vector3 SuperiorNormal = Vector3.up;
        public Vector3 InferiorNormal = Vector3.down;

        public float Confidence = 1f;
        public string Source = "stl_analysis";

        // Anatomy averages from published literature.
        // Used as fallback when no segmentation is available — e.g. in
        // mannequin demo mode for the Twitch stream.
        public static DiscSpaceMeasurement FromLiterature(SpineLevel level)
        {
            var d = LiteratureDefaults[level];
            float h = d.h;
            return new DiscSpaceMeasurement
            {
                Level = level,
                ApDepthMm = d.ap,
                MlWidthMm = d.ml,
                DiscHeightAnteriorMm = h * 1.2f,
                DiscHeightPosteriorMm = h * 0.8f,
                DiscHeightMeanMm = h,
                NaturalLordosisDeg = d.lord,
                EndplateAreaMm2 = d.area,
                SuperiorCentroid = Vector3.zero,
                InferiorCentroid = new Vector3(0, 0, -h),
                SuperiorNormal = Vector3.forward,
                InferiorNormal = -Vector3.forward,
                Confidence = 0.5f,
                Source = "literature_default",
            };
        }

        private struct LitDefaults { public float ap, ml, h, lord, area; }

        private static readonly Dictionary<SpineLevel, LitDefaults> LiteratureDefaults = new()
        {
            { SpineLevel.C3_C4, new LitDefaults { ap=14.5f, ml=14f, h=4.5f, lord=5f, area=157f } },
            { SpineLevel.C4_C5, new LitDefaults { ap=15f, ml=15f, h=5f, lord=6f, area=177f } },
            { SpineLevel.C5_C6, new LitDefaults { ap=16f, ml=16f, h=5.5f, lord=7f, area=201f } },
            { SpineLevel.C6_C7, new LitDefaults { ap=16.5f, ml=16f, h=5f, lord=6f, area=208f } },
            { SpineLevel.L1_L2, new LitDefaults { ap=34f, ml=42f, h=9.5f, lord=6f, area=1120f } },
            { SpineLevel.L2_L3, new LitDefaults { ap=37f, ml=44f, h=10f, lord=7f, area=1282f } },
            { SpineLevel.L3_L4, new LitDefaults { ap=40f, ml=46f, h=11f, lord=8f, area=1446f } },
            { SpineLevel.L4_L5, new LitDefaults { ap=43f, ml=48f, h=11.5f, lord=10f, area=1620f } },
            { SpineLevel.L5_S1, new LitDefaults { ap=44f, ml=50f, h=10f, lord=14f, area=1727f } },
        };
    }

    public class FitScore
    {
        public ImplantSpec Implant;
        public DiscSpaceMeasurement Measurement;
        public float FootprintScore;
        public float HeightScore;
        public float LordosisScore;
        public float OverhangMm;
        public float CoverageFraction;
        public float TotalScore;
        public int Rank;
        public List<string> Warnings = new();
    }
}
