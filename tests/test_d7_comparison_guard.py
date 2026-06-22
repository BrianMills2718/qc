"""Tests for guarded D7 retrieval comparison CLI behavior."""

from __future__ import annotations

import asyncio
import hashlib
import json

from qc_clean.core.d7_live_baseline import (
    D7LiveCandidateSelection,
    export_d7_live_candidate_baseline_async,
)
from qc_clean.core.d7_retrieval import export_d7_retrieval_baseline
from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.core.segmentation import segment_corpus
from qc_clean.schemas.domain import (
    AnalyticClaim,
    ClaimKind,
    ClaimScope,
    Code,
    Codebook,
    Corpus,
    Document,
    ProjectState,
)
from scripts import compare_d7_retrieval


def test_compare_d7_retrieval_guard_includes_preflight_report(tmp_path, monkeypatch, capsys):
    state, store = _saved_state(tmp_path)
    package = _prediction_package(state)
    prediction_path = _write_json(tmp_path / "predictions.json", package)
    gold = _gold_package(package)
    gold_path = _write_json(tmp_path / "gold.json", gold)
    protocol = _protocol_for(
        package,
        gold,
        prediction_file_sha256=_sha256_file(prediction_path),
    )
    protocol_path = _write_json(tmp_path / "protocol.json", protocol)
    output_path = tmp_path / "report.json"
    monkeypatch.setattr(compare_d7_retrieval, "ProjectStore", lambda: store)

    exit_code = compare_d7_retrieval.main([
        state.id,
        "--gold-file",
        str(gold_path),
        "--predictions-file",
        str(prediction_path),
        "--protocol-package",
        str(protocol_path),
        "--output",
        str(output_path),
    ])

    output = json.loads(capsys.readouterr().out)
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert output["report_type"] == "qualitative_coding.d7_retrieval_comparison"
    assert output["preflight_report"]["status"] == "pass"
    assert written["preflight_report"]["status"] == "pass"


def test_compare_d7_retrieval_includes_input_hashes_and_command_provenance(
    tmp_path,
    monkeypatch,
    capsys,
):
    state, store = _saved_state(tmp_path)
    package = _prediction_package(state)
    prediction_path = _write_json(tmp_path / "predictions.json", package)
    gold = _gold_package(package)
    gold_path = _write_json(tmp_path / "gold.json", gold)
    protocol = _protocol_for(
        package,
        gold,
        prediction_file_sha256=_sha256_file(prediction_path),
    )
    protocol_path = _write_json(tmp_path / "protocol.json", protocol)
    output_path = tmp_path / "report.json"
    monkeypatch.setattr(compare_d7_retrieval, "ProjectStore", lambda: store)

    exit_code = compare_d7_retrieval.main([
        state.id,
        "--gold-file",
        str(gold_path),
        "--predictions-file",
        str(prediction_path),
        "--protocol-package",
        str(protocol_path),
        "--output",
        str(output_path),
    ])

    output = json.loads(capsys.readouterr().out)
    written = json.loads(output_path.read_text(encoding="utf-8"))
    hashes = output["_meta"]["input_hashes"]
    command = output["_meta"]["command"]
    assert exit_code == 0
    assert output["_meta"] == written["_meta"]
    assert hashes["hash_algorithm"] == "sha256"
    assert hashes["project_id"] == state.id
    assert hashes["project_state_sha256"] == _sha256_jsonable(
        state.model_dump(mode="json")
    )
    assert hashes["corpus_sha256"] == _sha256_jsonable(
        state.corpus.model_dump(mode="json")
    )
    assert hashes["gold_file_sha256"] == _sha256_file(gold_path)
    assert hashes["prediction_files"] == [
        {"path": str(prediction_path), "sha256": _sha256_file(prediction_path)}
    ]
    assert hashes["protocol_file_sha256"] == _sha256_file(protocol_path)
    assert command == {
        "project_id": state.id,
        "gold_file": str(gold_path),
        "prediction_files": [str(prediction_path)],
        "protocol_package": str(protocol_path),
        "output": str(output_path),
    }


