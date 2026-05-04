# Architecture

Three layers, intentionally separated so each can be tested or replaced
independently.

```
┌───────────────────────────────────────────────────────────────┐
│  XR layer (Unity, depends on Meta XR SDK)                     │
│  SpineAnchor • VoiceCommandRouter • ProcedureStepMachine      │
│  StreamOverlay • DragonflySession                             │
└────────────────────────────┬──────────────────────────────────┘
                             │ no XR dependencies below this line
┌────────────────────────────▼──────────────────────────────────┐
│  Deterministic core (pure C#, port of dragonfly Python)       │
│  FitEngine                                                    │
└────────────────────────────┬──────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────┐
│  Domain + data                                                │
│  SpineLevel • ImplantSpec • DiscSpaceMeasurement • FitScore   │
│  implant_catalog.json (loaded via ImplantCatalog)             │
└───────────────────────────────────────────────────────────────┘
```

## Why this split

- **The fit engine has zero Unity dependencies.** It runs in a console
  app, in a unit test, and in the editor smoke test. If the ranking is
  wrong, you don't need the headset to debug it.
- **The XR layer holds no spine knowledge.** `VoiceCommandRouter` emits
  events; it does not know what L4-L5 means. The session glue translates
  events to domain calls.
- **The catalog is data, not code.** Regenerated from the canonical
  `dragonfly/spineoptimizer/core/catalog.py` via `tools/port_catalog.py`,
  so we never have two hand-maintained copies drifting apart.

## Data flow during a demo

1. `SpineAnchor` sets the spine root transform from two controller picks.
2. `VoiceCommandRouter` hears "show L5 S1" and fires `OnShowLevel(L5_S1)`.
3. `DragonflySession.SelectLevel` builds a literature-default
   `DiscSpaceMeasurement`, calls `FitEngine.BestFit`, pushes the result
   to `StreamOverlay`.
4. `ProcedureStepMachine.Next` advances the surgeon-facing instruction;
   the overlay redraws.

## Where this should evolve

- **Real anatomy in place of literature defaults.** Today
  `DiscSpaceMeasurement.FromLiterature` is fine for a mannequin demo.
  For real cases, the desktop dragonfly app already extracts patient
  measurements from segmented STL — pipe the result through (or load a
  case JSON) instead of generating from averages.
- **Mesh occlusion using Quest 3 depth API.** When ready, depth occlusion
  makes the spine appear to live inside the mannequin instead of floating
  in front of it. Big perceived-fidelity win for a small code change.
- **Hand tracking** as a fallback when controllers are stowed.
