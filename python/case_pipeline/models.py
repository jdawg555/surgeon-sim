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


def _disc_pair_keys(levels: tuple[str, ...]) -> tuple[str, ...]:
    """Adjacent-pair labels for inter-vertebral discs in `levels` order, e.g.
    ('L1-L2', 'L2-L3', ..., 'L5-S1'). Convention is `<above>-<below>`."""

    return tuple(f"{a}-{b}" for a, b in zip(levels, levels[1:]))


@dataclass(frozen=True)
class Pathology:
    """Optional pathology layered on top of the baseline phantom anatomy.

    Each pathology is an additive perturbation: omit a field and the
    baseline anatomy is unchanged. Multiple pathologies can stack on one
    case (e.g. degenerative disc + scoliosis is realistic).

    Severity scales (rule of thumb, not clinical thresholds):
      - degenerative_disc[level_pair]: 0.0 healthy ... 1.0 fully collapsed
      - spondylolisthesis[level_pair]: anterior translation in mm
      - scoliosis_cobb_deg: Cobb angle of lateral curvature, 0 = straight
    """

    degenerative_disc: dict[str, float] = field(default_factory=dict)
    spondylolisthesis: dict[str, float] = field(default_factory=dict)
    scoliosis_cobb_deg: float = 0.0
    scoliosis_apex_level: str | None = None

    def __post_init__(self) -> None:
        for k, v in self.degenerative_disc.items():
            if not 0.0 <= v <= 1.0:
                raise ValueError(
                    f"degenerative_disc[{k!r}] = {v}; severity must be in [0, 1]"
                )
        for k, v in self.spondylolisthesis.items():
            if not -30.0 <= v <= 30.0:
                # Clinical Meyerding grade 4 is ~75% body width (~16 mm) so
                # 30 mm is a generous outer bound; outside that, the pelvic
                # geometry stops making sense.
                raise ValueError(
                    f"spondylolisthesis[{k!r}] = {v} mm; expected -30..30 mm"
                )
        if not -60.0 <= self.scoliosis_cobb_deg <= 60.0:
            raise ValueError(
                f"scoliosis_cobb_deg = {self.scoliosis_cobb_deg}; "
                "expected -60..60 deg"
            )
        if self.scoliosis_cobb_deg != 0.0 and self.scoliosis_apex_level is None:
            raise ValueError(
                "scoliosis_cobb_deg is non-zero but scoliosis_apex_level is "
                "not set; specify which vertebra the curve apexes on"
            )

    def is_healthy(self) -> bool:
        return (
            not self.degenerative_disc
            and not self.spondylolisthesis
            and self.scoliosis_cobb_deg == 0.0
        )


@dataclass(frozen=True)
class PhantomSpec:
    """Parametric inputs for the synthetic phantom volume.

    All measurements in millimetres / degrees. Defaults are literature-mean
    adult lumbar values; varying these is how we generate case variety.
    `pathology` layers optional perturbations on top of the baseline.
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
    pathology: Pathology = field(default_factory=Pathology)

    def __post_init__(self) -> None:
        for lv in self.levels:
            if lv not in LUMBAR_LEVELS:
                raise ValueError(
                    f"unsupported level {lv!r}; case_pipeline currently only "
                    f"phantoms {LUMBAR_LEVELS}"
                )
        if self.voxel_size_mm <= 0:
            raise ValueError("voxel_size_mm must be positive")

        valid_pairs = set(_disc_pair_keys(self.levels))
        for k in self.pathology.degenerative_disc:
            if k not in valid_pairs:
                raise ValueError(
                    f"degenerative_disc references {k!r} which is not an "
                    f"adjacent pair in levels={self.levels}; "
                    f"valid pairs: {sorted(valid_pairs)}"
                )
        for k in self.pathology.spondylolisthesis:
            if k not in valid_pairs:
                raise ValueError(
                    f"spondylolisthesis references {k!r} which is not an "
                    f"adjacent pair in levels={self.levels}; "
                    f"valid pairs: {sorted(valid_pairs)}"
                )
        if (
            self.pathology.scoliosis_apex_level is not None
            and self.pathology.scoliosis_apex_level not in self.levels
        ):
            raise ValueError(
                f"scoliosis_apex_level {self.pathology.scoliosis_apex_level!r} "
                f"is not in levels={self.levels}"
            )


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
        if "pathology" in phantom_data:
            phantom_data["pathology"] = Pathology(**phantom_data["pathology"])
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
