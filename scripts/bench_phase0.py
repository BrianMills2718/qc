#!/usr/bin/env python3
"""Evaluation-harness Phase 0: print a grounding/reliability scorecard for a project.

Usage:
    python scripts/bench_phase0.py <project_id> [--d3-gold-file d3_gold.json]
        [--d3-baselines-file baselines.json] [--gold-file gold.json]
        [--d7-baselines-file baselines.json] [--prompt-injection-file inv7.json]
        [--bias-counterfactual-file bias.json]
        [--codebook-quality-file quality.json]
        [--gt-fidelity-file gt_fidelity.json]
        [--interpretive-preference-file preference.json]
        [--confidence-calibration-file calibration.json]
        [--output scorecard.json]

Agent-drivable: emits JSON to stdout (and optionally a file). See
docs/EVALUATION_HARNESS.md (Phase 0). Deterministic, no LLM calls.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
import re
import sys
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.bench import (
    DEFAULT_OBSERVABILITY_DB_PATH,
    d10_cost_latency_scorecard,
    d10_wall_clock_scorecard,
    phase0_scorecard,
)
from qc_clean.core.d3_gold import application_gold_payload_for_scorecard
from qc_clean.core.d7_gold import d7_gold_payload_for_scorecard
from qc_clean.core.persistence.project_store import ProjectStore


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Phase 0 scorecard CLI."""
    parser = argparse.ArgumentParser(description="Evaluation-harness Phase 0 scorecard")
    parser.add_argument("project_id", help="Project ID to score")
    parser.add_argument(
        "--d3-gold-file",
        help="Optional D3 application-validity gold JSON file; applied in memory only",
    )
    parser.add_argument(
        "--d3-baselines-file",
        help="Optional D3 baseline prediction JSON file; applied in memory only",
    )
    parser.add_argument(
        "--gold-file",
        help="Optional D7 disconfirmation gold JSON file; applied in memory only",
    )
    parser.add_argument(
        "--d7-baselines-file",
        help="Optional D7 baseline prediction JSON file; applied in memory only",
    )
    parser.add_argument(
        "--prompt-injection-file",
        help="Optional INV-7 prompt-injection fixture results JSON file; applied in memory only",
    )
    parser.add_argument(
        "--bias-counterfactual-file",
        help="Optional D6 counterfactual identity-swap outcome JSON file; applied in memory only",
    )
    parser.add_argument(
        "--codebook-quality-file",
        help="Optional D4 codebook-quality rubric outcome JSON file; applied in memory only",
    )
    parser.add_argument(
        "--gt-fidelity-file",
        help="Optional D8 GT-fidelity rubric outcome JSON file; applied in memory only",
    )
    parser.add_argument(
        "--interpretive-preference-file",
        help="Optional D9 blind forced-choice preference outcome JSON file; applied in memory only",
    )
    parser.add_argument(
        "--confidence-calibration-file",
        help="Optional confidence/correctness calibration JSON file; applied in memory only",
    )
    parser.add_argument(
        "--observability-db",
        type=Path,
        default=None,
        help=(
            "Optional llm_client observability SQLite DB for D10 cost/latency; "
            "defaults to the shared llm_client DB when omitted"
        ),
    )
    parser.add_argument(
        "--trace-id",
        help="Optional exact trace_id for D10 cost/latency; default uses project trace prefix",
    )
    parser.add_argument("--output", help="Optional path to write the JSON scorecard")
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        help="Optional root directory for a versioned Phase 0 benchmark artifact package",
    )
    args = parser.parse_args(argv)

    store = ProjectStore()
    try:
        state = store.load(args.project_id)
    except FileNotFoundError:
        print(json.dumps({"error": f"Project '{args.project_id}' not found."}))
        return 1
    loaded_state = state

    if args.d3_gold_file:
        try:
            d3_gold = load_d3_gold_file(Path(args.d3_gold_file))
        except ValueError as exc:
            print(json.dumps({"error": str(exc)}))
            return 1
        state = state.model_copy(deep=True)
        state.config.extra = dict(state.config.extra)
        state.config.extra["application_gold"] = d3_gold

    if args.d3_baselines_file:
        try:
            d3_baselines = load_d3_baselines_file(Path(args.d3_baselines_file))
        except ValueError as exc:
            print(json.dumps({"error": str(exc)}))
            return 1
        state = state.model_copy(deep=True)
        state.config.extra = dict(state.config.extra)
        state.config.extra["application_baselines"] = d3_baselines

    if args.gold_file:
        try:
            gold = load_d7_gold_file(Path(args.gold_file))
        except ValueError as exc:
            print(json.dumps({"error": str(exc)}))
            return 1
        state = state.model_copy(deep=True)
        state.config.extra = dict(state.config.extra)
        state.config.extra["disconfirmation_gold"] = gold

    if args.d7_baselines_file:
        try:
            baselines = load_d7_baselines_file(Path(args.d7_baselines_file))
        except ValueError as exc:
            print(json.dumps({"error": str(exc)}))
            return 1
        state = state.model_copy(deep=True)
        state.config.extra = dict(state.config.extra)
        state.config.extra["disconfirmation_baselines"] = baselines

    if args.prompt_injection_file:
        try:
            prompt_injection_results = load_prompt_injection_file(Path(args.prompt_injection_file))
        except ValueError as exc:
            print(json.dumps({"error": str(exc)}))
            return 1
        state = state.model_copy(deep=True)
        state.config.extra = dict(state.config.extra)
        state.config.extra["prompt_injection_evaluations"] = prompt_injection_results

    if args.bias_counterfactual_file:
        try:
            bias_counterfactual_results = load_bias_counterfactual_file(
                Path(args.bias_counterfactual_file)
            )
        except ValueError as exc:
            print(json.dumps({"error": str(exc)}))
            return 1
        state = state.model_copy(deep=True)
        state.config.extra = dict(state.config.extra)
        state.config.extra["bias_counterfactual_evaluations"] = bias_counterfactual_results

    if args.codebook_quality_file:
        try:
            codebook_quality_results = load_codebook_quality_file(
                Path(args.codebook_quality_file)
            )
        except ValueError as exc:
            print(json.dumps({"error": str(exc)}))
            return 1
        state = state.model_copy(deep=True)
        state.config.extra = dict(state.config.extra)
        state.config.extra["codebook_quality_evaluations"] = codebook_quality_results

    if args.gt_fidelity_file:
        try:
            gt_fidelity_results = load_gt_fidelity_file(Path(args.gt_fidelity_file))
        except ValueError as exc:
            print(json.dumps({"error": str(exc)}))
            return 1
        state = state.model_copy(deep=True)
        state.config.extra = dict(state.config.extra)
        state.config.extra["gt_fidelity_evaluations"] = gt_fidelity_results

    if args.interpretive_preference_file:
        try:
            interpretive_preference_results = load_interpretive_preference_file(
                Path(args.interpretive_preference_file)
            )
        except ValueError as exc:
            print(json.dumps({"error": str(exc)}))
            return 1
        state = state.model_copy(deep=True)
        state.config.extra = dict(state.config.extra)
        state.config.extra["interpretive_preference_evaluations"] = (
            interpretive_preference_results
        )

    if args.confidence_calibration_file:
        try:
            confidence_calibration_results = load_confidence_calibration_file(
                Path(args.confidence_calibration_file)
            )
        except ValueError as exc:
            print(json.dumps({"error": str(exc)}))
            return 1
        state = state.model_copy(deep=True)
        state.config.extra = dict(state.config.extra)
        state.config.extra["confidence_calibration_evaluations"] = (
            confidence_calibration_results
        )

    try:
        card = phase0_scorecard(state)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    card.setdefault("_meta", {})["input_hashes"] = phase0_input_hashes(
        loaded_state,
        d3_gold_file=Path(args.d3_gold_file) if args.d3_gold_file else None,
        d3_baselines_file=(
            Path(args.d3_baselines_file) if args.d3_baselines_file else None
        ),
        gold_file=Path(args.gold_file) if args.gold_file else None,
        d7_baselines_file=Path(args.d7_baselines_file) if args.d7_baselines_file else None,
        prompt_injection_file=Path(args.prompt_injection_file) if args.prompt_injection_file else None,
        bias_counterfactual_file=(
            Path(args.bias_counterfactual_file) if args.bias_counterfactual_file else None
        ),
        codebook_quality_file=(
            Path(args.codebook_quality_file) if args.codebook_quality_file else None
        ),
        gt_fidelity_file=Path(args.gt_fidelity_file) if args.gt_fidelity_file else None,
        interpretive_preference_file=(
            Path(args.interpretive_preference_file)
            if args.interpretive_preference_file
            else None
        ),
        confidence_calibration_file=(
            Path(args.confidence_calibration_file)
            if args.confidence_calibration_file
            else None
        ),
        observability_db=args.observability_db,
    )
    card["_meta"]["run_configuration_hashes"] = phase0_run_configuration_hashes(
        loaded_state,
    )
    observability_db = args.observability_db or DEFAULT_OBSERVABILITY_DB_PATH
    card["wall_clock_d10"] = d10_wall_clock_scorecard(state)
    card["cost_latency_d10"] = d10_cost_latency_scorecard(
        state,
        observability_db,
        trace_id=args.trace_id,
    )

    text = json.dumps(card, indent=2)
    if args.artifact_dir:
        try:
            write_phase0_benchmark_artifact(
                card,
                args.artifact_dir,
                state=loaded_state,
                command=phase0_command_provenance(args),
                scorecard_text=text,
            )
        except (OSError, ValueError) as exc:
            print(json.dumps({"error": str(exc)}))
            return 1
    print(text)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    return 0


