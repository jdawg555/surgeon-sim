"""End-to-end smoke test for the case pipeline.

Builds the literature-default lumbar phantom plus three pathology variants
through the full pipeline into temp directories, asserts every structure
is produced and is non-empty, asserts the build is deterministic across
two runs, and asserts pathology variants actually differ from baseline
(so a typo in PhantomSpec.pathology can't silently no-op).

Also verifies CT synthesis (HU range sanity check) without requiring
TotalSegmentator. Runs the TotalSegmentator end-to-end path only if
TotalSegmentator + nibabel are importable, otherwise reports SKIP.

Run with:

    python -m case_pipeline.smoke_test

Exits non-zero on any failure so CI can pick it up later.
"""

from __future__ import annotations

import os
import sys
import tempfile

import numpy as np

from case_pipeline.models import CaseSpec, PhantomSpec, Pathology, TotalSegmentatorConfig
from case_pipeline.pipeline import build_case


EXPECTED_STRUCTURES = {
    "skin",
    "soft_tissue",
    "vertebral_body",
    "disc",
    "dura",
    "spinal_cord",
}


def _build(spec: CaseSpec, tmp: str) -> dict[str, int]:
    """Build a case and return {structure_name: triangle_count}."""
    out = os.path.join(tmp, spec.case_id)
    manifest = build_case(spec, out)

    produced = {s.name for s in manifest.structures}
    missing = EXPECTED_STRUCTURES - produced
    if missing:
        raise AssertionError(
            f"{spec.case_id}: missing structures: {sorted(missing)}"
        )
    for s in manifest.structures:
        mesh_abs = os.path.join(out, s.mesh_path)
        if not os.path.exists(mesh_abs):
            raise AssertionError(
                f"{spec.case_id}: mesh file missing: {mesh_abs}"
            )
        if os.path.getsize(mesh_abs) < 256:
            raise AssertionError(
                f"{spec.case_id}: mesh file suspiciously small: "
                f"{mesh_abs} ({os.path.getsize(mesh_abs)} bytes)"
            )
        if s.triangle_count < 32:
            raise AssertionError(
                f"{spec.case_id}: {s.name} has only {s.triangle_count} triangles"
            )
    return {s.name: s.triangle_count for s in manifest.structures}


def main() -> int:
    cases = [
        CaseSpec(
            case_id="smoke-default-lumbar",
            description="Literature-default lumbar phantom for smoke testing.",
            phantom=PhantomSpec(),
        ),
        CaseSpec(
            case_id="smoke-degen-l4-l5",
            description="Degenerative disc at L4-L5.",
            phantom=PhantomSpec(
                pathology=Pathology(
                    degenerative_disc={"L4-L5": 0.7, "L5-S1": 0.35},
                ),
            ),
        ),
        CaseSpec(
            case_id="smoke-spondy-l5-s1",
            description="Grade 1 spondy at L5-S1.",
            phantom=PhantomSpec(
                pathology=Pathology(
                    spondylolisthesis={"L5-S1": 8.0},
                    degenerative_disc={"L5-S1": 0.5},
                ),
            ),
        ),
        CaseSpec(
            case_id="smoke-scoliosis-l3",
            description="25 deg right-convex curve apex at L3.",
            phantom=PhantomSpec(
                pathology=Pathology(
                    scoliosis_cobb_deg=25.0,
                    scoliosis_apex_level="L3",
                ),
            ),
        ),
    ]

    try:
        with tempfile.TemporaryDirectory() as tmp:
            counts: dict[str, dict[str, int]] = {}
            for spec in cases:
                counts[spec.case_id] = _build(spec, tmp)
                print(f"OK: {spec.case_id}")
                for name, tris in counts[spec.case_id].items():
                    print(f"  {name:<18} {tris:>6} tris")

            # Determinism: rebuild the default case and confirm identical
            # triangle counts.
            with tempfile.TemporaryDirectory() as tmp2:
                rerun = _build(cases[0], tmp2)
            if rerun != counts[cases[0].case_id]:
                print("FAIL: triangle counts not deterministic", file=sys.stderr)
                print(f"  run1: {counts[cases[0].case_id]}", file=sys.stderr)
                print(f"  run2: {rerun}", file=sys.stderr)
                return 1

            # Pathology must change *something* about the bone meshes vs
            # baseline. If a future refactor accidentally drops pathology
            # plumbing this catches it.
            baseline_bone = counts["smoke-default-lumbar"]["vertebral_body"]
            for cid in (
                "smoke-degen-l4-l5",
                "smoke-spondy-l5-s1",
                "smoke-scoliosis-l3",
            ):
                if counts[cid]["vertebral_body"] == baseline_bone:
                    # Triangle count alone could match by coincidence
                    # post-decimation; check disc count too. If both match,
                    # pathology is silently no-op.
                    if counts[cid]["disc"] == counts["smoke-default-lumbar"]["disc"]:
                        print(
                            f"FAIL: {cid} bone+disc tri counts match baseline; "
                            f"pathology may be no-op",
                            file=sys.stderr,
                        )
                        return 1

            print("OK: determinism + pathology divergence checks passed")

        _check_ct_synthesis()

        _check_totalsegmentator_path()

        return 0
    except AssertionError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1


