# surgeon-sim

Immersive spine-surgery simulator for Meta Quest 3.

A deterministic spine-surgery core (implant fit ranking, pedicle screw +
rod prediction, tray optimization) rendered as a passthrough-AR overlay
locked to a real mannequin or table. Voice-driven, step-paced, built to
demo well on stream.

## Status

Day-zero scaffold. The deterministic core (level taxonomy, implant catalog,
fit ranking) lives in Python under `python/` and is mirrored to C# under
`unity/Assets/Scripts/`. Both can be exercised in isolation: run the Python
modules from a REPL, or run the editor smoke test in Unity without putting
the headset on. The XR layer — anchoring, voice routing, step machine,
stream overlay — is wired up but needs a Unity project, the Meta XR Core
SDK, and a spine reference mesh imported before it runs on a Quest.

## Stack

- **Unity 2022 LTS** with the **XR Interaction Toolkit**
- **Meta XR Core SDK** for passthrough + controller pose tracking
- **TextMeshPro** for HUD text
- Optional: **Meta Voice SDK / Wit.ai** for on-device voice. The bundled
  `VoiceCommandRouter` falls back to `KeywordRecognizer` on the Windows
  editor for fast iteration.
- Optional: **Spout / NDI** plugin for capturing the stream camera into OBS.

## Repo layout

```
surgeon-sim/
├── README.md
├── docs/
│   ├── ARCHITECTURE.md       Subsystem map and data flow
│   ├── DEMO_SCRIPT.md        Twitch run-of-show
│   └── VOICE_COMMANDS.md     Surgeon-facing grammar
├── python/                   Reference implementation (canonical)
│   ├── core/                 Pedicle screw + rod prediction, tray + plan
│   └── spineoptimizer/       TDR fit engine (mirrored to C#)
├── unity/Assets/
│   ├── Scripts/
│   │   ├── Domain/           SpineLevel, ImplantSpec, DiscSpaceMeasurement, FitScore
│   │   ├── Fitting/          FitEngine — C# port of the Python ranker
│   │   ├── Catalog/          ImplantCatalog — loads JSON from Resources
│   │   ├── Anchoring/        SpineAnchor — two-point lock to mannequin
│   │   ├── Voice/            VoiceCommandRouter — keyword grammar
│   │   ├── Step/             ProcedureStepMachine — linear sequencer
│   │   ├── Stream/           StreamOverlay — HUD for the Twitch camera
│   │   ├── Editor/           FitEngineSmokeTest editor menu
│   │   └── DragonflySession  Top-level wire-up MonoBehaviour
│   ├── Resources/
│   │   └── implant_catalog.json
│   └── Models/               (drop spine reference meshes here)
└── tools/
    └── port_catalog.py       Regenerate JSON from python/spineoptimizer
```

## Python ↔ C# parity

| Python (`python/spineoptimizer/`) | C# (`unity/Assets/Scripts/`) |
|---|---|
| `core/models.py` | `Domain/SpineLevel.cs`, `ImplantSpec.cs`, `DiscSpaceMeasurement.cs` |
| `core/catalog.py` | `Resources/implant_catalog.json` (regenerate via `tools/port_catalog.py`) |
| `fitting/fit_engine.py` | `Fitting/FitEngine.cs` — same 0.40 / 0.35 / 0.25 weights |

`python/core/` (pedicle screw + rod predictor, tray optimizer, plan
generator) covers the fusion-procedure side and has not been ported to
C# yet — Quest visualization can call out to a Python service or wait for
a port, depending on demo scope.

## Getting it running

1. Clone and open `unity/` as a new Unity 2022 LTS project.
2. Install the Meta XR Core SDK (Asset Store) and TextMeshPro Essentials.
3. Run **Tools > Dragonfly > Run Fit Engine Smoke Test** in the editor.
   Console should print top-3 implants for every spine level.
4. Build to Quest 3, point at a mannequin, pull the right trigger twice
   (caudal then cranial) to anchor the spine model.

To exercise the Python core directly:

```
pip install numpy reportlab
python -c "from python.spineoptimizer.fitting.fit_engine import best_fit; \
           from python.spineoptimizer.core.models import DiscSpaceMeasurement, SpineLevel; \
           print(best_fit(DiscSpaceMeasurement.from_literature(SpineLevel.L4_L5)))"
```

## Streaming notes

`docs/DEMO_SCRIPT.md` has the run-of-show. Quick version: cast the headset
to OBS via Meta's mobile companion app or `adb scrcpy`, run a separate
stream camera in Unity that renders the HUD only, composite the two in OBS.

## Scope

Mannequin / phantom demo only. No PHI handling. No clinical-decision use.
