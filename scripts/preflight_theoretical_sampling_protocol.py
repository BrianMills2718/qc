#!/usr/bin/env python3
"""Preflight theoretical-sampling candidates/results against a protocol."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.theoretical_sampling_preflight import (
    THEORETICAL_SAMPLING_PREFLIGHT_CAUTION,
    TheoreticalSamplingPreflightError,
    TheoreticalSamplingPreflightReport,
    preflight_theoretical_sampling_payloads,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run theoretical-sampling preflight and emit machine-readable JSON."""
    parser = argparse.ArgumentParser(
        description="Preflight theoretical-sampling candidates/results against a protocol"
    )
    parser.add_argument(
        "protocol",
        help="Path to a schema_version=1 theoretical-sampling protocol JSON",
    )
    parser.add_argument(
        "--candidates-file",
        required=True,
        help="Theoretical-sampling candidate package JSON file",
    )
    parser.add_argument(
        "--results-file",
        help="Optional theoretical-sampling result package JSON file",
    )
    args = parser.parse_args(argv)

    try:
        protocol_payload = _load_json(Path(args.protocol), label="protocol")
        candidates_payload = _load_json(Path(args.candidates_file), label="candidates")
        results_payload = None
        if args.results_file:
            results_payload = _load_json(Path(args.results_file), label="results")
        report = preflight_theoretical_sampling_payloads(
            protocol_payload,
            candidates_payload,
            results_payload,
        )
    except ValueError as exc:
        report = TheoreticalSamplingPreflightReport(
            schema_version=1,
            package_type="theoretical_sampling_protocol_preflight",
            status="fail",
            target_gap_codes=[],
            covered_gap_codes=[],
            target_gap_types=[],
            covered_gap_types=[],
            candidate_count=0,
            result_selected_count=0,
            source_kinds=[],
            errors=[TheoreticalSamplingPreflightError(field="inputs", message=str(exc))],
            caution=THEORETICAL_SAMPLING_PREFLIGHT_CAUTION,
        )

    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0 if report.status == "pass" else 1


def _load_json(path: Path, *, label: str) -> Any:
    """Load a JSON file or raise a context-rich ValueError."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(
            f"Theoretical sampling {label} file '{path}' could not be read: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Theoretical sampling {label} file '{path}' is not valid JSON: {exc}"
        ) from exc


if __name__ == "__main__":
    raise SystemExit(main())
