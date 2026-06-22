"""Export theoretical-sampling result packages from selected candidates."""

from __future__ import annotations

from typing import Any

from qc_clean.core.theoretical_sampling_preflight import (
    THEORETICAL_SAMPLING_PREFLIGHT_CAUTION,
    TheoreticalSamplingCandidatePackage,
    TheoreticalSamplingResultPackage,
    preflight_theoretical_sampling_payloads,
)
from qc_clean.core.theoretical_sampling_protocol import (
    TheoreticalSamplingProtocolPackage,
    validate_theoretical_sampling_protocol_payload,
)


def export_theoretical_sampling_results(
    protocol_payload: TheoreticalSamplingProtocolPackage | dict[str, Any],
    candidates_payload: TheoreticalSamplingCandidatePackage | dict[str, Any],
    *,
    selected_candidate_ids: list[str],
    success_criteria_met: list[str],
    stopped_by_rule: bool = False,
) -> dict[str, Any]:
    """Export selected theoretical-sampling candidates as a result package."""

    protocol = _coerce_protocol(protocol_payload)
    candidates = _coerce_candidates(candidates_payload)
    selected_ids = _normalize_nonempty(selected_candidate_ids, label="selected candidate ID")
    criteria = _normalize_nonempty(success_criteria_met, label="success criterion")

    candidate_by_id = {candidate.candidate_id: candidate for candidate in candidates.candidates}
    unknown_ids = sorted(set(selected_ids) - set(candidate_by_id))
    if unknown_ids:
        raise ValueError("unknown candidate ID(s): " + ", ".join(unknown_ids))

    unregistered_criteria = sorted(set(criteria) - set(protocol.success_criteria))
    if unregistered_criteria:
        raise ValueError(
            "unregistered success criteria: " + " | ".join(unregistered_criteria)
        )

    selected_candidates = [candidate_by_id[candidate_id] for candidate_id in selected_ids]
    package = TheoreticalSamplingResultPackage(
        schema_version=1,
        package_type="qualitative_coding.theoretical_sampling_results",
        protocol_id=protocol.protocol_id,
        project_id=protocol.project_id,
        corpus_sha256=protocol.corpus_sha256,
        project_state_sha256=protocol.project_state_sha256,
        selected_candidate_ids=selected_ids,
        addressed_gap_codes=sorted(
            {gap_code for candidate in selected_candidates for gap_code in candidate.gap_codes}
        ),
        addressed_gap_types=sorted(
            {gap_type for candidate in selected_candidates for gap_type in candidate.gap_types}
        ),
        stopped_by_rule=stopped_by_rule,
        success_criteria_met=criteria,
        caution=THEORETICAL_SAMPLING_PREFLIGHT_CAUTION,
    )
    payload = package.model_dump(mode="json")
    report = preflight_theoretical_sampling_payloads(
        protocol.model_dump(mode="json"),
        candidates.model_dump(mode="json"),
        payload,
    )
    if report.status != "pass":
        raise ValueError(
            "theoretical sampling result package failed preflight: "
            + "; ".join(error.message for error in report.errors)
        )
    return payload


def _coerce_protocol(
    payload: TheoreticalSamplingProtocolPackage | dict[str, Any],
) -> TheoreticalSamplingProtocolPackage:
    """Return a validated theoretical-sampling protocol package."""

    if isinstance(payload, TheoreticalSamplingProtocolPackage):
        return payload
    return validate_theoretical_sampling_protocol_payload(payload)


def _coerce_candidates(
    payload: TheoreticalSamplingCandidatePackage | dict[str, Any],
) -> TheoreticalSamplingCandidatePackage:
    """Return a validated theoretical-sampling candidate package."""

    if isinstance(payload, TheoreticalSamplingCandidatePackage):
        return payload
    if not isinstance(payload, dict):
        raise ValueError("Theoretical sampling candidate package must be a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError("Theoretical sampling candidate package must include schema_version=1")
    return TheoreticalSamplingCandidatePackage.model_validate(payload)


def _normalize_nonempty(values: list[str], *, label: str) -> list[str]:
    """Normalize a list of operator-supplied strings."""

    normalized = [value.strip() for value in values if value.strip()]
    if not normalized:
        raise ValueError(f"Theoretical sampling {label} is required")
    duplicates = sorted(value for value in set(normalized) if normalized.count(value) > 1)
    if duplicates:
        raise ValueError(
            f"Duplicate theoretical sampling {label}(s): " + ", ".join(duplicates)
        )
    return normalized
