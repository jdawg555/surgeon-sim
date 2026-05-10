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
├── case_pipeline/             Case authoring: spec JSON → labelled volume → glTF + manifest.
│   ├── models.py              CaseSpec / PhantomSpec / Pathology / TotalSegmentatorConfig
│   ├── phantom.py             Parametric synthetic volume (lumbar + soft tissue)
│   ├── ct_synthesis.py        PhantomSpec → HU CT volume (input to TotalSegmentator)
│   ├── segmenters/
│   │   └── totalseg.py        TotalSegmentator wrapper, label remap, gap fill
│   ├── meshing.py             Marching cubes per label, decimate, smooth
│   ├── export.py              Per-structure .glb + manifest.json writer
│   ├── pipeline.py            build_case(spec) — dispatches on spec.source
│   ├── cli.py                 `python -m case_pipeline.cli <spec> <out_dir>`
│   ├── smoke_test.py          End-to-end + determinism + CT + (optional) TS check
│   └── specs/                 Example specs incl. pathology + TS-backed
└── simulation_assets/          Neutral interchange assets from offline simulators.
    ├── README.md               Usage for trajectory JSON + ORBIT HDF5 export
    ├── trajectory.py           InstrumentTrajectory / InstrumentPoseSample schema
    ├── export_demo_trajectory.py
    ├── orbit_robomimic_hdf5_to_trajectory.py
    └── smoke_test.py
```

## Why two trees

`spineoptimizer/` ranks artificial discs against patient endplate geometry
(disc replacement procedures). `core/` predicts pedicle screws + rods and
optimizes the implant tray (fusion procedures). They share the spine level
taxonomy but otherwise solve different problems.

The Quest 3 sim renders both: TDR fits when the user calls
`show implant`, fusion plans when running a fusion procedure step.

`simulation_assets/` is the bridge for systems that should not ship inside
the Quest runtime. ORBIT-Surgical, iMSTK desktop experiments, or scripted
generators can write instrument trajectory JSON; Unity consumes it through
`InstrumentTrajectoryReplay`.

## Regenerating the C# catalog

After editing `spineoptimizer/core/catalog.py`, run:

```
python tools/port_catalog.py
```

…to regenerate `unity/Assets/Resources/implant_catalog.json` so the C#
side stays in sync.

## Dependencies

Catalog and fit engine: `numpy` only. Plan generator: `reportlab` for PDF
output. Implant predictor and tray optimizer: stdlib. Case pipeline core:
`numpy`, `scikit-image`, `trimesh`, `fast-simplification`. Case pipeline
TS path (optional): `scipy`, `nibabel`, `TotalSegmentator`. See
[`case_pipeline/README.md`](case_pipeline/README.md) for the split and
`pip install` lines.

Simulation asset trajectory JSON uses only the Python standard library.
ORBIT Robomimic HDF5 conversion additionally requires `h5py`.
