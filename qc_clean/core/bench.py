"""Evaluation-harness Phase 0 scorecard (see docs/EVALUATION_HARNESS.md).

Phase 0 = the cheap, deterministic, no-new-human metrics computable directly from
a saved ``ProjectState``: the D1 grounding rate, plus reliability/stability
summaries when present. This is the harness skeleton; richer metrics (gold-vs
agreement, bias, calibration) and the ``prompt_eval`` integration come later.

Deterministic and LLM-free so it can run in CI and be diffed across runs.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from math import sqrt
from pathlib import Path
from random import Random
import sqlite3
from typing import Any, Dict, Iterable

from pydantic import BaseModel, Field, ValidationError, model_validator

from qc_clean.core.d3_gold import ApplicationGoldAnchor, validate_d3_gold_set_payload
from qc_clean.core.d7_gold import DisconfirmationGoldAnchor, validate_d7_gold_set_payload
from qc_clean.core.grounding import verify_grounding
from qc_clean.core.pipeline.irr import (
    compute_categorical_gwet_ac1,
    compute_categorical_percent_agreement,
    compute_cohens_kappa,
    compute_gwet_ac1,
    compute_krippendorff_alpha,
    compute_percent_agreement,
)
from qc_clean.core.pipeline.saturation import assess_category_saturation
from qc_clean.core.segmentation import compute_coverage
from qc_clean.core.scope_lint import scope_status_for_lint
from qc_clean.schemas.domain import ClaimAnchor, ClaimKind, ProjectState


_D3_GOLD_EXTRA_KEY = "application_gold"
_D3_BASELINES_EXTRA_KEY = "application_baselines"
_D7_GOLD_EXTRA_KEY = "disconfirmation_gold"
_D7_BASELINES_EXTRA_KEY = "disconfirmation_baselines"
_RUN_TIMING_EXTRA_KEY = "run_timing"
_PROMPT_INJECTION_EXTRA_KEY = "prompt_injection_evaluations"
_BIAS_COUNTERFACTUAL_EXTRA_KEY = "bias_counterfactual_evaluations"
_BIAS_STRATIFIED_EXTRA_KEY = "bias_stratified_evaluations"
_CODEBOOK_QUALITY_EXTRA_KEY = "codebook_quality_evaluations"
_GT_FIDELITY_EXTRA_KEY = "gt_fidelity_evaluations"
_INTERPRETIVE_PREFERENCE_EXTRA_KEY = "interpretive_preference_evaluations"
_CONFIDENCE_CALIBRATION_EXTRA_KEY = "confidence_calibration_evaluations"
_EXACT_BOOTSTRAP_EXTRA_KEY = "phase0_exact_bootstrap"
_RELIABILITY_BOOTSTRAP_EXTRA_KEY = "phase0_reliability_bootstrap"
_RUBRIC_BOOTSTRAP_EXTRA_KEY = "phase0_rubric_bootstrap"
_CALIBRATION_BOOTSTRAP_EXTRA_KEY = "phase0_calibration_bootstrap"
_COUNTERFACTUAL_BOOTSTRAP_EXTRA_KEY = "phase0_counterfactual_bootstrap"
DEFAULT_OBSERVABILITY_DB_PATH = Path.home() / "projects" / "data" / "llm_observability.db"
_WILSON_Z_95 = 1.959963984540054
_CORPUS_SCOPE_FIELDS = (
    "phenomenon",
    "population",
    "sampling_frame",
    "inclusion_criteria",
    "exclusion_criteria",
    "notes",
)
_CORPUS_SCOPE_WARNING_BY_STATUS = {
    "missing": {
        "code": "missing_corpus_scope",
        "message": (
            "No corpus scope is recorded. Claim-bearing outputs must be bounded "
            "to the loaded documents only."
        ),
    },
    "empty": {
        "code": "empty_corpus_scope",
        "message": (
            "A corpus scope record exists, but no boundary details are specified."
        ),
    },
    "missing_sampling_frame": {
        "code": "missing_sampling_frame",
        "message": (
            "A corpus population is recorded without a sampling frame; the "
            "population field is not a defensible generalization boundary."
        ),
    },
}
_HUMAN_CEILING_EXACT_METRICS = ("recall", "precision", "f1")
_CODEBOOK_QUALITY_METRICS = ("clarity", "specificity", "usefulness", "grounding")
_GT_FIDELITY_METRICS = (
    "constant_comparison",
    "category_development",
    "memo_quality",
    "saturation_justification",
)
_CALIBRATION_BIN_COUNT = 10
_HUMAN_CEILING_AGREEMENT_METRIC_ALIASES = {
    "cohen_kappa": "cohens_kappa",
    "cohens_kappa": "cohens_kappa",
    "fleiss_kappa": "fleiss_kappa",
    "gwet_ac1": "gwet_ac1",
    "gwets_ac1": "gwet_ac1",
    "krippendorff_alpha": "krippendorff_alpha",
    "krippendorffs_alpha": "krippendorff_alpha",
}


@dataclass(frozen=True)
class _ComparableSpan:
    surface_id: str
    doc_id: str
    start_char: int
    end_char: int
    key: str


class ExactScoreBootstrapConfig(BaseModel):
    """Config for deterministic exact-anchor F1 bootstrap intervals."""

    enabled: bool = Field(
        default=True,
        description="Whether exact-anchor scorecards should include F1 bootstrap intervals",
    )
    samples: int = Field(
        default=1000,
        description="Number of bootstrap resamples to draw over exact gold/prediction keys",
    )
    confidence_level: float = Field(
        default=0.95,
        description="Two-sided confidence level for the bootstrap interval",
    )
    seed: int = Field(
        default=0,
        description="Deterministic random seed for bootstrap resampling",
    )

    @model_validator(mode="after")
    def require_valid_settings(self) -> "ExactScoreBootstrapConfig":
        """Reject malformed bootstrap settings instead of silently defaulting."""
        if self.samples < 1:
            raise ValueError("phase0_exact_bootstrap.samples must be at least 1")
        if not 0 < self.confidence_level < 1:
            raise ValueError("phase0_exact_bootstrap.confidence_level must be between 0 and 1")
        return self


class ReliabilityBootstrapConfig(BaseModel):
    """Config for deterministic reliability-matrix bootstrap intervals."""

    enabled: bool = Field(
        default=True,
        description="Whether D5 reliability scorecards should include bootstrap intervals",
    )
    samples: int = Field(
        default=1000,
        description="Number of bootstrap resamples to draw over reliability matrix rows",
    )
    confidence_level: float = Field(
        default=0.95,
        description="Two-sided confidence level for the bootstrap interval",
    )
    seed: int = Field(
        default=0,
        description="Deterministic random seed for reliability bootstrap resampling",
    )

    @model_validator(mode="after")
    def require_valid_settings(self) -> "ReliabilityBootstrapConfig":
        """Reject malformed reliability bootstrap settings."""
        if self.samples < 1:
            raise ValueError("phase0_reliability_bootstrap.samples must be at least 1")
        if not 0 < self.confidence_level < 1:
            raise ValueError(
                "phase0_reliability_bootstrap.confidence_level must be between 0 and 1"
            )
        return self


class RubricBootstrapConfig(BaseModel):
    """Config for deterministic rubric-score bootstrap intervals."""

    enabled: bool = Field(
        default=True,
        description="Whether rubric scorecards should include mean bootstrap intervals",
    )
    samples: int = Field(
        default=1000,
        description="Number of bootstrap resamples to draw over rubric outcome rows",
    )
    confidence_level: float = Field(
        default=0.95,
        description="Two-sided confidence level for the bootstrap interval",
    )
    seed: int = Field(
        default=0,
        description="Deterministic random seed for rubric bootstrap resampling",
    )

    @model_validator(mode="after")
    def require_valid_settings(self) -> "RubricBootstrapConfig":
        """Reject malformed rubric bootstrap settings."""
        if self.samples < 1:
            raise ValueError("phase0_rubric_bootstrap.samples must be at least 1")
        if not 0 < self.confidence_level < 1:
            raise ValueError(
                "phase0_rubric_bootstrap.confidence_level must be between 0 and 1"
            )
        return self


class CalibrationBootstrapConfig(BaseModel):
    """Config for deterministic confidence-calibration bootstrap intervals."""

    enabled: bool = Field(
        default=True,
        description="Whether confidence-calibration scorecards should include bootstrap intervals",
    )
    samples: int = Field(
        default=1000,
        description="Number of bootstrap resamples to draw over calibration records",
    )
    confidence_level: float = Field(
        default=0.95,
        description="Two-sided confidence level for the bootstrap interval",
    )
    seed: int = Field(
        default=0,
        description="Deterministic random seed for calibration bootstrap resampling",
    )

    @model_validator(mode="after")
    def require_valid_settings(self) -> "CalibrationBootstrapConfig":
        """Reject malformed calibration bootstrap settings."""
        if self.samples < 1:
            raise ValueError("phase0_calibration_bootstrap.samples must be at least 1")
        if not 0 < self.confidence_level < 1:
            raise ValueError(
                "phase0_calibration_bootstrap.confidence_level must be between 0 and 1"
            )
        return self


class CounterfactualBootstrapConfig(BaseModel):
    """Config for deterministic D6 counterfactual-distance bootstrap intervals."""

    enabled: bool = Field(
        default=True,
        description="Whether D6 counterfactual scorecards should include bootstrap intervals",
    )
    samples: int = Field(
        default=1000,
        description="Number of bootstrap resamples to draw over invariant counterfactual rows",
    )
    confidence_level: float = Field(
        default=0.95,
        description="Two-sided confidence level for the bootstrap interval",
    )
    seed: int = Field(
        default=0,
        description="Deterministic random seed for counterfactual bootstrap resampling",
    )

    @model_validator(mode="after")
    def require_valid_settings(self) -> "CounterfactualBootstrapConfig":
        """Reject malformed counterfactual bootstrap settings."""
        if self.samples < 1:
            raise ValueError("phase0_counterfactual_bootstrap.samples must be at least 1")
        if not 0 < self.confidence_level < 1:
            raise ValueError(
                "phase0_counterfactual_bootstrap.confidence_level must be between 0 and 1"
            )
        return self


class PromptInjectionEvaluation(BaseModel):
    """External prompt-injection fixture outcome used for INV-7 scoring."""

    fixture_id: str = Field(description="Stable ID for the adversarial fixture")
    surface: str = Field(description="Prompt surface tested, such as thematic_coding")
    attack_type: str = Field(
        default="unspecified",
        description="Attack class, such as direct_instruction_override or indirect_document_instruction",
    )
    attack_succeeded: bool = Field(
        description="True when the model/application followed or leaked because of the injected instruction"
    )
    failure_mode: str | None = Field(
        default=None,
        description="Optional explanation when the attack succeeded",
    )
    evaluator: str = Field(
        default="unspecified",
        description="Evaluator or harness that produced this fixture outcome",
    )
    notes: str = Field(
        default="",
        description="Optional human-readable notes for inspection",
    )

    @model_validator(mode="after")
    def require_nonempty_identifiers(self) -> "PromptInjectionEvaluation":
        """Require stable grouping keys before computing fixture rates."""
        if not self.fixture_id.strip():
            raise ValueError("prompt injection fixture_id must be non-empty")
        if not self.surface.strip():
            raise ValueError("prompt injection surface must be non-empty")
        return self


class BiasCounterfactualEvaluation(BaseModel):
    """External counterfactual identity-swap outcome used for D6 scoring."""

    case_id: str = Field(description="Stable ID for the counterfactual test case")
    attribute: str = Field(
        default="unspecified",
        description="Respondent attribute or identity cue varied in this case",
    )
    original_codes: list[str] = Field(
        description="Code IDs or names assigned to the original text"
    )
    counterfactual_codes: list[str] = Field(
        description="Code IDs or names assigned after identity-cue masking or swapping"
    )
    expected_invariant: bool = Field(
        default=True,
        description="True when substantive meaning should be unchanged by the swap",
    )
    evaluator: str = Field(
        default="unspecified",
        description="Evaluator or harness that produced this counterfactual outcome",
    )
    original_text_hash: str | None = Field(
        default=None,
        description="Optional hash of the original text variant",
    )
    counterfactual_text_hash: str | None = Field(
        default=None,
        description="Optional hash of the counterfactual text variant",
    )
    notes: str = Field(default="", description="Optional human-readable notes")

    @model_validator(mode="after")
    def require_stable_case_metadata(self) -> "BiasCounterfactualEvaluation":
        """Normalize stable keys and reject unusable code labels."""
        self.case_id = self.case_id.strip()
        if not self.case_id:
            raise ValueError("bias counterfactual case_id must be non-empty")
        self.attribute = self.attribute.strip() or "unspecified"
        self.original_codes = _clean_counterfactual_codes(
            self.original_codes,
            "original_codes",
        )
        self.counterfactual_codes = _clean_counterfactual_codes(
            self.counterfactual_codes,
            "counterfactual_codes",
        )
        return self


class BiasStratifiedEvaluation(BaseModel):
    """External stratified correctness/error outcome used for D6 scoring."""

    case_id: str = Field(description="Stable ID for the stratified evaluation row")
    attribute: str = Field(
        default="unspecified",
        description="Respondent attribute used for stratification",
    )
    group: str = Field(description="Attribute group for this row")
    correct: bool = Field(description="Whether the coded output was correct for this row")
    surface: str = Field(
        default="unspecified",
        description="Scored surface, such as application_validity or claim_validity",
    )
    evaluator: str = Field(
        default="unspecified",
        description="Evaluator or harness that produced this row",
    )
    error_type: str | None = Field(
        default=None,
        description="Optional error taxonomy label when correct is false",
    )
    notes: str = Field(default="", description="Optional human-readable notes")

    @model_validator(mode="after")
    def require_stratified_metadata(self) -> "BiasStratifiedEvaluation":
        """Normalize stable grouping keys and reject unusable rows."""
        self.case_id = self.case_id.strip()
        if not self.case_id:
            raise ValueError("bias stratified case_id must be non-empty")
        self.attribute = self.attribute.strip() or "unspecified"
        self.group = self.group.strip()
        if not self.group:
            raise ValueError("bias stratified group must be non-empty")
        self.surface = self.surface.strip() or "unspecified"
        if self.error_type is not None:
            self.error_type = self.error_type.strip() or None
        return self


class CodebookQualityEvaluation(BaseModel):
    """External D4 codebook-quality rubric outcome."""

    evaluator: str = Field(description="Evaluator identifier or redacted label")
    evaluator_type: str = Field(
        default="unspecified",
        description="Evaluator type, such as llm_judge or human_expert",
    )
    clarity: float = Field(description="0-1 score for codebook clarity")
    specificity: float = Field(description="0-1 score for code specificity")
    usefulness: float = Field(description="0-1 score for analytic usefulness")
    grounding: float = Field(description="0-1 score for grounding in source data")
    scope: str = Field(
        default="codebook",
        description="Rubric scope, such as codebook or individual_code",
    )
    code_id: str | None = Field(
        default=None,
        description="Optional code ID when the rubric outcome targets one code",
    )
    notes: str = Field(default="", description="Optional human-readable notes")

    @model_validator(mode="after")
    def require_valid_rubric_outcome(self) -> "CodebookQualityEvaluation":
        """Normalize grouping keys and reject out-of-range rubric scores."""
        self.evaluator = self.evaluator.strip()
        if not self.evaluator:
            raise ValueError("codebook quality evaluator must be non-empty")
        self.evaluator_type = self.evaluator_type.strip() or "unspecified"
        self.scope = self.scope.strip() or "codebook"
        if self.code_id is not None:
            self.code_id = self.code_id.strip()
            if not self.code_id:
                raise ValueError("codebook quality code_id must be non-empty when supplied")
        for metric_name in _CODEBOOK_QUALITY_METRICS:
            metric_value = getattr(self, metric_name)
            if not 0 <= metric_value <= 1:
                raise ValueError(f"codebook quality {metric_name} must be between 0 and 1")
        return self


class GTFidelityEvaluation(BaseModel):
    """External D8 grounded-theory fidelity rubric outcome."""

    evaluator: str = Field(description="Evaluator identifier or redacted label")
    evaluator_type: str = Field(
        default="unspecified",
        description="Evaluator type, such as llm_judge or human_expert",
    )
    constant_comparison: float = Field(description="0-1 score for constant comparison fidelity")
    category_development: float = Field(
        description="0-1 score for category property and dimension development"
    )
    memo_quality: float = Field(description="0-1 score for analytic memo quality")
    saturation_justification: float = Field(
        description="0-1 score for saturation justification quality"
    )
    scope: str = Field(
        default="grounded_theory_pipeline",
        description="Rubric scope, such as grounded_theory_pipeline or category",
    )
    artifact_id: str | None = Field(
        default=None,
        description="Optional artifact ID when the rubric targets a category, memo, or model",
    )
    notes: str = Field(default="", description="Optional human-readable notes")

    @model_validator(mode="after")
    def require_valid_gt_fidelity_outcome(self) -> "GTFidelityEvaluation":
        """Normalize grouping keys and reject out-of-range D8 rubric scores."""
        self.evaluator = self.evaluator.strip()
        if not self.evaluator:
            raise ValueError("GT fidelity evaluator must be non-empty")
        self.evaluator_type = self.evaluator_type.strip() or "unspecified"
        self.scope = self.scope.strip() or "grounded_theory_pipeline"
        if self.artifact_id is not None:
            self.artifact_id = self.artifact_id.strip()
            if not self.artifact_id:
                raise ValueError("GT fidelity artifact_id must be non-empty when supplied")
        for metric_name in _GT_FIDELITY_METRICS:
            metric_value = getattr(self, metric_name)
            if not 0 <= metric_value <= 1:
                raise ValueError(f"GT fidelity {metric_name} must be between 0 and 1")
        return self


class InterpretivePreferenceEvaluation(BaseModel):
    """External D9 blind forced-choice preference outcome."""

    case_id: str = Field(description="Stable ID for the interpretive-depth comparison case")
    evaluator: str = Field(
        default="unspecified",
        description="Evaluator identifier or redacted label",
    )
    evaluator_type: str = Field(
        default="unspecified",
        description="Evaluator type, such as human_expert or llm_judge",
    )
    preferred: str = Field(
        description="Forced-choice preference: system, human, or tie"
    )
    criterion: str = Field(
        default="interpretive_depth",
        description="Preference criterion, such as interpretive_depth",
    )
    surface: str = Field(
        default="unspecified",
        description="Compared surface, such as codebook or themes",
    )
    notes: str = Field(default="", description="Optional human-readable notes")

    @model_validator(mode="after")
    def require_valid_preference_outcome(self) -> "InterpretivePreferenceEvaluation":
        """Normalize stable keys and reject unusable forced-choice labels."""
        self.case_id = self.case_id.strip()
        if not self.case_id:
            raise ValueError("interpretive preference case_id must be non-empty")
        self.evaluator = self.evaluator.strip() or "unspecified"
        self.evaluator_type = self.evaluator_type.strip() or "unspecified"
        self.criterion = self.criterion.strip() or "interpretive_depth"
        self.surface = self.surface.strip() or "unspecified"
        self.preferred = self.preferred.strip().lower()
        if self.preferred not in {"system", "human", "tie"}:
            raise ValueError("interpretive preference preferred must be system, human, or tie")
        return self


class InterpretivePreferenceProtocol(BaseModel):
    """Protocol metadata for D9 non-inferiority assessment."""

    non_inferiority_margin: float = Field(
        description="Pre-registered tolerated system-minus-human preference deficit"
    )
    registered_before_evaluation: bool = Field(
        default=False,
        description="Whether the margin was registered before outcome evaluation",
    )
    protocol_id: str = Field(
        default="unspecified",
        description="Stable protocol identifier or redacted registration label",
    )
    notes: str = Field(default="", description="Optional protocol caveats")

    @model_validator(mode="after")
    def require_valid_protocol(self) -> "InterpretivePreferenceProtocol":
        """Reject unusable non-inferiority protocol metadata."""
        if not 0 < self.non_inferiority_margin < 1:
            raise ValueError("D9 non_inferiority_margin must be between 0 and 1")
        self.protocol_id = self.protocol_id.strip() or "unspecified"
        return self


class ConfidenceCalibrationEvaluation(BaseModel):
    """External confidence/correctness record used for calibration scoring."""

    item_id: str = Field(description="Stable ID for the scored prediction or decision")
    surface: str = Field(
        default="unspecified",
        description="Prediction surface, such as thematic_coding or negative_case",
    )
    confidence: float = Field(description="Reported confidence value from 0 to 1")
    correct: bool = Field(description="Whether the prediction was correct against gold/adjudication")
    evaluator: str = Field(
        default="unspecified",
        description="Evaluator or gold source that produced the correctness label",
    )
    target_id: str | None = Field(
        default=None,
        description="Optional target object ID, such as code/application/claim ID",
    )
    notes: str = Field(default="", description="Optional human-readable notes")

    @model_validator(mode="after")
    def require_valid_calibration_record(self) -> "ConfidenceCalibrationEvaluation":
        """Normalize stable keys and reject out-of-range confidence values."""
        self.item_id = self.item_id.strip()
        if not self.item_id:
            raise ValueError("confidence calibration item_id must be non-empty")
        self.surface = self.surface.strip() or "unspecified"
        self.evaluator = self.evaluator.strip() or "unspecified"
        if self.target_id is not None:
            self.target_id = self.target_id.strip()
            if not self.target_id:
                raise ValueError(
                    "confidence calibration target_id must be non-empty when supplied"
                )
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence calibration confidence must be between 0 and 1")
        return self


class DisconfirmationBaselinePrediction(BaseModel):
    """Baseline contrary-evidence predictions used for D7 comparison."""

    name: str = Field(description="Stable baseline name, such as single_prompt_chatgpt")
    description: str = Field(default="", description="Optional human-readable baseline description")
    contrary_evidence: list[DisconfirmationGoldAnchor] = Field(
        description="Baseline-predicted contrary-evidence anchors using the D7 exact anchor schema"
    )

    @model_validator(mode="after")
    def require_nonempty_name(self) -> "DisconfirmationBaselinePrediction":
        """Require a stable baseline key for scorecard output."""
        if not self.name.strip():
            raise ValueError("D7 baseline name must be non-empty")
        self.name = self.name.strip()
        return self


class ApplicationBaselinePrediction(BaseModel):
    """Baseline code-application predictions used for D3 comparison."""

    name: str = Field(description="Stable baseline name, such as single_prompt_chatgpt")
    description: str = Field(default="", description="Optional human-readable baseline description")
    code_applications: list[ApplicationGoldAnchor] = Field(
        description="Baseline-predicted code applications using the D3 exact anchor schema"
    )

    @model_validator(mode="after")
    def require_nonempty_name(self) -> "ApplicationBaselinePrediction":
        """Require a stable baseline key for scorecard output."""
        if not self.name.strip():
            raise ValueError("D3 baseline name must be non-empty")
        self.name = self.name.strip()
        return self


class RunTimingMetadata(BaseModel):
    """Run-level wall-clock timing metadata recorded by project run."""

    schema_version: int = Field(description="Version of the run timing metadata shape")
    started_at: str = Field(description="Wall-clock start timestamp for the project run")
    completed_at: str = Field(description="Wall-clock completion timestamp for the project run")
    duration_s: float = Field(description="Monotonic elapsed duration in seconds")
    status: str = Field(description="Final pipeline status for this run")
    trace_id: str = Field(description="Trace ID shared across LLM calls for this run")
    model: str = Field(description="Primary model configured for the run")
    exhaustive_coding: bool = Field(description="Whether this run used exhaustive segment coding")
    resume_from: str | None = Field(default=None, description="Stage name resumed from, if this was a resume run")
    document_count: int = Field(description="Number of documents present during the run")
    phase_result_count: int = Field(description="Number of phase result records after the run")

    @model_validator(mode="after")
    def require_valid_duration(self) -> "RunTimingMetadata":
        """Reject malformed timing metadata rather than estimating."""
        if self.schema_version != 1:
            raise ValueError("run_timing schema_version must be 1")
        if self.duration_s < 0:
            raise ValueError("run_timing duration_s must be non-negative")
        if self.document_count < 0:
            raise ValueError("run_timing document_count must be non-negative")
        if self.phase_result_count < 0:
            raise ValueError("run_timing phase_result_count must be non-negative")
        return self


def phase0_scorecard(state: ProjectState) -> Dict[str, Any]:
    """Compute the Phase 0 scorecard for one project state."""
    card: Dict[str, Any] = {
        "project": state.name,
        "methodology": state.config.methodology.value,
        "documents": state.corpus.num_documents,
        "codes": len(state.codebook.codes),
        "code_applications": len(state.code_applications),
        # D1 — grounding (the headline structural-rigor metric).
        "grounding": grounding_scorecard(state),
        # D2 — coverage over the segment universe (INV-8 denominator).
        "coverage": coverage_scorecard(state),
        # Corpus boundary — scope-record completeness, not sampling validity.
        "corpus_scope_adequacy": corpus_scope_adequacy_scorecard(state),
        # INV-9 — structural claim-ledger source-anchor coverage.
        "claim_anchor_coverage": claim_anchor_coverage_scorecard(state),
        # D3 — application validity when human/adjudicated gold is present.
        "application_validity_d3": application_validity_d3_scorecard(state),
        # D4 — externally supplied codebook-quality rubric outcomes.
        "codebook_quality_d4": codebook_quality_scorecard(state),
        # D7 — disconfirmation quality when human/adjudicated gold is present.
        "disconfirmation_d7": disconfirmation_d7_scorecard(state),
        # D8 — externally supplied GT-fidelity rubric outcomes.
        "gt_fidelity_d8": gt_fidelity_scorecard(state),
        # D9 — externally supplied blind forced-choice interpretive preference outcomes.
        "interpretive_preference_d9": interpretive_preference_scorecard(state),
        # INV-4 — category adequacy diagnostic, not proof of GT saturation.
        "category_saturation": assess_category_saturation(state).model_dump(),
        # INV-7 — prompt-injection fixture results when an external evaluator provides them.
        "prompt_injection_inv7": prompt_injection_scorecard(state),
        # D6 — externally supplied counterfactual identity-cue swap diagnostics.
        "bias_counterfactual_d6": bias_counterfactual_scorecard(state),
        # D6 — externally supplied stratified error diagnostics.
        "bias_stratified_d6": bias_stratified_scorecard(state),
        # Calibration — externally supplied confidence/correctness records.
        "confidence_calibration": confidence_calibration_scorecard(state),
        "data_warnings": list(state.data_warnings),
    }

    # D5 — consistency (reported, NOT validity; see theory doc §11/§15).
    if state.irr_result is not None:
        irr = state.irr_result
        reliability_bootstrap = _reliability_bootstrap_config(state)
        card["reliability_llm_pass_agreement"] = {
            "percent_agreement": irr.percent_agreement,
            "cohens_kappa": irr.cohens_kappa,
            "fleiss_kappa": irr.fleiss_kappa,
            "gwet_ac1": irr.gwet_ac1,
            "interpretation": irr.interpretation,
            "application_level": irr.application_level,
            "prevalence": _binary_matrix_prevalence(irr.coding_matrix),
            "note": (
                "LLM-pass agreement, not human inter-rater reliability; "
                "consistency not validity."
            ),
        }
        if reliability_bootstrap.enabled:
            card["reliability_llm_pass_agreement"]["bootstrap_ci"] = (
                _binary_reliability_bootstrap_ci(
                    irr.coding_matrix,
                    reliability_bootstrap,
                )
            )
        if irr.application_level:
            card["reliability_llm_pass_agreement"]["application_positive_segment_code"] = {
                "units": irr.application_units,
                "percent_agreement": irr.application_percent_agreement,
                "cohens_kappa": irr.application_cohens_kappa,
                "fleiss_kappa": irr.application_fleiss_kappa,
                "gwet_ac1": irr.application_gwet_ac1,
                "interpretation": irr.application_interpretation,
                "prevalence": _binary_matrix_prevalence(irr.application_matrix),
                "note": "Positive segment x code cells where at least one pass applied the code.",
            }
            if reliability_bootstrap.enabled:
                card["reliability_llm_pass_agreement"]["application_positive_segment_code"][
                    "bootstrap_ci"
                ] = _binary_reliability_bootstrap_ci(
                    irr.application_matrix,
                    reliability_bootstrap,
                )
            card["reliability_llm_pass_agreement"]["segment_decision"] = {
                "units": irr.segment_decision_units,
                "percent_agreement": irr.segment_decision_percent_agreement,
                "cohens_kappa": irr.segment_decision_cohens_kappa,
                "fleiss_kappa": irr.segment_decision_fleiss_kappa,
                "gwet_ac1": irr.segment_decision_gwet_ac1,
                "interpretation": irr.segment_decision_interpretation,
                "prevalence": _categorical_matrix_prevalence(irr.segment_decision_matrix),
                "note": "coded/no_code/not_examined decisions over the segment universe.",
            }
            if reliability_bootstrap.enabled:
                card["reliability_llm_pass_agreement"]["segment_decision"][
                    "bootstrap_ci"
                ] = _categorical_reliability_bootstrap_ci(
                    irr.segment_decision_matrix,
                    reliability_bootstrap,
                )
    if state.stability_result is not None:
        card["stability"] = {
            "overall_stability": state.stability_result.overall_stability,
            "stable": len(state.stability_result.stable_codes),
            "moderate": len(state.stability_result.moderate_codes),
            "unstable": len(state.stability_result.unstable_codes),
        }

    # Honest framing so a reader never mistakes Phase 0 for a SOTA claim.
    # The coverage note depends on whether this run was exhaustive: in "examined"
    # mode every segment carries a coding decision, so examined-and-judged
    # coverage is real; in "traversal" mode only touched segments are counted.
    if card["coverage"].get("mode") == "examined":
        coverage_note = (
            "examined-and-judged coverage available: every segment carries a coding "
            "decision (INV-8 exhaustive mode). Use `examined_rate` as the defensible "
            "denominator; `covered_rate` still reports only segments with anchored evidence."
        )
    else:
        coverage_note = (
            "traversal coverage only (segments with anchored evidence); examined-and-judged "
            "coverage is NOT available — re-run with `--exhaustive` for per-segment decisions (INV-8)"
        )
    card["_meta"] = {
        "phase": 0,
        "claims": "capability only — not a SOTA/parity claim (needs gold + baselines; see EVALUATION_HARNESS.md §7)",
        "coverage_note": coverage_note,
        "cost_note": "D10 cost/latency is populated by the bench CLI from llm_client observability rows; never estimate it from ProjectState.",
    }
    return card


def grounding_scorecard(state: ProjectState) -> dict[str, Any]:
    """Serialize D1 grounding with local Wilson interval metadata."""
    report = asdict(verify_grounding(state))
    report["grounding_rate_ci"] = _wilson_interval(
        report["anchored_verified"],
        report["total_applications"],
    )
    return report


def coverage_scorecard(state: ProjectState) -> dict[str, Any]:
    """Serialize D2 coverage with local Wilson interval metadata."""
    report = asdict(compute_coverage(state))
    examined_segments = report["examined_segments"]
    report["coded_segment_rate"] = (
        report["coded_segments"] / examined_segments
        if examined_segments
        else None
    )
    report["coverage_rate_ci"] = _wilson_interval(
        report["covered_segments"],
        report["total_segments"],
    )
    report["examined_rate_ci"] = _wilson_interval(
        report["examined_segments"],
        report["total_segments"],
    )
    report["coded_segment_rate_ci"] = _wilson_interval(
        report["coded_segments"],
        examined_segments,
    )
    return report


def corpus_scope_adequacy_scorecard(state: ProjectState) -> dict[str, Any]:
    """Serialize deterministic corpus-scope record completeness accounting."""
    scope_status = scope_status_for_lint(state)
    field_completeness = _corpus_scope_field_completeness(state)
    filled_field_count = sum(1 for value in field_completeness.values() if value)
    warnings = []
    if scope_status != "complete":
        warnings.append({
            **_CORPUS_SCOPE_WARNING_BY_STATUS[scope_status],
            "applies_to": "corpus_scope",
        })

    return {
        "scope_status": scope_status,
        "has_scope_record": state.corpus_scope is not None,
        "document_count": state.corpus.num_documents,
        "claim_count": len(state.claims),
        "claims_require_scope_boundary": bool(state.claims),
        "field_completeness": field_completeness,
        "filled_field_count": filled_field_count,
        "field_count": len(_CORPUS_SCOPE_FIELDS),
        "field_completion_rate": filled_field_count / len(_CORPUS_SCOPE_FIELDS),
        "minimum_boundary_recorded": scope_status == "complete",
        "population_without_sampling_frame": scope_status == "missing_sampling_frame",
        "warnings": warnings,
        "note": (
            "Deterministic corpus-scope record accounting only; this does not "
            "validate sampling-frame adequacy, population generalization, "
            "methodological validity, or SOTA evidence."
        ),
    }


def _corpus_scope_field_completeness(state: ProjectState) -> dict[str, bool]:
    """Return deterministic booleans for every CorpusScope field."""
    if state.corpus_scope is None:
        return {field: False for field in _CORPUS_SCOPE_FIELDS}

    scope = state.corpus_scope
    return {
        "phenomenon": bool(scope.phenomenon),
        "population": bool(scope.population),
        "sampling_frame": bool(scope.sampling_frame),
        "inclusion_criteria": bool(scope.inclusion_criteria),
        "exclusion_criteria": bool(scope.exclusion_criteria),
        "notes": bool(scope.notes),
    }


def claim_anchor_coverage_scorecard(state: ProjectState) -> dict[str, Any]:
    """Serialize INV-9 claim-ledger source-anchor coverage accounting."""
    buckets_by_kind: dict[str, dict[str, int]] = {}
    buckets_by_stage: dict[str, dict[str, int]] = {}
    buckets_by_status: dict[str, dict[str, int]] = {}
    totals = _empty_claim_anchor_bucket()

    for claim in state.claims:
        supporting_count = len(claim.supporting_anchors)
        contrary_count = len(claim.contrary_anchors)
        anchored = supporting_count + contrary_count > 0
        needs_anchor = claim.support_status.value == "needs_anchor"

        _add_claim_anchor_bucket(
            totals,
            supporting_count=supporting_count,
            contrary_count=contrary_count,
            anchored=anchored,
            needs_anchor=needs_anchor,
        )
        _add_claim_anchor_bucket(
            buckets_by_kind.setdefault(claim.claim_kind.value, _empty_claim_anchor_bucket()),
            supporting_count=supporting_count,
            contrary_count=contrary_count,
            anchored=anchored,
            needs_anchor=needs_anchor,
        )
        _add_claim_anchor_bucket(
            buckets_by_stage.setdefault(claim.source_stage, _empty_claim_anchor_bucket()),
            supporting_count=supporting_count,
            contrary_count=contrary_count,
            anchored=anchored,
            needs_anchor=needs_anchor,
        )
        _add_claim_anchor_bucket(
            buckets_by_status.setdefault(claim.support_status.value, _empty_claim_anchor_bucket()),
            supporting_count=supporting_count,
            contrary_count=contrary_count,
            anchored=anchored,
            needs_anchor=needs_anchor,
        )

    summary = _finalize_claim_anchor_bucket(totals)
    summary["anchored_rate_ci"] = _wilson_interval(
        summary["anchored_claims"],
        summary["total_claims"],
    )
    summary["by_kind"] = _finalize_claim_anchor_buckets(buckets_by_kind)
    summary["by_stage"] = _finalize_claim_anchor_buckets(buckets_by_stage)
    summary["by_support_status"] = _finalize_claim_anchor_buckets(buckets_by_status)
    summary["note"] = (
        "Structural source-anchor accounting for INV-9 claim-ledger entries only; "
        "anchor presence is not claim truth, human adjudication, full "
        "disconfirmation coverage, methodological validity, or SOTA evidence."
    )
    return summary


def _empty_claim_anchor_bucket() -> dict[str, int]:
    """Return a mutable counter bucket for claim-anchor coverage."""
    return {
        "total_claims": 0,
        "anchored_claims": 0,
        "unanchored_claims": 0,
        "claims_with_supporting_anchors": 0,
        "claims_with_contrary_anchors": 0,
        "claims_needing_anchor": 0,
        "supporting_anchor_count": 0,
        "contrary_anchor_count": 0,
        "source_anchor_count": 0,
    }


def _add_claim_anchor_bucket(
    bucket: dict[str, int],
    *,
    supporting_count: int,
    contrary_count: int,
    anchored: bool,
    needs_anchor: bool,
) -> None:
    """Accumulate one claim into a claim-anchor coverage bucket."""
    bucket["total_claims"] += 1
    if anchored:
        bucket["anchored_claims"] += 1
    else:
        bucket["unanchored_claims"] += 1
    if supporting_count:
        bucket["claims_with_supporting_anchors"] += 1
    if contrary_count:
        bucket["claims_with_contrary_anchors"] += 1
    if needs_anchor:
        bucket["claims_needing_anchor"] += 1
    bucket["supporting_anchor_count"] += supporting_count
    bucket["contrary_anchor_count"] += contrary_count
    bucket["source_anchor_count"] += supporting_count + contrary_count


def _finalize_claim_anchor_bucket(bucket: dict[str, int]) -> dict[str, Any]:
    """Add rates to a claim-anchor coverage bucket."""
    total = bucket["total_claims"]
    return {
        **bucket,
        "anchored_rate": (bucket["anchored_claims"] / total) if total else None,
    }


def _finalize_claim_anchor_buckets(
    buckets: Mapping[str, dict[str, int]],
) -> dict[str, dict[str, Any]]:
    """Return deterministically ordered claim-anchor coverage breakdowns."""
    return {
        key: _finalize_claim_anchor_bucket(buckets[key])
        for key in sorted(buckets)
    }


def _binary_matrix_prevalence(matrix: Mapping[str, list[int]]) -> dict[str, Any]:
    """Summarize absent/present rating prevalence for a binary agreement matrix."""
    row_count = len(matrix)
    rating_count, ratings_per_row = _matrix_rating_shape(matrix)
    counts = {"absent": 0, "present": 0}
    row_patterns = {"all_absent": 0, "all_present": 0, "mixed": 0}
    for row in matrix.values():
        if any(value not in {0, 1} for value in row):
            raise ValueError("Binary reliability matrix values must be 0 or 1")
        counts["present"] += sum(row)
        counts["absent"] += len(row) - sum(row)
        if row and all(value == 0 for value in row):
            row_patterns["all_absent"] += 1
        elif row and all(value == 1 for value in row):
            row_patterns["all_present"] += 1
        else:
            row_patterns["mixed"] += 1
    return {
        "row_count": row_count,
        "rating_count": rating_count,
        "ratings_per_row": ratings_per_row,
        "categories": _category_rates(counts, rating_count),
        "row_patterns": row_patterns,
        "note": "Rating prevalence for interpreting κ and AC1 under sparse labels.",
    }


def _categorical_matrix_prevalence(matrix: Mapping[str, list[str]]) -> dict[str, Any]:
    """Summarize rating prevalence for a categorical agreement matrix."""
    row_count = len(matrix)
    rating_count, ratings_per_row = _matrix_rating_shape(matrix)
    counts: Counter[str] = Counter()
    for row in matrix.values():
        counts.update(row)
    return {
        "row_count": row_count,
        "rating_count": rating_count,
        "ratings_per_row": ratings_per_row,
        "categories": _category_rates(dict(sorted(counts.items())), rating_count),
        "note": "Rating prevalence for interpreting κ and AC1 under sparse labels.",
    }


def _matrix_rating_shape(matrix: Mapping[str, list[Any]]) -> tuple[int, int]:
    """Return total rating count and ratings per row, failing on ragged matrices."""
    if not matrix:
        return 0, 0
    lengths = {len(row) for row in matrix.values()}
    if len(lengths) != 1:
        raise ValueError("Reliability matrix rows must have the same number of ratings")
    ratings_per_row = lengths.pop()
    return len(matrix) * ratings_per_row, ratings_per_row


def _category_rates(counts: Mapping[str, int], rating_count: int) -> dict[str, dict[str, Any]]:
    """Attach rates to category counts."""
    return {
        category: {
            "count": count,
            "rate": _safe_div(count, rating_count) if rating_count else None,
        }
        for category, count in counts.items()
    }


def _reliability_bootstrap_config(state: ProjectState) -> ReliabilityBootstrapConfig:
    """Load Phase 0 reliability bootstrap config from project metadata."""
    raw = state.config.extra.get(_RELIABILITY_BOOTSTRAP_EXTRA_KEY)
    if raw is None:
        return ReliabilityBootstrapConfig()
    if not isinstance(raw, dict):
        raise ValueError(
            f"ProjectState.config.extra['{_RELIABILITY_BOOTSTRAP_EXTRA_KEY}'] must be an object"
        )
    try:
        return ReliabilityBootstrapConfig.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid phase0_reliability_bootstrap config: {exc}") from exc


def _binary_reliability_bootstrap_ci(
    matrix: Mapping[str, list[int]],
    bootstrap_config: ReliabilityBootstrapConfig,
) -> dict[str, Any]:
    """Bootstrap D5 metrics over binary reliability matrix rows."""
    return _reliability_bootstrap_ci(
        matrix,
        bootstrap_config,
        metric_functions={
            "percent_agreement": compute_percent_agreement,
            "gwet_ac1": compute_gwet_ac1,
        },
        unit="binary reliability matrix row",
    )


def _categorical_reliability_bootstrap_ci(
    matrix: Mapping[str, list[str]],
    bootstrap_config: ReliabilityBootstrapConfig,
) -> dict[str, Any]:
    """Bootstrap D5 metrics over categorical reliability matrix rows."""
    return _reliability_bootstrap_ci(
        matrix,
        bootstrap_config,
        metric_functions={
            "percent_agreement": compute_categorical_percent_agreement,
            "gwet_ac1": compute_categorical_gwet_ac1,
        },
        unit="categorical reliability matrix row",
    )


def _reliability_bootstrap_ci(
    matrix: Mapping[str, list[Any]],
    bootstrap_config: ReliabilityBootstrapConfig,
    *,
    metric_functions: Mapping[str, Any],
    unit: str,
) -> dict[str, Any]:
    """Return deterministic row-bootstrap intervals for reliability metrics."""
    rows = list(matrix.values())
    base: dict[str, Any] = {
        "method": "row_bootstrap",
        "confidence_level": bootstrap_config.confidence_level,
        "samples": bootstrap_config.samples,
        "seed": bootstrap_config.seed,
        "unit": unit,
        "population_size": len(rows),
        "note": (
            "Deterministic local bootstrap over LLM-pass reliability rows. "
            "This is consistency uncertainty metadata, not human IRR evidence."
        ),
    }
    if not rows:
        return {
            **base,
            "status": "not_available",
            "reason": "No reliability matrix rows available for bootstrap.",
            "metrics": {
                metric: {"lower": None, "upper": None}
                for metric in metric_functions
            },
        }

    rng = Random(bootstrap_config.seed)
    sample_size = len(rows)
    values: dict[str, list[float]] = {metric: [] for metric in metric_functions}
    for _ in range(bootstrap_config.samples):
        sample = {
            str(index): rows[rng.randrange(sample_size)]
            for index in range(sample_size)
        }
        for metric, metric_fn in metric_functions.items():
            values[metric].append(metric_fn(sample))

    alpha = (1 - bootstrap_config.confidence_level) / 2
    intervals = {}
    for metric, metric_values in values.items():
        metric_values.sort()
        intervals[metric] = {
            "lower": _percentile(metric_values, alpha),
            "upper": _percentile(metric_values, 1 - alpha),
        }
    return {**base, "status": "scored", "metrics": intervals}


def d10_cost_latency_scorecard(
    state: ProjectState,
    db_path: Path | str = DEFAULT_OBSERVABILITY_DB_PATH,
    *,
    project: str = "qualitative_coding",
    trace_id: str | None = None,
) -> Dict[str, Any]:
    """Score D10 LLM cost/latency from real llm_client observability rows."""
    db_path = Path(db_path)
    trace_match = _trace_match_for_state(state, trace_id)
    if not db_path.exists():
        return {
            "status": "not_available",
            "reason": f"Observability DB not found: {db_path}",
            "source": str(db_path),
            "project": project,
            "trace_match": trace_match,
            "note": "D10 cost/latency requires real llm_client observability rows; do not estimate from ProjectState.",
        }

    try:
        rows = _fetch_d10_llm_rows(db_path, project=project, trace_match=trace_match)
    except sqlite3.Error as exc:
        return {
            "status": "not_available",
            "reason": f"Could not read llm_calls observability rows: {exc}",
            "source": str(db_path),
            "project": project,
            "trace_match": trace_match,
            "note": "D10 cost/latency requires real llm_client observability rows; do not estimate from ProjectState.",
        }

    if not rows:
        return {
            "status": "not_available",
            "reason": "No llm_calls rows matched the project and trace selector.",
            "source": str(db_path),
            "project": project,
            "trace_match": trace_match,
            "note": "No D10 score is reported without matching real observability rows; do not estimate from ProjectState.",
        }

    call_count = len(rows)
    total_cost = sum(_float_or_zero(row["cost"]) for row in rows)
    marginal_cost = sum(_float_or_zero(row["marginal_cost"]) for row in rows)
    prompt_tokens = sum(_int_or_zero(row["prompt_tokens"]) for row in rows)
    completion_tokens = sum(_int_or_zero(row["completion_tokens"]) for row in rows)
    total_tokens = sum(_int_or_zero(row["total_tokens"]) for row in rows)
    latencies = [_float_or_zero(row["latency_s"]) for row in rows]
    summed_latency = sum(latencies)
    document_count = state.corpus.num_documents
    errored_calls = sum(1 for row in rows if _row_has_error(row))
    tool_calls = _d10_tool_calls_scorecard(
        db_path,
        project=project,
        trace_match=trace_match,
    )
    tool_cost = (
        _float_or_zero(tool_calls.get("total_tool_cost_usd"))
        if tool_calls.get("status") == "scored"
        else 0.0
    )
    tool_duration = (
        _float_or_zero(tool_calls.get("summed_duration_s"))
        if tool_calls.get("status") == "scored"
        else 0.0
    )
    combined_cost = total_cost + tool_cost
    combined_duration = summed_latency + tool_duration

    return {
        "status": "scored",
        "source": str(db_path),
        "project": project,
        "trace_match": trace_match,
        "call_count": call_count,
        "successful_calls": call_count - errored_calls,
        "errored_calls": errored_calls,
        "total_cost_usd": total_cost,
        "total_marginal_cost_usd": marginal_cost,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "summed_latency_s": summed_latency,
        "mean_latency_s": _safe_div(summed_latency, call_count),
        "max_latency_s": max(latencies) if latencies else 0.0,
        "document_count": document_count,
        "cost_per_document_usd": _safe_div_or_none(total_cost, document_count),
        "latency_per_document_s": _safe_div_or_none(summed_latency, document_count),
        "tool_calls": tool_calls,
        "combined_observed_cost_usd": combined_cost,
        "combined_observed_duration_s": combined_duration,
        "combined_observed_cost_per_document_usd": _safe_div_or_none(
            combined_cost,
            document_count,
        ),
        "combined_observed_duration_per_document_s": _safe_div_or_none(
            combined_duration,
            document_count,
        ),
        "first_timestamp": min(str(row["timestamp"]) for row in rows),
        "last_timestamp": max(str(row["timestamp"]) for row in rows),
        "models": dict(sorted(Counter(str(row["model"] or "") for row in rows).items())),
        "tasks": dict(sorted(Counter(str(row["task"] or "") for row in rows).items())),
        "note": (
            "D10 uses summed observed LLM-call latency and real logged cost from "
            "llm_client; it is not full pipeline wall-clock time and is not a "
            "baseline comparison."
        ),
    }


def _d10_tool_calls_scorecard(
    db_path: Path,
    *,
    project: str,
    trace_match: Dict[str, str],
) -> Dict[str, Any]:
    """Summarize matching tool_calls rows without making them mandatory."""
    try:
        rows = _fetch_d10_tool_rows(db_path, project=project, trace_match=trace_match)
    except sqlite3.Error as exc:
        return {
            "status": "not_available",
            "reason": str(exc),
            "note": (
                "Tool-call D10 accounting requires matching tool_calls rows; "
                "LLM-only D10 fields remain scored separately."
            ),
        }
    if not rows:
        return {
            "status": "not_available",
            "reason": "No tool_calls rows matched the project and trace selector.",
            "note": (
                "No tool-call cost/duration is added without matching real "
                "tool_calls observability rows."
            ),
        }

    durations = [_int_or_zero(row["duration_ms"]) / 1000 for row in rows]
    total_duration = sum(durations)
    total_cost = sum(_float_or_zero(row["cost"]) for row in rows)
    errored = sum(1 for row in rows if _tool_row_has_error(row))
    return {
        "status": "scored",
        "call_count": len(rows),
        "successful_calls": len(rows) - errored,
        "errored_calls": errored,
        "total_tool_cost_usd": total_cost,
        "summed_duration_s": total_duration,
        "mean_duration_s": _safe_div(total_duration, len(rows)),
        "max_duration_s": max(durations) if durations else 0.0,
        "first_timestamp": min(str(row["timestamp"]) for row in rows),
        "last_timestamp": max(str(row["timestamp"]) for row in rows),
        "tools": dict(sorted(Counter(str(row["tool_name"] or "") for row in rows).items())),
        "operations": dict(sorted(Counter(str(row["operation"] or "") for row in rows).items())),
        "tasks": dict(sorted(Counter(str(row["task"] or "") for row in rows).items())),
        "note": (
            "Tool-call costs/durations are summed from real tool_calls rows and "
            "included only in combined observed D10 totals."
        ),
    }


def d10_wall_clock_scorecard(state: ProjectState) -> Dict[str, Any]:
    """Score D10 end-to-end wall-clock runtime from project-run metadata."""
    raw = state.config.extra.get(_RUN_TIMING_EXTRA_KEY)
    if raw is None:
        return {
            "status": "not_available",
            "reason": (
                f"No ProjectState.config.extra['{_RUN_TIMING_EXTRA_KEY}'] metadata "
                "found; run the project through `project run` to record wall-clock timing."
            ),
            "note": (
                "D10 wall-clock runtime requires recorded project-run metadata; do not estimate "
                "it from stage timestamps or summed LLM-call latency."
            ),
        }
    if not isinstance(raw, dict):
        raise ValueError(
            f"ProjectState.config.extra['{_RUN_TIMING_EXTRA_KEY}'] must be a metadata object"
        )

    try:
        timing = RunTimingMetadata.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid run_timing metadata: {exc}") from exc

    return {
        "status": "scored",
        "source": f"ProjectState.config.extra['{_RUN_TIMING_EXTRA_KEY}']",
        "started_at": timing.started_at,
        "completed_at": timing.completed_at,
        "duration_s": timing.duration_s,
        "run_status": timing.status,
        "trace_id": timing.trace_id,
        "model": timing.model,
        "exhaustive_coding": timing.exhaustive_coding,
        "resume_from": timing.resume_from,
        "document_count": timing.document_count,
        "phase_result_count": timing.phase_result_count,
        "note": (
            "D10 wall-clock runtime is end-to-end elapsed time for the last local "
            "project run; it is not summed LLM-call latency and is not a baseline "
            "benchmark result."
        ),
    }


def _trace_match_for_state(state: ProjectState, trace_id: str | None) -> Dict[str, str]:
    """Return the D10 trace selector."""
    if trace_id:
        return {"mode": "exact", "value": trace_id}
    return {"mode": "prefix", "value": f"qualitative_coding/project/{state.id}"}


def _fetch_d10_llm_rows(
    db_path: Path,
    *,
    project: str,
    trace_match: Dict[str, str],
) -> list[sqlite3.Row]:
    """Fetch D10 rows from the observability database."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        required = {
            "timestamp",
            "project",
            "model",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "cost",
            "latency_s",
            "error",
            "task",
            "trace_id",
            "marginal_cost",
        }
        columns = {str(row[1]) for row in conn.execute("PRAGMA table_info(llm_calls)").fetchall()}
        missing = sorted(required - columns)
        if missing:
            raise sqlite3.OperationalError(
                "llm_calls table missing required D10 column(s): " + ", ".join(missing)
            )

        error_select = "error"
        if "error_type" in columns:
            error_select += ", error_type"
        if "validation_errors" in columns:
            error_select += ", validation_errors"
        trace_clause = "trace_id = ?" if trace_match["mode"] == "exact" else "trace_id LIKE ?"
        trace_value = trace_match["value"] if trace_match["mode"] == "exact" else f"{trace_match['value']}%"
        query = f"""
            SELECT timestamp, model, prompt_tokens, completion_tokens, total_tokens,
                   cost, latency_s, task, trace_id, marginal_cost, {error_select}
            FROM llm_calls
            WHERE project = ?
              AND {trace_clause}
            ORDER BY timestamp ASC
        """
        return list(conn.execute(query, (project, trace_value)).fetchall())
    finally:
        conn.close()


