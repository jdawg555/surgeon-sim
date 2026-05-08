# case_pipeline/

Builds Quest-loadable patient cases from a JSON spec. Deterministic, no
hand-editing of meshes, no real DICOM. The output is what Unity Addressables
loads at runtime.

## Pipeline

```
CaseSpec (JSON)
   │
   ▼
phantom.generate     parametric labelled volume (uint8, mm-spaced)
   │
   ▼
meshing.extract      marching cubes per label, decimate, smooth
   │
   ▼
export.write_*       one .glb per structure + manifest.json
   │
   ▼
<out_dir>/
  manifest.json
  meshes/skin.glb
  meshes/soft_tissue.glb
  meshes/disc.glb
  meshes/dura.glb
  meshes/spinal_cord.glb
  meshes/vertebra_L1.glb
  meshes/vertebra_L2.glb
  meshes/vertebra_L3.glb
  meshes/vertebra_L4.glb
  meshes/vertebra_L5.glb
  meshes/vertebra_S1.glb
  spec.json
```

Per-vertebra meshes (one .glb per level rather than a single merged
bone mesh) so the surgeon can highlight or select an individual
vertebra in Unity for screw planning. All vertebra structures share
the same `bone` material_hint, so the Unity loader applies one bone
material across them.

## Usage

```bash
cd python
python -m case_pipeline.cli specs/literature_default.json out/cases/literature_default
```

Or programmatically:

```python
from case_pipeline import CaseSpec, build_case
spec = CaseSpec.from_json_file("specs/literature_default.json")
manifest = build_case(spec, "out/cases/literature_default")
```

## Volume sources

This PR ships the parametric phantom only. The phantom is a synthetic
torso with a lumbar column, discs, dura, and cord. Not anatomically
faithful in fine detail — the goal is a deterministic, regeneratable
volume that exercises the same mesh + export stages real segmented data
will go through.

A later PR will add a `segmented_ct` source that runs TotalSegmentator
over a synthetic CT and feeds its labels into the same downstream stages.
The output layout doesn't change.

## Pathology

The phantom anatomy is healthy by default. Set
`spec.phantom.pathology` to layer in clinically realistic perturbations:

| field | type | effect |
|---|---|---|
| `degenerative_disc` | `{level_pair: severity 0..1}` | Reduces disc height. Severity 1.0 collapses the disc to ~15% of normal height (floored at 1 mm). |
| `spondylolisthesis` | `{level_pair: anterior_mm}` | Translates the upper vertebra of the pair, and every level above it, anteriorly by `anterior_mm`. The lower vertebra anchors. |
| `scoliosis_cobb_deg` + `scoliosis_apex_level` | `float`, `str` | Smooth lateral curvature peaking at the named vertebra. Sign of `cobb_deg` picks left/right convexity. |

Pathologies stack: a degenerative L5-S1 disc plus an L5-S1 slip plus a
right-convex curve apexing at L3 is one valid `Pathology` value. See the
example specs in `specs/`:

- `degen_l4_l5.json` — moderate L4-L5 disc disease, mild L5-S1
- `spondy_l5_s1.json` — Grade 1 isthmic spondylolisthesis at L5-S1
- `scoliosis_l3_apex.json` — 25° right-convex Cobb apexing at L3

What pathology does *not* cover yet: osteophytes, facet hypertrophy,
canal stenosis, foraminal narrowing, vertebral fractures, tumour,
infection. Those are extensions to phantom.py once the loader is
rendering what we have.

## Dependencies

`numpy`, `scikit-image` (marching cubes), `trimesh` (cleanup + glTF
export), `fast-simplification` (quadric decimation backend trimesh
dispatches to — required, Quest 3 cannot ship the raw 800k-tri marching
cubes output). Install with:

```bash
pip install numpy scikit-image trimesh fast-simplification
```

No GPU required for the phantom path. TotalSegmentator (next PR) will
add a heavy ML dependency; we'll keep it optional so this pipeline still
runs on machines that only need the phantom.

## Smoke test

```bash
cd python
python -m case_pipeline.smoke_test
```

Builds the literature-default lumbar phantom plus three pathology
variants into tempdirs, asserts the expected per-level vertebra
structures plus the soft-tissue structures are all produced with sane
triangle counts, and asserts pathology cases diverge from baseline.
Total per case: ~32k triangles across 11 structures (5 soft-tissue +
6 vertebrae).

## Stream-safety note

Per the project's CLAUDE.md: this pipeline never touches real DICOM and
never produces files containing patient-identifiable data. The phantom
is parameterized by anatomic averages from the literature, exactly the
same posture as `python/spineoptimizer/core/models.DiscSpaceMeasurement.from_literature`.
