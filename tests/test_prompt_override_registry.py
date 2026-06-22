"""Tests for INV-7 prompt override surface registry governance."""

from __future__ import annotations

import json
from pathlib import Path

from qc_clean.core.prompt_override_registry import PROMPT_OVERRIDE_SURFACES
from scripts import check_prompt_override_registry

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_registry_declares_current_prompt_override_surfaces():
    """Current override surfaces and placeholder roles are centrally declared."""
    assert set(PROMPT_OVERRIDE_SURFACES) == {
        "gt_constant_comparison",
        "thematic_coding",
    }

    thematic = PROMPT_OVERRIDE_SURFACES["thematic_coding"]
    assert thematic.stage_name == "thematic_coding"
    assert thematic.required_data_placeholders == frozenset({"combined_text"})
    assert thematic.optional_data_placeholders == frozenset()
    assert thematic.metadata_placeholders == frozenset({"num_interviews"})

    gt = PROMPT_OVERRIDE_SURFACES["gt_constant_comparison"]
    assert gt.stage_name == "gt_constant_comparison"
    assert gt.required_data_placeholders == frozenset({"segment_text"})
    assert gt.optional_data_placeholders == frozenset({"codebook_context"})
    assert gt.metadata_placeholders == frozenset({
        "doc_name",
        "seg_idx",
        "total_segments",
    })


def test_check_prompt_override_registry_passes_current_source():
    """Current source uses only registered prompt override surfaces."""
    report = check_prompt_override_registry.check_prompt_override_registry(
        REPO_ROOT / "qc_clean"
    )

    assert report.ok is True
    assert report.registered_surfaces == [
        "gt_constant_comparison",
        "thematic_coding",
    ]
    assert report.used_surfaces == [
        "gt_constant_comparison",
        "thematic_coding",
    ]
    assert report.unregistered_surfaces == []
    assert report.unused_registered_surfaces == []


def test_check_prompt_override_registry_fails_for_unregistered_surface(tmp_path):
    """A future source use without registry declaration fails loudly."""
    source = tmp_path / "stage.py"
    source.write_text(
        'if ctx.prompt_overrides.get("unknown_stage"):\n'
        '    prompt = ctx.prompt_overrides["unknown_stage"]\n',
        encoding="utf-8",
    )

    report = check_prompt_override_registry.check_prompt_override_registry(tmp_path)

    assert report.ok is False
    assert report.unregistered_surfaces == ["unknown_stage"]
    assert "unknown_stage" in report.errors[0]


def test_check_prompt_override_registry_cli_outputs_json(capsys):
    """The checker CLI emits machine-readable pass/fail reports."""
    exit_code = check_prompt_override_registry.main([
        "--root",
        str(REPO_ROOT / "qc_clean"),
    ])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["schema_version"] == 1
    assert payload["ok"] is True
    assert payload["registered_surfaces"] == [
        "gt_constant_comparison",
        "thematic_coding",
    ]
