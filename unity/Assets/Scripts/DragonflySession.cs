using System.Linq;
using Dragonfly.XR.Anchoring;
using Dragonfly.XR.Catalog;
using Dragonfly.XR.Domain;
using Dragonfly.XR.Fitting;
using Dragonfly.XR.Step;
using Dragonfly.XR.Stream;
using Dragonfly.XR.Voice;
using UnityEngine;

namespace Dragonfly.XR
{
    // Wires the standalone subsystems together. Drop one of these into the
    // root scene and assign the references in the inspector.
    public class DragonflySession : MonoBehaviour
    {
        public SpineAnchor anchor;
        public VoiceCommandRouter voice;
        public ProcedureStepMachine steps;
        public StreamOverlay overlay;

        public SpineLevel currentLevel = SpineLevel.L4_L5;
        FitScore _currentFit;

        void Start()
        {
            if (voice != null)
            {
                voice.OnShowLevel += SelectLevel;
                voice.OnShowImplant += ShowBestFit;
                voice.OnHideImplant += () => overlay?.SetFit(null);
                voice.OnNextStep += () => steps?.Next();
                voice.OnPreviousStep += () => steps?.Previous();
                voice.OnAnchorReset += () => anchor?.Reset();
            }

            if (steps != null)
            {
                steps.OnStepEntered += (s, i) => overlay?.SetStep(s.Title, i, steps.steps.Count);
            }

            SelectLevel(currentLevel);
        }

        public void SelectLevel(SpineLevel level)
        {
            currentLevel = level;
            overlay?.SetLevel(level);
            ShowBestFit();
        }

        public void ShowBestFit()
        {
            var meas = DiscSpaceMeasurement.FromLiterature(currentLevel);
            _currentFit = FitEngine.BestFit(meas, ImplantCatalog.All);
            overlay?.SetFit(_currentFit);
            if (_currentFit != null)
            {
                Debug.Log($"[Dragonfly.XR] {currentLevel.Display()} → " +
                          $"{_currentFit.Implant.ProductName} ({_currentFit.TotalScore:F1})");
            }
        }
    }
}