def write_phase0_benchmark_artifact(
    card: dict[str, Any],
    artifact_root: Path,
    *,
    state,
    command: dict[str, Any],
    generated_at: datetime | None = None,
    scorecard_text: str | None = None,
) -> Path:
    """Write a versioned Phase 0 benchmark artifact package."""
    generated_at = _utc_generated_at(generated_at)
    run_dir = artifact_root / phase0_artifact_dir_name(state.id, generated_at)
    if run_dir.exists():
        raise ValueError(f"Benchmark artifact directory already exists: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=False)

    scorecard_text = scorecard_text if scorecard_text is not None else json.dumps(card, indent=2)
    scorecard_bytes = scorecard_text.encode("utf-8")
    scorecard_path = run_dir / "scorecard.json"
    scorecard_path.write_bytes(scorecard_bytes)

    timing_payload = phase0_timing_artifact(card)
    timing_text = json.dumps(timing_payload, indent=2, sort_keys=True)
    timing_bytes = timing_text.encode("utf-8")
    timing_path = run_dir / "timing_d10.json"
    timing_path.write_bytes(timing_bytes)

    manifest = phase0_artifact_manifest(
        card,
        state=state,
        command=command,
        generated_at=generated_at,
        scorecard_sha256=hashlib.sha256(scorecard_bytes).hexdigest(),
        timing_sha256=hashlib.sha256(timing_bytes).hexdigest(),
    )
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return run_dir


def phase0_artifact_manifest(
    card: dict[str, Any],
    *,
    state,
    command: dict[str, Any],
    generated_at: datetime,
    scorecard_sha256: str,
    timing_sha256: str,
) -> dict[str, Any]:
    """Build the manifest for a Phase 0 benchmark artifact package."""
    meta = card.get("_meta", {})
    input_hashes = meta.get("input_hashes")
    if not isinstance(input_hashes, dict):
        raise ValueError("Phase 0 scorecard is missing _meta.input_hashes; cannot write artifact")
    run_configuration_hashes = meta.get("run_configuration_hashes")
    if not isinstance(run_configuration_hashes, dict):
        run_configuration_hashes = phase0_run_configuration_hashes(state)
    return {
        "schema_version": 1,
        "artifact_type": "qualitative_coding.phase0_scorecard",
        "generated_at": _format_generated_at(generated_at),
        "project_id": state.id,
        "project_name": state.name,
        "phase": meta.get("phase", 0),
        "scorecard_file": "scorecard.json",
        "scorecard_sha256": scorecard_sha256,
        "timing_file": "timing_d10.json",
        "timing_sha256": timing_sha256,
        "input_hashes": input_hashes,
        "run_configuration_hashes": run_configuration_hashes,
        "claim_discipline": meta.get("claims"),
        "prompt_eval": {
            "status": "not_run",
            "owner": "prompt_eval",
            "note": (
                "Phase 0 artifact packaging only; bootstrap intervals, statistical "
                "comparisons, held-out datasets, and full experiment tracking belong "
                "to the future prompt_eval-backed suite."
            ),
        },
        "command": command,
    }


def phase0_timing_artifact(card: dict[str, Any]) -> dict[str, Any]:
    """Extract D10 timing sections into a dedicated artifact payload."""
    return {
        "schema_version": 1,
        "artifact_type": "qualitative_coding.phase0_d10_timing",
        "source_file": "scorecard.json",
        "cost_latency_d10": card.get(
            "cost_latency_d10",
            _missing_d10_artifact_section("cost_latency_d10"),
        ),
        "wall_clock_d10": card.get(
            "wall_clock_d10",
            _missing_d10_artifact_section("wall_clock_d10"),
        ),
        "runtime_environment": _runtime_environment_metadata(),
        "note": (
            "D10 timing artifact packages local Phase 0 timing metadata for "
            "review. It is not public benchmark timing evidence, a baseline "
            "comparison, or a SOTA claim."
        ),
    }


def _runtime_environment_metadata() -> dict[str, Any]:
    """Return non-sensitive runtime context for local timing artifacts."""
    return {
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
        },
        "os": {
            "system": platform.system(),
            "release": platform.release(),
        },
        "machine": platform.machine(),
        "logical_cpu_count": os.cpu_count() or 0,
    }