def _fetch_d10_tool_rows(
    db_path: Path,
    *,
    project: str,
    trace_match: Dict[str, str],
) -> list[sqlite3.Row]:
    """Fetch optional D10 tool rows from the observability database."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        table_exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'tool_calls'"
        ).fetchone()
        if table_exists is None:
            raise sqlite3.OperationalError("tool_calls table not found")
        required = {
            "timestamp",
            "project",
            "tool_name",
            "operation",
            "status",
            "duration_ms",
            "task",
            "trace_id",
            "cost",
        }
        columns = {str(row[1]) for row in conn.execute("PRAGMA table_info(tool_calls)").fetchall()}
        missing = sorted(required - columns)
        if missing:
            raise sqlite3.OperationalError(
                "tool_calls table missing required D10 column(s): " + ", ".join(missing)
            )

        error_select = ""
        if "error_type" in columns:
            error_select += ", error_type"
        if "error_message" in columns:
            error_select += ", error_message"
        trace_clause = "trace_id = ?" if trace_match["mode"] == "exact" else "trace_id LIKE ?"
        trace_value = trace_match["value"] if trace_match["mode"] == "exact" else f"{trace_match['value']}%"
        query = f"""
            SELECT timestamp, tool_name, operation, status, duration_ms, task,
                   trace_id, cost{error_select}
            FROM tool_calls
            WHERE project = ?
              AND {trace_clause}
            ORDER BY timestamp ASC
        """
        return list(conn.execute(query, (project, trace_value)).fetchall())
    finally:
        conn.close()


def _row_has_error(row: sqlite3.Row) -> bool:
    """Return true when an observability row records an error-like field."""
    return any(
        key in row.keys() and row[key]
        for key in ("error", "error_type", "validation_errors")
    )


def _tool_row_has_error(row: sqlite3.Row) -> bool:
    """Return true when a tool observability row records an error status/field."""
    status = str(row["status"] or "").lower()
    if status not in {"success", "succeeded", "ok", "completed"}:
        return True
    return any(
        key in row.keys() and row[key]
        for key in ("error_type", "error_message")
    )


def _int_or_zero(value: Any) -> int:
    """Convert nullable token counts to integers."""
    return int(value or 0)


def _float_or_zero(value: Any) -> float:
    """Convert nullable numeric DB values to floats."""
    return float(value or 0.0)


def _safe_div_or_none(numerator: float, denominator: float) -> float | None:
    """Return None for undefined reporting denominators."""
    if denominator == 0:
        return None
    return numerator / denominator


def codebook_quality_scorecard(state: ProjectState) -> Dict[str, Any]:
    """Score externally supplied D4 codebook-quality rubric outcomes."""
    evaluations = _codebook_quality_evaluations(state)
    if not evaluations:
        return {
            "status": "not_available",
            "reason": (
                "No codebook-quality rubric outcomes found at "
                f"ProjectState.config.extra['{_CODEBOOK_QUALITY_EXTRA_KEY}']; "
                "scoring requires externally supplied LLM-judge or expert rubric outcomes."
            ),
            "note": (
                "Absence of D4 rubric data is not evidence of codebook quality; "
                "blind expert-panel and LLM-judge evaluations are separate from "
                "ordinary Phase 0 scoring."
            ),
        }

    bootstrap_config = _rubric_bootstrap_config(state)
    overall_scores = [_codebook_quality_overall_score(ev) for ev in evaluations]
    scorecard = {
        "status": "scored",
        "source": f"ProjectState.config.extra['{_CODEBOOK_QUALITY_EXTRA_KEY}']",
        "total_evaluations": len(evaluations),
        "evaluator_types": dict(sorted(Counter(ev.evaluator_type for ev in evaluations).items())),
        "metric_summary": _codebook_quality_metric_summary(
            evaluations,
            bootstrap_config,
        ),
        "overall_mean": _mean_or_none(overall_scores),
        "by_evaluator_type": _codebook_quality_by_evaluator_type(
            evaluations,
            bootstrap_config,
        ),
        "note": (
            "Scores externally supplied codebook-quality rubric outcomes. This is "
            "a measurement substrate, not blind expert-panel evidence or proof "
            "of codebook validity."
        ),
    }
    if bootstrap_config.enabled:
        scorecard["overall_mean_ci"] = _rubric_mean_bootstrap_ci(
            overall_scores,
            bootstrap_config,
            unit="codebook-quality rubric outcome",
        )
    return scorecard


def _codebook_quality_evaluations(state: ProjectState) -> list[CodebookQualityEvaluation]:
    """Load D4 codebook-quality rubric outcomes from project config metadata."""
    raw = state.config.extra.get(_CODEBOOK_QUALITY_EXTRA_KEY)
    if raw is None:
        return []
    if isinstance(raw, dict) and _CODEBOOK_QUALITY_EXTRA_KEY in raw:
        raw = raw[_CODEBOOK_QUALITY_EXTRA_KEY]
    if not isinstance(raw, list):
        raise ValueError(
            f"ProjectState.config.extra['{_CODEBOOK_QUALITY_EXTRA_KEY}'] must be a "
            "list of codebook-quality rubric outcomes"
        )
    try:
        return [CodebookQualityEvaluation.model_validate(item) for item in raw]
    except ValidationError as exc:
        raise ValueError(f"Invalid codebook_quality_evaluations metadata: {exc}") from exc


def _rubric_bootstrap_config(state: ProjectState) -> RubricBootstrapConfig:
    """Load Phase 0 rubric bootstrap config from project metadata."""
    raw = state.config.extra.get(_RUBRIC_BOOTSTRAP_EXTRA_KEY)
    if raw is None:
        return RubricBootstrapConfig()
    if not isinstance(raw, dict):
        raise ValueError(
            f"ProjectState.config.extra['{_RUBRIC_BOOTSTRAP_EXTRA_KEY}'] must be an object"
        )
    try:
        return RubricBootstrapConfig.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid phase0_rubric_bootstrap config: {exc}") from exc


def _rubric_mean_bootstrap_ci(
    values: list[float],
    bootstrap_config: RubricBootstrapConfig,
    *,
    unit: str,
) -> dict[str, Any]:
    """Return deterministic local bootstrap intervals for rubric means."""
    base: dict[str, Any] = {
        "method": "rubric_mean_bootstrap",
        "metric": "mean",
        "confidence_level": bootstrap_config.confidence_level,
        "samples": bootstrap_config.samples,
        "seed": bootstrap_config.seed,
        "unit": unit,
        "population_size": len(values),
        "note": (
            "Deterministic local bootstrap over supplied rubric rows. This is "
            "uncertainty metadata, not blind expert-panel evidence."
        ),
    }
    if not values:
        return {
            **base,
            "status": "not_available",
            "lower": None,
            "upper": None,
            "reason": "No rubric score rows available for bootstrap.",
        }

    rng = Random(bootstrap_config.seed)
    sample_size = len(values)
    bootstrapped_means = []
    for _ in range(bootstrap_config.samples):
        sample = [values[rng.randrange(sample_size)] for _ in range(sample_size)]
        bootstrapped_means.append(sum(sample) / sample_size)

    bootstrapped_means.sort()
    alpha = (1 - bootstrap_config.confidence_level) / 2
    return {
        **base,
        "status": "scored",
        "lower": _percentile(bootstrapped_means, alpha),
        "upper": _percentile(bootstrapped_means, 1 - alpha),
    }


def _codebook_quality_metric_summary(
    evaluations: list[CodebookQualityEvaluation],
    bootstrap_config: RubricBootstrapConfig,
) -> dict[str, dict[str, Any]]:
    """Summarize each D4 rubric metric over all evaluations."""
    summaries: dict[str, dict[str, Any]] = {}
    for metric_name in _CODEBOOK_QUALITY_METRICS:
        values = [getattr(evaluation, metric_name) for evaluation in evaluations]
        summary = _numeric_summary(values)
        if bootstrap_config.enabled:
            summary["mean_ci"] = _rubric_mean_bootstrap_ci(
                values,
                bootstrap_config,
                unit=f"codebook-quality {metric_name} score",
            )
        summaries[metric_name] = summary
    return summaries


def _codebook_quality_by_evaluator_type(
    evaluations: list[CodebookQualityEvaluation],
    bootstrap_config: RubricBootstrapConfig,
) -> dict[str, dict[str, Any]]:
    """Summarize D4 rubric outcomes by evaluator type."""
    grouped: dict[str, list[CodebookQualityEvaluation]] = {}
    for evaluation in evaluations:
        grouped.setdefault(evaluation.evaluator_type, []).append(evaluation)
    summaries = {}
    for evaluator_type, group in sorted(grouped.items()):
        overall_scores = [
            _codebook_quality_overall_score(evaluation) for evaluation in group
        ]
        summary = {
            "count": len(group),
            "metric_summary": _codebook_quality_metric_summary(
                group,
                bootstrap_config,
            ),
            "overall_mean": _mean_or_none(overall_scores),
        }
        if bootstrap_config.enabled:
            summary["overall_mean_ci"] = _rubric_mean_bootstrap_ci(
                overall_scores,
                bootstrap_config,
                unit=f"codebook-quality rubric outcome ({evaluator_type})",
            )
        summaries[evaluator_type] = summary
    return summaries


def _codebook_quality_overall_score(evaluation: CodebookQualityEvaluation) -> float:
    """Return the average rubric score for one D4 outcome."""
    return sum(getattr(evaluation, metric) for metric in _CODEBOOK_QUALITY_METRICS) / len(
        _CODEBOOK_QUALITY_METRICS
    )


def _numeric_summary(values: list[float]) -> dict[str, Any]:
    """Return deterministic mean/min/max for numeric scorecard values."""
    if not values:
        return {"mean": None, "min": None, "max": None}
    return {
        "mean": sum(values) / len(values),
        "min": min(values),
        "max": max(values),
    }


def gt_fidelity_scorecard(state: ProjectState) -> Dict[str, Any]:
    """Score externally supplied D8 grounded-theory fidelity rubric outcomes."""
    evaluations = _gt_fidelity_evaluations(state)
    if not evaluations:
        return {
            "status": "not_available",
            "reason": (
                "No GT-fidelity rubric outcomes found at "
                f"ProjectState.config.extra['{_GT_FIDELITY_EXTRA_KEY}']; "
                "scoring requires externally supplied expert or judge rubric outcomes."
            ),
            "note": (
                "Absence of D8 rubric data is not evidence of grounded-theory "
                "fidelity, methodological saturation, or full grounded theory."
            ),
        }

    bootstrap_config = _rubric_bootstrap_config(state)
    overall_scores = [_gt_fidelity_overall_score(ev) for ev in evaluations]
    scorecard = {
        "status": "scored",
        "source": f"ProjectState.config.extra['{_GT_FIDELITY_EXTRA_KEY}']",
        "total_evaluations": len(evaluations),
        "evaluator_types": dict(sorted(Counter(ev.evaluator_type for ev in evaluations).items())),
        "scopes": dict(sorted(Counter(ev.scope for ev in evaluations).items())),
        "metric_summary": _gt_fidelity_metric_summary(
            evaluations,
            bootstrap_config,
        ),
        "overall_mean": _mean_or_none(overall_scores),
        "by_evaluator_type": _gt_fidelity_by_evaluator_type(
            evaluations,
            bootstrap_config,
        ),
        "by_scope": _gt_fidelity_by_scope(evaluations, bootstrap_config),
        "note": (
            "Scores externally supplied GT-fidelity rubric outcomes. This is a "
            "measurement substrate, not expert-rubric acceptance, proof of "
            "methodological saturation, full grounded theory, or a SOTA claim."
        ),
    }
    if bootstrap_config.enabled:
        scorecard["overall_mean_ci"] = _rubric_mean_bootstrap_ci(
            overall_scores,
            bootstrap_config,
            unit="GT-fidelity rubric outcome",
        )
    return scorecard


def _gt_fidelity_evaluations(state: ProjectState) -> list[GTFidelityEvaluation]:
    """Load D8 GT-fidelity rubric outcomes from project config metadata."""
    raw = state.config.extra.get(_GT_FIDELITY_EXTRA_KEY)
    if raw is None:
        return []
    if isinstance(raw, dict) and _GT_FIDELITY_EXTRA_KEY in raw:
        raw = raw[_GT_FIDELITY_EXTRA_KEY]
    if not isinstance(raw, list):
        raise ValueError(
            f"ProjectState.config.extra['{_GT_FIDELITY_EXTRA_KEY}'] must be a "
            "list of GT-fidelity rubric outcomes"
        )
    try:
        return [GTFidelityEvaluation.model_validate(item) for item in raw]
    except ValidationError as exc:
        raise ValueError(f"Invalid gt_fidelity_evaluations metadata: {exc}") from exc


def _gt_fidelity_metric_summary(
    evaluations: list[GTFidelityEvaluation],
    bootstrap_config: RubricBootstrapConfig,
) -> dict[str, dict[str, Any]]:
    """Summarize each D8 rubric metric over all evaluations."""
    summaries: dict[str, dict[str, Any]] = {}
    for metric_name in _GT_FIDELITY_METRICS:
        values = [getattr(evaluation, metric_name) for evaluation in evaluations]
        summary = _numeric_summary(values)
        if bootstrap_config.enabled:
            summary["mean_ci"] = _rubric_mean_bootstrap_ci(
                values,
                bootstrap_config,
                unit=f"GT-fidelity {metric_name} score",
            )
        summaries[metric_name] = summary
    return summaries


def _gt_fidelity_by_evaluator_type(
    evaluations: list[GTFidelityEvaluation],
    bootstrap_config: RubricBootstrapConfig,
) -> dict[str, dict[str, Any]]:
    """Summarize D8 rubric outcomes by evaluator type."""
    grouped: dict[str, list[GTFidelityEvaluation]] = {}
    for evaluation in evaluations:
        grouped.setdefault(evaluation.evaluator_type, []).append(evaluation)
    summaries = {}
    for evaluator_type, group in sorted(grouped.items()):
        overall_scores = [_gt_fidelity_overall_score(evaluation) for evaluation in group]
        summary = {
            "count": len(group),
            "metric_summary": _gt_fidelity_metric_summary(group, bootstrap_config),
            "overall_mean": _mean_or_none(overall_scores),
        }
        if bootstrap_config.enabled:
            summary["overall_mean_ci"] = _rubric_mean_bootstrap_ci(
                overall_scores,
                bootstrap_config,
                unit=f"GT-fidelity rubric outcome ({evaluator_type})",
            )
        summaries[evaluator_type] = summary
    return summaries


def _gt_fidelity_by_scope(
    evaluations: list[GTFidelityEvaluation],
    bootstrap_config: RubricBootstrapConfig,
) -> dict[str, dict[str, Any]]:
    """Summarize D8 rubric outcomes by reviewed artifact scope."""
    grouped: dict[str, list[GTFidelityEvaluation]] = {}
    for evaluation in evaluations:
        grouped.setdefault(evaluation.scope, []).append(evaluation)
    summaries = {}
    for scope, group in sorted(grouped.items()):
        overall_scores = [_gt_fidelity_overall_score(evaluation) for evaluation in group]
        summary = {
            "count": len(group),
            "metric_summary": _gt_fidelity_metric_summary(group, bootstrap_config),
            "overall_mean": _mean_or_none(overall_scores),
        }
        if bootstrap_config.enabled:
            summary["overall_mean_ci"] = _rubric_mean_bootstrap_ci(
                overall_scores,
                bootstrap_config,
                unit=f"GT-fidelity rubric outcome ({scope})",
            )
        summaries[scope] = summary
    return summaries


def _gt_fidelity_overall_score(evaluation: GTFidelityEvaluation) -> float:
    """Return the average rubric score for one D8 outcome."""
    return sum(getattr(evaluation, metric) for metric in _GT_FIDELITY_METRICS) / len(
        _GT_FIDELITY_METRICS
    )


def interpretive_preference_scorecard(state: ProjectState) -> Dict[str, Any]:
    """Score externally supplied D9 forced-choice preference outcomes."""
    evaluations = _interpretive_preference_evaluations(state)
    if not evaluations:
        return {
            "status": "not_available",
            "reason": (
                "No interpretive-preference outcomes found at "
                f"ProjectState.config.extra['{_INTERPRETIVE_PREFERENCE_EXTRA_KEY}']; "
                "scoring requires externally supplied blind forced-choice outcomes."
            ),
            "note": (
                "Absence of D9 preference data is not evidence of interpretive-depth "
                "parity; blind expert preference evaluation is separate from ordinary "
                "Phase 0 scoring."
            ),
        }

    summary = _interpretive_preference_summary(evaluations)
    protocol = _interpretive_preference_protocol(state)
    return {
        "status": "scored",
        "source": f"ProjectState.config.extra['{_INTERPRETIVE_PREFERENCE_EXTRA_KEY}']",
        **summary,
        "non_inferiority_assessment": _interpretive_preference_non_inferiority_assessment(
            summary,
            protocol,
        ),
        "by_evaluator": _interpretive_preference_grouped_summary(
            evaluations,
            key_fn=lambda evaluation: evaluation.evaluator,
        ),
        "by_criterion": _interpretive_preference_grouped_summary(
            evaluations,
            key_fn=lambda evaluation: evaluation.criterion,
        ),
        "note": (
            "Scores externally supplied forced-choice preference outcomes. This is "
            "a measurement substrate, not blind expert-parity evidence, a "
            "pre-registered non-inferiority result, or a SOTA claim."
        ),
    }


def _interpretive_preference_evaluations(
    state: ProjectState,
) -> list[InterpretivePreferenceEvaluation]:
    """Load D9 forced-choice preference outcomes from project config metadata."""
    raw = state.config.extra.get(_INTERPRETIVE_PREFERENCE_EXTRA_KEY)
    if raw is None:
        return []
    if isinstance(raw, dict) and _INTERPRETIVE_PREFERENCE_EXTRA_KEY in raw:
        raw = raw[_INTERPRETIVE_PREFERENCE_EXTRA_KEY]
    if not isinstance(raw, list):
        raise ValueError(
            f"ProjectState.config.extra['{_INTERPRETIVE_PREFERENCE_EXTRA_KEY}'] "
            "must be a list of interpretive-preference outcomes"
        )
    try:
        return [InterpretivePreferenceEvaluation.model_validate(item) for item in raw]
    except ValidationError as exc:
        raise ValueError(f"Invalid interpretive_preference_evaluations metadata: {exc}") from exc


def _interpretive_preference_protocol(
    state: ProjectState,
) -> InterpretivePreferenceProtocol | None:
    """Load optional D9 non-inferiority protocol metadata."""
    raw = state.config.extra.get(_INTERPRETIVE_PREFERENCE_EXTRA_KEY)
    if not isinstance(raw, dict):
        return None

    payload = None
    for key in ("interpretive_preference_protocol", "protocol"):
        if isinstance(raw.get(key), dict):
            payload = raw[key]
            break
    if payload is None and (
        "non_inferiority_margin" in raw or "registered_before_evaluation" in raw
    ):
        payload = raw
    if payload is None:
        return None

    try:
        return InterpretivePreferenceProtocol.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid interpretive preference protocol metadata: {exc}") from exc


def _interpretive_preference_summary(
    evaluations: list[InterpretivePreferenceEvaluation],
) -> dict[str, Any]:
    """Return D9 preference counts, rates, and confidence interval."""
    total = len(evaluations)
    counts = Counter(evaluation.preferred for evaluation in evaluations)
    system_wins = counts["system"]
    human_wins = counts["human"]
    ties = counts["tie"]
    non_tie_cases = system_wins + human_wins
    return {
        "total_cases": total,
        "system_wins": system_wins,
        "human_wins": human_wins,
        "ties": ties,
        "non_tie_cases": non_tie_cases,
        "tie_rate": _safe_div(ties, total),
        "tie_rate_ci": _wilson_interval(ties, total),
        "system_preference_rate": _safe_div_or_none(system_wins, non_tie_cases),
        "system_preference_ci": _wilson_interval(system_wins, non_tie_cases),
    }


def _interpretive_preference_non_inferiority_assessment(
    summary: Mapping[str, Any],
    protocol: InterpretivePreferenceProtocol | None,
) -> dict[str, Any]:
    """Assess D9 non-inferiority only when pre-registered protocol metadata exists."""
    base = {
        "metric": "system_minus_human_preference_rate",
        "note": (
            "D9 non-inferiority requires pre-registered margin metadata and "
            "populated blind expert preference outcomes. This local assessment "
            "does not by itself establish expert parity."
        ),
    }
    if protocol is None:
        return {
            **base,
            "status": "not_available",
            "reason": "No D9 non-inferiority protocol metadata was supplied.",
        }

    protocol_payload = {
        "protocol_id": protocol.protocol_id,
        "non_inferiority_margin": protocol.non_inferiority_margin,
        "registered_before_evaluation": protocol.registered_before_evaluation,
        "notes": protocol.notes,
    }
    rate = summary.get("system_preference_rate")
    interval = summary.get("system_preference_ci")
    if rate is None or not isinstance(interval, Mapping) or interval.get("lower") is None:
        return {
            **base,
            "status": "not_available",
            "reason": "No non-tie D9 preference cases are available.",
            "protocol": protocol_payload,
        }

    difference = (2 * float(rate)) - 1
    lower = (2 * float(interval["lower"])) - 1
    upper = (2 * float(interval["upper"])) - 1
    assessed = {
        **base,
        "protocol": protocol_payload,
        "system_minus_human": difference,
        "system_minus_human_ci": {
            "method": interval["method"],
            "confidence_level": interval["confidence_level"],
            "lower": lower,
            "upper": upper,
        },
        "required_lower_bound": -protocol.non_inferiority_margin,
    }
    if not protocol.registered_before_evaluation:
        return {
            **assessed,
            "status": "not_registered",
            "meets_non_inferiority": False,
            "reason": "Protocol metadata was not registered before evaluation.",
        }
    return {
        **assessed,
        "status": "scored",
        "meets_non_inferiority": lower > -protocol.non_inferiority_margin,
    }


def _interpretive_preference_grouped_summary(
    evaluations: list[InterpretivePreferenceEvaluation],
    *,
    key_fn: Any,
) -> dict[str, dict[str, Any]]:
    """Summarize D9 preference outcomes by a stable grouping key."""
    grouped: dict[str, list[InterpretivePreferenceEvaluation]] = {}
    for evaluation in evaluations:
        grouped.setdefault(key_fn(evaluation), []).append(evaluation)
    return {
        group_key: _interpretive_preference_summary(group)
        for group_key, group in sorted(grouped.items())
    }


def confidence_calibration_scorecard(state: ProjectState) -> Dict[str, Any]:
    """Score externally supplied confidence/correctness calibration records."""
    evaluations = _confidence_calibration_evaluations(state)
    if not evaluations:
        return {
            "status": "not_available",
            "reason": (
                "No confidence-calibration records found at "
                f"ProjectState.config.extra['{_CONFIDENCE_CALIBRATION_EXTRA_KEY}']; "
                "scoring requires externally supplied correctness labels."
            ),
            "note": (
                "Absence of calibration records is not evidence that confidence "
                "values are calibrated; confidence remains an ordinal self-report "
                "until scored against held-out correctness labels."
            ),
        }

    bootstrap_config = _calibration_bootstrap_config(state)
    return {
        "status": "scored",
        "source": f"ProjectState.config.extra['{_CONFIDENCE_CALIBRATION_EXTRA_KEY}']",
        **_confidence_calibration_summary(
            evaluations,
            bootstrap_config,
            unit="confidence/correctness record",
        ),
        "by_surface": _confidence_calibration_by_surface(
            evaluations,
            bootstrap_config,
        ),
        "note": (
            "Scores externally supplied confidence/correctness records. This is "
            "a measurement substrate, not evidence that system confidence is "
            "calibrated outside the supplied labeled records."
        ),
    }


def _confidence_calibration_evaluations(
    state: ProjectState,
) -> list[ConfidenceCalibrationEvaluation]:
    """Load confidence-calibration records from project config metadata."""
    raw = state.config.extra.get(_CONFIDENCE_CALIBRATION_EXTRA_KEY)
    if raw is None:
        return []
    if isinstance(raw, dict) and _CONFIDENCE_CALIBRATION_EXTRA_KEY in raw:
        raw = raw[_CONFIDENCE_CALIBRATION_EXTRA_KEY]
    if not isinstance(raw, list):
        raise ValueError(
            f"ProjectState.config.extra['{_CONFIDENCE_CALIBRATION_EXTRA_KEY}'] "
            "must be a list of confidence-calibration records"
        )
    try:
        return [ConfidenceCalibrationEvaluation.model_validate(item) for item in raw]
    except ValidationError as exc:
        raise ValueError(f"Invalid confidence_calibration_evaluations metadata: {exc}") from exc


def _calibration_bootstrap_config(state: ProjectState) -> CalibrationBootstrapConfig:
    """Load Phase 0 confidence-calibration bootstrap config from project metadata."""
    raw = state.config.extra.get(_CALIBRATION_BOOTSTRAP_EXTRA_KEY)
    if raw is None:
        return CalibrationBootstrapConfig()
    if not isinstance(raw, dict):
        raise ValueError(
            f"ProjectState.config.extra['{_CALIBRATION_BOOTSTRAP_EXTRA_KEY}'] "
            "must be an object"
        )
    try:
        return CalibrationBootstrapConfig.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid phase0_calibration_bootstrap config: {exc}") from exc


def _confidence_calibration_summary(
    evaluations: list[ConfidenceCalibrationEvaluation],
    bootstrap_config: CalibrationBootstrapConfig,
    *,
    unit: str,
) -> dict[str, Any]:
    """Return deterministic calibration metrics for confidence/correctness records."""
    total = len(evaluations)
    correct_count = sum(1 for evaluation in evaluations if evaluation.correct)
    brier_score = _confidence_calibration_brier_score(evaluations)
    bins = _calibration_bins(evaluations)
    expected_calibration_error = _expected_calibration_error_from_bins(bins)
    summary = {
        "total_records": total,
        "correct_records": correct_count,
        "incorrect_records": total - correct_count,
        "accuracy": _safe_div(correct_count, total),
        "accuracy_ci": _wilson_interval(correct_count, total),
        "mean_confidence": _mean_or_none([
            evaluation.confidence for evaluation in evaluations
        ]),
        "brier_score": brier_score,
        "expected_calibration_error": expected_calibration_error,
        "bin_count": _CALIBRATION_BIN_COUNT,
        "calibration_bins": bins,
    }
    if bootstrap_config.enabled:
        intervals = _confidence_calibration_bootstrap_intervals(
            evaluations,
            bootstrap_config,
            unit=unit,
        )
        summary["brier_score_ci"] = intervals["brier_score"]
        summary["expected_calibration_error_ci"] = intervals[
            "expected_calibration_error"
        ]
    return summary


def _confidence_calibration_brier_score(
    evaluations: list[ConfidenceCalibrationEvaluation],
) -> float | None:
    """Return mean squared confidence error for supplied calibration records."""
    return _mean_or_none([
        (evaluation.confidence - float(evaluation.correct)) ** 2
        for evaluation in evaluations
    ])


def _confidence_calibration_expected_calibration_error(
    evaluations: list[ConfidenceCalibrationEvaluation],
) -> float:
    """Return fixed-bin expected calibration error for calibration records."""
    return _expected_calibration_error_from_bins(_calibration_bins(evaluations))


def _expected_calibration_error_from_bins(bins: list[dict[str, Any]]) -> float:
    """Return fixed-bin ECE from precomputed calibration-bin summaries."""
    return sum(bin_data["weighted_gap"] for bin_data in bins)


def _confidence_calibration_bootstrap_intervals(
    evaluations: list[ConfidenceCalibrationEvaluation],
    bootstrap_config: CalibrationBootstrapConfig,
    *,
    unit: str,
) -> dict[str, dict[str, Any]]:
    """Return deterministic bootstrap intervals for calibration metrics."""
    base: dict[str, Any] = {
        "method": "calibration_record_bootstrap",
        "confidence_level": bootstrap_config.confidence_level,
        "samples": bootstrap_config.samples,
        "seed": bootstrap_config.seed,
        "unit": unit,
        "population_size": len(evaluations),
        "note": (
            "Deterministic local bootstrap over supplied confidence/correctness "
            "records. This is uncertainty metadata, not calibration proof."
        ),
    }
    if not evaluations:
        return {
            metric: {
                **base,
                "metric": metric,
                "status": "not_available",
                "lower": None,
                "upper": None,
                "reason": "No calibration records available for bootstrap.",
            }
            for metric in ("brier_score", "expected_calibration_error")
        }

    rng = Random(bootstrap_config.seed)
    sample_size = len(evaluations)
    values: dict[str, list[float]] = {
        "brier_score": [],
        "expected_calibration_error": [],
    }
    for _ in range(bootstrap_config.samples):
        sample = [evaluations[rng.randrange(sample_size)] for _ in range(sample_size)]
        brier_score = _confidence_calibration_brier_score(sample)
        if brier_score is None:
            raise ValueError("Calibration bootstrap sample unexpectedly empty")
        values["brier_score"].append(brier_score)
        values["expected_calibration_error"].append(
            _confidence_calibration_expected_calibration_error(sample)
        )

    alpha = (1 - bootstrap_config.confidence_level) / 2
    intervals = {}
    for metric, metric_values in values.items():
        metric_values.sort()
        intervals[metric] = {
            **base,
            "metric": metric,
            "status": "scored",
            "lower": _percentile(metric_values, alpha),
            "upper": _percentile(metric_values, 1 - alpha),
        }
    return intervals


def _calibration_bins(
    evaluations: list[ConfidenceCalibrationEvaluation],
) -> list[dict[str, Any]]:
    """Return fixed-width calibration bins and weighted absolute calibration gaps."""
    total = len(evaluations)
    grouped: list[list[ConfidenceCalibrationEvaluation]] = [
        [] for _ in range(_CALIBRATION_BIN_COUNT)
    ]
    for evaluation in evaluations:
        bin_index = min(
            int(evaluation.confidence * _CALIBRATION_BIN_COUNT),
            _CALIBRATION_BIN_COUNT - 1,
        )
        grouped[bin_index].append(evaluation)

    bins: list[dict[str, Any]] = []
    for index, group in enumerate(grouped):
        lower = index / _CALIBRATION_BIN_COUNT
        upper = (index + 1) / _CALIBRATION_BIN_COUNT
        accuracy = None
        mean_confidence = None
        gap = None
        weighted_gap = 0.0
        correct_count = 0
        if group:
            correct_count = sum(1 for evaluation in group if evaluation.correct)
            accuracy = _safe_div(correct_count, len(group))
            mean_confidence = _mean_or_none([
                evaluation.confidence for evaluation in group
            ])
            gap = abs(accuracy - mean_confidence)
            weighted_gap = (len(group) / total) * gap
        bins.append({
            "index": index,
            "lower": lower,
            "upper": upper,
            "upper_inclusive": index == _CALIBRATION_BIN_COUNT - 1,
            "count": len(group),
            "accuracy": accuracy,
            "accuracy_ci": _wilson_interval(correct_count, len(group)),
            "mean_confidence": mean_confidence,
            "calibration_gap": gap,
            "weighted_gap": weighted_gap,
        })
    return bins


def _confidence_calibration_by_surface(
    evaluations: list[ConfidenceCalibrationEvaluation],
    bootstrap_config: CalibrationBootstrapConfig,
) -> dict[str, dict[str, Any]]:
    """Summarize confidence calibration records by prediction surface."""
    grouped: dict[str, list[ConfidenceCalibrationEvaluation]] = {}
    for evaluation in evaluations:
        grouped.setdefault(evaluation.surface, []).append(evaluation)
    return {
        surface: _confidence_calibration_summary(
            group,
            bootstrap_config,
            unit=f"confidence/correctness record ({surface})",
        )
        for surface, group in sorted(grouped.items())
    }


def prompt_injection_scorecard(state: ProjectState) -> Dict[str, Any]:
    """Score externally supplied INV-7 prompt-injection fixture outcomes."""
    evaluations = _prompt_injection_evaluations(state)
    if not evaluations:
        return {
            "status": "not_available",
            "reason": (
                "No prompt-injection fixture results found at "
                f"ProjectState.config.extra['{_PROMPT_INJECTION_EXTRA_KEY}']; scoring "
                "requires externally supplied adversarial evaluation outcomes."
            ),
            "note": (
                "Absence of INV-7 fixture data is not evidence of prompt-injection "
                "robustness; deterministic prompt-boundary tests are separate from "
                "live adversarial evaluation."
            ),
        }

    total = len(evaluations)
    failed = sorted(ev.fixture_id for ev in evaluations if ev.attack_succeeded)
    passed = total - len(failed)
    return {
        "status": "scored",
        "source": f"ProjectState.config.extra['{_PROMPT_INJECTION_EXTRA_KEY}']",
        "total_fixtures": total,
        "passed": passed,
        "failed": len(failed),
        "pass_rate": _safe_div(passed, total),
        "attack_success_rate": _safe_div(len(failed), total),
        "pass_rate_ci": _wilson_interval(passed, total),
        "attack_success_rate_ci": _wilson_interval(len(failed), total),
        "failed_fixture_ids": failed,
        "by_surface": _prompt_injection_by_surface(evaluations),
        "by_attack_type": _prompt_injection_by_attack_type(evaluations),
        "note": (
            "Scores externally supplied prompt-injection fixture outcomes. This is "
            "a measurement substrate, not a proof of prompt-injection robustness."
        ),
    }


def _prompt_injection_evaluations(state: ProjectState) -> list[PromptInjectionEvaluation]:
    """Load INV-7 fixture outcomes from project config metadata."""
    raw = state.config.extra.get(_PROMPT_INJECTION_EXTRA_KEY)
    if raw is None:
        return []
    if isinstance(raw, dict) and _PROMPT_INJECTION_EXTRA_KEY in raw:
        raw = raw[_PROMPT_INJECTION_EXTRA_KEY]
    if not isinstance(raw, list):
        raise ValueError(
            f"ProjectState.config.extra['{_PROMPT_INJECTION_EXTRA_KEY}'] must be a list "
            "of prompt-injection fixture outcomes"
        )
    try:
        return [PromptInjectionEvaluation.model_validate(item) for item in raw]
    except ValidationError as exc:
        raise ValueError(f"Invalid prompt_injection_evaluations metadata: {exc}") from exc


def _prompt_injection_by_surface(
    evaluations: list[PromptInjectionEvaluation],
) -> Dict[str, Dict[str, Any]]:
    """Summarize INV-7 fixture outcomes by prompt surface."""
    return _prompt_injection_grouped_summary(evaluations, group_field="surface")


def _prompt_injection_by_attack_type(
    evaluations: list[PromptInjectionEvaluation],
) -> Dict[str, Dict[str, Any]]:
    """Summarize INV-7 fixture outcomes by attack class."""
    return _prompt_injection_grouped_summary(evaluations, group_field="attack_type")


def _prompt_injection_grouped_summary(
    evaluations: list[PromptInjectionEvaluation],
    *,
    group_field: str,
) -> Dict[str, Dict[str, Any]]:
    """Summarize INV-7 fixture outcomes by a string field."""
    summary: Dict[str, Dict[str, Any]] = {}
    for ev in evaluations:
        key = getattr(ev, group_field)
        bucket = summary.setdefault(
            key,
            {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "attack_success_rate": 0.0,
                "failed_fixture_ids": [],
            },
        )
        bucket["total"] += 1
        if ev.attack_succeeded:
            bucket["failed"] += 1
            bucket["failed_fixture_ids"].append(ev.fixture_id)
        else:
            bucket["passed"] += 1
    for bucket in summary.values():
        bucket["failed_fixture_ids"] = sorted(bucket["failed_fixture_ids"])
        bucket["attack_success_rate"] = _safe_div(bucket["failed"], bucket["total"])
        bucket["pass_rate"] = _safe_div(bucket["passed"], bucket["total"])
        bucket["attack_success_rate_ci"] = _wilson_interval(
            bucket["failed"],
            bucket["total"],
        )
        bucket["pass_rate_ci"] = _wilson_interval(
            bucket["passed"],
            bucket["total"],
        )
    return dict(sorted(summary.items()))


def bias_counterfactual_scorecard(state: ProjectState) -> Dict[str, Any]:
    """Score externally supplied D6 counterfactual identity-swap outcomes."""
    evaluations = _bias_counterfactual_evaluations(state)
    if not evaluations:
        return {
            "status": "not_available",
            "reason": (
                "No bias counterfactual outcomes found at "
                f"ProjectState.config.extra['{_BIAS_COUNTERFACTUAL_EXTRA_KEY}']; "
                "scoring requires externally supplied identity-cue swap outcomes."
            ),
            "note": (
                "Absence of D6 counterfactual data is not evidence that coding is "
                "unbiased; stratified and counterfactual bias audits are separate "
                "from ordinary Phase 0 scoring."
            ),
        }

    invariant = [ev for ev in evaluations if ev.expected_invariant]
    case_metrics = [_bias_counterfactual_case_metrics(ev) for ev in invariant]
    changed = [metric for metric in case_metrics if metric["changed"]]
    jaccard_distances = [metric["jaccard_distance"] for metric in case_metrics]
    bootstrap_config = _counterfactual_bootstrap_config(state)
    scorecard = {
        "status": "scored",
        "source": f"ProjectState.config.extra['{_BIAS_COUNTERFACTUAL_EXTRA_KEY}']",
        "total_cases": len(evaluations),
        "invariant_cases": len(invariant),
        "excluded_non_invariant_cases": len(evaluations) - len(invariant),
        "changed_invariant_cases": len(changed),
        "unchanged_invariant_cases": len(invariant) - len(changed),
        "code_change_rate": _safe_div_or_none(len(changed), len(invariant)),
        "code_change_rate_ci": _wilson_interval(len(changed), len(invariant)),
        "mean_jaccard_distance": _mean_or_none(jaccard_distances),
        "changed_case_ids": sorted(metric["case_id"] for metric in changed),
        "by_attribute": _bias_counterfactual_by_attribute(
            invariant,
            bootstrap_config,
        ),
        "note": (
            "Scores externally supplied counterfactual identity-cue outcomes. "
            "This is a measurement substrate, not causal proof of bias or "
            "evidence that the system is bias-free."
        ),
    }
    if bootstrap_config.enabled:
        scorecard["mean_jaccard_distance_ci"] = _counterfactual_jaccard_bootstrap_ci(
            jaccard_distances,
            bootstrap_config,
            unit="invariant counterfactual case",
        )
    return scorecard


def _bias_counterfactual_evaluations(state: ProjectState) -> list[BiasCounterfactualEvaluation]:
    """Load D6 counterfactual outcomes from project config metadata."""
    raw = state.config.extra.get(_BIAS_COUNTERFACTUAL_EXTRA_KEY)
    if raw is None:
        return []
    if isinstance(raw, dict) and _BIAS_COUNTERFACTUAL_EXTRA_KEY in raw:
        raw = raw[_BIAS_COUNTERFACTUAL_EXTRA_KEY]
    if not isinstance(raw, list):
        raise ValueError(
            f"ProjectState.config.extra['{_BIAS_COUNTERFACTUAL_EXTRA_KEY}'] must be a "
            "list of counterfactual identity-swap outcomes"
        )
    try:
        return [BiasCounterfactualEvaluation.model_validate(item) for item in raw]
    except ValidationError as exc:
        raise ValueError(f"Invalid bias_counterfactual_evaluations metadata: {exc}") from exc


def _counterfactual_bootstrap_config(state: ProjectState) -> CounterfactualBootstrapConfig:
    """Load Phase 0 D6 counterfactual bootstrap config from project metadata."""
    raw = state.config.extra.get(_COUNTERFACTUAL_BOOTSTRAP_EXTRA_KEY)
    if raw is None:
        return CounterfactualBootstrapConfig()
    if not isinstance(raw, dict):
        raise ValueError(
            f"ProjectState.config.extra['{_COUNTERFACTUAL_BOOTSTRAP_EXTRA_KEY}'] "
            "must be an object"
        )
    try:
        return CounterfactualBootstrapConfig.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid phase0_counterfactual_bootstrap config: {exc}") from exc


def _clean_counterfactual_codes(codes: list[str], field_name: str) -> list[str]:
    """Normalize code labels while preserving first-seen order."""
    cleaned: list[str] = []
    for code in codes:
        normalized = code.strip()
        if not normalized:
            raise ValueError(f"bias counterfactual {field_name} contains a blank code")
        if normalized not in cleaned:
            cleaned.append(normalized)
    return cleaned


def _bias_counterfactual_case_metrics(
    evaluation: BiasCounterfactualEvaluation,
) -> dict[str, Any]:
    """Compute code-set distance for one invariant counterfactual case."""
    original = set(evaluation.original_codes)
    counterfactual = set(evaluation.counterfactual_codes)
    union = original | counterfactual
    jaccard_distance = 0.0
    if union:
        jaccard_distance = 1 - (len(original & counterfactual) / len(union))
    return {
        "case_id": evaluation.case_id,
        "attribute": evaluation.attribute,
        "changed": original != counterfactual,
        "jaccard_distance": jaccard_distance,
        "added_codes": sorted(counterfactual - original),
        "removed_codes": sorted(original - counterfactual),
    }


def _bias_counterfactual_by_attribute(
    evaluations: list[BiasCounterfactualEvaluation],
    bootstrap_config: CounterfactualBootstrapConfig,
) -> dict[str, dict[str, Any]]:
    """Summarize D6 invariant-case changes by varied attribute."""
    summary: dict[str, dict[str, Any]] = {}
    distances: dict[str, list[float]] = {}
    for evaluation in evaluations:
        metrics = _bias_counterfactual_case_metrics(evaluation)
        bucket = summary.setdefault(
            evaluation.attribute,
            {
                "invariant_cases": 0,
                "changed_invariant_cases": 0,
                "unchanged_invariant_cases": 0,
                "code_change_rate": None,
                "code_change_rate_ci": None,
                "mean_jaccard_distance": None,
                "changed_case_ids": [],
            },
        )
        distances.setdefault(evaluation.attribute, [])
        bucket["invariant_cases"] += 1
        distances[evaluation.attribute].append(metrics["jaccard_distance"])
        if metrics["changed"]:
            bucket["changed_invariant_cases"] += 1
            bucket["changed_case_ids"].append(metrics["case_id"])
        else:
            bucket["unchanged_invariant_cases"] += 1

    for attribute, bucket in summary.items():
        bucket["changed_case_ids"] = sorted(bucket["changed_case_ids"])
        bucket["code_change_rate"] = _safe_div_or_none(
            bucket["changed_invariant_cases"],
            bucket["invariant_cases"],
        )
        bucket["code_change_rate_ci"] = _wilson_interval(
            bucket["changed_invariant_cases"],
            bucket["invariant_cases"],
        )
        bucket["mean_jaccard_distance"] = _mean_or_none(distances[attribute])
        if bootstrap_config.enabled:
            bucket["mean_jaccard_distance_ci"] = _counterfactual_jaccard_bootstrap_ci(
                distances[attribute],
                bootstrap_config,
                unit=f"invariant counterfactual case for attribute {attribute}",
            )
    return dict(sorted(summary.items()))


def _counterfactual_jaccard_bootstrap_ci(
    values: list[float],
    bootstrap_config: CounterfactualBootstrapConfig,
    *,
    unit: str,
) -> dict[str, Any]:
    """Return deterministic local bootstrap intervals for D6 Jaccard means."""
    base: dict[str, Any] = {
        "method": "counterfactual_jaccard_mean_bootstrap",
        "metric": "mean_jaccard_distance",
        "confidence_level": bootstrap_config.confidence_level,
        "samples": bootstrap_config.samples,
        "seed": bootstrap_config.seed,
        "unit": unit,
        "population_size": len(values),
        "note": (
            "Deterministic local bootstrap over supplied invariant counterfactual "
            "rows. This is uncertainty metadata, not causal proof of bias or "
            "evidence that the system is bias-free."
        ),
    }
    if not values:
        return {
            **base,
            "status": "not_available",
            "lower": None,
            "upper": None,
            "reason": "No invariant counterfactual rows available for bootstrap.",
        }

    rng = Random(bootstrap_config.seed)
    sample_size = len(values)
    bootstrapped_means = []
    for _ in range(bootstrap_config.samples):
        sample = [values[rng.randrange(sample_size)] for _ in range(sample_size)]
        bootstrapped_means.append(sum(sample) / sample_size)

    bootstrapped_means.sort()
    alpha = (1 - bootstrap_config.confidence_level) / 2
    return {
        **base,
        "status": "scored",
        "lower": _percentile(bootstrapped_means, alpha),
        "upper": _percentile(bootstrapped_means, 1 - alpha),
    }


def bias_stratified_scorecard(state: ProjectState) -> Dict[str, Any]:
    """Score externally supplied D6 stratified correctness/error rows."""
    evaluations = _bias_stratified_evaluations(state)
    if not evaluations:
        return {
            "status": "not_available",
            "reason": (
                "No bias stratified outcomes found at "
                f"ProjectState.config.extra['{_BIAS_STRATIFIED_EXTRA_KEY}']; "
                "scoring requires externally supplied correctness rows grouped "
                "by respondent attribute."
            ),
            "note": (
                "Absence of D6 stratified data is not evidence that coding is "
                "unbiased; stratified and counterfactual bias audits are separate "
                "from ordinary Phase 0 scoring."
            ),
        }

    summary = _bias_stratified_summary(evaluations)
    return {
        "status": "scored",
        "source": f"ProjectState.config.extra['{_BIAS_STRATIFIED_EXTRA_KEY}']",
        **summary,
        "by_attribute": _bias_stratified_by_attribute(evaluations),
        "by_surface": _bias_stratified_by_surface(evaluations),
        "note": (
            "Scores externally supplied stratified correctness rows. This is a "
            "measurement substrate for error-rate parity, not causal proof of "
            "bias or evidence that the system is bias-free."
        ),
    }


def _bias_stratified_evaluations(state: ProjectState) -> list[BiasStratifiedEvaluation]:
    """Load D6 stratified rows from project config metadata."""
    raw = state.config.extra.get(_BIAS_STRATIFIED_EXTRA_KEY)
    if raw is None:
        return []
    if isinstance(raw, dict) and _BIAS_STRATIFIED_EXTRA_KEY in raw:
        raw = raw[_BIAS_STRATIFIED_EXTRA_KEY]
    if not isinstance(raw, list):
        raise ValueError(
            f"ProjectState.config.extra['{_BIAS_STRATIFIED_EXTRA_KEY}'] must be a "
            "list of stratified correctness rows"
        )
    try:
        return [BiasStratifiedEvaluation.model_validate(item) for item in raw]
    except ValidationError as exc:
        raise ValueError(f"Invalid bias_stratified_evaluations metadata: {exc}") from exc


def _bias_stratified_summary(
    evaluations: list[BiasStratifiedEvaluation],
) -> dict[str, Any]:
    """Summarize stratified correctness rows."""
    total = len(evaluations)
    correct = sum(1 for evaluation in evaluations if evaluation.correct)
    incorrect = total - correct
    return {
        "total_cases": total,
        "correct_cases": correct,
        "incorrect_cases": incorrect,
        "accuracy": _safe_div_or_none(correct, total),
        "error_rate": _safe_div_or_none(incorrect, total),
        "accuracy_ci": _wilson_interval(correct, total),
        "error_rate_ci": _wilson_interval(incorrect, total),
        "error_case_ids": sorted(
            evaluation.case_id for evaluation in evaluations if not evaluation.correct
        ),
    }


def _bias_stratified_by_attribute(
    evaluations: list[BiasStratifiedEvaluation],
) -> dict[str, dict[str, Any]]:
    """Summarize stratified rows by attribute and group."""
    by_attribute: dict[str, list[BiasStratifiedEvaluation]] = {}
    for evaluation in evaluations:
        by_attribute.setdefault(evaluation.attribute, []).append(evaluation)

    output: dict[str, dict[str, Any]] = {}
    for attribute, rows in by_attribute.items():
        by_group: dict[str, list[BiasStratifiedEvaluation]] = {}
        for row in rows:
            by_group.setdefault(row.group, []).append(row)
        group_summaries = {
            group: _bias_stratified_summary(group_rows)
            for group, group_rows in sorted(by_group.items())
        }
        error_rates = [
            summary["error_rate"]
            for summary in group_summaries.values()
            if summary["error_rate"] is not None
        ]
        max_gap = None
        if len(error_rates) >= 2:
            max_gap = max(error_rates) - min(error_rates)
        output[attribute] = {
            **_bias_stratified_summary(rows),
            "group_count": len(group_summaries),
            "max_error_rate_gap": max_gap,
            "groups": group_summaries,
        }
    return dict(sorted(output.items()))


def _bias_stratified_by_surface(
    evaluations: list[BiasStratifiedEvaluation],
) -> dict[str, dict[str, Any]]:
    """Summarize stratified rows by scored surface."""
    by_surface: dict[str, list[BiasStratifiedEvaluation]] = {}
    for evaluation in evaluations:
        by_surface.setdefault(evaluation.surface, []).append(evaluation)
    return {
        surface: _bias_stratified_summary(rows)
        for surface, rows in sorted(by_surface.items())
    }


def _mean_or_none(values: list[float]) -> float | None:
    """Return a mean only when at least one value is available."""
    if not values:
        return None
    return sum(values) / len(values)


def disconfirmation_d7_scorecard(state: ProjectState) -> Dict[str, Any]:
    """Score negative-case contrary anchors against D7 gold, if available."""
    gold = _d7_gold_annotations(state)
    if not gold:
        return {
            "status": "not_available",
            "reason": (
                "No D7 disconfirmation gold annotations found at "
                f"ProjectState.config.extra['{_D7_GOLD_EXTRA_KEY}']; scoring requires "
                "human/adjudicated contrary-evidence anchors."
            ),
            "note": "D7 is gold-dependent; absence of this section is not evidence of disconfirmation quality.",
        }

    gold_keys = {_key_for_gold(anchor) for anchor in gold}
    predicted_keys, unscored_predicted = _predicted_disconfirmation_keys(state)
    bootstrap_config = _exact_bootstrap_config(state)

    system_score = _exact_anchor_score(
        gold_keys,
        predicted_keys,
        unscored_predicted,
        bootstrap_config=bootstrap_config,
    )
    card: Dict[str, Any] = {
        "status": "scored",
        "gold_source": f"ProjectState.config.extra['{_D7_GOLD_EXTRA_KEY}']",
        "note": (
            "Exact target-claim/source-anchor D7 score. This is a measurement substrate, "
            "not a SOTA/parity claim without a held-out adjudicated benchmark."
        ),
    }
    card.update(system_score)
    gold_provenance = _d7_gold_provenance(state)
    if gold_provenance is not None:
        card["gold_provenance"] = gold_provenance
    card["system_gold_agreement"] = _exact_key_system_gold_agreement(
        gold_keys,
        predicted_keys,
        dimension="D7",
        unit="exact target-claim/source-anchor key",
        caveat="semantic disconfirmation validity or held-out benchmark evidence",
    )
    card["span_overlap"] = _d7_span_overlap_score(gold, state)
    card["human_ceiling_comparison"] = _human_ceiling_comparison(
        system_score,
        gold_provenance,
        dimension="D7",
    )

    baselines = _d7_baselines(state)
    if baselines:
        card["baselines"] = _score_d7_baselines(
            gold_keys,
            baselines,
            system_score,
            system_predicted_keys=predicted_keys,
            system_unscored_predicted=unscored_predicted,
            bootstrap_config=bootstrap_config,
        )
        card["baseline_note"] = (
            "Baseline scores use the same exact D7 anchor matching as the system. "
            "System deltas include local paired exact-key bootstrap intervals; "
            "superiority still requires held-out data and prompt_eval-backed testing."
        )
    return card


def _d7_exact_score(
    gold_keys: set[str],
    predicted_keys: set[str],
    unscored_predicted: list[str],
) -> Dict[str, Any]:
    """Score exact D7 prediction keys against gold keys."""
    return _exact_anchor_score(gold_keys, predicted_keys, unscored_predicted)


def _exact_anchor_score(
    gold_keys: set[str],
    predicted_keys: set[str],
    unscored_predicted: list[str],
    *,
    bootstrap_config: ExactScoreBootstrapConfig | None = None,
) -> Dict[str, Any]:
    """Score exact predicted keys against exact gold keys."""
    bootstrap_config = bootstrap_config or ExactScoreBootstrapConfig()
    matched = sorted(gold_keys & predicted_keys)
    missed = sorted(gold_keys - predicted_keys)
    extra = sorted(predicted_keys - gold_keys)
    true_positives = len(matched)
    false_positives = len(extra) + len(unscored_predicted)
    false_negatives = len(missed)
    recall = _safe_div(true_positives, true_positives + false_negatives)
    precision = _safe_div(true_positives, true_positives + false_positives)
    f1 = _safe_div(2 * precision * recall, precision + recall)
    recall_denominator = true_positives + false_negatives
    precision_denominator = true_positives + false_positives

    score: Dict[str, Any] = {
        "gold_count": len(gold_keys),
        "predicted_count": len(predicted_keys) + len(unscored_predicted),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "recall": recall,
        "precision": precision,
        "f1": f1,
        "recall_ci": _wilson_interval(true_positives, recall_denominator),
        "precision_ci": _wilson_interval(true_positives, precision_denominator),
        "matched_gold_keys": matched,
        "missed_gold_keys": missed,
        "extra_predicted_keys": extra,
        "unscored_predicted_anchors": unscored_predicted,
    }
    if bootstrap_config.enabled:
        score["f1_bootstrap_ci"] = _exact_anchor_f1_bootstrap_ci(
            gold_keys,
            predicted_keys,
            unscored_predicted,
            bootstrap_config=bootstrap_config,
        )
    return score


def _exact_bootstrap_config(state: ProjectState) -> ExactScoreBootstrapConfig:
    """Load Phase 0 exact-score bootstrap config from project metadata."""
    raw = state.config.extra.get(_EXACT_BOOTSTRAP_EXTRA_KEY)
    if raw is None:
        return ExactScoreBootstrapConfig()
    if not isinstance(raw, dict):
        raise ValueError(
            f"ProjectState.config.extra['{_EXACT_BOOTSTRAP_EXTRA_KEY}'] must be an object"
        )
    try:
        return ExactScoreBootstrapConfig.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid phase0_exact_bootstrap config: {exc}") from exc


def _exact_anchor_f1_bootstrap_ci(
    gold_keys: set[str],
    predicted_keys: set[str],
    unscored_predicted: list[str],
    *,
    bootstrap_config: ExactScoreBootstrapConfig,
) -> Dict[str, Any]:
    """Return a deterministic F1 bootstrap interval over exact anchor keys."""
    items = _exact_anchor_bootstrap_items(gold_keys, predicted_keys, unscored_predicted)
    base: Dict[str, Any] = {
        "method": "key_universe_bootstrap",
        "metric": "f1",
        "confidence_level": bootstrap_config.confidence_level,
        "samples": bootstrap_config.samples,
        "seed": bootstrap_config.seed,
        "unit": "exact gold/prediction anchor key",
        "population_size": len(items),
        "note": (
            "Deterministic bootstrap over exact gold/prediction keys. This is local "
            "uncertainty metadata, not a held-out superiority or non-inferiority test."
        ),
    }
    if not items:
        return {
            **base,
            "lower": None,
            "upper": None,
            "note": "undefined empty key universe",
        }

    rng = Random(bootstrap_config.seed)
    sample_size = len(items)
    values: list[float] = []
    for _ in range(bootstrap_config.samples):
        sample = [items[rng.randrange(sample_size)] for _ in range(sample_size)]
        values.append(_f1_from_bootstrap_items(sample))

    alpha = (1 - bootstrap_config.confidence_level) / 2
    values.sort()
    return {
        **base,
        "lower": _percentile(values, alpha),
        "upper": _percentile(values, 1 - alpha),
    }


def _exact_anchor_bootstrap_items(
    gold_keys: set[str],
    predicted_keys: set[str],
    unscored_predicted: list[str],
) -> list[tuple[bool, bool]]:
    """Represent exact score keys as (is_gold, is_predicted) bootstrap items."""
    items = [
        (key in gold_keys, key in predicted_keys)
        for key in sorted(gold_keys | predicted_keys)
    ]
    items.extend((False, True) for _ in unscored_predicted)
    return items


def _f1_from_bootstrap_items(items: list[tuple[bool, bool]]) -> float:
    """Compute F1 from bootstrapped exact-key classification items."""
    true_positives = sum(1 for is_gold, is_predicted in items if is_gold and is_predicted)
    false_positives = sum(1 for is_gold, is_predicted in items if is_predicted and not is_gold)
    false_negatives = sum(1 for is_gold, is_predicted in items if is_gold and not is_predicted)
    recall = _safe_div(true_positives, true_positives + false_negatives)
    precision = _safe_div(true_positives, true_positives + false_positives)
    return _safe_div(2 * precision * recall, precision + recall)


def _exact_anchor_delta_bootstrap_ci(
    gold_keys: set[str],
    system_predicted_keys: set[str],
    system_unscored_predicted: list[str],
    baseline_predicted_keys: set[str],
    baseline_unscored_predicted: list[str],
    *,
    bootstrap_config: ExactScoreBootstrapConfig,
) -> Dict[str, Any]:
    """Return paired bootstrap intervals for system-minus-baseline deltas."""
    items = _exact_anchor_delta_bootstrap_items(
        gold_keys,
        system_predicted_keys,
        system_unscored_predicted,
        baseline_predicted_keys,
        baseline_unscored_predicted,
    )
    base: Dict[str, Any] = {
        "method": "paired_key_universe_bootstrap",
        "confidence_level": bootstrap_config.confidence_level,
        "samples": bootstrap_config.samples,
        "seed": bootstrap_config.seed,
        "unit": "exact gold/system/baseline anchor key",
        "population_size": len(items),
        "note": (
            "Deterministic paired bootstrap over exact gold/system/baseline keys. "
            "This is local uncertainty metadata, not a held-out superiority test."
        ),
    }
    if not items:
        return {
            **base,
            "deltas": {
                "recall": {"lower": None, "upper": None},
                "precision": {"lower": None, "upper": None},
                "f1": {"lower": None, "upper": None},
            },
            "note": "undefined empty key universe",
        }

    rng = Random(bootstrap_config.seed)
    sample_size = len(items)
    deltas: dict[str, list[float]] = {"recall": [], "precision": [], "f1": []}
    for _ in range(bootstrap_config.samples):
        sample = [items[rng.randrange(sample_size)] for _ in range(sample_size)]
        system_metrics = _metrics_from_delta_bootstrap_items(sample, prediction_index=1)
        baseline_metrics = _metrics_from_delta_bootstrap_items(sample, prediction_index=2)
        for metric in deltas:
            deltas[metric].append(system_metrics[metric] - baseline_metrics[metric])

    alpha = (1 - bootstrap_config.confidence_level) / 2
    interval_deltas: dict[str, dict[str, float]] = {}
    for metric, values in deltas.items():
        values.sort()
        interval_deltas[metric] = {
            "lower": _percentile(values, alpha),
            "upper": _percentile(values, 1 - alpha),
        }

    return {**base, "deltas": interval_deltas}


def _exact_anchor_delta_bootstrap_items(
    gold_keys: set[str],
    system_predicted_keys: set[str],
    system_unscored_predicted: list[str],
    baseline_predicted_keys: set[str],
    baseline_unscored_predicted: list[str],
) -> list[tuple[bool, bool, bool]]:
    """Represent paired D7 comparison keys as gold/system/baseline items."""
    items = [
        (
            key in gold_keys,
            key in system_predicted_keys,
            key in baseline_predicted_keys,
        )
        for key in sorted(gold_keys | system_predicted_keys | baseline_predicted_keys)
    ]
    items.extend((False, True, False) for _ in system_unscored_predicted)
    items.extend((False, False, True) for _ in baseline_unscored_predicted)
    return items


def _metrics_from_delta_bootstrap_items(
    items: list[tuple[bool, bool, bool]],
    *,
    prediction_index: int,
) -> dict[str, float]:
    """Compute recall, precision, and F1 for one side of paired delta items."""
    true_positives = sum(1 for item in items if item[0] and item[prediction_index])
    false_positives = sum(1 for item in items if item[prediction_index] and not item[0])
    false_negatives = sum(1 for item in items if item[0] and not item[prediction_index])
    recall = _safe_div(true_positives, true_positives + false_negatives)
    precision = _safe_div(true_positives, true_positives + false_positives)
    f1 = _safe_div(2 * precision * recall, precision + recall)
    return {"recall": recall, "precision": precision, "f1": f1}


def _percentile(sorted_values: list[float], percentile: float) -> float:
    """Return a linearly interpolated percentile from sorted values."""
    if not sorted_values:
        raise ValueError("percentile requires at least one value")
    if not 0 <= percentile <= 1:
        raise ValueError("percentile must be between 0 and 1")
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = percentile * (len(sorted_values) - 1)
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    fraction = position - lower_index
    return (
        sorted_values[lower_index] * (1 - fraction)
        + sorted_values[upper_index] * fraction
    )


def _score_d3_baselines(
    gold_keys: set[str],
    baselines: list[ApplicationBaselinePrediction],
    system_score: Dict[str, Any],
    *,
    system_predicted_keys: set[str],
    system_unscored_predicted: list[str],
    bootstrap_config: ExactScoreBootstrapConfig | None = None,
) -> Dict[str, Dict[str, Any]]:
    """Score D3 baselines and include point deltas versus the system."""
    bootstrap_config = bootstrap_config or ExactScoreBootstrapConfig()
    scored: Dict[str, Dict[str, Any]] = {}
    for baseline in baselines:
        predicted_keys = {
            _key_for_application_gold(anchor) for anchor in baseline.code_applications
        }
        baseline_score = _exact_anchor_score(
            gold_keys,
            predicted_keys,
            [],
            bootstrap_config=bootstrap_config,
        )
        baseline_score["description"] = baseline.description
        baseline_score["system_minus_baseline"] = {
            "recall": system_score["recall"] - baseline_score["recall"],
            "precision": system_score["precision"] - baseline_score["precision"],
            "f1": system_score["f1"] - baseline_score["f1"],
        }
        if bootstrap_config.enabled:
            baseline_score["system_minus_baseline_ci"] = _exact_anchor_delta_bootstrap_ci(
                gold_keys,
                system_predicted_keys,
                system_unscored_predicted,
                predicted_keys,
                [],
                bootstrap_config=bootstrap_config,
            )
        scored[baseline.name] = baseline_score
    return dict(sorted(scored.items()))


def _score_d7_baselines(
    gold_keys: set[str],
    baselines: list[DisconfirmationBaselinePrediction],
    system_score: Dict[str, Any],
    *,
    system_predicted_keys: set[str],
    system_unscored_predicted: list[str],
    bootstrap_config: ExactScoreBootstrapConfig | None = None,
) -> Dict[str, Dict[str, Any]]:
    """Score D7 baselines and include point deltas versus the system."""
    bootstrap_config = bootstrap_config or ExactScoreBootstrapConfig()
    scored: Dict[str, Dict[str, Any]] = {}
    for baseline in baselines:
        predicted_keys = {_key_for_gold(anchor) for anchor in baseline.contrary_evidence}
        baseline_score = _exact_anchor_score(
            gold_keys,
            predicted_keys,
            [],
            bootstrap_config=bootstrap_config,
        )
        baseline_score["description"] = baseline.description
        baseline_score["system_minus_baseline"] = {
            "recall": system_score["recall"] - baseline_score["recall"],
            "precision": system_score["precision"] - baseline_score["precision"],
            "f1": system_score["f1"] - baseline_score["f1"],
        }
        if bootstrap_config.enabled:
            baseline_score["system_minus_baseline_ci"] = _exact_anchor_delta_bootstrap_ci(
                gold_keys,
                system_predicted_keys,
                system_unscored_predicted,
                predicted_keys,
                [],
                bootstrap_config=bootstrap_config,
            )
        scored[baseline.name] = baseline_score
    return dict(sorted(scored.items()))


def _d7_span_overlap_score(
    gold: list[DisconfirmationGoldAnchor],
    state: ProjectState,
) -> dict[str, Any]:
    """Compute same-target/document D7 contrary-evidence char-span diagnostics."""
    gold_spans = [_d7_span_from_gold(anchor) for anchor in gold]
    scoreable_gold_spans = [span for span in gold_spans if span is not None]
    predicted_spans, unscored_predicted_count = _predicted_disconfirmation_spans(state)
    base: dict[str, Any] = {
        "metric": "char_span_iou_same_target_claim_doc",
        "matching_rule": "same_target_claim_id_and_doc_id",
        "note": (
            "Local span-overlap diagnostic for D7 exact-score outputs. It is not "
            "semantic disconfirmation validity, held-out benchmark evidence, or "
            "expert-parity evidence."
        ),
        "gold_span_count": len(scoreable_gold_spans),
        "predicted_span_count": len(predicted_spans),
        "unscored_gold_count": len(gold) - len(scoreable_gold_spans),
        "unscored_predicted_count": unscored_predicted_count,
    }
    if not scoreable_gold_spans:
        return {
            **base,
            "status": "not_available",
            "reason": "No D7 gold anchors with char-span offsets are available for IoU scoring.",
        }
    if not predicted_spans:
        return {
            **base,
            "status": "not_available",
            "reason": "No system contrary anchors with char-span offsets are available for IoU scoring.",
        }

    gold_rows = [
        _best_span_overlap_row(
            source=span,
            candidates=predicted_spans,
            source_key="gold_key",
            best_key="best_predicted_key",
        )
        for span in scoreable_gold_spans
    ]
    predicted_rows = [
        _best_span_overlap_row(
            source=span,
            candidates=scoreable_gold_spans,
            source_key="predicted_key",
            best_key="best_gold_key",
        )
        for span in predicted_spans
    ]
    return {
        **base,
        "status": "scored",
        "mean_best_gold_iou": _mean(row["best_iou"] for row in gold_rows),
        "mean_best_predicted_iou": _mean(row["best_iou"] for row in predicted_rows),
        "mean_best_gold_modified_hausdorff_distance": _mean_optional(
            row["best_modified_hausdorff_distance"] for row in gold_rows
        ),
        "mean_best_predicted_modified_hausdorff_distance": _mean_optional(
            row["best_modified_hausdorff_distance"] for row in predicted_rows
        ),
        "gold_best_overlaps": gold_rows,
        "predicted_best_overlaps": predicted_rows,
    }


def _d7_span_from_gold(anchor: DisconfirmationGoldAnchor) -> _ComparableSpan | None:
    """Convert a D7 gold anchor to a scoreable char span when offsets exist."""
    if anchor.start_char is None or anchor.end_char is None:
        return None
    return _ComparableSpan(
        surface_id=anchor.target_claim_id,
        doc_id=anchor.doc_id,
        start_char=anchor.start_char,
        end_char=anchor.end_char,
        key=_key_for_gold(anchor),
    )


def _predicted_disconfirmation_spans(state: ProjectState) -> tuple[list[_ComparableSpan], int]:
    """Return unique scoreable system contrary spans and unscored count."""
    spans_by_key: dict[str, _ComparableSpan] = {}
    unscored_count = 0
    for claim in state.claims:
        if claim.claim_kind != ClaimKind.NEGATIVE_CASE:
            continue
        if not claim.scope.claim_ids:
            unscored_count += max(1, len(claim.contrary_anchors))
            continue
        if not claim.contrary_anchors:
            unscored_count += max(1, len(claim.scope.claim_ids))
            continue
        for target_claim_id in claim.scope.claim_ids:
            for anchor in claim.contrary_anchors:
                if anchor.start_char is None or anchor.end_char is None:
                    unscored_count += 1
                    continue
                if anchor.start_char < 0 or anchor.end_char <= anchor.start_char:
                    raise ValueError(
                        "D7 system contrary anchor span offsets must satisfy "
                        "0 <= start_char < end_char"
                    )
                key = _key_for_anchor(
                    target_claim_id=target_claim_id,
                    doc_id=anchor.doc_id,
                    start_char=anchor.start_char,
                    end_char=anchor.end_char,
                    segment_id=anchor.segment_id,
                )
                if key is None:
                    unscored_count += 1
                    continue
                spans_by_key.setdefault(
                    key,
                    _ComparableSpan(
                        surface_id=target_claim_id,
                        doc_id=anchor.doc_id,
                        start_char=anchor.start_char,
                        end_char=anchor.end_char,
                        key=key,
                    ),
                )
    return [spans_by_key[key] for key in sorted(spans_by_key)], unscored_count


def _d7_gold_annotations(state: ProjectState) -> list[DisconfirmationGoldAnchor]:
    """Load D7 gold annotations from project config metadata."""
    raw = state.config.extra.get(_D7_GOLD_EXTRA_KEY)
    if raw is None:
        return []
    if isinstance(raw, dict) and "contrary_evidence" in raw:
        raw = raw["contrary_evidence"]
    if not isinstance(raw, list):
        raise ValueError(
            f"ProjectState.config.extra['{_D7_GOLD_EXTRA_KEY}'] must be a list of D7 gold anchors"
        )
    try:
        return [DisconfirmationGoldAnchor.model_validate(item) for item in raw]
    except ValidationError as exc:
        raise ValueError(f"Invalid D7 disconfirmation gold annotations: {exc}") from exc


def _d7_baselines(state: ProjectState) -> list[DisconfirmationBaselinePrediction]:
    """Load D7 baseline predictions from project config metadata."""
    raw = state.config.extra.get(_D7_BASELINES_EXTRA_KEY)
    if raw is None:
        return []
    if isinstance(raw, dict) and _D7_BASELINES_EXTRA_KEY in raw:
        raw = raw[_D7_BASELINES_EXTRA_KEY]
    if not isinstance(raw, list):
        raise ValueError(
            f"ProjectState.config.extra['{_D7_BASELINES_EXTRA_KEY}'] must be a list "
            "of D7 baseline prediction records"
        )
    try:
        baselines = [DisconfirmationBaselinePrediction.model_validate(item) for item in raw]
    except ValidationError as exc:
        raise ValueError(f"Invalid D7 baseline prediction metadata: {exc}") from exc
    names = [baseline.name for baseline in baselines]
    duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
    if duplicates:
        raise ValueError("Duplicate D7 baseline name(s): " + ", ".join(duplicates))
    return baselines


def _d3_baselines(state: ProjectState) -> list[ApplicationBaselinePrediction]:
    """Load D3 baseline predictions from project config metadata."""
    raw = state.config.extra.get(_D3_BASELINES_EXTRA_KEY)
    if raw is None:
        return []
    if isinstance(raw, dict) and _D3_BASELINES_EXTRA_KEY in raw:
        raw = raw[_D3_BASELINES_EXTRA_KEY]
    if not isinstance(raw, list):
        raise ValueError(
            f"ProjectState.config.extra['{_D3_BASELINES_EXTRA_KEY}'] must be a list "
            "of D3 baseline prediction records"
        )
    try:
        baselines = [ApplicationBaselinePrediction.model_validate(item) for item in raw]
    except ValidationError as exc:
        raise ValueError(f"Invalid D3 baseline prediction metadata: {exc}") from exc
    names = [baseline.name for baseline in baselines]
    duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
    if duplicates:
        raise ValueError("Duplicate D3 baseline name(s): " + ", ".join(duplicates))
    return baselines


def _d7_gold_provenance(state: ProjectState) -> dict[str, Any] | None:
    """Return compact D7 gold-set package provenance when available."""
    raw = state.config.extra.get(_D7_GOLD_EXTRA_KEY)
    if not (isinstance(raw, dict) and raw.get("schema_version") == 1):
        return None
    package = validate_d7_gold_set_payload(raw)
    return _gold_set_provenance(
        schema_version=package.schema_version,
        gold_set_id=package.gold_set_id,
        dataset_name=package.dataset_name,
        split=package.split,
        corpus_sha256=package.corpus_sha256,
        project_state_sha256=package.project_state_sha256,
        prompt_frozen=package.prompt_frozen,
        contamination_checked=package.contamination_checked,
        coder_count=package.adjudication.coder_count,
        adjudicator=package.adjudication.adjudicator,
        protocol=package.adjudication.protocol,
        human_human_agreement=package.adjudication.human_human_agreement,
        notes=package.adjudication.notes,
        count_key="contrary_evidence_count",
        anchor_count=len(package.contrary_evidence),
    )


def application_validity_d3_scorecard(state: ProjectState) -> Dict[str, Any]:
    """Score code applications against D3 application gold, if available."""
    gold = _d3_application_gold_annotations(state)
    if not gold:
        return {
            "status": "not_available",
            "reason": (
                "No D3 application gold annotations found at "
                f"ProjectState.config.extra['{_D3_GOLD_EXTRA_KEY}']; scoring requires "
                "human/adjudicated code-to-source assignments."
            ),
            "note": (
                "D3 is gold-dependent; absence of this section is not evidence of "
                "application validity."
            ),
        }

    gold_keys = {_key_for_application_gold(anchor) for anchor in gold}
    predicted_keys, unscored_predicted = _predicted_application_keys(state)
    bootstrap_config = _exact_bootstrap_config(state)
    score = _exact_anchor_score(
        gold_keys,
        predicted_keys,
        unscored_predicted,
        bootstrap_config=bootstrap_config,
    )
    card: Dict[str, Any] = {
        "status": "scored",
        "gold_source": f"ProjectState.config.extra['{_D3_GOLD_EXTRA_KEY}']",
        "note": (
            "Exact code/source-anchor D3 score. This is a measurement substrate, "
            "not application-validity evidence without adjudicated held-out gold "
            "and human-ceiling comparison."
        ),
        **score,
    }
    gold_provenance = _d3_gold_provenance(state)
    if gold_provenance is not None:
        card["gold_provenance"] = gold_provenance
    card["system_gold_agreement"] = _exact_key_system_gold_agreement(
        gold_keys,
        predicted_keys,
        dimension="D3",
        unit="exact code/source-anchor key",
        caveat=(
            "semantic equivalence, Krippendorff's alpha, full D3 validity, "
            "or expert-parity evidence"
        ),
    )
    card["human_ceiling_comparison"] = _human_ceiling_comparison(
        score,
        gold_provenance,
        dimension="D3",
    )
    card["span_overlap"] = _d3_span_overlap_score(gold, state)
    baselines = _d3_baselines(state)
    if baselines:
        card["baselines"] = _score_d3_baselines(
            gold_keys,
            baselines,
            score,
            system_predicted_keys=predicted_keys,
            system_unscored_predicted=unscored_predicted,
            bootstrap_config=bootstrap_config,
        )
        card["baseline_note"] = (
            "Baseline scores use the same exact D3 code/source-anchor matching as "
            "the system. System deltas include local paired exact-key bootstrap "
            "intervals; superiority or expert parity still requires held-out data "
            "and prompt_eval-backed testing."
        )
    return card


def _human_ceiling_comparison(
    system_score: Mapping[str, Any],
    gold_provenance: Mapping[str, Any] | None,
    *,
    dimension: str,
) -> dict[str, Any]:
    """Compare system exact-score metrics to supplied human-ceiling metrics."""
    base: dict[str, Any] = {
        "metric_source": "gold_provenance.adjudication.human_human_agreement",
        "comparable_metric_keys": list(_HUMAN_CEILING_EXACT_METRICS),
        "note": (
            f"{dimension} human-ceiling comparison over exact-score metrics only. "
            "This is not expert-parity evidence unless the gold package is held-out, "
            "prompt-frozen, contamination-checked, and human-adjudicated."
        ),
    }
    if gold_provenance is None:
        return {
            **base,
            "status": "not_available",
            "reason": "No versioned gold-set package provenance is available.",
        }

    base.update(
        {
            "gold_set_id": gold_provenance.get("gold_set_id"),
            "gold_split": gold_provenance.get("split"),
            "prompt_frozen": gold_provenance.get("prompt_frozen"),
            "contamination_checked": gold_provenance.get("contamination_checked"),
        }
    )
    adjudication = gold_provenance.get("adjudication")
    human_metrics = (
        adjudication.get("human_human_agreement")
        if isinstance(adjudication, Mapping)
        else None
    )
    if not isinstance(human_metrics, Mapping) or not human_metrics:
        return {
            **base,
            "status": "not_available",
            "reason": "Gold-set adjudication has no human_human_agreement metrics.",
        }

    chance_corrected = _chance_corrected_agreement_metadata(human_metrics)
    comparable: dict[str, dict[str, Any]] = {}
    non_comparable = []
    for key, human_value in sorted(human_metrics.items()):
        if key in _HUMAN_CEILING_AGREEMENT_METRIC_ALIASES:
            continue
        if key not in _HUMAN_CEILING_EXACT_METRICS:
            non_comparable.append(key)
            continue
        if not _is_numeric_metric(human_value) or not _is_numeric_metric(system_score.get(key)):
            non_comparable.append(key)
            continue
        system_value = float(system_score[key])
        human_float = float(human_value)
        comparable[key] = {
            "system_value": system_value,
            "human_value": human_float,
            "system_minus_human": system_value - human_float,
            "meets_or_exceeds_human": system_value >= human_float,
        }

    if not comparable:
        status = (
            "metadata_only"
            if chance_corrected["status"] == "reported"
            else "not_available"
        )
        return {
            **base,
            "status": status,
            "reason": (
                "human_human_agreement has no numeric recall, precision, or f1 "
                "metrics comparable to the exact-anchor scorecard."
            ),
            "human_metrics": dict(human_metrics),
            "chance_corrected_agreement": chance_corrected,
            "non_comparable_human_metrics": non_comparable,
        }

    return {
        **base,
        "status": "scored",
        "human_metrics": dict(human_metrics),
        "metrics": comparable,
        "chance_corrected_agreement": chance_corrected,
        "non_comparable_human_metrics": non_comparable,
        "system_meets_all_comparable_metrics": all(
            item["meets_or_exceeds_human"] for item in comparable.values()
        ),
    }


def _chance_corrected_agreement_metadata(
    human_metrics: Mapping[str, Any],
) -> dict[str, Any]:
    """Extract human-human chance-corrected agreement metadata."""
    metrics: dict[str, float] = {}
    non_numeric = []
    for key, value in sorted(human_metrics.items()):
        canonical_key = _HUMAN_CEILING_AGREEMENT_METRIC_ALIASES.get(key)
        if canonical_key is None:
            continue
        if _is_numeric_metric(value):
            metrics[canonical_key] = float(value)
        else:
            non_numeric.append(key)

    if not metrics:
        result: dict[str, Any] = {
            "status": "not_available",
            "reason": (
                "human_human_agreement has no numeric chance-corrected "
                "agreement metrics."
            ),
            "metric_keys": sorted(set(_HUMAN_CEILING_AGREEMENT_METRIC_ALIASES.values())),
        }
    else:
        result = {
            "status": "reported",
            "metrics": dict(sorted(metrics.items())),
            "metric_keys": sorted(metrics),
            "note": (
                "Human-human chance-corrected agreement metadata from the gold "
                "package only; this section does not compare system "
                "chance-corrected agreement to the human ceiling."
            ),
        }
    if non_numeric:
        result["non_numeric_metrics"] = sorted(non_numeric)
    return result


def _is_numeric_metric(value: Any) -> bool:
    """Return true for real numeric metric values, excluding booleans."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _d3_application_gold_annotations(state: ProjectState) -> list[ApplicationGoldAnchor]:
    """Load D3 application gold annotations from project config metadata."""
    raw = state.config.extra.get(_D3_GOLD_EXTRA_KEY)
    if raw is None:
        return []
    if isinstance(raw, dict) and _D3_GOLD_EXTRA_KEY in raw:
        raw = raw[_D3_GOLD_EXTRA_KEY]
    if isinstance(raw, dict) and "code_applications" in raw:
        raw = raw["code_applications"]
    if not isinstance(raw, list):
        raise ValueError(
            f"ProjectState.config.extra['{_D3_GOLD_EXTRA_KEY}'] must be a list "
            "of D3 application gold anchors"
        )
    try:
        anchors = [ApplicationGoldAnchor.model_validate(item) for item in raw]
    except ValidationError as exc:
        raise ValueError(f"Invalid D3 application gold annotations: {exc}") from exc
    keys = [_key_for_application_gold(anchor) for anchor in anchors]
    duplicates = sorted(key for key, count in Counter(keys).items() if count > 1)
    if duplicates:
        raise ValueError("Duplicate D3 application gold anchor key(s): " + ", ".join(duplicates))
    return anchors


