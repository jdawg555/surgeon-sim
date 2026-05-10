"""Smoke test for simulation asset interchange formats.

Run with:
    python -m simulation_assets.smoke_test
"""

from __future__ import annotations

import os
import sys
import tempfile

from simulation_assets.trajectory import (
    InstrumentPoseSample,
    InstrumentTrajectory,
    demo_needle_lift_trajectory,
)


def main() -> int:
    try:
        trajectory = demo_needle_lift_trajectory()
        if len(trajectory.samples) != 5:
            raise AssertionError("demo trajectory should contain 5 samples")

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "trajectory.json")
            trajectory.write_json(path)
            loaded = InstrumentTrajectory.from_json_file(path)
            if loaded.to_dict() != trajectory.to_dict():
                raise AssertionError("trajectory JSON roundtrip changed data")

        try:
            InstrumentTrajectory(
                trajectory_id="bad-order",
                instrument_id="needle_driver",
                source="test",
                samples=(
                    InstrumentPoseSample(1.0, (0.0, 0.0, 0.0)),
                    InstrumentPoseSample(1.0, (1.0, 0.0, 0.0)),
                ),
            )
        except ValueError as e:
            if "strictly increasing" not in str(e):
                raise
        else:
            raise AssertionError("duplicate timestamps should fail validation")

        print(
            "OK: simulation_assets trajectory roundtrip + validation "
            f"({trajectory.trajectory_id})"
        )
        return 0
    except AssertionError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

