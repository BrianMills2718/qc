#!/usr/bin/env python3
"""Write a versioned product-gate evidence package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.product_gate_package import build_product_gate_package_from_files


def main(argv: Sequence[str] | None = None) -> int:
    """Run the product-gate evidence package writer."""
    parser = argparse.ArgumentParser(
        description="Write a product-gate evidence package with artifact hashes"
    )
    parser.add_argument("project_id", help="Project ID the evidence package belongs to")
    parser.add_argument("--reviewer-report", required=True, type=Path)
    parser.add_argument("--audit-report", type=Path)
    parser.add_argument("--baseline-package", type=Path)
    parser.add_argument("--baseline-comparison", type=Path)
    parser.add_argument("--review-packet", type=Path)
    parser.add_argument("--review-response", type=Path)
    parser.add_argument("--export-manifest", type=Path)
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args(argv)

    try:
        package = build_product_gate_package_from_files(
            project_id=args.project_id,
            reviewer_report=args.reviewer_report,
            audit_report=args.audit_report,
            baseline_package=args.baseline_package,
            baseline_comparison=args.baseline_comparison,
            review_packet=args.review_packet,
            review_response=args.review_response,
            export_manifest=args.export_manifest,
        )
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1

    text = json.dumps(package, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
