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
  meshes/{skin,soft_tissue,vertebral_body,disc,dura,spinal_cord}.glb
  spec.json
```

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

Builds the literature-default lumbar phantom into a tempdir, asserts all
six structures were produced with sane triangle counts, and asserts the
build is deterministic across two runs.

## Stream-safety note

Per the project's CLAUDE.md: this pipeline never touches real DICOM and
never produces files containing patient-identifiable data. The phantom
is parameterized by anatomic averages from the literature, exactly the
same posture as `python/spineoptimizer/core/models.DiscSpaceMeasurement.from_literature`.
