using System;
using System.Collections.Generic;
using UnityEngine;

namespace Dragonfly.XR.Step
{
    // Simple linear step sequencer. Pattern borrowed from SurgeonLife's
    // data-driven InteractiveSurgery, simplified for AR overlay use.
    [Serializable]
    public class ProcedureStep
    {
        public string Title;
        [TextArea] public string Instruction;
        public string VoiceCue;       // Spoken once on enter, e.g. "Identify L4 pedicle"
        public bool RequiresAnchor;   // If true, step is gated until anchor is set
    }

    public class ProcedureStepMachine : MonoBehaviour
    {
        public List<ProcedureStep> steps = new();
        public int currentIndex = -1;

        public event Action<ProcedureStep, int> OnStepEntered;
        public event Action OnProcedureComplete;

        public ProcedureStep Current =>
            (currentIndex >= 0 && currentIndex < steps.Count) ? steps[currentIndex] : null;

        public void Begin()
        {
            currentIndex = -1;
            Next();
        }

        public void Next()
        {
            if (currentIndex + 1 >= steps.Count) { OnProcedureComplete?.Invoke(); return; }
            currentIndex++;
            OnStepEntered?.Invoke(Current, currentIndex);
        }

        public void Previous()
        {
            if (currentIndex <= 0) return;
            currentIndex--;
            OnStepEntered?.Invoke(Current, currentIndex);
        }
    }
}
