# python/

Reference Python implementation. The C# under `unity/Assets/Scripts/` is a
direct port of these modules — keep this directory canonical and let the
C# follow.

## Layout

```
python/
├── core/                      Pedicle screw + rod prediction, tray optimization,
│   ├── implant_predictor.py   plan generation. Used for fusion procedures.
│   ├── plan_generator.py
│   └── tray_optimizer.py
├── spineoptimizer/            Total disc replacement (TDR) fit engine.
│   ├── core/
│   │   ├── models.py          SpineLevel / ImplantSpec / DiscSpaceMeasurement
│   │   ├── catalog.py         22-SKU lumbar + cervical TDR catalog
│   │   └── implant_loader.py  STEP / STL → bounding box + metadata
│   └── fitting/
│       └── fit_engine.py      Deterministic ranker (0.40 / 0.35 / 0.25 weights)
└── case_pipeline/             Case authoring: spec JSON → labelled volume → glTF + manifest.
    ├── models.py              CaseSpec / PhantomSpec / CaseManifest
    ├── phantom.py             Parametric synthetic volume (lumbar + soft tissue)
    ├── meshing.py             Marching cubes per label, decimate, smooth
    ├── export.py              Per-structure .glb + manifest.json writer
    ├── pipeline.py            Orchestration entry: build_case(spec, out_dir)
    ├── cli.py                 `python -m case_pipeline.cli <spec> <out_dir>`
    ├── smoke_test.py          End-to-end + determinism check
    └── specs/                 Example case specs (literature_default.json)
```

## Why two trees

`spineoptimizer/` ranks artificial discs against patient endplate geometry
(disc replacement procedures). `core/` predicts pedicle screws + rods and
optimizes the implant tray (fusion procedures). They share the spine level
taxonomy but otherwise solve different problems.

The Quest 3 sim renders both: TDR fits when the user calls
`show implant`, fusion plans when running a fusion procedure step.

## Regenerating the C# catalog

After editing `spineoptimizer/core/catalog.py`, run:

```
python tools/port_catalog.py
```

…to regenerate `unity/Assets/Resources/implant_catalog.json` so the C#
side stays in sync.

## Dependencies

Catalog and fit engine: `numpy` only. Plan generator: `reportlab` for PDF
output. Implant predictor and tray optimizer: stdlib. Case pipeline:
`numpy`, `scikit-image`, `trimesh`, `fast-simplification` (see
[`case_pipeline/README.md`](case_pipeline/README.md)). See each file's
imports for specifics.