def _missing_d10_artifact_section(section: str) -> dict[str, str]:
    """Represent absent D10 scorecard sections without estimating timing."""
    return {
        "status": "not_available",
        "reason": f"Scorecard did not contain {section}; artifact writer did not estimate it.",
        "note": "D10 artifact sections must come from scored Phase 0 data.",
    }


def phase0_command_provenance(args: argparse.Namespace) -> dict[str, Any]:
    """Return CLI provenance for Phase 0 artifact manifests."""
    return {
        "entrypoint": "scripts/bench_phase0.py",
        "project_id": args.project_id,
        "d3_gold_file": str(Path(args.d3_gold_file)) if args.d3_gold_file else None,
        "d3_baselines_file": (
            str(Path(args.d3_baselines_file)) if args.d3_baselines_file else None
        ),
        "gold_file": str(Path(args.gold_file)) if args.gold_file else None,
        "d7_baselines_file": (
            str(Path(args.d7_baselines_file)) if args.d7_baselines_file else None
        ),
        "prompt_injection_file": (
            str(Path(args.prompt_injection_file)) if args.prompt_injection_file else None
        ),
        "bias_counterfactual_file": (
            str(Path(args.bias_counterfactual_file))
            if args.bias_counterfactual_file
            else None
        ),
        "codebook_quality_file": (
            str(Path(args.codebook_quality_file)) if args.codebook_quality_file else None
        ),
        "gt_fidelity_file": (
            str(Path(args.gt_fidelity_file)) if args.gt_fidelity_file else None
        ),
        "interpretive_preference_file": (
            str(Path(args.interpretive_preference_file))
            if args.interpretive_preference_file
            else None
        ),
        "confidence_calibration_file": (
            str(Path(args.confidence_calibration_file))
            if args.confidence_calibration_file
            else None
        ),
        "observability_db": str(args.observability_db) if args.observability_db else None,
        "trace_id": args.trace_id,
        "output": args.output,
        "artifact_dir": str(args.artifact_dir) if args.artifact_dir else None,
    }


