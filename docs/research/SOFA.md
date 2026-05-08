# SOFA integration plan

**Status:** decided 2026-05-08.
**Decision:** **Defer SOFA.** Invest the same effort into Unity-native physics polish (Obi Softbody for retraction, custom C# voxel-bone drilling, particle blood). Revisit SOFA when (a) a tethered-PC mode is in scope and (b) Unity-native limits are visible to actual users.
**Replacement plan:** [`UNITY_PHYSICS_POLISH.md`](UNITY_PHYSICS_POLISH.md) (next-physics direction).
**Rationale:** at the bottom of this doc.
**Question (resolved):** should we use SOFA for tissue + bone physics in surgeon-sim, and if so, how do we bridge it to Unity on Quest 3?

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

## Decision (2026-05-08): defer

**SOFA is deferred. Replacement plan:
[`UNITY_PHYSICS_POLISH.md`](UNITY_PHYSICS_POLISH.md).** Reasons:

1. **No tethered PC exists today.** The dev box is the M5 Max, demos
   are streamed from a standalone Quest 3. Without a PC in the loop,
   SOFA can't run at the rate the headset needs. Committing to
   tethered-PC mode now means committing to a future hardware setup
   the project doesn't yet have.
2. **2-3 weeks is too much for a pre-validation investment.** The
   value of SOFA is "interactive cutting and tearing fidelity," which
   the surgeons in the audience may or may not care about for a
   stream-demo sim. Spending weeks on a bridge before any user has
   said "Unity-native physics isn't enough" is premature optimization.
3. **Unity-native physics gets us 80% of the visible value.** Obi
   Softbody (mature Unity asset) for retraction, a custom C# voxel
   approach for bone drilling, and particle-based blood ship on Quest
   standalone with no bridge, no second process, no PC.
4. **The decision is reversible.** If user feedback later says "the
   physics looks weak," we can revisit SOFA *then*, after the PC is in
   the loop and after we know specifically which interactions are
   underwhelming. Nothing about the current architecture forecloses
   that.

When to revisit:

- A tethered PC is part of the dev/demo setup.
- Unity-native physics has been pushed to its limit and a specific
  interaction (cutting flavum, tearing dura, dynamic bone fracture)
  is identified as visibly inadequate.
- Or: the project pivots from "stream demo" to "training credentialing
  platform," in which case fidelity requirements shift dramatically
  and SOFA becomes table stakes, not a nice-to-have.

Until then, this doc stays as a record of the analysis. Re-open by
opening a new PR that references it.
