"""End-to-end smoke test for the case pipeline.

Runs the literature-default lumbar phantom through the full pipeline into
a temp directory, asserts every structure was produced and is non-empty,
and prints a summary. Run with:

    python -m case_pipeline.smoke_test

Exits non-zero on any failure so CI can pick it up later.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

from case_pipeline.models import CaseSpec, PhantomSpec
from case_pipeline.pipeline import build_case


EXPECTED_STRUCTURES = {
    "skin",
    "soft_tissue",
    "vertebral_body",
    "disc",
    "dura",
    "spinal_cord",
}


def main() -> int:
    spec = CaseSpec(
        case_id="smoke-default-lumbar",
        description="Literature-default lumbar phantom for smoke testing.",
        phantom=PhantomSpec(),
    )

    with tempfile.TemporaryDirectory() as tmp:
        manifest = build_case(spec, tmp)

        produced = {s.name for s in manifest.structures}
        missing = EXPECTED_STRUCTURES - produced
        if missing:
            print(f"FAIL: missing structures: {sorted(missing)}", file=sys.stderr)
            return 1

        for s in manifest.structures:
            mesh_abs = os.path.join(tmp, s.mesh_path)
            if not os.path.exists(mesh_abs):
                print(f"FAIL: mesh file missing: {mesh_abs}", file=sys.stderr)
                return 1
            if os.path.getsize(mesh_abs) < 256:
                print(
                    f"FAIL: mesh file suspiciously small: {mesh_abs} "
                    f"({os.path.getsize(mesh_abs)} bytes)",
                    file=sys.stderr,
                )
                return 1
            if s.triangle_count < 32:
                print(
                    f"FAIL: {s.name} has only {s.triangle_count} triangles",
                    file=sys.stderr,
                )
                return 1

        # Determinism check: a second run with the same spec should produce
        # the same spec_hash and the same structure topology counts.
        manifest2 = build_case(spec, tmp)
        if manifest.spec_hash != manifest2.spec_hash:
            print("FAIL: spec_hash not deterministic", file=sys.stderr)
            return 1
        counts1 = sorted((s.name, s.triangle_count) for s in manifest.structures)
        counts2 = sorted((s.name, s.triangle_count) for s in manifest2.structures)
        if counts1 != counts2:
            print("FAIL: triangle counts differ between runs", file=sys.stderr)
            print(f"  run1: {counts1}", file=sys.stderr)
            print(f"  run2: {counts2}", file=sys.stderr)
            return 1

        print(f"OK: built {len(manifest.structures)} structures")
        for s in manifest.structures:
            print(
                f"  {s.name:<18} {s.triangle_count:>6} tris  "
                f"{s.vertex_count:>6} verts  ({s.material_hint})"
            )
        print(f"  spec_hash: {manifest.spec_hash}")
        print(f"  manifest:  {json.dumps(manifest.to_dict())[:80]}...")
        return 0


if __name__ == "__main__":
    sys.exit(main())
