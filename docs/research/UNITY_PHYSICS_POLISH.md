# Unity-native physics polish

**Status:** the chosen physics direction (replaces deferred SOFA — see
[`SOFA.md`](SOFA.md)).
**Goal:** ship visible, plausible physics on Quest 3 standalone without
a tethered-PC bridge, in weeks not months.

## Three pieces, in priority order

### 1. Bone drilling (custom C# voxel approach)

The hero interaction. Pedicle screws are placed by drilling a pilot
hole, tapping, then driving the screw — the surgeon needs tactile + visual
feedback that a real-feeling burr is removing bone.

**Approach:** the case_pipeline already produces a labelled volume.
Keep a downsampled copy (e.g. 2 mm voxels) of the bone label in memory
alongside the surface mesh. As the drill tip traverses, mark voxels as
removed and rebuild the local surface patch (marching cubes on the
modified region only). Re-meshing a 16x16x16 voxel patch per drill
contact event is well within Quest's frame budget.

**Sources to reference:** the NeuroVR papers (Llinas et al., late-2010s)
described essentially this; surgical sim research has been doing voxel
bone drilling for 15+ years. We don't need to invent anything.

**Estimated effort:** 1 week. Most of it is the local re-meshing and
making sure the visual + audio + controller-haptic feedback line up so
it *feels* like a drill, not a glitch.

### 2. Soft-tissue retraction (Obi Softbody)

Paraspinal muscles need to be pulled aside to expose bone. The user
will not believe a sim where retracted tissue stays where the
controller leaves it stiffly — it has to deform under contact and
spring back when released.

**Approach:** Obi Softbody (Virtual Method, ~$60 on the Asset Store) is
the mature Unity-native option. Particle-based, well-optimised, runs on
Quest. Wrap each soft-tissue mesh from `CaseLoader` in an Obi softbody
component at load time. Tune per material_hint.

**Estimated effort:** 2-3 days. Mostly tuning (stiffness, damping, contact
margins) and making sure the FPS budget on Quest doesn't blow up when
multiple softbodies are active.

### 3. Bleeding (particle + decal)

A passion-project surgical sim that doesn't bleed when bone is drilled
or vessels are nicked feels off, but volumetric blood (Zibra Liquids,
WebGL fluid sims) is overkill on Quest.

**Approach:** GPU particle system emitting from drill contact points,
fading to a screen-space decal that pools on lower surfaces. Visual
fidelity over physical accuracy. Well within Quest's particle budget if
particle counts stay under ~500 alive.

**Estimated effort:** 2-3 days. The particle system itself is half a
day; the rest is making it look right under passthrough lighting,
which is its own art problem.

## What this gets us, what it doesn't

**Gets us:** drilling that looks and sounds real, retracted tissue that
deforms and springs back, blood that pools when things go wrong. All
of it ships on Quest 3 standalone with no host PC.

**Doesn't get us:** true cutting and tearing along arbitrary planes,
dura puncture with realistic CSF leak, vessel-tree blood flow,
real-time interactive FEM. Those are SOFA's territory and stay
deferred.

**Is "as realistic as possible" — bounded by Quest 3.** Mobile GPU and
8 CPU cores set the ceiling regardless of which middleware we pick. The
question is how we use the budget. Drilling + retraction + blood is
where the perceived realism returns are highest.

## Order of work

1. **Bone drilling** first. It's the hero interaction and unblocks every
   later "now place the screw" demo. PR-sized.
2. **Soft-tissue retraction** second. Once the bone is exposed via
   retraction, the drilling demo gets visibly more compelling.
3. **Bleeding** third. Polish; doesn't gate other work but adds a lot of
   visceral feedback when it lands.

Each is its own PR. The first deliverable is a video clip — drilling
into a phantom L5 vertebra with audible burr feedback and visible
voxel removal — runnable on the Quest with no PC attached.

## Dependencies that need to land first

- PR #5 (case_pipeline scaffold) — gives us the labelled volume
  drilling reads from.
- PR #7 (Unity case loader) — gives us the bone GameObject the drill
  interacts with.
- An Obi Softbody license — ~$60. Worth bringing up as a small
  expense before retraction work starts.

## What to do *not* do under this plan

- Build a SOFA bridge speculatively.
- Try to get Nanite or HDRP-class rendering on Quest (won't fit).
- Pretend Quest controllers can simulate burr resistance — they can't.
  Use audio + visual + rumble together to imply force; don't build for
  haptic gloves we don't have.