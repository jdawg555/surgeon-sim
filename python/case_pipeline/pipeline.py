"""Orchestration: CaseSpec -> CaseManifest + meshes on disk.

This module is what the CLI and the smoke test both call. Keeping it as a
single function rather than a class so it stays trivial to read and to
swap stages later (e.g. replace `phantom.generate` with a TotalSegmentator
wrapper)."""

from __future__ import annotations

import os

from case_pipeline.export import (
    PIPELINE_VERSION,
    write_manifest,
    write_meshes,
)
from case_pipeline.meshing import extract_meshes
from case_pipeline.models import CaseManifest, CaseSpec, now_iso
from case_pipeline.phantom import generate as generate_phantom


def build_case(spec: CaseSpec, out_dir: str) -> CaseManifest:
    """Run the full pipeline for `spec`, writing into `out_dir`.

    `out_dir` is created if missing. Existing contents are overwritten,
    not deleted — callers that need a clean dir should rm it first.
    """

    os.makedirs(out_dir, exist_ok=True)

    volume = generate_phantom(spec.phantom)
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
    import json

    with open(os.path.join(out_dir, "spec.json"), "w", encoding="utf-8") as fh:
        json.dump(spec.to_dict(), fh, indent=2)
        fh.write("\n")

    return manifest