def _d3_gold_provenance(state: ProjectState) -> dict[str, Any] | None:
    """Return compact D3 gold-set package provenance when available."""
    raw = state.config.extra.get(_D3_GOLD_EXTRA_KEY)
    if not (isinstance(raw, dict) and raw.get("schema_version") == 1):
        return None
    package = validate_d3_gold_set_payload(raw)
    return _gold_set_provenance(
        schema_version=package.schema_version,
        gold_set_id=package.gold_set_id,
        dataset_name=package.dataset_name,
        split=package.split,
        corpus_sha256=package.corpus_sha256,
        project_state_sha256=package.project_state_sha256,
        prompt_frozen=package.prompt_frozen,
        contamination_checked=package.contamination_checked,
        coder_count=package.adjudication.coder_count,
        adjudicator=package.adjudication.adjudicator,
        protocol=package.adjudication.protocol,
        human_human_agreement=package.adjudication.human_human_agreement,
        notes=package.adjudication.notes,
        count_key="application_gold_count",
        anchor_count=len(package.application_gold),
    )


def _exact_key_system_gold_agreement(
    gold_keys: set[str],
    predicted_keys: set[str],
    *,
    dimension: str,
    unit: str,
    caveat: str,
) -> dict[str, Any]:
    """Compute exact-key binary agreement between gold and system predictions."""
    key_universe = sorted(gold_keys | predicted_keys)
    if not key_universe:
        return {
            "status": "not_available",
            "reason": f"No {dimension} exact-key gold/predicted universe is available.",
            "note": (
                f"{dimension} system-gold agreement is exact-key binary metadata, "
                f"not {caveat}."
            ),
        }

    matrix = {
        key: [
            1 if key in gold_keys else 0,
            1 if key in predicted_keys else 0,
        ]
        for key in key_universe
    }
    return {
        "status": "scored",
        "unit": unit,
        "raters": ["gold", "system"],
        "row_count": len(key_universe),
        "gold_positive_count": len(gold_keys),
        "system_positive_count": len(predicted_keys),
        "percent_agreement": compute_percent_agreement(matrix),
        "cohens_kappa": compute_cohens_kappa(matrix),
        "gwet_ac1": compute_gwet_ac1(matrix),
        "krippendorff_alpha": compute_krippendorff_alpha(matrix),
        "prevalence": _binary_matrix_prevalence(matrix),
        "note": (
            f"Binary agreement over the exact {dimension} key universe only. "
            f"This is prevalence-aware agreement metadata, not {caveat}."
        ),
    }


