using System;

namespace Dragonfly.XR.Domain
{
    public enum SpineLevel
    {
        C3_C4,
        C4_C5,
        C5_C6,
        C6_C7,
        L1_L2,
        L2_L3,
        L3_L4,
        L4_L5,
        L5_S1,
    }

    public enum ImplantType
    {
        LumbarTDR,
        CervicalTDR,
    }

    public static class SpineLevelExtensions
    {
        public static string Display(this SpineLevel level) => level switch
        {
            SpineLevel.C3_C4 => "C3-C4",
            SpineLevel.C4_C5 => "C4-C5",
            SpineLevel.C5_C6 => "C5-C6",
            SpineLevel.C6_C7 => "C6-C7",
            SpineLevel.L1_L2 => "L1-L2",
            SpineLevel.L2_L3 => "L2-L3",
            SpineLevel.L3_L4 => "L3-L4",
            SpineLevel.L4_L5 => "L4-L5",
            SpineLevel.L5_S1 => "L5-S1",
            _ => level.ToString(),
        };

        public static bool IsCervical(this SpineLevel level) =>
            level == SpineLevel.C3_C4 || level == SpineLevel.C4_C5 ||
            level == SpineLevel.C5_C6 || level == SpineLevel.C6_C7;

        public static bool IsLumbar(this SpineLevel level) => !level.IsCervical();

        public static bool TryParse(string token, out SpineLevel level)
        {
            switch ((token ?? "").Trim().ToUpperInvariant().Replace("–", "-").Replace("_", "-"))
            {
                case "C3-C4": level = SpineLevel.C3_C4; return true;
                case "C4-C5": level = SpineLevel.C4_C5; return true;
                case "C5-C6": level = SpineLevel.C5_C6; return true;
                case "C6-C7": level = SpineLevel.C6_C7; return true;
                case "L1-L2": level = SpineLevel.L1_L2; return true;
                case "L2-L3": level = SpineLevel.L2_L3; return true;
                case "L3-L4": level = SpineLevel.L3_L4; return true;
                case "L4-L5": level = SpineLevel.L4_L5; return true;
                case "L5-S1": level = SpineLevel.L5_S1; return true;
                default: level = SpineLevel.L4_L5; return false;
            }
        }
    }
}
