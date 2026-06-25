#!/usr/bin/env python3
"""Validate the default-path surface contract registry.

Minimum viable enforcement validates registry structure in the default docs
gate and can optionally surface non-blocking warnings for known producer gaps.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Literal

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, Field, ValidationError, model_validator


SURFACE_ID_RE = re.compile(r"^[a-z0-9_.-]+$")
ROLLOUT_STATUSES = {
    "enforced_now",
    "warning_until_follow_on_fix",
    "warning_until_density_criteria_exist",
}


class OperationalValidationContract(BaseModel):
    """Operational-validation requirement for one surface."""

    real_run_requirement: Literal["required", "not_required", "future"]
    rollout_status: str = Field(description="Current rollout posture for this surface")

    @model_validator(mode="after")
    def validate_rollout_status(self) -> "OperationalValidationContract":
        if self.rollout_status not in ROLLOUT_STATUSES:
            allowed = ", ".join(sorted(ROLLOUT_STATUSES))
            raise ValueError(f"rollout_status must be one of: {allowed}")
        return self


class ProducerContract(BaseModel):
    """One producer declaration for one supported path."""

    path: str
    status: Literal["present", "partial", "missing", "not_applicable"]
    producers: list[str] = Field(default_factory=list)
    note: str = ""

    @model_validator(mode="after")
    def validate_producer_list(self) -> "ProducerContract":
        self.path = self.path.strip()
        if not self.path:
            raise ValueError("producer contract path must be non-empty")
        if self.status == "present" and not self.producers:
            raise ValueError("status='present' requires at least one producer path")
        return self


class SurfaceContract(BaseModel):
    """One visible surface and its producer contract."""

    surface_id: str
    label: str
    visible_by_default: bool
    user_facing: bool
    claim_bearing: bool
    default_paths: list[str] = Field(default_factory=list)
    producer_contracts: list[ProducerContract]
    operational_validation: OperationalValidationContract

    @model_validator(mode="after")
    def validate_surface(self) -> "SurfaceContract":
        self.surface_id = self.surface_id.strip()
        self.label = self.label.strip()
        if not SURFACE_ID_RE.fullmatch(self.surface_id):
            raise ValueError("surface_id must match ^[a-z0-9_.-]+$")
        if not self.label:
            raise ValueError("label must be non-empty")
        if self.visible_by_default and not self.user_facing:
            raise ValueError("visible_by_default surfaces must also be user_facing")
        if self.visible_by_default and not self.default_paths:
            raise ValueError("visible_by_default surfaces must declare default_paths")
        contract_paths = {contract.path for contract in self.producer_contracts}
        missing_paths = [path for path in self.default_paths if path not in contract_paths]
        if missing_paths:
            raise ValueError(
                "default_paths missing producer contracts for: " + ", ".join(sorted(missing_paths))
            )
        return self


class PolicyBlock(BaseModel):
    """Top-level policy metadata for the registry."""

    scope: str
    default_gate_mode: Literal["validate_config", "warn_only", "strict"]
    strict_gate_mode: Literal["future", "enabled"]


class SurfaceContractRegistry(BaseModel):
    """Root registry model."""

    version: Literal[1]
    policy: PolicyBlock
    surfaces: list[SurfaceContract]

    @model_validator(mode="after")
    def validate_unique_surface_ids(self) -> "SurfaceContractRegistry":
        seen: set[str] = set()
        duplicates: list[str] = []
        for surface in self.surfaces:
            if surface.surface_id in seen:
                duplicates.append(surface.surface_id)
            seen.add(surface.surface_id)
        if duplicates:
            raise ValueError("Duplicate surface_id(s): " + ", ".join(sorted(duplicates)))
        return self


def load_registry(path: Path) -> SurfaceContractRegistry:
    """Load and validate one registry file."""
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise ValueError(f"Registry file '{path}' could not be read: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"Registry file '{path}' is not valid YAML: {exc}") from exc
    try:
        return SurfaceContractRegistry.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid surface contract registry: {exc}") from exc


def warning_messages(registry: SurfaceContractRegistry) -> list[str]:
    """Return non-blocking rollout warnings."""
    warnings: list[str] = []
    for surface in registry.surfaces:
        for contract in surface.producer_contracts:
            if surface.visible_by_default and contract.path in surface.default_paths:
                if contract.status == "missing":
                    warnings.append(
                        f"{surface.surface_id}: visible-by-default path '{contract.path}' "
                        "has no compatible producer yet"
                    )
    return warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="docs/governance/default_path_surface_contracts.yaml",
        help="Path to the default-path surface contract registry",
    )
    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate registry structure and print non-blocking warnings",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat rollout warnings as blocking failures",
    )
    args = parser.parse_args(argv)

    try:
        registry = load_registry(Path(args.config))
    except ValueError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        return 1

    warnings = warning_messages(registry)
    if warnings:
        print("Default-path surface contract warnings:")
        for warning in warnings:
            print(f"  - {warning}")
        if args.strict:
            return 1

    if args.validate_config or not warnings:
        print(f"Validated {len(registry.surfaces)} default-path surface contract(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