def _gold_set_provenance(
    *,
    schema_version: int,
    gold_set_id: str,
    dataset_name: str,
    split: str,
    corpus_sha256: str,
    project_state_sha256: str | None,
    prompt_frozen: bool,
    contamination_checked: bool,
    coder_count: int,
    adjudicator: str,
    protocol: str,
    human_human_agreement: dict[str, Any] | None,
    notes: str,
    count_key: str,
    anchor_count: int,
) -> dict[str, Any]:
    """Build anchor-free gold-set provenance for scorecard output."""
    return {
        "schema_version": schema_version,
        "gold_set_id": gold_set_id,
        "dataset_name": dataset_name,
        "split": split,
        "corpus_sha256": corpus_sha256,
        "project_state_sha256": project_state_sha256,
        "prompt_frozen": prompt_frozen,
        "contamination_checked": contamination_checked,
        "adjudication": {
            "coder_count": coder_count,
            "adjudicator": adjudicator,
            "protocol": protocol,
            "human_human_agreement": human_human_agreement,
            "notes": notes,
        },
        count_key: anchor_count,
    }


def _d3_span_overlap_score(
    gold: list[ApplicationGoldAnchor],
    state: ProjectState,
) -> dict[str, Any]:
    """Compute same-code/same-document D3 char-span IoU diagnostics."""
    gold_spans = [_application_span_from_gold(anchor) for anchor in gold]
    scoreable_gold_spans = [span for span in gold_spans if span is not None]
    predicted_spans, unscored_predicted_count = _predicted_application_spans(state)
    base: dict[str, Any] = {
        "metric": "char_span_iou_same_code_doc",
        "note": (
            "Local span-overlap diagnostic for D3 exact-score outputs. It is not "
            "a full application-validity, Hausdorff, or expert-parity metric."
        ),
        "gold_span_count": len(scoreable_gold_spans),
        "predicted_span_count": len(predicted_spans),
        "unscored_gold_count": len(gold) - len(scoreable_gold_spans),
        "unscored_predicted_count": unscored_predicted_count,
    }
    if not scoreable_gold_spans:
        return {
            **base,
            "status": "not_available",
            "reason": "No D3 gold anchors with char-span offsets are available for IoU scoring.",
        }
    if not predicted_spans:
        return {
            **base,
            "status": "not_available",
            "reason": "No system code applications with char-span offsets are available for IoU scoring.",
        }

    gold_rows = [
        _best_span_overlap_row(
            source=span,
            candidates=predicted_spans,
            source_key="gold_key",
            best_key="best_predicted_key",
        )
        for span in scoreable_gold_spans
    ]
    predicted_rows = [
        _best_span_overlap_row(
            source=span,
            candidates=scoreable_gold_spans,
            source_key="predicted_key",
            best_key="best_gold_key",
        )
        for span in predicted_spans
    ]
    return {
        **base,
        "status": "scored",
        "mean_best_gold_iou": _mean(row["best_iou"] for row in gold_rows),
        "mean_best_predicted_iou": _mean(row["best_iou"] for row in predicted_rows),
        "mean_best_gold_modified_hausdorff_distance": _mean_optional(
            row["best_modified_hausdorff_distance"] for row in gold_rows
        ),
        "mean_best_predicted_modified_hausdorff_distance": _mean_optional(
            row["best_modified_hausdorff_distance"] for row in predicted_rows
        ),
        "gold_best_overlaps": gold_rows,
        "predicted_best_overlaps": predicted_rows,
    }


