# Open-source stack

Curated list of the third-party pieces this project leans on or could
adopt. Pinned for license sanity; check before adding new dependencies.

## Hard dependencies (already wired in `Packages/manifest.json`)

| Package | Version | License | Purpose |
|---|---|---|---|
| Meta XR All-in-One SDK | 77.0.0 | Oculus SDK License | Passthrough, anchors, controllers, hands |
| Meta XR Voice SDK | 77.0.0 | Oculus SDK License | On-device voice + Wit.ai intent |
| Unity OpenXR Plugin | 1.13.2 | Unity Companion | Quest 3 OpenXR runtime |
| Unity XR Interaction Toolkit | 3.1.2 | Unity Companion | Interaction primitives |
| Unity Input System | 1.11.2 | Unity Companion | Controller / hand input |
| TextMeshPro | 3.2.0-pre.10 | Unity Companion | HUD text |

The Oculus SDK License lets you ship apps on Quest. It does not let you
fork the SDK or redistribute it standalone — fine for our use, just don't
copy Meta's source files into this repo.

## Anatomy models (pick one for the spine reference mesh)

Drop the result into `unity/Assets/Models/`. Retopologize for VR
(target ~30k tris for the full L1-S1 segment).

### BodyParts3D / Anatomography — recommended
- https://lifesciencedb.jp/bp3d/
- License: **CC BY-SA 2.1 JP** (compatible with public repo, requires
  attribution + share-alike on derivatives)
- Format: OBJ, STL
- Coverage: full skeleton; lumbar L1-L5 and pelvis are separately
  segmented meshes you can import individually.

### Z-Anatomy
- https://github.com/LluisV/Z-Anatomy
- License: **CC BY-SA 4.0**
- Format: Blend, FBX
- Coverage: well-segmented full atlas with pre-built scenes; heavier
  poly count than BodyParts3D, but better topology for shading.

### NIH 3D Print Exchange
- https://3d.nih.gov (search "lumbar vertebra", "pelvis CT")
- License: usually **CC0** or **CC BY** (check per-asset)
- Format: STL
- Coverage: patient-derived CT segmentations, more realistic geometry,
  but variable quality and per-vertebra not always pre-separated.

Avoid TurboSquid / Sketchfab "free" models — most are CC BY-NC or have
unclear licensing. Skip them for anything we plan to demo publicly.

## Reference projects (read for patterns, do not vendor)

### 3D Slicer + SlicerVirtualReality
- https://github.com/KitwareMedical/SlicerVirtualReality
- License: BSD
- Why: canonical open-source DICOM → VR pipeline. If we add real
  patient data later, mirror Slicer's volume rendering + segmentation
  workflow rather than rolling our own.

### UnityVolumeRendering
- https://github.com/mlavik1/UnityVolumeRendering
- License: MIT
- Why: drop-in DICOM/NIfTI volume renderer for Unity. Direct path to
  showing CT volumes inside the Quest scene if/when we want that.

### ImHotep
- https://github.com/ImHotepCloud/ImHotep-Open
- License: MIT
- Why: medical VR viewer in Unity. Older code, but the scene
  structure for "patient + tools + UI in VR" is worth a read.

### ORBIT-Surgical
- https://github.com/orbit-surgical/orbit-surgical
- License: BSD-3-Clause
- Why: Isaac Sim / Isaac Lab surgical robot simulation, teleoperation,
  RL, imitation learning, and demonstration workflows. Use as an
  offline robotics workbench that exports trajectories or policies into
  Unity-readable data. Do not make Isaac Sim a Quest runtime dependency.

### iMSTK
- https://gitlab.kitware.com/iMSTK/iMSTK
- License: Apache-2.0
- Why: surgical simulation reference code for tissue cutting, needle
  contact, suturing, haptics, collision, and PBD/FEM-style interactions.
  The project is sunsetted as of 2025-05-02, so use it as reference or a
  desktop companion prototype, not as a hard Quest dependency.

### SOFA Framework
- https://github.com/sofa-framework/sofa
- License: LGPL
- Why: open-source soft-tissue / FEM simulation. Way overkill for the
  current scope, but if we ever need haptic feedback or tissue
  deformation, SOFA is the open-source answer.

### whisper.unity
- https://github.com/Macoron/whisper.unity
- License: MIT
- Why: fully on-device Whisper.cpp wrapper, no cloud round-trip.
  Alternative to Wit.ai if the HIPAA story matters more than wake-word
  ergonomics — you'd write your own intent parsing on top of raw
  transcription.

### Awesome AI Tools for Game Developers
- https://github.com/simoninithomas/awesome-ai-tools-for-game-dev
- License: check each linked tool
- Why: curated discovery list for AI-assisted game-dev tooling: asset
  generation, texture generation, speech recognition, voice generation,
  conversational models, and Unity/Python interop references. Use it for
  vendor/tool selection, not as source code.

### SurgeonLife (internal)
- Already in your repos. Patterns worth borrowing: data-driven
  procedure steps via ScriptableObject, event-based decoupling between
  managers and UI. Architecture noted in
  [ARCHITECTURE.md](ARCHITECTURE.md).

## Streaming

| Tool | License | Purpose |
|---|---|---|
| OBS Studio | GPL-2.0 | Stream broadcast |
| KlakSpout (https://github.com/keijiro/KlakSpout) | Unlicense | Unity → OBS via Spout texture share |
| scrcpy (https://github.com/Genymobile/scrcpy) | Apache-2.0 | Mirror headset to PC for OBS Window Capture |

## Things deliberately not on this list

- **Asset Store "Oculus Integration"** — deprecated in 2023, replaced by
  the UPM packages above. Don't import it.
- **Photon / Mirror multiplayer** — not multi-user yet, no need.
- **DOTS / ECS** — overkill for the scene scale we're targeting.
- **AR Foundation** — fine on phones, but for Quest 3 the Meta XR SDK
  is the lower-friction path to passthrough + hand tracking.
