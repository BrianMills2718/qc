"""Tests for default-path surface contract governance checks."""

from pathlib import Path

import pytest

from scripts import check_default_path_surface_contracts as contracts
from scripts import check_surface_operational_readiness as readiness


def test_contract_registry_validates_known_surface_fields(tmp_path: Path):
    registry_path = tmp_path / "contracts.yaml"
    registry_path.write_text(
        """
version: 1
policy:
  scope: default_path_user_facing_analytic_surfaces
  default_gate_mode: validate_config
  strict_gate_mode: future
surfaces:
  - surface_id: graph.example_tab
    label: Example graph tab
    visible_by_default: true
    user_facing: true
    claim_bearing: false
    default_paths: ["thematic_analysis"]
    producer_contracts:
      - path: thematic_analysis
        status: present
        producers:
          - qc_clean/core/pipeline/stages/example.py
    operational_validation:
      real_run_requirement: required
      rollout_status: enforced_now
""".strip()
        + "\n",
        encoding="utf-8",
    )

    registry = contracts.load_registry(registry_path)

    assert registry.version == 1
    assert registry.surfaces[0].surface_id == "graph.example_tab"


def test_surface_contract_registry_warns_on_missing_default_producer(tmp_path: Path):
    registry_path = tmp_path / "contracts.yaml"
    registry_path.write_text(
        """
version: 1
policy:
  scope: default_path_user_facing_analytic_surfaces
  default_gate_mode: validate_config
  strict_gate_mode: future
surfaces:
  - surface_id: graph.code_relationships_tab
    label: Graph UI code relationships tab
    visible_by_default: true
    user_facing: true
    claim_bearing: true
    default_paths: ["thematic_analysis"]
    producer_contracts:
      - path: thematic_analysis
        status: missing
        producers: []
    operational_validation:
      real_run_requirement: required
      rollout_status: warning_until_follow_on_fix
""".strip()
        + "\n",
        encoding="utf-8",
    )

    registry = contracts.load_registry(registry_path)

    warnings = contracts.warning_messages(registry)

    assert any("graph.code_relationships_tab" in warning for warning in warnings)


def test_surface_operational_readiness_flags_missing_surface_ids():
    problems = readiness.validate_operational_fields(
        Path("docs/plans/EXAMPLE.md"),
        {
            "Classification": "claim_bearing_output",
            "Surface IDs": "None",
            "Real-Run Requirement": "required",
        },
    )

    assert any("must declare Surface IDs" in problem for problem in problems)


def test_surface_operational_readiness_rejects_not_required_for_visible_surface():
    problems = readiness.validate_operational_fields(
        Path("docs/plans/EXAMPLE.md"),
        {
            "Classification": "default_path_visible_surface",
            "Surface IDs": "`graph.code_relationships_tab`",
            "Real-Run Requirement": "not_required",
        },
    )

    assert any("cannot declare Real-Run Requirement as not_required" in problem for problem in problems)


def test_extract_operational_validation_fields_reads_section():
    text = """
# Plan

## Operational Validation

**Classification:** governance_only
**Surface IDs:** None
**Real-Run Requirement:** not_required

## Files Affected
"""

    fields = readiness.extract_operational_validation_fields(text)

    assert fields == {
        "Classification": "governance_only",
        "Surface IDs": "None",
        "Real-Run Requirement": "not_required",
    }