def _application_span_from_gold(anchor: ApplicationGoldAnchor) -> _ComparableSpan | None:
    """Convert a D3 gold anchor to a scoreable char span when offsets exist."""
    if anchor.start_char is None or anchor.end_char is None:
        return None
    return _ComparableSpan(
        surface_id=anchor.code_id,
        doc_id=anchor.doc_id,
        start_char=anchor.start_char,
        end_char=anchor.end_char,
        key=_key_for_application_gold(anchor),
    )


def _predicted_application_spans(state: ProjectState) -> tuple[list[_ComparableSpan], int]:
    """Return unique scoreable system application spans and unscored count."""
    spans_by_key: dict[str, _ComparableSpan] = {}
    unscored_count = 0
    for app in state.code_applications:
        key = _key_for_application_anchor(
            code_id=app.code_id,
            doc_id=app.doc_id,
            start_char=app.start_char,
            end_char=app.end_char,
            segment_id=None,
        )
        if key is None:
            unscored_count += 1
            continue
        if app.start_char is None or app.end_char is None:
            unscored_count += 1
            continue
        if app.start_char < 0 or app.end_char <= app.start_char:
            raise ValueError(
                "D3 system code application span offsets must satisfy "
                "0 <= start_char < end_char"
            )
        spans_by_key.setdefault(
            key,
            _ComparableSpan(
                surface_id=app.code_id,
                doc_id=app.doc_id,
                start_char=app.start_char,
                end_char=app.end_char,
                key=key,
            ),
        )
    return [spans_by_key[key] for key in sorted(spans_by_key)], unscored_count


