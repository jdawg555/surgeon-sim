"""End-to-end smoke test for the case pipeline.

Builds the literature-default lumbar phantom plus three pathology variants
through the full pipeline into temp directories, asserts every structure
is produced and is non-empty, asserts the build is deterministic across
two runs, and asserts pathology variants actually differ from baseline
(so a typo in PhantomSpec.pathology can't silently no-op).

Run with:

    python -m case_pipeline.smoke_test

Exits non-zero on any failure so CI can pick it up later.
"""

from __future__ import annotations

import os
import sys
import tempfile

from case_pipeline.models import CaseSpec, PhantomSpec, Pathology
from case_pipeline.pipeline import build_case


SOFT_TISSUE_STRUCTURES = {
    "skin",
    "soft_tissue",
    "disc",
    "dura",
    "spinal_cord",
}


def _expected_structures(spec: CaseSpec) -> set[str]:
    """Per-level vertebrae plus the soft-tissue set. Matches the manifest
    that `build_case` should produce for `spec`."""
    return SOFT_TISSUE_STRUCTURES | {f"vertebra_{lvl}" for lvl in spec.phantom.levels}


def _build(spec: CaseSpec, tmp: str) -> dict[str, int]:
    """Build a case and return {structure_name: triangle_count}."""
    out = os.path.join(tmp, spec.case_id)
    manifest = build_case(spec, out)

    produced = {s.name for s in manifest.structures}
    expected = _expected_structures(spec)
    missing = expected - produced
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
            # plumbing this catches it. With per-vertebra meshes the bone
            # signal is the sum across all vertebra_* structures plus disc.
            def _bone_disc_signature(c: dict[str, int]) -> tuple[int, int]:
                bone = sum(t for n, t in c.items() if n.startswith("vertebra_"))
                disc = c.get("disc", 0)
                return bone, disc

            baseline_sig = _bone_disc_signature(counts["smoke-default-lumbar"])
            for cid in (
                "smoke-degen-l4-l5",
                "smoke-spondy-l5-s1",
                "smoke-scoliosis-l3",
            ):
                if _bone_disc_signature(counts[cid]) == baseline_sig:
                    print(
                        f"FAIL: {cid} bone+disc tri totals match baseline; "
                        f"pathology may be no-op",
                        file=sys.stderr,
                    )
                    return 1

            print("OK: determinism + pathology divergence checks passed")
            return 0
    except AssertionError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
