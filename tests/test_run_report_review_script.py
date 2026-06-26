"""Tests for report review runner script."""

import json

from scripts import run_report_review


def test_run_report_review_script_writes_output(tmp_path, monkeypatch, capsys):
    packet_path = tmp_path / "packet.json"
    output_path = tmp_path / "response.json"
    packet_path.write_text(json.dumps({"packet": "payload"}), encoding="utf-8")

    async def fake_review(packet, **kwargs):
        return {
            "package_type": "qualitative_coding.report_review_response",
            "packet": str(packet),
            "kwargs": kwargs,
        }

    monkeypatch.setattr(run_report_review, "review_report_packet_file_async", fake_review)

    exit_code = run_report_review.main([
        str(packet_path),
        "--output",
        str(output_path),
        "--model",
        "fake-model",
        "--reviewer-id",
        "reviewer-1",
        "--trace-id",
        "trace-review",
        "--max-budget",
        "0.5",
    ])

    assert exit_code == 0
    stdout_payload = json.loads(capsys.readouterr().out)
    file_payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert stdout_payload == file_payload
    assert stdout_payload["kwargs"]["model_name"] == "fake-model"
    assert stdout_payload["kwargs"]["reviewer_id"] == "reviewer-1"
    assert stdout_payload["kwargs"]["trace_id"] == "trace-review"
    assert stdout_payload["kwargs"]["max_budget"] == 0.5
