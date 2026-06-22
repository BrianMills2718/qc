#!/usr/bin/env python3
"""Validate a theoretical-sampling protocol package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.theoretical_sampling_protocol import load_theoretical_sampling_protocol


def main(argv: Sequence[str] | None = None) -> int:
    """Run the theoretical-sampling protocol validator CLI."""
    parser = argparse.ArgumentParser(
        description="Validate a theoretical-sampling protocol package"
    )
    parser.add_argument("protocol_file", type=Path, help="Theoretical-sampling protocol JSON file")
    args = parser.parse_args(argv)

    try:
        package = load_theoretical_sampling_protocol(args.protocol_file)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1

    print(json.dumps(package.model_dump(mode="json"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
