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

- **Unity 6 LTS (6000.0)** with the **XR Interaction Toolkit 3.x** + **OpenXR**
- **Meta XR All-in-One SDK v77** (UPM scoped registry, not the deprecated
  Asset Store package) for passthrough, anchors, hands, controllers
- **Meta Voice SDK** (Wit.ai backend) for on-device voice + intent
- **TextMeshPro** for HUD text
- Optional: **Spout / NDI** plugin for capturing the stream camera into OBS.

Pinned versions live in [`unity/Packages/manifest.json`](unity/Packages/manifest.json).
Setup walkthrough: [`docs/QUEST_SETUP.md`](docs/QUEST_SETUP.md).
Curated open-source stack (anatomy models, references): [`docs/OPEN_SOURCE_STACK.md`](docs/OPEN_SOURCE_STACK.md).

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
│   ├── spineoptimizer/       TDR fit engine (mirrored to C#)
│   ├── case_pipeline/        Case authoring: spec JSON -> labelled volume -> glTF + manifest
│   └── simulation_assets/    Neutral trajectories from offline simulators -> Unity replay
├── unity/Assets/
│   ├── Scripts/
│   │   ├── Domain/           SpineLevel, ImplantSpec, DiscSpaceMeasurement, FitScore
│   │   ├── Fitting/          FitEngine — C# port of the Python ranker
│   │   ├── Catalog/          ImplantCatalog — loads JSON from Resources
│   │   ├── Anchoring/        SpineAnchor — two-point lock to mannequin
│   │   ├── Voice/            VoiceCommandRouter — keyword grammar
│   │   ├── Step/             ProcedureStepMachine — linear sequencer
│   │   ├── Stream/           StreamOverlay — HUD for the Twitch camera
│   │   ├── Simulation/       InstrumentTrajectoryReplay — offline sim motion playback
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

| Python (`python/core/`)  | C# (`unity/Assets/Scripts/`) |
|---|---|
| `implant_predictor.py`   | `Fusion/ImplantPredictor.cs` (pedicle screw + rod sizing, validation) |
| `tray_optimizer.py`      | `Fusion/TrayOptimizer.cs` (per-case tray reduction) |
| `plan_generator.py`      | not ported — ReportLab PDF, kept Python-only; Quest builds the in-headset HUD via `Stream/StreamOverlay.cs` |

The fusion-side Domain types live in `Domain/VertebraLevel.cs`,
`Domain/ImplantPlan.cs`, `Domain/LandmarkSet.cs`, and
`Domain/TrayConfiguration.cs`. Run the editor smoke test at
**Tools > Dragonfly > Run Fusion Predictor Smoke Test** to exercise the
fusion port without launching XR.

## Case authoring

Patient cases are built from JSON specs, not hand-authored. The
`python/case_pipeline/` package turns a `CaseSpec` into a labelled CT-like
volume, runs marching cubes per anatomical structure, decimates, smooths,
and emits one glTF per structure plus a `manifest.json`. Unity loads the
output via Addressables.

```
cd python
python -m case_pipeline.cli case_pipeline/specs/literature_default.json out/cases/lit_default
python -m case_pipeline.smoke_test  # end-to-end + determinism check
```

This PR ships the parametric phantom volume source. A later PR will add a
`segmented_ct` source backed by TotalSegmentator over a synthetic CT; the
downstream meshing + manifest stages don't change.

See [`python/case_pipeline/README.md`](python/case_pipeline/README.md) for
the pipeline diagram and dependency list.

## Offline simulator trajectories

External simulators stay out of the Quest runtime. ORBIT-Surgical, iMSTK
desktop experiments, or scripted demos should export neutral instrument
trajectory JSON via `python/simulation_assets/`. Unity replays that data
with `Simulation/InstrumentTrajectoryReplay.cs`.

```
cd python
PYTHONPATH=. python3 -m simulation_assets.export_demo_trajectory out/demo_needle_lift.json
PYTHONPATH=. python3 -m simulation_assets.smoke_test
```

Bundled copy for Unity editor checks lives at
`unity/Assets/StreamingAssets/trajectories/demo_needle_lift.json` (regenerate with the same module into that path).

Robomimic HDF5 from ORBIT-Surgical / Isaac Lab → trajectory JSON (needs `pip install h5py`):

```
PYTHONPATH=. python3 -m simulation_assets.orbit_robomimic_hdf5_to_trajectory --hdf5 dataset.hdf5 --list-structure
```

See [`python/simulation_assets/README.md`](python/simulation_assets/README.md).

In Unity, run **Tools > Dragonfly > Load Instrument Trajectory...** and pick
the exported JSON, or **Tools > Dragonfly > Load bundled demo trajectory (StreamingAssets)** for the checked-in fixture. The editor test creates a capsule, applies the final pose,
and logs trajectory id, sample count, and duration.

## Getting it running

See [`docs/QUEST_SETUP.md`](docs/QUEST_SETUP.md) for the full walkthrough.
Short version:

1. Clone, open `unity/` in **Unity 6 LTS**. UPM auto-resolves Meta XR v77
   from the scoped registry pinned in `Packages/manifest.json`.
2. Switch platform to Android, set the device to Quest 3, hit **Build &
   Run** with the headset attached over USB-C.
3. Run **Tools > Dragonfly > Run Fit Engine Smoke Test** to confirm the
   deterministic core works without the headset.
4. In the headset, point the right controller at the mannequin and pull
   the trigger twice (caudal then cranial) to anchor the spine model.

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
