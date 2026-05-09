"""Orchestration: CaseSpec -> CaseManifest + meshes on disk.

The single function `build_case` dispatches on `spec.source` to pick a
volume source (parametric phantom or TotalSegmentator over a synthetic
CT) and feeds the resulting labelled volume through the same meshing +
export stages. Adding a future source (e.g. a real anonymised CT, or
TotalSpineSeg on MRI) means adding a new branch here and a new module
under `segmenters/`; nothing downstream changes.
"""

from __future__ import annotations

import json
import os

from case_pipeline.export import (
    PIPELINE_VERSION,
    write_manifest,
    write_meshes,
)
from case_pipeline.meshing import extract_meshes
from case_pipeline.models import CaseManifest, CaseSpec, now_iso
from case_pipeline.phantom import PhantomVolume, generate as generate_phantom


def build_case(spec: CaseSpec, out_dir: str) -> CaseManifest:
    """Run the full pipeline for `spec`, writing into `out_dir`.

    `out_dir` is created if missing. Existing contents are overwritten,
    not deleted — callers that need a clean dir should rm it first.
    """

    os.makedirs(out_dir, exist_ok=True)

    volume = _build_volume(spec)
    structures = extract_meshes(volume)
    structure_entries = write_meshes(structures, out_dir)

    manifest = CaseManifest(
        case_id=spec.case_id,
        description=spec.description,
        spec_hash=spec.content_hash(),
        generated_at=now_iso(),
        pipeline_version=PIPELINE_VERSION,
        structures=tuple(structure_entries),
    )
    write_manifest(manifest, out_dir)

    # Persist the input spec alongside the output for reproducibility.
    # Anyone diffing two cases can compare specs without rerunning anything.
    with open(os.path.join(out_dir, "spec.json"), "w", encoding="utf-8") as fh:
        json.dump(spec.to_dict(), fh, indent=2)
        fh.write("\n")

    return manifest


def _build_volume(spec: CaseSpec) -> PhantomVolume:
    """Dispatch to the configured volume source. Returns whatever the
    source produces in our taxonomy — currently always a `PhantomVolume`,
    since the TS source uses the same dataclass for its output."""

    if spec.source == "phantom":
        return generate_phantom(spec.phantom)

    if spec.source == "totalsegmentator":
        # Imports deferred so the phantom path stays importable on
        # installations without ct_synthesis / segmenters dependencies
        # (scipy for ct_synthesis; nibabel + TotalSegmentator for the
        # segmenter itself).
        from case_pipeline.ct_synthesis import synthesize_ct
        from case_pipeline.segmenters import totalseg

        ct = synthesize_ct(spec.phantom, noise_hu=spec.totalsegmentator.ct_noise_hu)
        return totalseg.segment(ct, spec.phantom, spec.totalsegmentator)

    raise ValueError(f"unknown source {spec.source!r} (PhantomSpec validation should have caught this)")