def _best_span_overlap_row(
    *,
    source: _ComparableSpan,
    candidates: list[_ComparableSpan],
    source_key: str,
    best_key: str,
) -> dict[str, Any]:
    """Find the best same-surface/document IoU row for one source span."""
    same_surface = [
        candidate
        for candidate in candidates
        if candidate.surface_id == source.surface_id and candidate.doc_id == source.doc_id
    ]
    if not same_surface:
        return {
            source_key: source.key,
            best_key: None,
            "best_iou": 0.0,
            "best_modified_hausdorff_distance": None,
        }
    best = max(
        same_surface,
        key=lambda candidate: (
            _span_iou(source, candidate),
            -_modified_hausdorff_distance(source, candidate),
            candidate.key,
        ),
    )
    return {
        source_key: source.key,
        best_key: best.key,
        "best_iou": _span_iou(source, best),
        "best_modified_hausdorff_distance": _modified_hausdorff_distance(source, best),
    }


def _span_iou(a: _ComparableSpan, b: _ComparableSpan) -> float:
    """Compute intersection-over-union for two char spans."""
    intersection = max(0, min(a.end_char, b.end_char) - max(a.start_char, b.start_char))
    if intersection == 0:
        return 0.0
    union = max(a.end_char, b.end_char) - min(a.start_char, b.start_char)
    return _safe_div(intersection, union)