def _check_ct_synthesis() -> None:
    """Verify CT synthesis produces a HU volume with sane ranges. No TS
    install required — this only exercises ct_synthesis.py."""
    from case_pipeline.ct_synthesis import (
        HU_AIR,
        HU_BONE_CORTICAL,
        HU_BONE_TRABECULAR,
        HU_SOFT_TISSUE,
        synthesize_ct,
    )

    ct = synthesize_ct(PhantomSpec(), noise_hu=0.0)
    if ct.hu.dtype != np.float32:
        raise AssertionError(f"CT dtype is {ct.hu.dtype}, expected float32")
    # Air voxels should be at HU_AIR exactly when noise=0.
    if not np.isclose(ct.hu.min(), HU_AIR):
        raise AssertionError(
            f"CT min {ct.hu.min()} != HU_AIR {HU_AIR}; air not present"
        )
    # Bone voxels should hit the cortical HU value.
    if ct.hu.max() < HU_BONE_TRABECULAR:
        raise AssertionError(
            f"CT max {ct.hu.max()} below trabecular bone {HU_BONE_TRABECULAR}; "
            "bone-shell logic may be broken"
        )
    if ct.hu.max() < HU_BONE_CORTICAL - 1.0:
        raise AssertionError(
            f"CT max {ct.hu.max()} below cortical bone {HU_BONE_CORTICAL}; "
            "cortical shell may be missing"
        )
    # Roughly: a healthy CT histogram has a big mode around soft-tissue HU.
    soft_band = ((ct.hu > HU_SOFT_TISSUE - 5) & (ct.hu < HU_SOFT_TISSUE + 5)).sum()
    if soft_band < 10000:
        raise AssertionError(
            f"CT soft-tissue band has only {soft_band} voxels; "
            "phantom envelope may have collapsed"
        )
    print(
        "OK: CT synthesis HU range "
        f"[{ct.hu.min():.0f} .. {ct.hu.max():.0f}], "
        f"shape={ct.hu.shape}"
    )


def _check_totalsegmentator_path() -> None:
    """Run a tiny TotalSegmentator-backed case if TS is installed.
    Otherwise print SKIP — the phantom path covers everything else and
    forcing a 2 GB model download in CI is not the right default."""
    from case_pipeline.segmenters import totalseg

    if not totalseg.is_available():
        print(
            "SKIP: TotalSegmentator not installed. "
            "Install with `pip install TotalSegmentator nibabel scipy` "
            "to enable the TS-backed path."
        )
        return

    spec = CaseSpec(
        case_id="smoke-ts-default",
        description="Smoke: TS-backed lumbar.",
        source="totalsegmentator",
        phantom=PhantomSpec(),
        # Fast model — keeps the smoke test under a couple of minutes
        # on M5 MPS even on first run.
        totalsegmentator=TotalSegmentatorConfig(fast=True),
    )

    with tempfile.TemporaryDirectory() as tmp:
        counts = _build(spec, tmp)
        # Bone must be present; if TS returns nothing, that's a failure.
        if counts.get("vertebral_body", 0) < 32:
            raise AssertionError(
                f"TS path produced no bone mesh: {counts}"
            )
        print(f"OK: TS path produced {sum(counts.values())} total triangles")


if __name__ == "__main__":
    sys.exit(main())
