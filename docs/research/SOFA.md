# SOFA integration plan

**Status:** decision doc, not a commitment.
**Question:** should we use SOFA for tissue + bone physics in
surgeon-sim, and if so, how do we bridge it to Unity on Quest 3?

## What it is

[SOFA](https://www.sofa-framework.org/) is the open-source FEM
framework most surgical simulators are built on. LGPL licensed, ~20
years old, the gold standard for soft-tissue + interaction physics in
surgical training (PixelAffirm, OssoVR, NeuroVR-class systems).

It does what Unity's built-in physics cannot:

- True FEM tissue deformation (corotated linear, hyperelastic, Mooney-Rivlin)
- Cutting and tearing along arbitrary planes
- Voxel/SDF-based bone drilling with material removal
- Haptic-loop-rate (1 kHz) collision and contact
- Constraint-based instrument-tissue coupling

Unity's PhysX is fine for rigid bodies and basic soft body, but it
collapses on the cutting/drilling/contact-rich workloads a surgical
sim demands.

## The Quest 3 reality

SOFA is **CPU-bound** (some GPU acceleration, but the core solver
runs on the host CPU). Quest 3's Snapdragon XR2 Gen 2 has 8 ARM cores
total, ~2-3 of which are available to the app after Meta XR's overhead.
Running SOFA's solver on-device at headset frame rate is **not viable**
for anything but trivial models.

Two architectures are realistic:

### Option A: SOFA as a desktop companion process

SOFA runs on a tethered PC over Quest Link (or future native Quest 3
PC streaming). Unity sends instrument poses; SOFA returns deformed
geometry + force feedback. Pros: full SOFA capability, no perf
ceiling. Cons: requires PC, not standalone, doesn't work in passthrough
mannequin mode without WiFi to a host.

### Option B: Pre-baked SOFA simulations

Run SOFA offline, pre-compute deformation responses to a bank of
canonical interaction scenarios (drill-into-pedicle, tap-screw,
retract-paraspinals), bake into Unity-loadable animations + lookup
tables. Pros: runs standalone on Quest. Cons: no true interactive
deformation; limits believable variety.

### Option C: Tier the simulation

Default to Unity-native physics (PhysX + Obi Softbody) for ambient
deformation. Switch to a SOFA-backed mode when the user is doing the
specific high-fidelity interaction (drilling into a vertebra, cutting
ligamentum flavum). The high-fidelity mode runs the SOFA solver on
the same M5/PC dev box during development; the Quest demo uses
pre-baked outputs.

**Recommendation: option C, with option B as the standalone shipping
mode.** Trying to make SOFA run on Quest natively would consume months
and almost certainly fail.

## Bridging SOFA to Unity

| approach | maturity | notes |
|---|---|---|
| `sofa-unity` plugin | community-maintained | Native plugin, exposes SOFA scenes as Unity components. Last meaningful update was 2023-ish — needs verification. |
| Out-of-process IPC | DIY | SOFA as a subprocess, ZeroMQ / shared memory bridge. Most flexible, most code to write. |
| WebAssembly SOFA | experimental | Some published proofs of concept, not production-ready. |
| Custom port to C# | enormous | Off the table. |

**Recommendation: out-of-process IPC.** Decouples the Unity render
loop from the SOFA solver loop, lets SOFA run on a host that has the
CPU for it, and the protocol surface is small (instrument pose in,
deformed mesh + force out at a fixed rate).

## Hardware on the M5 Max

SOFA builds and runs natively on Apple Silicon (CMake + clang since
SOFA v22). Solver performance on the M5 Max should be excellent —
8 P-cores at sustained boost is more than enough for a 5-10k tetrahedra
spine model at 60-100 Hz. We can develop and tune without ever leaving
the Mac.

## Estimated effort to land a usable PR

- SOFA install + a hello-world scene rendering a deformable mesh: 1-2 days
- Out-of-process bridge protocol design + C# client + SOFA-side server: 3-5 days
- One real interaction (paraspinal retraction) end-to-end: 3-5 days
- Polish, docs, integration with `CaseLoader`: 1-2 days

**~2-3 weeks of focused work.** This is not a single session; it's a
project of its own.

## What an MVP looks like

Not "render a full deformable spine in the headset." A useful first
SOFA PR is:

- SOFA running locally on the M5
- A static lumbar mesh (one of our case_pipeline outputs) loaded into
  a SOFA scene
- A scripted instrument pushing into a paraspinal region, deforming it
- A 30-second video of the result

Once that exists we know the bridge architecture is sound and can
plan the Unity integration properly.

## Decision needed

Two questions before committing a session:

1. **Does the project commit to a tethered-PC mode for high-fidelity
   interactions?** (Option A/C) If we strictly require standalone
   Quest, SOFA's value drops considerably and we might be better
   served by a custom voxel-bone-drilling implementation in C#.
2. **What's the minimum-viable interaction we want SOFA to handle?**
   Drilling? Retraction? Cutting? The answer drives which SOFA
   scene templates we start from.

A sensible alternative until those decisions land: invest the same
effort into Unity-native physics polish + Obi Softbody for visible
deformation, defer SOFA until the project has decided whether
tethered-PC is acceptable.
