#!/usr/bin/env python3
"""Write a report-comparison review packet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.report_review_packet import build_report_review_packet_from_files


def main(argv: Sequence[str] | None = None) -> int:
    """Run the report review packet writer."""
    parser = argparse.ArgumentParser(
        description="Write a human/agent review packet for report baseline comparison"
    )
    parser.add_argument("structured_report", type=Path, help="Structured Markdown report path")
    parser.add_argument("baseline_package", type=Path, help="Report-baseline JSON package path")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args(argv)

    try:
        packet = build_report_review_packet_from_files(
            structured_report_path=args.structured_report,
            baseline_package_path=args.baseline_package,
        )
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1

    text = json.dumps(packet, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
