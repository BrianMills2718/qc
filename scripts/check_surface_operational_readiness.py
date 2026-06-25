#!/usr/bin/env python3
"""Validate active-plan operational-readiness declarations."""

from __future__ import annotations

import re
import sys
from pathlib import Path


PLANS_DIR = Path("docs/plans")
PLANS_INDEX = PLANS_DIR / "CLAUDE.md"
ALLOWED_CLASSIFICATIONS = {
    "default_path_visible_surface",
    "claim_bearing_output",
    "internal_only",
    "governance_only",
}
ALLOWED_REAL_RUN_REQUIREMENTS = {"required", "not_required", "deferred"}
ACTIVE_RECORD_RE = re.compile(r"`?([A-Z0-9][A-Z0-9_]*\.md)`?")
FIELD_RE = re.compile(r"^\*\*(.+?):\*\*\s*(.+?)\s*$")


def active_plan_paths(index_text: str) -> list[Path]:
    """Return active plan paths from the plan index."""
    paths: list[Path] = []
    in_active = False
    for line in index_text.splitlines():
        if line.startswith("## "):
            in_active = line.strip() == "## Active Plans"
            continue
        if not in_active or not line.lstrip().startswith("|"):
            continue
        match = ACTIVE_RECORD_RE.search(line)
        if match:
            paths.append(PLANS_DIR / match.group(1))
    return paths


def extract_operational_validation_fields(text: str) -> dict[str, str] | None:
    """Return key-value pairs from the Operational Validation section."""
    marker = "\n## Operational Validation\n"
    if marker not in text:
        return None
    section = text.split(marker, 1)[1]
    next_section = section.find("\n## ")
    if next_section != -1:
        section = section[:next_section]
    fields: dict[str, str] = {}
    for line in section.splitlines():
        match = FIELD_RE.match(line.strip())
        if match:
            fields[match.group(1)] = match.group(2)
    return fields


def validate_operational_fields(plan_path: Path, fields: dict[str, str]) -> list[str]:
    """Return validation problems for one plan declaration."""
    problems: list[str] = []
    classification = fields.get("Classification", "").strip()
    surface_ids = fields.get("Surface IDs", "").strip()
    real_run_requirement = fields.get("Real-Run Requirement", "").strip()

    if classification not in ALLOWED_CLASSIFICATIONS:
        problems.append(
            f"{plan_path}: Classification must be one of {', '.join(sorted(ALLOWED_CLASSIFICATIONS))}"
        )
    if real_run_requirement not in ALLOWED_REAL_RUN_REQUIREMENTS:
        problems.append(
            f"{plan_path}: Real-Run Requirement must be one of "
            f"{', '.join(sorted(ALLOWED_REAL_RUN_REQUIREMENTS))}"
        )

    if classification in {"default_path_visible_surface", "claim_bearing_output"}:
        if not surface_ids or surface_ids.lower() == "none":
            problems.append(f"{plan_path}: visible/claim-bearing plans must declare Surface IDs")
        if real_run_requirement == "not_required":
            problems.append(
                f"{plan_path}: visible/claim-bearing plans cannot declare Real-Run Requirement as not_required"
            )

    if real_run_requirement == "deferred" and "Deferred Reason" not in fields:
        problems.append(f"{plan_path}: deferred real-run declarations require a Deferred Reason")

    return problems


def main(argv: list[str] | None = None) -> int:
    _ = argv
    if not PLANS_INDEX.exists():
        print(f"Missing plan index: {PLANS_INDEX}", file=sys.stderr)
        return 1

    problems: list[str] = []
    for plan_path in active_plan_paths(PLANS_INDEX.read_text(encoding="utf-8")):
        if not plan_path.exists():
            problems.append(f"Missing active plan file: {plan_path}")
            continue
        fields = extract_operational_validation_fields(plan_path.read_text(encoding="utf-8"))
        if fields is None:
            problems.append(f"{plan_path}: missing required '## Operational Validation' section")
            continue
        problems.extend(validate_operational_fields(plan_path, fields))

    if problems:
        print("Operational readiness policy failures:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print("Active plans satisfy operational-readiness declaration policy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
