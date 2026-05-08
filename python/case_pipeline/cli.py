"""`dragonfly-build-case` command-line entry point.

Usage:
    python -m case_pipeline.cli <spec.json> <out_dir>

We don't install a console script via setuptools because the rest of the
project doesn't have a packaging story yet — running as a module keeps it
self-contained. A future PR can add a `pyproject.toml` and pin the entry
point if/when we publish the pipeline.
"""

from __future__ import annotations

import argparse
import sys

from case_pipeline.models import CaseSpec
from case_pipeline.pipeline import build_case


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dragonfly-build-case",
        description="Build a Dragonfly XR case from a spec JSON.",
    )
    parser.add_argument("spec", help="Path to the case spec JSON.")
    parser.add_argument("out_dir", help="Output directory; created if missing.")
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress per-structure progress lines.",
    )
    args = parser.parse_args(argv)

    spec = CaseSpec.from_json_file(args.spec)
    if not args.quiet:
        print(f"[case_pipeline] case_id={spec.case_id} hash={spec.content_hash()}")

    manifest = build_case(spec, args.out_dir)

    if not args.quiet:
        print(f"[case_pipeline] wrote {len(manifest.structures)} structures:")
        for s in manifest.structures:
            print(
                f"  {s.name:<18} {s.triangle_count:>7} tris  "
                f"{s.vertex_count:>7} verts  ({s.material_hint})"
            )
        print(f"[case_pipeline] manifest -> {args.out_dir}/manifest.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
