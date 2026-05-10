# simulation_assets

Neutral interchange formats between offline simulators (ORBIT-Surgical,
iMSTK experiments, scripted tooling) and the Unity Quest runtime.

## Instrument trajectory JSON

Schema: `trajectory.py`. Units for positions are millimetres in an arbitrary
case-local frame (`coordinate_frame` defaults to `case_mm`). Unity replay
scales by `InstrumentTrajectoryReplay.MillimetresToUnity`.

Generate the scripted fixture:

```bash
cd python
PYTHONPATH=. python3 -m simulation_assets.export_demo_trajectory \
  ../unity/Assets/StreamingAssets/trajectories/demo_needle_lift.json
```

Smoke test:

```bash
cd python
PYTHONPATH=. python3 -m simulation_assets.smoke_test
```

## ORBIT-Surgical Robomimic HDF5

After collecting demos with Isaac Lab plus ORBIT (see upstream
`collect_demonstrations.py`), inspect HDF5 keys:

```bash
pip install h5py
python -m simulation_assets.orbit_robomimic_hdf5_to_trajectory \
  --hdf5 /path/to/hdf_dataset.hdf5 --list-structure
```

Export positions from a chosen observation dataset (Isaac Lab lift demos
often store observations such as `object_position` under `obs/` — confirm
with `--list-structure`):

```bash
python -m simulation_assets.orbit_robomimic_hdf5_to_trajectory \
  --hdf5 /path/to/hdf_dataset.hdf5 \
  --demo demo_0 \
  --position-key object_position \
  --units isaac_m \
  --instrument-id psm_tool_tip \
  --source orbit-surgical-robomimic \
  --out orbit_demo_0.json
```

`--units isaac_m` converts metres to millimetres for our schema. Add
`--quaternion-key` when your HDF5 stores an EE quaternion compatible with
shape `[T, 4]` in **xyzw** order.
