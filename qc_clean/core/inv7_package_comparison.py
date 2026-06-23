"""Comparison reports for versioned INV-7 prompt-injection packages."""

from __future__ import annotations

from itertools import combinations
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from qc_clean.core.inv7_package import Inv7PromptInjectionPackage, load_inv7_prompt_injection_package


class Inv7GroupedSummary(BaseModel):
    """Grouped INV-7 outcome counts for one package."""

    model_config = ConfigDict(extra="forbid")

    total: int = Field(description="Number of fixture outcomes in this group")
    passed: int = Field(description="Number of fixture outcomes where the attack did not succeed")
    failed: int = Field(description="Number of fixture outcomes where the attack succeeded")
    pass_rate: float = Field(description="Passed divided by total")
    attack_success_rate: float = Field(description="Failed divided by total")
    failed_fixture_ids: list[str] = Field(description="Fixture IDs whose attacks succeeded")


class Inv7ComparedPackageSummary(BaseModel):
    """Per-package metrics inside an INV-7 comparison report."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(description="Package identifier from the INV-7 result package")
    source_path: str = Field(description="Input path used to load this package")
    mode: Literal["structural", "live_model"] = Field(description="Package execution mode")
    split: Literal["canary", "dev", "held_out", "public_comparator"] = Field(
        description="Evaluation split represented by the package"
    )
    fixture_set_id: str = Field(description="Fixture set identifier")
    fixture_set_version: str = Field(description="Fixture set version")
    prompt_frozen: bool = Field(description="Whether prompts were frozen before scoring")
    contamination_checked: bool = Field(description="Whether contamination checks were recorded")
    evaluator: str = Field(description="Package-level evaluator or harness name")
    model: str | None = Field(description="Live model name when mode is live_model")
    trace_id: str | None = Field(description="llm_client trace ID when mode is live_model")
    total_fixtures: int = Field(description="Total fixture outcomes in the package")
    passed: int = Field(description="Fixture outcomes where the attack did not succeed")
    failed: int = Field(description="Fixture outcomes where the attack succeeded")
    pass_rate: float = Field(description="Passed divided by total fixtures")
    attack_success_rate: float = Field(description="Failed divided by total fixtures")
    failed_fixture_ids: list[str] = Field(description="Fixture IDs whose attacks succeeded")
    by_surface: dict[str, Inv7GroupedSummary] = Field(description="Outcome counts grouped by prompt surface")
    by_attack_type: dict[str, Inv7GroupedSummary] = Field(description="Outcome counts grouped by attack class")


class Inv7PairwiseFixtureComparison(BaseModel):
    """Pairwise fixture-set comparison between two INV-7 packages."""

    model_config = ConfigDict(extra="forbid")

    left_package_id: str = Field(description="Package ID of the left comparison input")
    right_package_id: str = Field(description="Package ID of the right comparison input")
    shared_fixture_ids: list[str] = Field(description="Fixture IDs present in both packages")
    only_left_fixture_ids: list[str] = Field(description="Fixture IDs present only in the left package")
    only_right_fixture_ids: list[str] = Field(description="Fixture IDs present only in the right package")
    changed_attack_outcome_fixture_ids: list[str] = Field(
        description="Shared fixture IDs whose attack_succeeded values differ"
    )
    left_attack_success_rate: float = Field(description="Left package attack success rate")
    right_attack_success_rate: float = Field(description="Right package attack success rate")
    attack_success_rate_delta: float = Field(
        description="Right attack success rate minus left attack success rate"
    )


class Inv7PackageComparisonReport(BaseModel):
    """Machine-readable comparison report for INV-7 prompt-injection packages."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = Field(description="Comparison report schema version")
    package_type: Literal["inv7_package_comparison"] = Field(description="Report package type")
    status: Literal["compared"] = Field(description="Comparison status")
    package_count: int = Field(description="Number of compared INV-7 packages")
    compared_packages: list[Inv7ComparedPackageSummary] = Field(
        description="Per-package metrics in input order"
    )
    pairwise_fixture_comparisons: list[Inv7PairwiseFixtureComparison] = Field(
        description="Pairwise fixture overlap and changed-outcome diagnostics"
    )
    caution: str = Field(description="Claim-discipline caveat for interpreting the report")


def compare_inv7_package_files(package_paths: list[Path | str]) -> Inv7PackageComparisonReport:
    """Load validated INV-7 packages from paths and compare their outcomes."""
    if len(package_paths) < 2:
        raise ValueError("INV-7 package comparison requires at least two package files")

    loaded = [
        (str(path), load_inv7_prompt_injection_package(Path(path)))
        for path in package_paths
    ]
    return compare_inv7_packages(loaded)


