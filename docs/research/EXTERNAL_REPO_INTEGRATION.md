# External repo integration

Status: researched 2026-05-10.

Question: how should surgeon-sim use these repos?

- `simoninithomas/awesome-ai-tools-for-game-dev`
- `orbit-surgical/orbit-surgical`
- `iMSTK/iMSTK`

## Recommendation

Use all three, but at different levels:

1. Use `awesome-ai-tools-for-game-dev` as a curated tool source, not as a
   code dependency.
2. Use `ORBIT-Surgical` as an offline robotics and learning workbench,
   not as a Quest runtime dependency.
3. Use `iMSTK` as a reference implementation source for surgical physics,
   plus a possible desktop companion process later. Do not embed it in the
   standalone Quest app.

The Quest build should remain Unity-first. External engines should feed
assets, policies, animation clips, parameters, and reference behavior into
Unity rather than becoming hard runtime dependencies.

## Repo roles

### Awesome AI Tools for Game Developers

Use for workflow selection:

- Speech recognition options: Whisper / Wav2Vec alternatives to Meta Voice.
- Voice generation options: prototype non-clinical narration and demo audio.
- Asset and texture generation options: placeholder props, UI boards,
  procedural texture ideas, and stream-safe mock assets.
- C# / Python interop ideas: useful pointers such as Python.NET or Unity to
  Python socket patterns.

Do not vendor this repo. It is a list, not a library.

### ORBIT-Surgical

Use for robot-skill training and offline simulation:

- Good fit for surgical robot control experiments, especially PSM / STAR
  reach, lift, teleoperation, demonstration capture, and RL / imitation
  learning workflows.
- Built on Isaac Sim 4.1 and Isaac Lab, Python 3.10, Linux 64-bit, and
  GPU-heavy Omniverse infrastructure.
- Uses Gym-style environment registration and Isaac Lab manager-based
  environment configs for observations, rewards, actions, events,
  curricula, and terminations.

Integration shape:

- Keep ORBIT-Surgical outside the Unity app.
- Export trained policies, trajectories, tool poses, instrument motion clips,
  or task metadata into neutral formats.
- Consume those outputs in `surgeon-sim` through the Python case pipeline or
  Unity resources.

Good first use:

- Create a small offline "instrument motion dataset" exporter from
  ORBIT-Surgical demonstrations, then import those trajectories into Unity
  as replayable scripted instrument motion.

### iMSTK

Use for surgical physics references and desktop experiments:

- Apache-2.0 licensed, C++ surgical simulation toolkit.
- Development/support was discontinued as of 2025-05-02, so treat it as
  stable reference code rather than an actively maintained platform.
- Relevant examples include PBD tissue cutting, tissue needle contact,
  tissue grasping, suturing, SDF haptics, virtual coupling, rigid body
  laparoscopic tool collision, and volume rendering.
- Has SWIG-based C# wrapper support, but the wrapper is documented as work in
  progress and tested against the 5.0 release path.

Integration shape:

- For standalone Quest: port the simple behavioral ideas into Unity-native
  C# systems where needed.
- For high-fidelity desktop mode: run iMSTK as an out-of-process simulator
  and send tool poses in, then mesh or force state out.
- Avoid linking iMSTK directly into the Quest Android build unless a narrow
  prototype proves build, performance, and deployment viability.

Good first use:

- Recreate a small Unity-native prototype inspired by iMSTK's PBD tissue cut
  or needle contact examples, using our own simplified mesh/voxel state.

## Data flow target

```text
AI/game-dev tools
  -> asset/audio/voice/tooling choices

ORBIT-Surgical / Isaac Sim
  -> robot demonstrations, trajectories, policies, task metadata
  -> surgeon-sim Python import/export tools
  -> Unity resources and scripted procedure playback

iMSTK desktop experiments
  -> physics reference behavior, deformation/cutting parameters, test scenes
  -> Unity-native approximations or optional desktop companion bridge
```

## Near-term implementation plan

1. Add a neutral trajectory format under the Python side, for example
   `case_pipeline` or a new `simulation_assets` package:
   instrument id, timestamp, pose, gripper state, contact state, and optional
   annotation. Done in `python/simulation_assets/trajectory.py`.
2. Add a Unity loader that reads those trajectories from disk, `Resources`, or
   Addressables and replays them through a deterministic replay component.
   First disk-backed editor path is in
   `unity/Assets/Scripts/Simulation/InstrumentTrajectoryReplay.cs`.
3. Run ORBIT Robomimic HDF5 → JSON via
   `python -m simulation_assets.orbit_robomimic_hdf5_to_trajectory` (requires
   `h5py`) or export demonstrations from your fork into the same schema.
4. Prototype one iMSTK-inspired Unity interaction: tissue puncture, tissue
   cut, or tool contact. Keep it in a feature folder and benchmark it on
   Quest before expanding.
5. Keep the awesome AI tools repo as a research source. When a tool is
   selected, document the actual dependency in `OPEN_SOURCE_STACK.md`.

## Guardrails

- No clinical claims. This remains a mannequin / phantom demo.
- No PHI, DICOM headers, or patient-identifiable assets.
- No hard Isaac Sim or iMSTK runtime dependency in the Quest app.
- Favor neutral interchange files over engine coupling.
- License-check every actual dependency before adding it to the build.
