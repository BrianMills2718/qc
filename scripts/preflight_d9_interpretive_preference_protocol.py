#!/usr/bin/env python3
"""Preflight D9 interpretive-preference results against a protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.d9_interpretive_preference_preflight import (  # noqa: E402
    D9_INTERPRETIVE_PREFERENCE_PREFLIGHT_CAUTION,
    D9InterpretivePreferencePreflightError,
    D9InterpretivePreferencePreflightReport,
    preflight_d9_interpretive_preference_payloads,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run D9 interpretive-preference preflight and emit JSON."""
    parser = argparse.ArgumentParser(
        description=(
            "Preflight D9 interpretive-preference result files against a "
            "registered protocol"
        )
    )
    parser.add_argument(
        "protocol",
        help="Path to a schema_version=1 D9 interpretive-preference protocol JSON",
    )
    parser.add_argument(
        "--preference-file",
        help="Optional D9 interpretive-preference result JSON file",
    )
    args = parser.parse_args(argv)

    try:
        protocol_payload = _load_json(Path(args.protocol), label="protocol")
        preference_payload = None
        preference_hash = None
        if args.preference_file:
            preference_path = Path(args.preference_file)
            preference_payload = _load_json(preference_path, label="preference")
            preference_hash = _sha256_file(preference_path, label="preference")
        report = preflight_d9_interpretive_preference_payloads(
            protocol_payload,
            preference_payload,
            preference_file_sha256=preference_hash,
        )
    except ValueError as exc:
        report = D9InterpretivePreferencePreflightReport(
            schema_version=1,
            package_type="d9_interpretive_preference_protocol_result_preflight",
            status="fail",
            target_criteria=[],
            target_surfaces=[],
            result_row_count=0,
            case_count=0,
            evaluator_count=0,
            evaluator_types=[],
            errors=[
                D9InterpretivePreferencePreflightError(
                    field="inputs",
                    message=str(exc),
                )
            ],
            caution=D9_INTERPRETIVE_PREFERENCE_PREFLIGHT_CAUTION,
        )

    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0 if report.status == "pass" else 1


def _load_json(path: Path, *, label: str) -> Any:
    """Load a JSON file or raise a context-rich ValueError."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(
            f"D9 interpretive-preference {label} file '{path}' could not be read: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"D9 interpretive-preference {label} file '{path}' is not valid JSON: {exc}"
        ) from exc


def _sha256_file(path: Path, *, label: str) -> str:
    """Hash file bytes with SHA-256."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ValueError(
            f"D9 interpretive-preference {label} file '{path}' could not be hashed: {exc}"
        ) from exc


if __name__ == "__main__":
    raise SystemExit(main())
