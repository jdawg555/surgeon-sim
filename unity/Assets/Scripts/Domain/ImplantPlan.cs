using System.Collections.Generic;

namespace Dragonfly.XR.Domain
{
    // Pedicle screw + rod plan for a lumbar fusion construct.
    // C# port of python/core/implant_predictor.py::ImplantPlan.

    public enum ScrewSide { Left, Right }

    public enum SizingBasis { Measured, Normative }

    public enum RodMaterial { Ti, CoCr }

    public class ScrewSpec
    {
        public float DiameterMm;
        public int LengthMm;
        public VertebraLevel Vertebra;
        public ScrewSide Side;
        public SizingBasis Basis;

        public string Key => $"{Vertebra.Display()}-{(Side == ScrewSide.Left ? "left" : "right")}";

        public string Label() =>
            $"{Vertebra.Display()}-{(Side == ScrewSide.Left ? "left" : "right")}  " +
            $"⌀{DiameterMm}mm × {LengthMm}mm  [{Basis.ToString().ToLowerInvariant()}]";
    }

    public class ImplantPlan
    {
        public IReadOnlyList<SpineLevel> FusedLevels;
        public Dictionary<string, ScrewSpec> Screws = new();
        public float RodLengthMm;
        public float RodCurvatureDeg;
        public RodMaterial RodMaterial;
        public Dictionary<string, List<ScrewSpec>> BackupScrews = new();
        public Dictionary<VertebraLevel, float> Confidence = new();
        public List<string> Warnings = new();
    }

    public struct SpinopelvicParams
    {
        public float LumbarLordosisDeg;
        public float PelvicIncidenceDeg;

        public static SpinopelvicParams Default => new()
        {
            LumbarLordosisDeg = 40f,
            PelvicIncidenceDeg = 50f,
        };
    }

    public enum Sex { Male, Female }
}
