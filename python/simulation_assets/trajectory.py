"""Neutral instrument trajectory schema.

ORBIT-Surgical, scripted demos, and future desktop physics experiments can
export into this JSON shape. Unity then replays the same data without knowing
which simulator produced it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class InstrumentPoseSample:
    """One timestamped instrument pose.

    Position is millimetres in the exported case coordinate frame. Rotation is
    a unit quaternion in x, y, z, w order because that maps directly to Unity's
    Quaternion fields and common robotics export formats.
    """

    timestamp_s: float
    position_mm: tuple[float, float, float]
    rotation_xyzw: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    gripper: float = 0.0
    contact_state: str = "free"
    annotation: str = ""

    def __post_init__(self) -> None:
        if self.timestamp_s < 0.0:
            raise ValueError("timestamp_s must be non-negative")
        if len(self.position_mm) != 3:
            raise ValueError("position_mm must contain x, y, z")
        if len(self.rotation_xyzw) != 4:
            raise ValueError("rotation_xyzw must contain x, y, z, w")
        if not 0.0 <= self.gripper <= 1.0:
            raise ValueError("gripper must be in [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp_s": self.timestamp_s,
            "position_mm": {
                "x": self.position_mm[0],
                "y": self.position_mm[1],
                "z": self.position_mm[2],
            },
            "rotation_xyzw": {
                "x": self.rotation_xyzw[0],
                "y": self.rotation_xyzw[1],
                "z": self.rotation_xyzw[2],
                "w": self.rotation_xyzw[3],
            },
            "gripper": self.gripper,
            "contact_state": self.contact_state,
            "annotation": self.annotation,
        }


@dataclass(frozen=True)
class InstrumentTrajectory:
    """A replayable motion track for one instrument."""

    trajectory_id: str
    instrument_id: str
    source: str
    coordinate_frame: str = "case_mm"
    generated_at: str = field(default_factory=_now_iso)
    samples: tuple[InstrumentPoseSample, ...] = ()

    def __post_init__(self) -> None:
        if not self.trajectory_id:
            raise ValueError("trajectory_id is required")
        if not self.instrument_id:
            raise ValueError("instrument_id is required")
        if not self.samples:
            raise ValueError("samples must not be empty")

        previous = -1.0
        for sample in self.samples:
            if sample.timestamp_s <= previous:
                raise ValueError("samples must be strictly increasing by timestamp_s")
            previous = sample.timestamp_s

    def to_dict(self) -> dict[str, Any]:
        return {
            "trajectory_id": self.trajectory_id,
            "instrument_id": self.instrument_id,
            "source": self.source,
            "coordinate_frame": self.coordinate_frame,
            "generated_at": self.generated_at,
            "samples": [s.to_dict() for s in self.samples],
        }

    def write_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
            fh.write("\n")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InstrumentTrajectory":
        return cls(
            trajectory_id=data["trajectory_id"],
            instrument_id=data["instrument_id"],
            source=data.get("source", "unknown"),
            coordinate_frame=data.get("coordinate_frame", "case_mm"),
            generated_at=data.get("generated_at", _now_iso()),
            samples=tuple(
                InstrumentPoseSample(
                    timestamp_s=float(s["timestamp_s"]),
                    position_mm=_vec3_from_json(s["position_mm"]),
                    rotation_xyzw=_quat_from_json(
                        s.get("rotation_xyzw", (0.0, 0.0, 0.0, 1.0))
                    ),
                    gripper=float(s.get("gripper", 0.0)),
                    contact_state=s.get("contact_state", "free"),
                    annotation=s.get("annotation", ""),
                )
                for s in data.get("samples", [])
            ),
        )

    @classmethod
    def from_json_file(cls, path: str) -> "InstrumentTrajectory":
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))


def demo_needle_lift_trajectory() -> InstrumentTrajectory:
    """Small deterministic fixture useful for Unity replay smoke tests."""

    return InstrumentTrajectory(
        trajectory_id="demo-needle-lift",
        instrument_id="needle_driver",
        source="scripted",
        samples=(
            InstrumentPoseSample(
                timestamp_s=0.0,
                position_mm=(-35.0, 95.0, 20.0),
                gripper=0.0,
                annotation="approach",
            ),
            InstrumentPoseSample(
                timestamp_s=0.75,
                position_mm=(-12.0, 82.0, 12.0),
                gripper=0.35,
                contact_state="near_tissue",
            ),
            InstrumentPoseSample(
                timestamp_s=1.5,
                position_mm=(0.0, 76.0, 8.0),
                gripper=1.0,
                contact_state="grasping",
                annotation="needle captured",
            ),
            InstrumentPoseSample(
                timestamp_s=2.25,
                position_mm=(24.0, 108.0, 30.0),
                gripper=1.0,
                contact_state="lifting",
            ),
            InstrumentPoseSample(
                timestamp_s=3.0,
                position_mm=(42.0, 124.0, 40.0),
                gripper=0.15,
                contact_state="released",
                annotation="release",
            ),
        ),
    )


def _vec3_from_json(value: Any) -> tuple[float, float, float]:
    if isinstance(value, dict):
        return (float(value["x"]), float(value["y"]), float(value["z"]))
    return tuple(value)  # type: ignore[return-value]


def _quat_from_json(value: Any) -> tuple[float, float, float, float]:
    if isinstance(value, dict):
        return (
            float(value.get("x", 0.0)),
            float(value.get("y", 0.0)),
            float(value.get("z", 0.0)),
            float(value.get("w", 1.0)),
        )
    return tuple(value)  # type: ignore[return-value]

