using System;
using System.Collections.Generic;

namespace Dragonfly.XR.Domain
{
    [Serializable]
    public class ImplantSpec
    {
        public string ImplantId;
        public string Manufacturer;
        public string ProductName;
        public ImplantType ImplantType;

        public float ApDepthMm;
        public float MlWidthMm;
        public float HeightMm;
        public float HeightMinMm;
        public float HeightMaxMm;
        public float LordoticAngleDeg;
        public List<float> AvailableAnglesDeg = new();

        public string MaterialEndplate;
        public string MaterialCore;
        public bool HasKeel;
        public float KeelHeightMm;

        public bool FdaCleared;
        public bool CeMarked;
        public List<SpineLevel> Indications = new();

        public float FootprintAreaMm2 =>
            (float)(Math.PI * (ApDepthMm / 2f) * (MlWidthMm / 2f));

        public override int GetHashCode() => ImplantId?.GetHashCode() ?? 0;
        public override bool Equals(object obj) =>
            obj is ImplantSpec other && other.ImplantId == ImplantId;
    }
}
