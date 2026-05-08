"""Case spec (input) and case manifest (output) schemas.

Plain dataclasses with `from_dict` / `to_dict` so cases can live in git as
human-readable JSON without pulling in pydantic. The spec JSON is the
canonical source; the manifest JSON is build output and lives next to the
generated meshes.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


# Spine levels we know how to phantom. The fusion predictor uses a richer
# enum (VertebraLevel) but the case pipeline only needs the lumbar block
# for now: thoracic and cervical are deferred to later PRs.
LUMBAR_LEVELS: tuple[str, ...] = ("L1", "L2", "L3", "L4", "L5", "S1")


@dataclass(frozen=True)
class PhantomSpec:
    """Parametric inputs for the synthetic phantom volume.

    All measurements in millimetres / degrees. Defaults are literature-mean
    adult lumbar values; varying these is how we generate case variety.
    """

    levels: tuple[str, ...] = LUMBAR_LEVELS
    lordosis_deg: float = 48.0
    body_radius_mm: float = 22.0
    body_height_mm: float = 28.0
    disc_height_mm: float = 9.0
    cord_radius_mm: float = 6.0
    skin_radius_ap_mm: float = 110.0
    skin_radius_lat_mm: float = 145.0
    voxel_size_mm: float = 1.0
    seed: int = 0

    def __post_init__(self) -> None:
        for lv in self.levels:
            if lv not in LUMBAR_LEVELS:
                raise ValueError(
                    f"unsupported level {lv!r}; case_pipeline currently only "
                    f"phantoms {LUMBAR_LEVELS}"
                )
        if self.voxel_size_mm <= 0:
            raise ValueError("voxel_size_mm must be positive")


@dataclass(frozen=True)
class CaseSpec:
    """Top-level case input. One CaseSpec produces one CaseManifest.

    `case_id` is the slug used for output directory naming. `phantom` is the
    only volume source supported in this PR; later PRs will add a
    `segmented_ct` source pointing at a TotalSegmentator output.
    """

    case_id: str
    description: str = ""
    phantom: PhantomSpec = field(default_factory=PhantomSpec)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CaseSpec":
        phantom_data = dict(data.get("phantom", {}))
        if "levels" in phantom_data:
            phantom_data["levels"] = tuple(phantom_data["levels"])
        return cls(
            case_id=data["case_id"],
            description=data.get("description", ""),
            phantom=PhantomSpec(**phantom_data),
        )

    @classmethod
    def from_json_file(cls, path: str) -> "CaseSpec":
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))

    def content_hash(self) -> str:
        # Deterministic hash of the spec for reproducibility tracking. Tuples
        # are coerced to lists by asdict + json so this is stable.
        payload = json.dumps(self.to_dict(), sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:16]


@dataclass(frozen=True)
class StructureManifest:
    """One named anatomical structure in a case."""

    name: str
    mesh_path: str
    vertex_count: int
    triangle_count: int
    material_hint: str  # 'bone' | 'soft_tissue' | 'cord' | 'skin' | 'disc'


@dataclass(frozen=True)
class CaseManifest:
    """Build output. Lives at `<out_dir>/manifest.json` next to the meshes."""

    case_id: str
    description: str
    spec_hash: str
    generated_at: str  # ISO-8601 UTC
    pipeline_version: str
    structures: tuple[StructureManifest, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "description": self.description,
            "spec_hash": self.spec_hash,
            "generated_at": self.generated_at,
            "pipeline_version": self.pipeline_version,
            "structures": [asdict(s) for s in self.structures],
        }

    def write(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
            fh.write("\n")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
