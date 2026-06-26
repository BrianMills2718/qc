"""Shared checks for reviewer-report authoritativeness."""

from __future__ import annotations

import re


PREVALENCE_PATTERN = re.compile(
    r"(?P<label>[*A-Za-z][*A-Za-z0-9 ,/&+'().:-]{3,140}?)"
    r"\s*:?\s+(?:appears|present)\s+in\s+"
    r"(?P<count>\d+)\s*/\s*(?P<total>\d+)\s+documents?",
    re.IGNORECASE,
)


def find_prevalence_conflicts(text: str) -> dict[str, list[str]]:
    """Find labels reported with incompatible X/Y document prevalence counts."""
    prevalence_counts: dict[str, set[str]] = {}
    for match in PREVALENCE_PATTERN.finditer(text):
        label = normalize_prevalence_label(match.group("label"))
        prevalence_counts.setdefault(label, set()).add(
            f"{match.group('count')}/{match.group('total')}"
        )
    return {
        label: sorted(counts)
        for label, counts in prevalence_counts.items()
        if len(counts) > 1
    }


def normalize_prevalence_label(label: str) -> str:
    """Normalize a Markdown prevalence label for conflict comparison."""
    compact = re.sub(r"[^a-z0-9]+", " ", label.lower().strip("*")).strip()
    return re.sub(r"\s+", " ", compact)
