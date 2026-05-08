using System.Collections.Generic;

namespace Dragonfly.XR.Domain
{
    // Optimised single-case implant tray. C# port of
    // python/core/tray_optimizer.py::TrayConfiguration.

    public class TrayItem
    {
        public float DiameterMm;
        public int LengthMm;
        public int Quantity;
        public string Role;   // "primary", "primary+backup", or "backup"

        public string Label() =>
            $"⌀{DiameterMm}mm × {LengthMm}mm  qty={Quantity}  [{Role}]";
    }

    public class TrayConfiguration
    {
        public List<TrayItem> Items = new();
        public int TotalImplants;
        public int StandardBaseline;
        public float ReductionPct;
        public List<string> RodSpecs = new();
        public float EstimatedSterilizationCostUsd;
        public List<string> Warnings = new();
    }
}
