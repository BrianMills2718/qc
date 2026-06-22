#!/usr/bin/env python3
"""Preflight an INV-7 live result package against a live protocol package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.inv7_live_preflight import (
    Inv7LivePreflightError,
    Inv7LivePreflightReport,
    preflight_inv7_live_payloads,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run INV-7 live preflight and emit machine-readable JSON."""
    parser = argparse.ArgumentParser(
        description="Preflight an INV-7 live result package against a live protocol"
    )
    parser.add_argument("protocol", help="Path to a schema_version=1 INV-7 live protocol JSON")
    parser.add_argument("package", help="Path to a schema_version=1 INV-7 result package JSON")
    args = parser.parse_args(argv)

    try:
        protocol_payload = _load_json(Path(args.protocol), label="protocol")
        package_payload = _load_json(Path(args.package), label="package")
        report = preflight_inv7_live_payloads(protocol_payload, package_payload)
    except ValueError as exc:
        report = Inv7LivePreflightReport(
            schema_version=1,
            package_type="inv7_live_preflight",
            status="fail",
            fixture_count=0,
            errors=[Inv7LivePreflightError(field="package", message=str(exc))],
            caution=(
                "INV-7 live preflight is process metadata only; it is not a live "
                "benchmark result, not prompt-injection robustness evidence, not "
                "model-obedience evidence, and not validity evidence."
            ),
        )

    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0 if report.status == "pass" else 1


def _load_json(path: Path, *, label: str) -> Any:
    """Load a JSON file or raise a context-rich ValueError."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"INV-7 live {label} file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"INV-7 live {label} file '{path}' is not valid JSON: {exc}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
