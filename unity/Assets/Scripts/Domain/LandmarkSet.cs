using System.Collections.Generic;
using UnityEngine;

namespace Dragonfly.XR.Domain
{
    // Sparse landmark container for the fusion predictor input. Mirrors the
    // string-keyed dict used in python/core/implant_predictor.py without
    // forcing C# callers into a stringly-typed API everywhere.
    //
    // Mannequin/literature-default demos can pass an empty LandmarkSet and
    // the predictor falls back to normative tables.
    public class LandmarkSet
    {
        readonly Dictionary<string, Vector3> points = new();
        readonly Dictionary<VertebraLevel, float> vbDepthsMm = new();

        public void SetPoint(string key, Vector3 v) => points[key] = v;
        public bool TryGetPoint(string key, out Vector3 v) => points.TryGetValue(key, out v);

        // Vertebral body AP depth — surface override for cases where bounds
        // are precomputed rather than carried as anterior/posterior corner
        // landmarks. Equivalent to the {vert}_bounds branch in Python.
        public void SetVbDepthMm(VertebraLevel v, float depthMm) => vbDepthsMm[v] = depthMm;
        public bool TryGetVbDepthMm(VertebraLevel v, out float depthMm) =>
            vbDepthsMm.TryGetValue(v, out depthMm);

        public float? PedicleWidthMm(VertebraLevel vert, ScrewSide side)
        {
            string s = side == ScrewSide.Left ? "left" : "right";
            string medKey = $"{vert.Display()}_{s}_pedicle_medial";
            string latKey = $"{vert.Display()}_{s}_pedicle_lateral";
            if (TryGetPoint(medKey, out var med) && TryGetPoint(latKey, out var lat))
            {
                float d = Vector3.Distance(med, lat);
                return d > 0f ? d : null;
            }
            return null;
        }

        public float? VbDepthMm(VertebraLevel vert)
        {
            if (TryGetPoint($"{vert.Display()}_anterior_corner", out var a) &&
                TryGetPoint($"{vert.Display()}_posterior_corner", out var p))
            {
                return Vector3.Distance(a, p);
            }
            if (TryGetVbDepthMm(vert, out var d)) return d;
            return null;
        }

        public float? CentroidDistanceMm(VertebraLevel a, VertebraLevel b)
        {
            if (TryGetPoint($"{a.Display()}_centroid", out var pa) &&
                TryGetPoint($"{b.Display()}_centroid", out var pb))
            {
                return Vector3.Distance(pa, pb);
            }
            return null;
        }
    }
}