def phase0_artifact_dir_name(project_id: str, generated_at: datetime) -> str:
    """Return the versioned run-directory name for a Phase 0 artifact."""
    return f"{_format_artifact_timestamp(generated_at)}-{_artifact_slug(project_id)}-phase0"


def _utc_generated_at(generated_at: datetime | None) -> datetime:
    if generated_at is None:
        return datetime.now(timezone.utc)
    if generated_at.tzinfo is None:
        return generated_at.replace(tzinfo=timezone.utc)
    return generated_at.astimezone(timezone.utc)


def _format_generated_at(generated_at: datetime) -> str:
    return _utc_generated_at(generated_at).isoformat().replace("+00:00", "Z")


def _format_artifact_timestamp(generated_at: datetime) -> str:
    return _utc_generated_at(generated_at).strftime("%Y%m%dT%H%M%S%fZ")


def _artifact_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-._")
    return slug or "project"


def phase0_input_hashes(
    state,
    *,
    d3_gold_file: Path | None,
    d3_baselines_file: Path | None,
    gold_file: Path | None,
    d7_baselines_file: Path | None,
    prompt_injection_file: Path | None,
    bias_counterfactual_file: Path | None,
    codebook_quality_file: Path | None,
    gt_fidelity_file: Path | None,
    interpretive_preference_file: Path | None,
    confidence_calibration_file: Path | None,
    observability_db: Path | None,
) -> dict[str, Any]:
    """Return deterministic SHA-256 input hashes for Phase 0 bench output."""
    return {
        "hash_algorithm": "sha256",
        "project_id": state.id,
        "project_state_sha256": sha256_jsonable(state.model_dump(mode="json")),
        "corpus_sha256": sha256_jsonable(corpus_hash_payload(state)),
        "d3_gold_file_sha256": (
            sha256_file(d3_gold_file) if d3_gold_file else None
        ),
        "d3_baselines_file_sha256": (
            sha256_file(d3_baselines_file) if d3_baselines_file else None
        ),
        "gold_file_sha256": sha256_file(gold_file) if gold_file else None,
        "d7_baselines_file_sha256": (
            sha256_file(d7_baselines_file) if d7_baselines_file else None
        ),
        "prompt_injection_file_sha256": (
            sha256_file(prompt_injection_file) if prompt_injection_file else None
        ),
        "bias_counterfactual_file_sha256": (
            sha256_file(bias_counterfactual_file) if bias_counterfactual_file else None
        ),
        "codebook_quality_file_sha256": (
            sha256_file(codebook_quality_file) if codebook_quality_file else None
        ),
        "gt_fidelity_file_sha256": (
            sha256_file(gt_fidelity_file) if gt_fidelity_file else None
        ),
        "interpretive_preference_file_sha256": (
            sha256_file(interpretive_preference_file)
            if interpretive_preference_file
            else None
        ),
        "confidence_calibration_file_sha256": (
            sha256_file(confidence_calibration_file)
            if confidence_calibration_file
            else None
        ),
        "observability_db_sha256": sha256_file(observability_db),
    }


