"""Tests for the top-level qc_cli bench command."""

import hashlib
import json
import sys

import qc_cli
from scripts import bench_phase0
from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.schemas.domain import Corpus, Document, ProjectState


def test_qc_cli_bench_emits_phase0_scorecard(tmp_path, monkeypatch, capsys):
    state = ProjectState(
        id="cli_bench",
        name="CLI Bench",
        corpus=Corpus(documents=[Document(id="d1", name="a.txt", content="A")]),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)
    monkeypatch.setattr(sys, "argv", ["qc_cli.py", "bench", state.id])

    exit_code = qc_cli.main()

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["project"] == "CLI Bench"
    assert output["_meta"]["phase"] == 0
    assert output["_meta"]["input_hashes"]["project_id"] == state.id


def test_qc_cli_bench_forwards_files_and_output(tmp_path, monkeypatch, capsys):
    content = "AI failed here."
    doc = Document(id="d1", name="a.txt", content=content)
    state = ProjectState(id="cli_bench_files", name="CLI Bench Files", corpus=Corpus(documents=[doc]))
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    gold_file = tmp_path / "gold.json"
    gold_file.write_text(
        json.dumps({
            "contrary_evidence": [
                {
                    "target_claim_id": "claim-ai",
                    "doc_id": doc.id,
                    "start_char": 0,
                    "end_char": len(content),
                }
            ],
        }),
        encoding="utf-8",
    )
    output_file = tmp_path / "scorecard.json"
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "bench",
            state.id,
            "--gold-file",
            str(gold_file),
            "--output",
            str(output_file),
        ],
    )

    exit_code = qc_cli.main()

    assert exit_code == 0
    stdout_scorecard = json.loads(capsys.readouterr().out)
    file_scorecard = json.loads(output_file.read_text(encoding="utf-8"))
    assert stdout_scorecard == file_scorecard
    assert stdout_scorecard["disconfirmation_d7"]["status"] == "scored"
    expected_hash = hashlib.sha256(gold_file.read_bytes()).hexdigest()
    assert stdout_scorecard["_meta"]["input_hashes"]["gold_file_sha256"] == expected_hash


def test_qc_cli_bench_forwards_artifact_dir(tmp_path, monkeypatch, capsys):
    state = ProjectState(
        id="cli_bench_artifacts",
        name="CLI Bench Artifacts",
        corpus=Corpus(documents=[Document(id="d1", name="a.txt", content="A")]),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    artifact_root = tmp_path / "benchmark_results"
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "bench",
            state.id,
            "--artifact-dir",
            str(artifact_root),
        ],
    )

    exit_code = qc_cli.main()

    assert exit_code == 0
    stdout_scorecard = json.loads(capsys.readouterr().out)
    run_dirs = [path for path in artifact_root.iterdir() if path.is_dir()]
    assert len(run_dirs) == 1
    scorecard = json.loads((run_dirs[0] / "scorecard.json").read_text(encoding="utf-8"))
    assert scorecard == stdout_scorecard
    assert (run_dirs[0] / "manifest.json").exists()
