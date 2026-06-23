"""Tests for INV-7 package comparison reports."""

import json
import sys

import pytest

import qc_cli
from qc_clean.core.inv7_package_comparison import compare_inv7_package_files, compare_inv7_packages
from scripts import compare_inv7_packages as compare_inv7_packages_script


def test_compare_inv7_packages_reports_package_metrics_and_overlap(tmp_path):
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    first_path.write_text(json.dumps(_package_payload("pkg-a", failures=["fixture-b"])), encoding="utf-8")
    second_path.write_text(
        json.dumps(
            _package_payload(
                "pkg-b",
                failures=["fixture-c"],
                extra_fixture={"fixture_id": "fixture-d", "surface": "synthesis"},
            )
        ),
        encoding="utf-8",
    )

    report = compare_inv7_package_files([first_path, second_path])

    assert report.status == "compared"
    assert report.package_count == 2
    assert "not prompt-injection robustness proof" in report.caution
    [first, second] = report.compared_packages
    assert first.package_id == "pkg-a"
    assert first.total_fixtures == 3
    assert first.failed == 1
    assert first.attack_success_rate == pytest.approx(1 / 3)
    assert first.failed_fixture_ids == ["fixture-b"]
    assert first.by_surface["thematic_coding"].total == 2
    assert first.by_attack_type["direct_instruction_override"].failed == 1
    assert second.package_id == "pkg-b"
    assert second.total_fixtures == 4

    [pairwise] = report.pairwise_fixture_comparisons
    assert pairwise.left_package_id == "pkg-a"
    assert pairwise.right_package_id == "pkg-b"
    assert pairwise.shared_fixture_ids == ["fixture-a", "fixture-b", "fixture-c"]
    assert pairwise.only_left_fixture_ids == []
    assert pairwise.only_right_fixture_ids == ["fixture-d"]
    assert pairwise.changed_attack_outcome_fixture_ids == ["fixture-b", "fixture-c"]
    assert pairwise.attack_success_rate_delta == pytest.approx((1 / 4) - (1 / 3))


def test_compare_inv7_packages_requires_at_least_two_packages():
    with pytest.raises(ValueError, match="at least two"):
        compare_inv7_packages([])


def test_compare_inv7_packages_script_writes_json(tmp_path, capsys):
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    output_path = tmp_path / "comparison.json"
    first_path.write_text(json.dumps(_package_payload("pkg-a")), encoding="utf-8")
    second_path.write_text(json.dumps(_package_payload("pkg-b", failures=["fixture-a"])), encoding="utf-8")

    exit_code = compare_inv7_packages_script.main(
        [str(first_path), str(second_path), "--output", str(output_path)]
    )

    assert exit_code == 0
    stdout_report = json.loads(capsys.readouterr().out)
    file_report = json.loads(output_path.read_text(encoding="utf-8"))
    assert stdout_report == file_report
    assert file_report["package_type"] == "inv7_package_comparison"
    assert file_report["compared_packages"][1]["failed_fixture_ids"] == ["fixture-a"]


def test_qc_cli_compare_inv7_packages_delegates_to_script(tmp_path, capsys, monkeypatch):
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    first_path.write_text(json.dumps(_package_payload("pkg-a")), encoding="utf-8")
    second_path.write_text(json.dumps(_package_payload("pkg-b")), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["qc_cli.py", "compare-inv7-packages", str(first_path), str(second_path)],
    )

    exit_code = qc_cli.main()

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "compared"
    assert report["package_count"] == 2


def _package_payload(
    package_id: str,
    *,
    failures: list[str] | None = None,
    extra_fixture: dict | None = None,
) -> dict:
    failures = failures or []
    fixtures = [
        {
            "fixture_id": "fixture-a",
            "surface": "thematic_coding",
            "attack_type": "direct_instruction_override",
            "attack_succeeded": "fixture-a" in failures,
            "failure_mode": "canary_emitted" if "fixture-a" in failures else None,
            "evaluator": "test_harness",
            "notes": "",
        },
        {
            "fixture_id": "fixture-b",
            "surface": "thematic_coding",
            "attack_type": "direct_instruction_override",
            "attack_succeeded": "fixture-b" in failures,
            "failure_mode": "canary_emitted" if "fixture-b" in failures else None,
            "evaluator": "test_harness",
            "notes": "",
        },
        {
            "fixture_id": "fixture-c",
            "surface": "gt_constant_comparison",
            "attack_type": "data_exfiltration",
            "attack_succeeded": "fixture-c" in failures,
            "failure_mode": "canary_emitted" if "fixture-c" in failures else None,
            "evaluator": "test_harness",
            "notes": "",
        },
    ]
    if extra_fixture:
        fixtures.append(
            {
                "attack_type": "direct_instruction_override",
                "attack_succeeded": False,
                "failure_mode": None,
                "evaluator": "test_harness",
                "notes": "",
                **extra_fixture,
            }
        )
    return {
        "schema_version": 1,
        "package_id": package_id,
        "mode": "structural",
        "split": "canary",
        "fixture_set_id": "comparison-fixtures",
        "fixture_set_version": "1",
        "prompt_frozen": True,
        "contamination_checked": False,
        "evaluator": "test_harness",
        "note": "Test package only.",
        "prompt_injection_evaluations": fixtures,
    }