def phase0_run_configuration_hashes(state) -> dict[str, Any]:
    """Return deterministic Phase 0 run-configuration hashes."""
    payload = run_configuration_hash_payload(state)
    return {
        "hash_algorithm": "sha256",
        "project_id": state.id,
        "methodology": payload["methodology"],
        "model_name": payload["model_name"],
        "project_config_sha256": sha256_jsonable(payload),
        "prompt_hashes": {
            "status": "not_run",
            "reason": (
                "Phase 0 does not execute prompt templates or live model calls; "
                "full prompt/model hashes belong to the future prompt_eval-backed suite."
            ),
        },
    }


def run_configuration_hash_payload(state) -> dict[str, Any]:
    """Return the canonical persisted config payload hashed by Phase 0."""
    methodology = getattr(state.config.methodology, "value", state.config.methodology)
    return {
        "methodology": methodology,
        "model_name": state.config.model_name,
        "config_extra": state.config.extra,
    }


def corpus_hash_payload(state) -> list[dict[str, Any]]:
    """Return the canonical corpus payload used for dataset hashing."""
    return [
        {
            "id": doc.id,
            "name": doc.name,
            "content": doc.content,
            "metadata": doc.metadata,
        }
        for doc in state.corpus.documents
    ]


def sha256_jsonable(value: Any) -> str:
    """Hash a JSON-serializable value using canonical compact JSON."""
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path | None) -> str | None:
    """Hash file bytes, returning None when no file exists."""
    if path is None or not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_d7_gold_file(path: Path) -> Any:
    """Load and shape-check an external D7 gold annotation file."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"D7 gold file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"D7 gold file '{path}' is not valid JSON: {exc}") from exc

    try:
        return d7_gold_payload_for_scorecard(raw)
    except ValueError as exc:
        raise ValueError(f"D7 gold file '{path}' is invalid: {exc}") from exc


def load_d3_gold_file(path: Path) -> Any:
    """Load and shape-check an external D3 application gold file."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"D3 gold file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"D3 gold file '{path}' is not valid JSON: {exc}") from exc

    try:
        return application_gold_payload_for_scorecard(raw)
    except ValueError as exc:
        raise ValueError(f"D3 gold file '{path}' is invalid: {exc}") from exc


