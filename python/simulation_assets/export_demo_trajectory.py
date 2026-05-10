"""Write the deterministic demo instrument trajectory.

Usage:
    python -m simulation_assets.export_demo_trajectory <out.json>
"""

from __future__ import annotations

import argparse
import os
import sys

from simulation_assets.trajectory import demo_needle_lift_trajectory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dragonfly-export-demo-trajectory",
        description="Write a scripted instrument trajectory JSON fixture.",
    )
    parser.add_argument("out_json", help="Output JSON path.")
    args = parser.parse_args(argv)

    out_dir = os.path.dirname(os.path.abspath(args.out_json))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    trajectory = demo_needle_lift_trajectory()
    trajectory.write_json(args.out_json)
    print(
        f"[simulation_assets] wrote {trajectory.trajectory_id} "
        f"({len(trajectory.samples)} samples) -> {args.out_json}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

