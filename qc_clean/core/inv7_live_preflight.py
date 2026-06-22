"""Preflight INV-7 live result packages against registered live protocols."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from qc_clean.core.inv7_live_protocol import (
    Inv7LiveProtocolPackage,
    validate_inv7_live_protocol_payload,
)
from qc_clean.core.inv7_package import (
    Inv7PromptInjectionPackage,
    validate_inv7_prompt_injection_package_payload,
)


INV7_LIVE_PREFLIGHT_CAUTION = (
    "INV-7 live preflight is process metadata only; it is not a live benchmark "
    "result, not prompt-injection robustness evidence, not model-obedience "
    "evidence, and not validity evidence."
)


class Inv7LivePreflightError(BaseModel):
    """One INV-7 live protocol/result preflight error."""

    field: str = Field(description="Field or cross-check that failed")
    message: str = Field(description="Human-readable failure description")


class Inv7LivePreflightReport(BaseModel):
    """Machine-readable report for INV-7 live protocol/result preflight."""

    schema_version: Literal[1] = Field(description="Preflight report schema version")
    package_type: Literal["inv7_live_preflight"] = Field(description="Report package kind")
    status: Literal["pass", "fail"] = Field(description="Overall preflight status")
    protocol_id: str | None = Field(default=None, description="Protocol ID when available")
    package_id: str | None = Field(default=None, description="Result package ID when available")
    split: str | None = Field(default=None, description="Protocol split when available")
    fixture_set_id: str | None = Field(default=None, description="Protocol fixture set ID")
    fixture_set_version: str | None = Field(default=None, description="Protocol fixture set version")
    model: str | None = Field(default=None, description="Protocol model name")
    trace_id: str | None = Field(default=None, description="Protocol trace ID")
    fixture_count: int = Field(description="Number of protocol fixture prompt hashes")
    errors: list[Inv7LivePreflightError] = Field(
        default_factory=list,
        description="Preflight failures",
    )
    caution: str = Field(description="Claim-discipline caveat for preflight reports")


def preflight_inv7_live_payloads(
    protocol_payload: Any,
    package_payload: Any,
) -> Inv7LivePreflightReport:
    """Cross-check an INV-7 live result package against a registered protocol."""
    errors: list[Inv7LivePreflightError] = []
    protocol = _validate_protocol(protocol_payload, errors)
    package = _validate_package(package_payload, errors)
    if protocol is not None and package is not None:
        _check_package_matches_protocol(protocol, package, errors)
    return _build_report(protocol=protocol, package=package, errors=errors)


def _validate_protocol(
    payload: Any,
    errors: list[Inv7LivePreflightError],
) -> Inv7LiveProtocolPackage | None:
    """Validate protocol payload and append a preflight error on failure."""
    try:
        return validate_inv7_live_protocol_payload(payload)
    except ValueError as exc:
        errors.append(Inv7LivePreflightError(field="protocol", message=str(exc)))
        return None


def _validate_package(
    payload: Any,
    errors: list[Inv7LivePreflightError],
) -> Inv7PromptInjectionPackage | None:
    """Validate result package payload and append a preflight error on failure."""
    try:
        return validate_inv7_prompt_injection_package_payload(payload)
    except ValueError as exc:
        errors.append(Inv7LivePreflightError(field="package", message=str(exc)))
        return None


def _check_package_matches_protocol(
    protocol: Inv7LiveProtocolPackage,
    package: Inv7PromptInjectionPackage,
    errors: list[Inv7LivePreflightError],
) -> None:
    """Append errors for result package metadata drift from the protocol."""
    if package.mode != "live_model":
        errors.append(
            Inv7LivePreflightError(
                field="mode",
                message=f"Result package mode must be 'live_model', got {package.mode!r}",
            )
        )
    _check_equal("split", protocol.split, package.split, errors)
    _check_equal("fixture_set_id", protocol.fixture_set_id, package.fixture_set_id, errors)
    _check_equal(
        "fixture_set_version",
        protocol.fixture_set_version,
        package.fixture_set_version,
        errors,
    )
    _check_equal("model", protocol.model, package.model, errors)
    _check_equal("trace_id", protocol.trace_id, package.trace_id, errors)
    _check_equal("prompt_frozen", protocol.prompt_frozen, package.prompt_frozen, errors)
    _check_equal(
        "contamination_checked",
        protocol.contamination_checked,
        package.contamination_checked,
        errors,
    )
    if package.max_budget is None:
        errors.append(
            Inv7LivePreflightError(
                field="max_budget",
                message="Live result package must include max_budget",
            )
        )
    elif package.max_budget > protocol.max_budget:
        errors.append(
            Inv7LivePreflightError(
                field="max_budget",
                message=(
                    f"Result package max_budget {package.max_budget} exceeds "
                    f"protocol max_budget {protocol.max_budget}"
                ),
            )
        )
    if package.fixture_prompt_hashes != protocol.fixture_prompt_hashes:
        errors.append(
            Inv7LivePreflightError(
                field="fixture_prompt_hashes",
                message="Result package fixture_prompt_hashes do not match protocol hashes",
            )
        )


def _check_equal(
    field: str,
    expected: Any,
    actual: Any,
    errors: list[Inv7LivePreflightError],
) -> None:
    """Append a field mismatch error when values differ."""
    if expected != actual:
        errors.append(
            Inv7LivePreflightError(
                field=field,
                message=f"Protocol {field} {expected!r} does not match result package {actual!r}",
            )
        )


def _build_report(
    *,
    protocol: Inv7LiveProtocolPackage | None,
    package: Inv7PromptInjectionPackage | None,
    errors: list[Inv7LivePreflightError],
) -> Inv7LivePreflightReport:
    """Build the final preflight report."""
    return Inv7LivePreflightReport(
        schema_version=1,
        package_type="inv7_live_preflight",
        status="fail" if errors else "pass",
        protocol_id=protocol.protocol_id if protocol is not None else None,
        package_id=package.package_id if package is not None else None,
        split=protocol.split if protocol is not None else None,
        fixture_set_id=protocol.fixture_set_id if protocol is not None else None,
        fixture_set_version=protocol.fixture_set_version if protocol is not None else None,
        model=protocol.model if protocol is not None else None,
        trace_id=protocol.trace_id if protocol is not None else None,
        fixture_count=len(protocol.fixture_prompt_hashes) if protocol is not None else 0,
        errors=errors,
        caution=INV7_LIVE_PREFLIGHT_CAUTION,
    )
