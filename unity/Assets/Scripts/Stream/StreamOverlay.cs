using Dragonfly.XR.Domain;
using TMPro;
using UnityEngine;

namespace Dragonfly.XR.Stream
{
    // Lightweight HUD shown to the Twitch audience (not the surgeon).
    // Lives on a separate camera that renders to a RenderTexture used by
    // OBS via Spout / NDI. Keep text large; viewers watch on phones.
    public class StreamOverlay : MonoBehaviour
    {
        public TMP_Text levelLabel;
        public TMP_Text implantLabel;
        public TMP_Text scoreLabel;
        public TMP_Text stepLabel;
        public TMP_Text warningsLabel;

        public void SetLevel(SpineLevel level) =>
            Set(levelLabel, $"Level  {level.Display()}");

        public void SetFit(FitScore fit)
        {
            if (fit == null)
            {
                Set(implantLabel, "Implant  —");
                Set(scoreLabel, "Fit  —");
                Set(warningsLabel, "");
                return;
            }
            Set(implantLabel, $"Implant  {fit.Implant.Manufacturer} {fit.Implant.ProductName}");
            Set(scoreLabel, $"Fit  {fit.TotalScore:F1} / 100");
            Set(warningsLabel, fit.Warnings != null && fit.Warnings.Count > 0
                ? string.Join("\n", fit.Warnings) : "");
        }

        public void SetStep(string title, int index, int total) =>
            Set(stepLabel, $"Step {index + 1}/{total}  {title}");

        static void Set(TMP_Text t, string s) { if (t != null) t.text = s; }
    }
}
