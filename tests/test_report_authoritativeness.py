"""Tests for reviewer-report authoritativeness checks."""

from qc_clean.core.report_authoritativeness import find_prevalence_conflicts


def test_find_prevalence_conflicts_detects_markdown_bold_colon_form():
    conflicts = find_prevalence_conflicts(
        "- **Local actors and diaspora influence**: present in 2/3 documents.\n"
        "- **Local actors and diaspora influence**: present in 3/3 documents.\n"
    )

    assert conflicts == {
        "local actors and diaspora influence": ["2/3", "3/3"],
    }


def test_find_prevalence_conflicts_ignores_consistent_repeated_counts():
    conflicts = find_prevalence_conflicts(
        "- **Local actors**: present in 3/3 documents.\n"
        "- Local actors appears in 3/3 documents.\n"
    )

    assert conflicts == {}


def test_find_prevalence_conflicts_detects_anchored_application_evidence_form():
    conflicts = find_prevalence_conflicts(
        "- **Local actors**: anchored application evidence in 2/3 loaded documents.\n"
        "- **Local actors**: anchored application evidence in 3/3 loaded documents.\n"
    )

    assert conflicts == {
        "local actors": ["2/3", "3/3"],
    }
