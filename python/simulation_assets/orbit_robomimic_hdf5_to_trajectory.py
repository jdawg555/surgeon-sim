"""Convert ORBIT-Surgical / Isaac Lab Robomimic HDF5 demos into trajectory JSON.

Requires ``h5py``::

    pip install h5py

Observation keys depend on the task and Isaac Lab config; always run with
``--list-structure`` first on your dataset.

Usage::

    python -m simulation_assets.orbit_robomimic_hdf5_to_trajectory \\
        --hdf5 dataset.hdf5 --list-structure

    python -m simulation_assets.orbit_robomimic_hdf5_to_trajectory \\
        --hdf5 dataset.hdf5 --demo demo_0 --position-key object_position \\
        --units isaac_m --out trajectory.json
"""

from __future__ import annotations

import argparse
import sys

from simulation_assets.trajectory import InstrumentPoseSample, InstrumentTrajectory


def _require_h5py():
    try:
        import h5py  # noqa: F401
    except ImportError as e:
        raise SystemExit(
            "h5py is required for HDF5 export. Install with: pip install h5py"
        ) from e


def _print_structure(path: str) -> None:
    import h5py

    with h5py.File(path, "r") as f:
        if "data" not in f:
            print("No top-level 'data' group found.")
            return
        data = f["data"]
        demo_keys = sorted(k for k in data.keys() if str(k).startswith("demo_"))
        print(f"demos ({len(demo_keys)}): {demo_keys[:15]}{' ...' if len(demo_keys) > 15 else ''}")
        if not demo_keys:
            return
        g0 = data[demo_keys[0]]
        if "obs" not in g0:
            print(f"{demo_keys[0]}: no obs group")
            return
        obs = g0["obs"]
        print(f"{demo_keys[0]}/obs datasets:")
        for key in sorted(obs.keys()):
            ds = obs[key]
            if hasattr(ds, "shape"):
                print(f"  {key}: shape={ds.shape} dtype={ds.dtype}")
            else:
                print(f"  {key}: (subgroup)")
        if "actions" in g0 and hasattr(g0["actions"], "shape"):
            a = g0["actions"]
            print(f"{demo_keys[0]}/actions: shape={a.shape} dtype={a.dtype}")


def _dataset_obs_demo(g_demo: Any, key: str):
    obs = g_demo["obs"]
    if key not in obs:
        avail = sorted(obs.keys())
        raise KeyError(f"obs/{key} not found. Available: {avail}")
    return obs[key]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Robomimic HDF5 → InstrumentTrajectory JSON",
    )
    parser.add_argument("--hdf5", required=True, help="Path to .hdf5 dataset.")
    parser.add_argument(
        "--list-structure",
        action="store_true",
        help="Print HDF5 data/demo observation layout and exit.",
    )
    parser.add_argument(
        "--demo",
        default=None,
        help="Demo group under data/, e.g. demo_0 (default: first demo_* key).",
    )
    parser.add_argument(
        "--position-key",
        help="Dataset name under obs/, e.g. object_position (shape [T, 3] or [T+1, 3]).",
    )
    parser.add_argument(
        "--quaternion-key",
        help="Optional dataset under obs/, shape [T, 4] or [T+1, 4], xyzw order.",
    )
    parser.add_argument(
        "--gripper-from-actions",
        action="store_true",
        help="If set, take gripper open/closed hint from last column of actions.",
    )
    parser.add_argument(
        "--units",
        choices=("isaac_m", "mm"),
        default="mm",
        help="Units stored in position arrays (isaac_m → multiply by 1000 for schema mm).",
    )
    parser.add_argument("--dt", type=float, default=1.0 / 60.0, help="Timestep seconds.")
    parser.add_argument("--instrument-id", default="orbit_tool", help="instrument_id field.")
    parser.add_argument(
        "--trajectory-id",
        default=None,
        help="trajectory_id field (default: demo name).",
    )
    parser.add_argument(
        "--source",
        default="orbit-surgical-robomimic",
        help="source metadata field.",
    )
    parser.add_argument("--out", required=False, help="Output JSON path.")
    args = parser.parse_args(argv)

    _require_h5py()
    import h5py
    import numpy as np

    if args.list_structure:
        _print_structure(args.hdf5)
        return 0

    if not args.position_key:
        print("--position-key is required unless --list-structure", file=sys.stderr)
        return 2

    if not args.out:
        print("--out is required for export", file=sys.stderr)
        return 2

    with h5py.File(args.hdf5, "r") as f:
        if "data" not in f:
            raise SystemExit("HDF5 missing top-level 'data' group (robomimic layout)")
        data = f["data"]
        demos = sorted(k for k in data.keys() if str(k).startswith("demo_"))
        if not demos:
            raise SystemExit("No demo_* groups found under data/")
        demo_name = args.demo if args.demo is not None else demos[0]
        if demo_name not in data:
            raise SystemExit(f"{demo_name!r} not in data/. Available: {demos[:20]}...")
        g_demo = data[demo_name]

        pos_ds = _dataset_obs_demo(g_demo, args.position_key)
        pos = np.asarray(pos_ds[:], dtype=np.float64)

        quat = None
        if args.quaternion_key:
            q_ds = _dataset_obs_demo(g_demo, args.quaternion_key)
            quat = np.asarray(q_ds[:], dtype=np.float64)

        gripper_seq = None
        if args.gripper_from_actions:
            if "actions" not in g_demo:
                raise SystemExit("demo has no actions group/dataset for gripper-from-actions")
            act = np.asarray(g_demo["actions"][:], dtype=np.float64)
            gripper_seq = act[:, -1]

        scale = 1000.0 if args.units == "isaac_m" else 1.0

    # Align trajectory length: robomimic often stores obs length T+1 vs actions T.
    n = len(pos)
    samples_list: list[InstrumentPoseSample] = []

    for i in range(n):
        p = pos[i]
        mm = (float(p[0]) * scale, float(p[1]) * scale, float(p[2]) * scale)
        rot = (0.0, 0.0, 0.0, 1.0)
        if quat is not None and i < len(quat):
            q = quat[i]
            rot = (float(q[0]), float(q[1]), float(q[2]), float(q[3]))

        g = 0.0
        if gripper_seq is not None:
            gi = min(i, len(gripper_seq) - 1)
            gv = float(gripper_seq[gi])
            if gv <= -0.5:
                g = 1.0
            elif gv >= 0.5:
                g = 0.0
            else:
                g = 0.5

        samples_list.append(
            InstrumentPoseSample(
                timestamp_s=float(i) * args.dt,
                position_mm=mm,
                rotation_xyzw=rot,
                gripper=g,
                contact_state="recorded",
            )
        )

    traj_id = args.trajectory_id or demo_name
    trajectory = InstrumentTrajectory(
        trajectory_id=traj_id,
        instrument_id=args.instrument_id,
        source=args.source,
        samples=tuple(samples_list),
    )
    trajectory.write_json(args.out)
    print(
        f"[orbit_robomimic_hdf5_to_trajectory] wrote {len(samples_list)} samples → {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