def test_compare_d7_retrieval_guard_includes_metric_criteria_results(
    tmp_path,
    monkeypatch,
    capsys,
):
    state, store = _saved_state(tmp_path)
    package = _prediction_package(state)
    prediction_path = _write_json(tmp_path / "predictions.json", package)
    gold = _gold_package(package)
    gold_path = _write_json(tmp_path / "gold.json", gold)
    protocol = _protocol_for(
        package,
        gold,
        prediction_file_sha256=_sha256_file(prediction_path),
    )
    baseline_name = package["disconfirmation_baselines"][0]["name"]
    protocol["metric_criteria"] = [
        {
            "criterion_id": "retrieval-recall-floor",
            "baseline_name": baseline_name,
            "metric": "recall",
            "operator": ">=",
            "threshold": 1.0,
            "rationale": "The synthetic fixture should recover the one gold anchor.",
        },
        {
            "criterion_id": "retrieval-span-iou-floor",
            "baseline_name": baseline_name,
            "metric": "mean_best_gold_iou",
            "operator": ">=",
            "threshold": 1.0,
            "rationale": "The synthetic fixture should match the one gold span exactly.",
        },
    ]
    protocol_path = _write_json(tmp_path / "protocol.json", protocol)
    monkeypatch.setattr(compare_d7_retrieval, "ProjectStore", lambda: store)

    exit_code = compare_d7_retrieval.main([
        state.id,
        "--gold-file",
        str(gold_path),
        "--predictions-file",
        str(prediction_path),
        "--protocol-package",
        str(protocol_path),
    ])

    output = json.loads(capsys.readouterr().out)
    criteria = output["metric_criteria_report"]
    assert exit_code == 0
    assert criteria["status"] == "pass"
    assert criteria["criterion_count"] == 2
    assert {row["status"] for row in criteria["results"]} == {"pass"}
    assert criteria["results"][0]["observed_value"] == 1.0


def test_compare_d7_retrieval_guard_reports_missing_metric_criteria(
    tmp_path,
    monkeypatch,
    capsys,
):
    state, store = _saved_state(tmp_path)
    package = _prediction_package(state)
    prediction_path = _write_json(tmp_path / "predictions.json", package)
    gold = _gold_package(package)
    gold_path = _write_json(tmp_path / "gold.json", gold)
    protocol = _protocol_for(
        package,
        gold,
        prediction_file_sha256=_sha256_file(prediction_path),
    )
    baseline_name = package["disconfirmation_baselines"][0]["name"]
    protocol["metric_criteria"] = [
        {
            "criterion_id": "missing-diagnostic",
            "baseline_name": baseline_name,
            "metric": "mean_best_predicted_modified_hausdorff_distance",
            "operator": "<=",
            "threshold": 0.0,
            "rationale": "This fixture has no predicted span-offset diagnostic value.",
        }
    ]
    package["disconfirmation_baselines"][0]["contrary_evidence"][0].pop("start_char")
    package["disconfirmation_baselines"][0]["contrary_evidence"][0].pop("end_char")
    prediction_path = _write_json(tmp_path / "predictions_missing_span.json", package)
    protocol["expected_predictions"][0]["prediction_file_sha256"] = _sha256_file(
        prediction_path
    )
    protocol_path = _write_json(tmp_path / "protocol.json", protocol)
    monkeypatch.setattr(compare_d7_retrieval, "ProjectStore", lambda: store)

    exit_code = compare_d7_retrieval.main([
        state.id,
        "--gold-file",
        str(gold_path),
        "--predictions-file",
        str(prediction_path),
        "--protocol-package",
        str(protocol_path),
    ])

    output = json.loads(capsys.readouterr().out)
    criteria = output["metric_criteria_report"]
    assert exit_code == 0
    assert criteria["status"] == "fail"
    assert criteria["missing_count"] == 1
    assert criteria["results"][0]["status"] == "missing"
    assert criteria["results"][0]["observed_value"] is None


def test_compare_d7_retrieval_guard_blocks_failed_preflight_and_writes_no_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    state, store = _saved_state(tmp_path)
    package = _prediction_package(state)
    prediction_path = _write_json(tmp_path / "predictions.json", package)
    gold = _gold_package(package)
    gold_path = _write_json(tmp_path / "gold.json", gold)
    protocol = _protocol_for(package, gold, prediction_file_sha256="f" * 64)
    protocol_path = _write_json(tmp_path / "protocol.json", protocol)
    output_path = tmp_path / "report.json"
    monkeypatch.setattr(compare_d7_retrieval, "ProjectStore", lambda: store)

    exit_code = compare_d7_retrieval.main([
        state.id,
        "--gold-file",
        str(gold_path),
        "--predictions-file",
        str(prediction_path),
        "--protocol-package",
        str(protocol_path),
        "--output",
        str(output_path),
    ])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["status"] == "error"
    assert output["error"] == "D7 comparison preflight failed"
    assert output["preflight_report"]["status"] == "fail"
    assert not output_path.exists()