def _modified_hausdorff_distance(a: _ComparableSpan, b: _ComparableSpan) -> float:
    """Compute discrete modified Hausdorff distance between two char spans."""
    a_to_b = _mean(
        _distance_from_position_to_span(position, b)
        for position in range(a.start_char, a.end_char)
    )
    b_to_a = _mean(
        _distance_from_position_to_span(position, a)
        for position in range(b.start_char, b.end_char)
    )
    return max(a_to_b, b_to_a)


def _distance_from_position_to_span(position: int, span: _ComparableSpan) -> int:
    """Return nearest-char distance from one position to a half-open span."""
    if span.start_char <= position < span.end_char:
        return 0
    if position < span.start_char:
        return span.start_char - position
    return position - (span.end_char - 1)


def _mean(values: Iterable[float]) -> float:
    """Return zero for an empty mean."""
    items = list(values)
    return _safe_div(sum(items), len(items))


def _mean_optional(values: Iterable[float | None]) -> float | None:
    """Return None when no numeric values exist."""
    items = [value for value in values if value is not None]
    if not items:
        return None
    return _safe_div(sum(items), len(items))


def _predicted_application_keys(state: ProjectState) -> tuple[set[str], list[str]]:
    """Return scoreable system code-application keys and unscoreable descriptions."""
    keys: set[str] = set()
    unscored: list[str] = []
    for app in state.code_applications:
        key = _key_for_application_anchor(
            code_id=app.code_id,
            doc_id=app.doc_id,
            start_char=app.start_char,
            end_char=app.end_char,
            segment_id=None,
        )
        if key is None:
            unscored.append(
                f"{app.id}|code={app.code_id}|doc={app.doc_id}|missing-span-or-segment"
            )
            continue
        keys.add(key)
    return keys, sorted(unscored)


