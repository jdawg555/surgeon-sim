# dragonfly-xr

Immersive spine-surgery overlay for Meta Quest 3.

Dragonfly's deterministic spine logic, rendered as a passthrough-AR overlay
locked to a real mannequin or table. Voice-driven, step-paced, and built to
demo well on stream.

## Status

Day-zero scaffold. The deterministic core (level taxonomy, implant catalog,
fit ranking) is ported from `dragonfly` Python to C# and is unit-testable in
the Unity editor without putting the headset on. The XR layer — anchoring,
voice routing, step machine, stream overlay — is wired up but needs a Unity
project, the Meta XR Core SDK, and the spine reference mesh imported before
it runs on a Quest.

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
dragonfly-xr/
├── README.md
├── docs/
│   ├── ARCHITECTURE.md       Subsystem map and data flow
│   ├── DEMO_SCRIPT.md        Twitch run-of-show
│   └── VOICE_COMMANDS.md     Surgeon-facing grammar
├── unity/Assets/
│   ├── Scripts/
│   │   ├── Domain/           SpineLevel, ImplantSpec, DiscSpaceMeasurement, FitScore
│   │   ├── Fitting/          FitEngine — port of dragonfly's deterministic ranker
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
    └── port_catalog.py       Regenerate JSON from dragonfly's Python catalog
```

## What's reused from dragonfly

| Source | Ported to | Notes |
|---|---|---|
| `spineoptimizer/core/models.py` | `Domain/*.cs` | Enums + dataclasses, 1:1 |
| `spineoptimizer/fitting/fit_engine.py` | `Fitting/FitEngine.cs` | Pure math; same weights (0.40 / 0.35 / 0.25) |
| `spineoptimizer/core/catalog.py` | `Resources/implant_catalog.json` | 22 SKUs, lumbar + cervical TDR |
| `research/processed/case01/bone_segment.stl` | (drop into `Models/`) | Reference L1-L5 mesh, retopologize for VR |

## Getting it running

1. `git clone` and open `unity/` as a new Unity 2022 LTS project.
2. Install the Meta XR Core SDK (Asset Store) and TextMeshPro Essentials.
3. Run **Tools > Dragonfly > Run Fit Engine Smoke Test** in the editor.
   Console should print top-3 implants for every spine level.
4. Build to Quest 3, point at a mannequin, pull the right trigger twice
   (caudal then cranial) to anchor the spine model.

## Streaming notes

`DEMO_SCRIPT.md` has the run-of-show. Quick version: cast the headset to OBS
via Meta's mobile companion app or `adb scrcpy`, run a separate stream camera
in Unity that renders the HUD only, composite the two in OBS.

## Companion repos

This repo is part of the Dragonfly family:

- [dragonfly](https://github.com/RexxGames/dragonfly) — desktop spine platform
- [dragonfly-core](https://github.com/RexxGames/dragonfly-core) — deterministic prediction core
- [dragonfly-ai](https://github.com/RexxGames/dragonfly-ai) — optional LLM layer
- [dragonfly-dashboard](https://github.com/RexxGames/dragonfly-dashboard) — rep / ASC web UI
- [dragonfly-insights-api](https://github.com/RexxGames/dragonfly-insights-api) — analytics API
- [dragonfly-infra](https://github.com/RexxGames/dragonfly-infra) — Terraform / K8s / CI

No PHI in this repo. Mannequin demo only.
