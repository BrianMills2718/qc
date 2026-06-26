#!/usr/bin/env python3
"""Verify a product-gate evidence package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.product_gate_package import verify_product_gate_package


def main(argv: Sequence[str] | None = None) -> int:
    """Run product-gate evidence package verification."""
    parser = argparse.ArgumentParser(
        description="Verify artifact hashes in a product-gate evidence package"
    )
    parser.add_argument("package", type=Path, help="Product-gate package JSON path")
    parser.add_argument("--base-dir", type=Path, help="Base directory for relative artifact paths")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args(argv)

    try:
        report = verify_product_gate_package(args.package, base_dir=args.base_dir)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1

    text = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