def compare_inv7_packages(
    packages: list[tuple[str, Inv7PromptInjectionPackage]],
) -> Inv7PackageComparisonReport:
    """Compare already validated INV-7 packages."""
    if len(packages) < 2:
        raise ValueError("INV-7 package comparison requires at least two packages")

    compared = [_summarize_package(source_path, package) for source_path, package in packages]
    pairwise = [
        _pairwise_comparison(left, right)
        for left, right in combinations(packages, 2)
    ]
    return Inv7PackageComparisonReport(
        schema_version=1,
        package_type="inv7_package_comparison",
        status="compared",
        package_count=len(packages),
        compared_packages=compared,
        pairwise_fixture_comparisons=pairwise,
        caution=(
            "This report compares observed outcomes in supplied INV-7 packages only. "
            "It is not prompt-injection robustness proof, model-obedience proof, "
            "methodological-validity evidence, or SOTA evidence."
        ),
    )


def _summarize_package(
    source_path: str,
    package: Inv7PromptInjectionPackage,
) -> Inv7ComparedPackageSummary:
    """Summarize one INV-7 package for comparison output."""
    failed_fixture_ids = sorted(
        item.fixture_id
        for item in package.prompt_injection_evaluations
        if item.attack_succeeded
    )
    return Inv7ComparedPackageSummary(
        package_id=package.package_id,
        source_path=source_path,
        mode=package.mode,
        split=package.split,
        fixture_set_id=package.fixture_set_id,
        fixture_set_version=package.fixture_set_version,
        prompt_frozen=package.prompt_frozen,
        contamination_checked=package.contamination_checked,
        evaluator=package.evaluator,
        model=package.model,
        trace_id=package.trace_id,
        total_fixtures=package.total_fixtures,
        passed=package.passed,
        failed=package.failed,
        pass_rate=_safe_div(package.passed, package.total_fixtures),
        attack_success_rate=_safe_div(package.failed, package.total_fixtures),
        failed_fixture_ids=failed_fixture_ids,
        by_surface=_grouped_summary(package, group_field="surface"),
        by_attack_type=_grouped_summary(package, group_field="attack_type"),
    )


def _grouped_summary(
    package: Inv7PromptInjectionPackage,
    *,
    group_field: Literal["surface", "attack_type"],
) -> dict[str, Inv7GroupedSummary]:
    """Summarize outcomes for one package grouped by a fixture string field."""
    buckets: dict[str, dict[str, object]] = {}
    for item in package.prompt_injection_evaluations:
        key = getattr(item, group_field)
        bucket = buckets.setdefault(
            key,
            {"total": 0, "passed": 0, "failed": 0, "failed_fixture_ids": []},
        )
        bucket["total"] = int(bucket["total"]) + 1
        if item.attack_succeeded:
            bucket["failed"] = int(bucket["failed"]) + 1
            failed_fixture_ids = bucket["failed_fixture_ids"]
            if not isinstance(failed_fixture_ids, list):
                raise TypeError("INV-7 grouped summary failed_fixture_ids bucket must be a list")
            failed_fixture_ids.append(item.fixture_id)
        else:
            bucket["passed"] = int(bucket["passed"]) + 1

    return {
        key: Inv7GroupedSummary(
            total=int(bucket["total"]),
            passed=int(bucket["passed"]),
            failed=int(bucket["failed"]),
            pass_rate=_safe_div(int(bucket["passed"]), int(bucket["total"])),
            attack_success_rate=_safe_div(int(bucket["failed"]), int(bucket["total"])),
            failed_fixture_ids=sorted(str(item) for item in bucket["failed_fixture_ids"]),
        )
        for key, bucket in sorted(buckets.items())
    }


def _pairwise_comparison(
    left: tuple[str, Inv7PromptInjectionPackage],
    right: tuple[str, Inv7PromptInjectionPackage],
) -> Inv7PairwiseFixtureComparison:
    """Compare fixture identity and outcomes for two packages."""
    _, left_package = left
    _, right_package = right
    left_outcomes = {
        item.fixture_id: item.attack_succeeded
        for item in left_package.prompt_injection_evaluations
    }
    right_outcomes = {
        item.fixture_id: item.attack_succeeded
        for item in right_package.prompt_injection_evaluations
    }
    left_ids = set(left_outcomes)
    right_ids = set(right_outcomes)
    shared_ids = left_ids & right_ids
    changed = sorted(
        fixture_id
        for fixture_id in shared_ids
        if left_outcomes[fixture_id] != right_outcomes[fixture_id]
    )
    return Inv7PairwiseFixtureComparison(
        left_package_id=left_package.package_id,
        right_package_id=right_package.package_id,
        shared_fixture_ids=sorted(shared_ids),
        only_left_fixture_ids=sorted(left_ids - right_ids),
        only_right_fixture_ids=sorted(right_ids - left_ids),
        changed_attack_outcome_fixture_ids=changed,
        left_attack_success_rate=_safe_div(left_package.failed, left_package.total_fixtures),
        right_attack_success_rate=_safe_div(right_package.failed, right_package.total_fixtures),
        attack_success_rate_delta=(
            _safe_div(right_package.failed, right_package.total_fixtures)
            - _safe_div(left_package.failed, left_package.total_fixtures)
        ),
    )


def _safe_div(numerator: int, denominator: int) -> float:
    """Divide with a zero guard for defensive report construction."""
    if denominator == 0:
        return 0.0
    return numerator / denominator
