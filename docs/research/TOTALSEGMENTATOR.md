# TotalSegmentator integration plan

**Status:** decided 2026-05-08.
**Decision:** **Option 1 (CT + geometric disc synthesis).** Greenlit for the next implementation session, ~2.5 days of focused work.
**Rationale:** at the bottom of this doc.
**Question (resolved):** is TotalSegmentator the right second volume source for `python/case_pipeline`?

## What it is

[TotalSegmentator](https://github.com/wasserth/TotalSegmentator) is an
open-source nnUNet-based segmentation tool that takes a CT volume in
NIfTI / DICOM and produces per-structure segmentation masks. Apache-2.0,
~2 GB of pre-trained weights, GPU strongly preferred but CPU works.

## Why we want a second source

The parametric phantom is fine for stream demos and case-pipeline
testing, but it is anatomically simple. To get realism past "literature
mean lumbar," we need volumes whose surface detail comes from real
anatomy variation: real vertebra shapes, real soft-tissue envelopes,
real cord curvature. Running TotalSegmentator over a synthetic CT (or
later, a public anonymised CT) gives us exactly that, and reuses the
same downstream meshing + glTF stages we just built.

## The disc gap (CT path)

TotalSegmentator's `total` task (CT) segments **117 structures**
including `vertebrae_L1`..`vertebrae_S1` and `spinal_cord`. It **does
not segment intervertebral discs**, dura, or paraspinals individually
on CT. For our case_pipeline we need:

| our label | TotalSegmentator class | gap |
|---|---|---|
| `vertebral_body` | `vertebrae_L1`..`vertebrae_S1` (merge) | ✓ |
| `spinal_cord` | `spinal_cord` | ✓ |
| `disc` | — | ✗ no class |
| `dura` | — | ✗ no class |
| `soft_tissue` | derive from `body_trunk` − bones − cord | ⚠ derivable |
| `skin` | derive from `body_trunk` outer shell | ⚠ derivable |

The disc gap is the actual blocker. Three options:

1. **Geometric synthesis.** After TotalSegmentator labels vertebrae,
   compute the volume between adjacent vertebra masks (along the column
   axis) and label it as a disc. Fast, deterministic, accuracy depends
   on how clean vertebral endplates segment. Estimated effort: 1 day.
2. **Second-stage disc model.** Train or import a separate nnUNet model
   on a lumbar disc dataset (e.g.
   [SpineCheck](https://github.com/anjany/verse) or open MRI-derived).
   Highest fidelity, requires training infra and data. Estimated
   effort: 1-2 weeks if a pre-trained model exists; 1-2 months if we
   train.
3. **Skip discs from segmentation.** Synthesise discs purely from
   geometry (current phantom approach) and only use TotalSegmentator
   for bone + cord. Drops realism but unblocks the rest.

**Recommendation: option 1.** Geometric synthesis off real vertebra
masks gets us 80% of the realism for 5% of the effort, and we can
upgrade to option 2 later without changing the case_pipeline interface.

### Pivot path if we want real disc fidelity later

The MRI ecosystem has filled this gap since the original draft of this
doc. Two alternatives exist if we ever want disc segmentation that
isn't synthetic:

- **TotalSegmentator's `total_mr` task** — TotalSegmentator's MRI
  variant *does* segment intervertebral discs. Requires synthesizing
  an MRI volume, which is non-trivial because tissue contrast is
  sequence-dependent and much harder to fake than CT HU values.
- **TotalSpineSeg** (neuropoly, 2024) — a separate nnUNet-based tool
  purpose-built for spine MRI: vertebrae + discs + cord + canal in one
  shot. Strongest fidelity but adds a second model to maintain.

Neither is on the path right now. The CT path with geometric discs is
the simpler, faster, more controllable starting point, and the
case_pipeline interface keeps the door open to switching sources
later without reworking the meshing or export stages.

## Hardware on the M5 Max

- TotalSegmentator's PyTorch backend: **MPS works** but is ~5x slower
  than CUDA on similar-tier dGPUs, and a few ops fall back to CPU. For
  a single 256³ volume, expect **~2-4 minutes** end-to-end on M5.
- Model weights: ~2 GB on first download, cached at
  `~/.totalsegmentator/`.
- Memory: comfortably fits in 36 GB unified memory; OK on the M5 Max
  base configuration.

## Where it slots into the pipeline

```
CaseSpec
   │
   ├── source: "phantom"           ──> phantom.generate (current)
   │
   └── source: "totalsegmentator"  ──> ct_synthesis.generate_hu(spec)
                                       totalseg_runner.segment(hu_volume)
                                       label_remap.to_case_taxonomy(masks)
                                       disc_synthesis.fill_gaps(labels) [option 1]
                                  └─> labelled volume (same downstream)
```

`pipeline.build_case` would dispatch on `spec.source` (a new field) and
call the right pre-stage. Meshing + export stay unchanged.

## Estimated effort to land a usable PR

- Synthetic CT (HU-valued volume from existing PhantomSpec): 0.5 day
- TotalSegmentator wrapper + label remap: 0.5 day
- Disc geometric synthesis (option 1): 1 day
- Tests, edge cases, docs: 0.5 day

**~2.5 days of focused work.** Worth committing a dedicated session.

## What we'd ship

- `python/case_pipeline/ct_synthesis.py` — turns a PhantomSpec into an
  HU volume (bone +600, soft tissue +40, fat -100, air -1000).
- `python/case_pipeline/segmenters/totalseg.py` — runs TS via its
  Python API, returns label arrays in our taxonomy.
- `python/case_pipeline/specs/<name>.json` — example spec with
  `source: "totalsegmentator"`.
- Smoke test: builds one TS-backed case, asserts all six structures
  exist with sensible triangle counts.

## Open questions

- Does TotalSegmentator's licensing remain Apache-2.0 in 2026? (Was
  Apache-2.0 last we checked, no obvious change pending.)
- Do we want to ship pre-segmented cases in the repo, or always
  regenerate? Pre-segmented = faster CI / Quest demo. Always-regenerate
  = repo stays small. Suggest: ship the spec + manifest, regenerate the
  segmentation in CI nightly.

## Decision (2026-05-08)

**Option 1: CT + TotalSegmentator (`total` task) + geometric disc
synthesis.** Reasons:

1. **CT synthesis is tractable.** The existing `phantom.py` already
   produces a labelled volume; converting labels to plausible HU
   values (bone +600, soft tissue +40, fat -100, air -1000, plus
   noise) is a hundred lines.
2. **MRI synthesis is not.** Sequence-dependent contrast, motion,
   chemical-shift artefacts — the synthetic MRI would be a project of
   its own and would still be a poor input to `total_mr` because the
   contrast wouldn't match its training distribution.
3. **Disc fidelity is not the bottleneck.** Pedicle-screw planning and
   construct visualisation are the demos. Discs need to look correct
   between vertebrae; they don't need to match a particular patient.
   Geometric synthesis does that job.
4. **The interface is forward-compatible.** Switching to `total_mr` or
   TotalSpineSeg later only requires swapping the segmenter module;
   meshing, manifest, and Unity-side loader don't change.

Next session deliverables (per the "Estimated effort to land a usable
PR" section above): synthetic CT, TotalSegmentator wrapper, label
remap, geometric disc synthesis, smoke test.