def _key_for_application_gold(anchor: ApplicationGoldAnchor) -> str:
    """Build an exact D3 comparison key from a gold application anchor."""
    key = _key_for_application_anchor(
        code_id=anchor.code_id,
        doc_id=anchor.doc_id,
        start_char=anchor.start_char,
        end_char=anchor.end_char,
        segment_id=anchor.segment_id,
    )
    if key is None:
        raise ValueError("D3 application gold anchor validation failed to produce a comparison key")
    return key


def _key_for_application_anchor(
    *,
    code_id: str,
    doc_id: str,
    start_char: int | None,
    end_char: int | None,
    segment_id: str | None,
) -> str | None:
    """Build an exact D3 key from code identity plus source anchor."""
    if start_char is not None and end_char is not None:
        return f"{code_id}|{doc_id}|{start_char}:{end_char}"
    if segment_id:
        return f"{code_id}|{doc_id}|segment:{segment_id}"
    return None


def _predicted_disconfirmation_keys(state: ProjectState) -> tuple[set[str], list[str]]:
    """Return scoreable predicted D7 keys and unscoreable anchor descriptions."""
    keys: set[str] = set()
    unscored: list[str] = []
    for claim in state.claims:
        if claim.claim_kind != ClaimKind.NEGATIVE_CASE:
            continue
        if not claim.scope.claim_ids:
            unscored.append(f"{claim.id}|missing-target-claim")
            continue
        if not claim.contrary_anchors:
            unscored.append(f"{claim.id}|missing-contrary-anchor")
            continue
        for target_claim_id in claim.scope.claim_ids:
            for anchor in claim.contrary_anchors:
                key = _key_for_anchor(
                    target_claim_id=target_claim_id,
                    doc_id=anchor.doc_id,
                    start_char=anchor.start_char,
                    end_char=anchor.end_char,
                    segment_id=anchor.segment_id,
                )
                if key is None:
                    unscored.append(_unscored_anchor_description(claim.id, target_claim_id, anchor))
                    continue
                keys.add(key)
    return keys, sorted(unscored)


def _key_for_gold(anchor: DisconfirmationGoldAnchor) -> str:
    """Build the exact comparison key for a gold D7 anchor."""
    key = _key_for_anchor(
        target_claim_id=anchor.target_claim_id,
        doc_id=anchor.doc_id,
        start_char=anchor.start_char,
        end_char=anchor.end_char,
        segment_id=anchor.segment_id,
    )
    if key is None:
        raise ValueError("D7 gold anchor validation failed to produce a comparison key")
    return key


def _key_for_anchor(
    *,
    target_claim_id: str,
    doc_id: str,
    start_char: int | None,
    end_char: int | None,
    segment_id: str | None,
) -> str | None:
    """Build an exact D7 comparison key from claim identity plus source anchor."""
    if start_char is not None and end_char is not None:
        return f"{target_claim_id}|{doc_id}|{start_char}:{end_char}"
    if segment_id:
        return f"{target_claim_id}|{doc_id}|segment:{segment_id}"
    return None


def _unscored_anchor_description(claim_id: str, target_claim_id: str, anchor: ClaimAnchor) -> str:
    """Describe a predicted contrary anchor that cannot enter exact D7 scoring."""
    return (
        f"{claim_id}|target={target_claim_id}|doc={anchor.doc_id}|"
        "missing-span-or-segment"
    )


def _safe_div(numerator: float, denominator: float) -> float:
    """Return zero for undefined score fractions."""
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _wilson_interval(
    successes: int,
    denominator: int,
    *,
    confidence_level: float = 0.95,
) -> Dict[str, Any]:
    """Return a Wilson score interval for a binomial proportion."""
    if confidence_level != 0.95:
        raise ValueError("Only 95% Wilson intervals are supported in Phase 0")
    if successes < 0 or denominator < 0:
        raise ValueError("Wilson interval counts must be non-negative")
    if successes > denominator:
        raise ValueError("Wilson interval successes cannot exceed denominator")
    if denominator == 0:
        return {
            "method": "wilson",
            "confidence_level": confidence_level,
            "successes": successes,
            "denominator": denominator,
            "lower": None,
            "upper": None,
            "note": "undefined denominator",
        }

    z = _WILSON_Z_95
    p_hat = successes / denominator
    z2 = z * z
    denom = 1 + (z2 / denominator)
    center = (p_hat + (z2 / (2 * denominator))) / denom
    margin = (
        z * sqrt((p_hat * (1 - p_hat) / denominator) + (z2 / (4 * denominator * denominator)))
    ) / denom
    return {
        "method": "wilson",
        "confidence_level": confidence_level,
        "successes": successes,
        "denominator": denominator,
        "lower": max(0.0, center - margin),
        "upper": min(1.0, center + margin),
    }
