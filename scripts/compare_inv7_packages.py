#!/usr/bin/env python3
"""Compare versioned INV-7 prompt-injection result packages."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.inv7_package_comparison import compare_inv7_package_files


def main(argv: Sequence[str] | None = None) -> int:
    """Compare INV-7 packages and emit a machine-readable JSON report."""
    parser = argparse.ArgumentParser(description="Compare versioned INV-7 prompt-injection packages")
    parser.add_argument(
        "packages",
        nargs="+",
        help="Two or more schema_version=1 INV-7 package JSON files",
    )
    parser.add_argument("--output", help="Optional path to write the comparison report JSON")
    args = parser.parse_args(argv)

    try:
        report = compare_inv7_package_files([Path(path) for path in args.packages])
    except ValueError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1

    output = json.dumps(report.model_dump(mode="json"), indent=2)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
