"""Case authoring pipeline: spec JSON -> labelled volume -> meshes -> glTF + manifest.

The pipeline is the canonical path for producing patient cases the Quest sim
loads at runtime. It is fully deterministic from a `CaseSpec` so cases live
in git as JSON, not as binary blobs, and CI can rebuild meshes from source.

Two volume sources are supported:

  1. Parametric phantom. Synthetic, reproducible, no real patient data.
     Used for development, smoke tests, and stream demos.
  2. TotalSegmentator over a synthetic CT. Same downstream meshing and
     export, just a different volume source. TotalSegmentator is an
     optional dependency; install with `pip install TotalSegmentator`.

Public surface kept intentionally small.
"""

from case_pipeline.models import (
    CaseManifest,
    CaseSpec,
    Pathology,
    PhantomSpec,
    StructureManifest,
    TotalSegmentatorConfig,
    VOLUME_SOURCES,
)
from case_pipeline.pipeline import build_case

__all__ = [
    "CaseManifest",
    "CaseSpec",
    "Pathology",
    "PhantomSpec",
    "StructureManifest",
    "TotalSegmentatorConfig",
    "VOLUME_SOURCES",
    "build_case",
]
