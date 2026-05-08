using System;
using System.Collections.Generic;

namespace Dragonfly.XR.Domain
{
    // Single-vertebra identifier. Distinct from SpineLevel (which names a
    // disc space, e.g. "L4-L5"). Used by the fusion predictor for
    // per-vertebra screw sizing.
    public enum VertebraLevel
    {
        L1,
        L2,
        L3,
        L4,
        L5,
        S1,
    }

    public static class VertebraLevelExtensions
    {
        public static string Display(this VertebraLevel v) => v switch
        {
            VertebraLevel.L1 => "L1",
            VertebraLevel.L2 => "L2",
            VertebraLevel.L3 => "L3",
            VertebraLevel.L4 => "L4",
            VertebraLevel.L5 => "L5",
            VertebraLevel.S1 => "S1",
            _ => v.ToString(),
        };

        // Vertebrae bracketing a disc-space level: L4-L5 -> [L4, L5].
        public static (VertebraLevel upper, VertebraLevel lower) Vertebrae(this SpineLevel level) => level switch
        {
            SpineLevel.L1_L2 => (VertebraLevel.L1, VertebraLevel.L2),
            SpineLevel.L2_L3 => (VertebraLevel.L2, VertebraLevel.L3),
            SpineLevel.L3_L4 => (VertebraLevel.L3, VertebraLevel.L4),
            SpineLevel.L4_L5 => (VertebraLevel.L4, VertebraLevel.L5),
            SpineLevel.L5_S1 => (VertebraLevel.L5, VertebraLevel.S1),
            _ => throw new ArgumentException(
                $"Vertebrae() is lumbar-only; got {level.Display()}", nameof(level)),
        };

        // Ordered, deduplicated list of vertebrae spanned by the construct.
        // ["L4-L5", "L5-S1"] -> [L4, L5, S1].
        public static List<VertebraLevel> SpannedVertebrae(IReadOnlyList<SpineLevel> fusedLevels)
        {
            var seen = new List<VertebraLevel>();
            foreach (var lvl in fusedLevels)
            {
                var (u, l) = lvl.Vertebrae();
                if (!seen.Contains(u)) seen.Add(u);
                if (!seen.Contains(l)) seen.Add(l);
            }
            return seen;
        }

        static readonly VertebraLevel[] ContiguousOrder =
        {
            VertebraLevel.L1, VertebraLevel.L2, VertebraLevel.L3,
            VertebraLevel.L4, VertebraLevel.L5, VertebraLevel.S1,
        };

        // True iff the spanned vertebrae form a single unbroken segment.
        public static bool IsContiguous(IReadOnlyList<SpineLevel> fusedLevels)
        {
            var verts = SpannedVertebrae(fusedLevels);
            if (verts.Count == 0) return false;
            int first = Array.IndexOf(ContiguousOrder, verts[0]);
            if (first < 0) return false;
            for (int i = 0; i < verts.Count; i++)
            {
                if (Array.IndexOf(ContiguousOrder, verts[i]) != first + i) return false;
            }
            return true;
        }
    }
}