def test_compare_d7_retrieval_guard_accepts_live_baseline_package(tmp_path, monkeypatch, capsys):
    state, store = _saved_state(tmp_path)
    package = _live_prediction_package(state)
    prediction_path = _write_json(tmp_path / "live_baseline.json", package)
    gold = _gold_package_from_metadata(package["live_baseline_run"])
    gold_path = _write_json(tmp_path / "gold.json", gold)
    protocol = _protocol_for_live(
        package,
        gold,
        prediction_file_sha256=_sha256_file(prediction_path),
    )
    protocol_path = _write_json(tmp_path / "protocol.json", protocol)
    output_path = tmp_path / "report.json"
    monkeypatch.setattr(compare_d7_retrieval, "ProjectStore", lambda: store)

    exit_code = compare_d7_retrieval.main([
        state.id,
        "--gold-file",
        str(gold_path),
        "--predictions-file",
        str(prediction_path),
        "--protocol-package",
        str(protocol_path),
        "--output",
        str(output_path),
    ])

    output = json.loads(capsys.readouterr().out)
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert output["preflight_report"]["status"] == "pass"
    assert written["preflight_report"]["status"] == "pass"
    assert output["disconfirmation_d7"]["baselines"]


def test_compare_d7_retrieval_without_protocol_remains_compatible(tmp_path, monkeypatch, capsys):
    state, store = _saved_state(tmp_path)
    package = _prediction_package(state)
    prediction_path = _write_json(tmp_path / "predictions.json", package)
    gold_path = _write_json(tmp_path / "gold.json", _gold_package(package))
    monkeypatch.setattr(compare_d7_retrieval, "ProjectStore", lambda: store)

    exit_code = compare_d7_retrieval.main([
        state.id,
        "--gold-file",
        str(gold_path),
        "--predictions-file",
        str(prediction_path),
    ])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["report_type"] == "qualitative_coding.d7_retrieval_comparison"
    assert "preflight_report" not in output
    assert output["_meta"]["input_hashes"]["protocol_file_sha256"] is None
    assert output["_meta"]["command"]["protocol_package"] is None


def _saved_state(tmp_path) -> tuple[ProjectState, ProjectStore]:
    state = _state_with_claim("AI failed badly after rollout.", "AI improves workflow.")
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    return store.load(state.id), store


def _prediction_package(state: ProjectState) -> dict:
    return export_d7_retrieval_baseline(
        state,
        candidates_per_claim=1,
        trace_id="qualitative_coding/d7-retrieval/project-d7",
        max_budget=1.0,
    )


def _live_prediction_package(state: ProjectState) -> dict:
    async def fake_selector(*, candidates, **_kwargs):
        return D7LiveCandidateSelection(
            selected_candidate_ids=[candidates[0].id],
            rationale="Candidate directly contradicts the claim.",
        )

    return asyncio.run(export_d7_live_candidate_baseline_async(
        state,
        model_name="fake-live-model",
        candidates_per_claim=1,
        trace_id="qualitative_coding/d7-live-baseline/project-d7",
        max_budget=1.0,
        candidate_selector=fake_selector,
    ))


def _gold_package(package: dict) -> dict:
    metadata = package["retrieval_run"]
    return _gold_package_from_metadata(metadata)


def _gold_package_from_metadata(metadata: dict) -> dict:
    return {
        "schema_version": 1,
        "gold_set_id": "d7-heldout-v1",
        "dataset_name": "Held-out D7 comparison v1",
        "split": "held_out",
        "corpus_sha256": metadata["corpus_sha256"],
        "project_state_sha256": metadata["project_state_sha256"],
        "prompt_frozen": True,
        "contamination_checked": True,
        "adjudication": {
            "coder_count": 2,
            "adjudicator": "expert-panel",
            "protocol": "Independent coding followed by adjudication.",
        },
        "contrary_evidence": [
            {
                "target_claim_id": "claim-ai",
                "doc_id": "d1",
                "start_char": 0,
                "end_char": len("AI failed badly after rollout."),
            }
        ],
    }


