using System;
using System.Collections.Generic;
using System.Linq;
using Dragonfly.XR.Domain;
using UnityEngine;

#if !UNITY_ANDROID && (UNITY_STANDALONE_WIN || UNITY_EDITOR_WIN)
using UnityEngine.Windows.Speech;
#endif

namespace Dragonfly.XR.Voice
{
    // Voice routing for the demo. On Quest, prefer Meta Voice SDK / Wit.ai
    // (set #define DRAGONFLY_USE_META_VOICE in Player Settings); on the
    // Windows editor, fall back to KeywordRecognizer for fast iteration.
    //
    // Surgeon-facing grammar is intentionally narrow and unambiguous:
    //   "show <level>"        → highlight a spine level (e.g. "show L5 S1")
    //   "next step" / "back"  → step machine
    //   "show implant"        → render best-fit implant overlay
    //   "hide implant"        → clear overlay
    //   "anchor reset"        → drop current anchor, re-anchor to mannequin
    public class VoiceCommandRouter : MonoBehaviour
    {
        public event Action<SpineLevel> OnShowLevel;
        public event Action OnNextStep;
        public event Action OnPreviousStep;
        public event Action OnShowImplant;
        public event Action OnHideImplant;
        public event Action OnAnchorReset;

#if !UNITY_ANDROID && (UNITY_STANDALONE_WIN || UNITY_EDITOR_WIN)
        KeywordRecognizer _recognizer;
#endif

        static readonly Dictionary<string, SpineLevel> LevelPhrases = new()
        {
            { "show c three c four", SpineLevel.C3_C4 },
            { "show c four c five", SpineLevel.C4_C5 },
            { "show c five c six", SpineLevel.C5_C6 },
            { "show c six c seven", SpineLevel.C6_C7 },
            { "show l one l two", SpineLevel.L1_L2 },
            { "show l two l three", SpineLevel.L2_L3 },
            { "show l three l four", SpineLevel.L3_L4 },
            { "show l four l five", SpineLevel.L4_L5 },
            { "show l five s one", SpineLevel.L5_S1 },
        };

        void Start()
        {
#if !UNITY_ANDROID && (UNITY_STANDALONE_WIN || UNITY_EDITOR_WIN)
            var keywords = LevelPhrases.Keys
                .Concat(new[] { "next step", "back", "show implant", "hide implant", "anchor reset" })
                .ToArray();
            _recognizer = new KeywordRecognizer(keywords);
            _recognizer.OnPhraseRecognized += OnPhrase;
            _recognizer.Start();
#endif
        }

#if !UNITY_ANDROID && (UNITY_STANDALONE_WIN || UNITY_EDITOR_WIN)
        void OnPhrase(PhraseRecognizedEventArgs args) => Dispatch(args.text);

        void OnDestroy()
        {
            if (_recognizer != null && _recognizer.IsRunning) _recognizer.Stop();
            _recognizer?.Dispose();
        }
#endif

        // Public so a Meta Voice SDK callback or unit test can drive the router.
        public void Dispatch(string phrase)
        {
            phrase = (phrase ?? "").Trim().ToLowerInvariant();
            if (LevelPhrases.TryGetValue(phrase, out var level)) { OnShowLevel?.Invoke(level); return; }
            switch (phrase)
            {
                case "next step": OnNextStep?.Invoke(); break;
                case "back": OnPreviousStep?.Invoke(); break;
                case "show implant": OnShowImplant?.Invoke(); break;
                case "hide implant": OnHideImplant?.Invoke(); break;
                case "anchor reset": OnAnchorReset?.Invoke(); break;
            }
        }
    }
}