def load_d3_baselines_file(path: Path) -> Any:
    """Load and shape-check an external D3 baseline prediction file."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"D3 baselines file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"D3 baselines file '{path}' is not valid JSON: {exc}") from exc

    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and isinstance(raw.get("application_baselines"), list):
        return raw["application_baselines"]
    raise ValueError(
        "D3 baselines file must be a JSON list of baseline predictions or an "
        "object with an 'application_baselines' list"
    )


def load_d7_baselines_file(path: Path) -> Any:
    """Load and shape-check an external D7 baseline prediction file."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"D7 baselines file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"D7 baselines file '{path}' is not valid JSON: {exc}") from exc

    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and isinstance(raw.get("disconfirmation_baselines"), list):
        return raw["disconfirmation_baselines"]
    raise ValueError(
        "D7 baselines file must be a JSON list of baseline predictions or an "
        "object with a 'disconfirmation_baselines' list"
    )


def load_prompt_injection_file(path: Path) -> Any:
    """Load and shape-check an external INV-7 prompt-injection result file."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Prompt injection file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Prompt injection file '{path}' is not valid JSON: {exc}") from exc

    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and isinstance(raw.get("prompt_injection_evaluations"), list):
        return raw["prompt_injection_evaluations"]
    raise ValueError(
        "Prompt injection file must be a JSON list of fixture outcomes or an "
        "object with a 'prompt_injection_evaluations' list"
    )


def load_bias_counterfactual_file(path: Path) -> Any:
    """Load and shape-check an external D6 counterfactual result file."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Bias counterfactual file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Bias counterfactual file '{path}' is not valid JSON: {exc}"
        ) from exc

    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and isinstance(raw.get("bias_counterfactual_evaluations"), list):
        return raw["bias_counterfactual_evaluations"]
    raise ValueError(
        "Bias counterfactual file must be a JSON list of counterfactual outcomes "
        "or an object with a 'bias_counterfactual_evaluations' list"
    )


def load_codebook_quality_file(path: Path) -> Any:
    """Load and shape-check an external D4 codebook-quality result file."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Codebook quality file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Codebook quality file '{path}' is not valid JSON: {exc}") from exc

    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and isinstance(raw.get("codebook_quality_evaluations"), list):
        return raw["codebook_quality_evaluations"]
    raise ValueError(
        "Codebook quality file must be a JSON list of rubric outcomes or an "
        "object with a 'codebook_quality_evaluations' list"
    )


def load_gt_fidelity_file(path: Path) -> Any:
    """Load and shape-check an external D8 GT-fidelity result file."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"GT fidelity file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"GT fidelity file '{path}' is not valid JSON: {exc}") from exc

    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and isinstance(raw.get("gt_fidelity_evaluations"), list):
        return raw["gt_fidelity_evaluations"]
    raise ValueError(
        "GT fidelity file must be a JSON list of rubric outcomes or an "
        "object with a 'gt_fidelity_evaluations' list"
    )


def load_interpretive_preference_file(path: Path) -> Any:
    """Load and shape-check an external D9 preference result file."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Interpretive preference file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Interpretive preference file '{path}' is not valid JSON: {exc}"
        ) from exc

    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and isinstance(raw.get("interpretive_preference_evaluations"), list):
        return raw
    raise ValueError(
        "Interpretive preference file must be a JSON list of forced-choice outcomes "
        "or an object with an 'interpretive_preference_evaluations' list"
    )


def load_confidence_calibration_file(path: Path) -> Any:
    """Load and shape-check an external confidence-calibration result file."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(
            f"Confidence calibration file '{path}' could not be read: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Confidence calibration file '{path}' is not valid JSON: {exc}"
        ) from exc

    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and isinstance(raw.get("confidence_calibration_evaluations"), list):
        return raw["confidence_calibration_evaluations"]
    raise ValueError(
        "Confidence calibration file must be a JSON list of confidence/correctness "
        "records or an object with a 'confidence_calibration_evaluations' list"
    )


if __name__ == "__main__":
    raise SystemExit(main())