def _protocol_for(
    package: dict,
    gold: dict,
    *,
    prediction_file_sha256: str | None,
) -> dict:
    metadata = package["retrieval_run"]
    baseline_name = package["disconfirmation_baselines"][0]["name"]
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.d7_retrieval_comparison_protocol",
        "protocol_id": "d7-heldout-comparison-v1",
        "project_id": metadata["project_id"],
        "dataset_name": gold["dataset_name"],
        "split": gold["split"],
        "gold_set_id": gold["gold_set_id"],
        "corpus_sha256": gold["corpus_sha256"],
        "project_state_sha256": gold["project_state_sha256"],
        "prompt_frozen": gold["prompt_frozen"],
        "contamination_checked": gold["contamination_checked"],
        "registered_before_run": True,
        "expected_predictions": [
            {
                "baseline_name": baseline_name,
                "retrieval_mode": metadata["retrieval_mode"],
                "candidates_per_claim": metadata["candidates_per_claim"],
                "max_targets": metadata["max_targets"],
                "embedding_model": metadata["embedding_model"],
                "embedding_dimensions": metadata["embedding_dimensions"],
                "trace_id": metadata["trace_id"],
                "max_budget": metadata["max_budget"],
                "prediction_file_sha256": prediction_file_sha256,
            }
        ],
        "success_criteria": [
            "Score retrieval predictions against the registered held-out D7 gold package."
        ],
        "caution": (
            "D7 comparison protocol validation is process metadata only; it is not "
            "held-out D7 evidence, live-baseline evidence, or superiority evidence."
        ),
    }


def _protocol_for_live(
    package: dict,
    gold: dict,
    *,
    prediction_file_sha256: str | None,
) -> dict:
    metadata = package["live_baseline_run"]
    baseline_name = package["disconfirmation_baselines"][0]["name"]
    protocol = _protocol_for_metadata(metadata, baseline_name, gold, prediction_file_sha256)
    protocol["expected_predictions"][0]["baseline_mode"] = metadata["baseline_mode"]
    protocol["expected_predictions"][0]["model"] = metadata["model"]
    return protocol


def _protocol_for_metadata(
    metadata: dict,
    baseline_name: str,
    gold: dict,
    prediction_file_sha256: str | None,
) -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.d7_retrieval_comparison_protocol",
        "protocol_id": "d7-heldout-comparison-v1",
        "project_id": metadata["project_id"],
        "dataset_name": gold["dataset_name"],
        "split": gold["split"],
        "gold_set_id": gold["gold_set_id"],
        "corpus_sha256": gold["corpus_sha256"],
        "project_state_sha256": gold["project_state_sha256"],
        "prompt_frozen": gold["prompt_frozen"],
        "contamination_checked": gold["contamination_checked"],
        "registered_before_run": True,
        "expected_predictions": [
            {
                "baseline_name": baseline_name,
                "retrieval_mode": metadata["retrieval_mode"],
                "candidates_per_claim": metadata["candidates_per_claim"],
                "max_targets": metadata["max_targets"],
                "embedding_model": metadata["embedding_model"],
                "embedding_dimensions": metadata["embedding_dimensions"],
                "trace_id": metadata["trace_id"],
                "max_budget": metadata["max_budget"],
                "prediction_file_sha256": prediction_file_sha256,
            }
        ],
        "success_criteria": [
            "Score retrieval/live predictions against the registered held-out D7 gold package."
        ],
        "caution": (
            "D7 comparison protocol validation is process metadata only; it is not "
            "held-out D7 evidence, live-baseline evidence, or superiority evidence."
        ),
    }


def _state_with_claim(content: str, claim_text: str) -> ProjectState:
    doc = Document(id="d1", name="interview.txt", content=content)
    state = ProjectState(
        id="project-d7",
        name="D7 guarded comparison test",
        corpus=Corpus(documents=[doc]),
        codebook=Codebook(codes=[
            Code(
                id="AI_USE",
                name="AI Use",
                description="Use of AI in workflow",
            )
        ]),
        claims=[_claim(claim_text)],
    )
    state.segments = segment_corpus(state.corpus.documents)
    return state


def _claim(text: str) -> AnalyticClaim:
    return AnalyticClaim(
        id="claim-ai",
        claim_kind=ClaimKind.SYNTHESIS_FINDING,
        source_stage="synthesis",
        claim_text=text,
        scope=ClaimScope(corpus_level=True, code_ids=["AI_USE"]),
        origin_object_type="synthesis",
        origin_object_id="finding:0",
    )


def _write_json(path, payload: dict) -> object:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _sha256_file(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_jsonable(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
