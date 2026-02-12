"""
Tests for analysis pipeline quality and correctness.
Covers schema validation, prompt logic, truncation detection, and output structure.
"""

import json
import pytest
from pydantic import ValidationError

from qc_clean.schemas.analysis_schemas import (
    ThematicCode,
    CodeHierarchy,
    ParticipantProfile,
    SpeakerAnalysis,
    EntityRelationship,
    EntityMapping,
    AnalysisRecommendation,
    AnalysisSynthesis,
)


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestThematicCodeSchema:
    def test_valid_code(self):
        code = ThematicCode(
            id="AI_USAGE",
            name="AI Usage",
            description="How AI is used in research workflows.",
            semantic_definition="Any description of using AI tools.",
            parent_id=None,
            level=0,
            example_quotes=["I use AI for code debugging."],
            mention_count=5,
            discovery_confidence=0.7,
        )
        assert code.id == "AI_USAGE"
        assert code.mention_count == 5

    def test_confidence_range_low(self):
        """Confidence can go down to 0.0"""
        code = ThematicCode(
            id="WEAK",
            name="Weak theme",
            description="Barely mentioned.",
            semantic_definition="Tangential reference.",
            level=0,
            example_quotes=["maybe once"],
            mention_count=1,
            discovery_confidence=0.1,
        )
        assert code.discovery_confidence == 0.1

    def test_confidence_out_of_range_rejected(self):
        with pytest.raises(ValidationError):
            ThematicCode(
                id="BAD",
                name="Bad",
                description="x",
                semantic_definition="x",
                level=0,
                example_quotes=["x"],
                mention_count=1,
                discovery_confidence=1.5,
            )

    def test_missing_mention_count_rejected(self):
        with pytest.raises(ValidationError):
            ThematicCode(
                id="NO_COUNT",
                name="No count",
                description="x",
                semantic_definition="x",
                level=0,
                example_quotes=["x"],
                discovery_confidence=0.5,
            )


class TestCodeHierarchy:
    def test_valid_hierarchy(self):
        codes = [
            ThematicCode(
                id="TOP", name="Top", description="d", semantic_definition="s",
                level=0, example_quotes=["q"], mention_count=3, discovery_confidence=0.8,
            ),
            ThematicCode(
                id="SUB", name="Sub", description="d", semantic_definition="s",
                parent_id="TOP", level=1, example_quotes=["q"], mention_count=2,
                discovery_confidence=0.6,
            ),
        ]
        hierarchy = CodeHierarchy(codes=codes, total_codes=2, analysis_confidence=0.75)
        assert len(hierarchy.codes) == 2

    def test_empty_codes_accepted(self):
        hierarchy = CodeHierarchy(codes=[], total_codes=0, analysis_confidence=0.0)
        assert hierarchy.total_codes == 0


class TestSpeakerAnalysis:
    def test_single_speaker(self):
        profile = ParticipantProfile(
            name="Jane Doe",
            role="Director",
            characteristics=["methodologist", "pragmatic"],
            perspective_summary="Focuses on practical applications.",
            codes_emphasized=["AI_USAGE", "METHODS", "TRAINING"],
        )
        analysis = SpeakerAnalysis(
            participants=[profile],
            consensus_themes=["AI is useful for tedious tasks"],
            divergent_viewpoints=["Enthusiasm vs caution about trust"],
            perspective_mapping={"Jane Doe": ["AI_USAGE", "METHODS", "TRAINING"]},
        )
        assert len(analysis.participants) == 1
        assert len(analysis.perspective_mapping["Jane Doe"]) == 3

    def test_multi_speaker(self):
        p1 = ParticipantProfile(
            name="Alice", role="Researcher",
            characteristics=["quantitative"],
            perspective_summary="Favors AI.",
            codes_emphasized=["AI_CODE", "PRODUCTIVITY"],
        )
        p2 = ParticipantProfile(
            name="Bob", role="Manager",
            characteristics=["cautious"],
            perspective_summary="Worried about risks.",
            codes_emphasized=["AI_LIMITS", "POLICY"],
        )
        analysis = SpeakerAnalysis(
            participants=[p1, p2],
            consensus_themes=["Both agree AI saves time"],
            divergent_viewpoints=["Alice trusts AI more than Bob"],
            perspective_mapping={
                "Alice": ["AI_CODE", "PRODUCTIVITY"],
                "Bob": ["AI_LIMITS", "POLICY"],
            },
        )
        assert len(analysis.participants) == 2


class TestAnalysisSynthesis:
    def test_valid_synthesis(self):
        rec = AnalysisRecommendation(
            title="Run training sessions",
            description="Host monthly demos.",
            priority="high",
            supporting_themes=["ADOPTION"],
        )
        synthesis = AnalysisSynthesis(
            executive_summary="AI is used for practical tasks but has trust issues.",
            key_findings=["AI helps with code", "Citations can be fabricated"],
            cross_cutting_patterns=["Efficiency vs trust tradeoff"],
            actionable_recommendations=[rec],
            confidence_assessment={"AI_USAGE": {"level": "high", "score": 0.85, "evidence": "Multiple examples"}},
        )
        assert len(synthesis.actionable_recommendations) == 1
        assert synthesis.confidence_assessment["AI_USAGE"]["score"] == 0.85

    def test_confidence_as_dict_any(self):
        """confidence_assessment accepts rich objects (Dict[str, Any])"""
        synthesis = AnalysisSynthesis(
            executive_summary="Summary.",
            key_findings=["Finding"],
            cross_cutting_patterns=["Pattern"],
            actionable_recommendations=[],
            confidence_assessment={
                "theme1": {"level": "high", "score": 0.9, "evidence": "strong"},
                "theme2": {"level": "low", "score": 0.3, "evidence": "weak"},
            },
        )
        assert synthesis.confidence_assessment["theme2"]["level"] == "low"


# ---------------------------------------------------------------------------
# Truncation detection tests
# ---------------------------------------------------------------------------


class TestTruncationDetection:
    """Test the truncation detection logic from api_server._process_analysis"""

    @staticmethod
    def _detect_truncation(content: str) -> bool:
        """Replicate the truncation detection logic from api_server"""
        stripped = content.rstrip()
        if stripped and not stripped[-1] in '.!?"\')\n':
            return True
        return False

    def test_normal_sentence(self):
        assert not self._detect_truncation("This is a complete sentence.")

    def test_question_ending(self):
        assert not self._detect_truncation("Is this truncated?")

    def test_quote_ending(self):
        assert not self._detect_truncation('She said "hello."')

    def test_truncated_mid_sentence(self):
        assert self._detect_truncation("they have right hand man/woman and they")

    def test_truncated_mid_word(self):
        assert self._detect_truncation("I was going to say tha")

    def test_empty_content(self):
        assert not self._detect_truncation("")

    def test_whitespace_only(self):
        assert not self._detect_truncation("   \n  ")


# ---------------------------------------------------------------------------
# Single vs multi speaker prompt selection
# ---------------------------------------------------------------------------


class TestSpeakerModeDetection:

    def test_single_speaker_when_no_speakers_detected(self):
        """A single doc with no detected speakers is treated as single-speaker."""
        from qc_clean.schemas.domain import Document, Corpus
        corpus = Corpus(documents=[
            Document(name="test.txt", content="Some text.", detected_speakers=[]),
        ])
        all_speakers = [s for doc in corpus.documents for s in doc.detected_speakers]
        assert len(all_speakers) <= 1

    def test_multi_speaker_focus_group(self):
        """A single doc with multiple detected speakers is treated as multi-speaker."""
        from qc_clean.schemas.domain import Document, Corpus
        corpus = Corpus(documents=[
            Document(name="focus_group.txt", content="text",
                     detected_speakers=["Alice", "Bob", "Carol"]),
        ])
        all_speakers = [s for doc in corpus.documents for s in doc.detected_speakers]
        assert len(all_speakers) > 1

    def test_multiple_docs_multi_speaker(self):
        """Multiple docs with distinct speakers are multi-speaker."""
        from qc_clean.schemas.domain import Document, Corpus
        corpus = Corpus(documents=[
            Document(name="a.txt", content="A", detected_speakers=["Alice"]),
            Document(name="b.txt", content="B", detected_speakers=["Bob"]),
        ])
        all_speakers = []
        for doc in corpus.documents:
            for s in doc.detected_speakers:
                if s not in all_speakers:
                    all_speakers.append(s)
        assert len(all_speakers) > 1


# ---------------------------------------------------------------------------
# Output structure validation
# ---------------------------------------------------------------------------


class TestOutputStructure:
    """Validate the structure of actual analysis output files if they exist."""

    @pytest.fixture
    def v2_output(self):
        import os
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "output_analyses", "gpt5mini_v2_fixed.json",
        )
        if not os.path.exists(path):
            pytest.skip("v2 output file not found")
        with open(path) as f:
            return json.load(f)

    def test_has_required_top_level_keys(self, v2_output):
        results = v2_output["results"]
        required = [
            "analysis_summary", "total_interviews", "total_codes",
            "single_speaker_mode", "codes_identified", "speakers_identified",
            "key_relationships", "key_themes", "recommendations",
            "processing_time_seconds", "model_used",
        ]
        for key in required:
            assert key in results, f"Missing key: {key}"

    def test_codes_have_mention_count(self, v2_output):
        for code in v2_output["results"]["codes_identified"]:
            assert "mention_count" in code, f"Code {code['code']} missing mention_count"
            assert isinstance(code["mention_count"], int)

    def test_no_fake_frequency_field(self, v2_output):
        for code in v2_output["results"]["codes_identified"]:
            assert "frequency" not in code, f"Code {code['code']} still has old frequency field"

    def test_total_codes_matches_actual(self, v2_output):
        results = v2_output["results"]
        assert results["total_codes"] == len(results["codes_identified"])

    def test_data_warnings_present_for_truncated(self, v2_output):
        results = v2_output["results"]
        if "data_warnings" in results:
            assert any("truncated" in w for w in results["data_warnings"])

    def test_single_speaker_mode_set(self, v2_output):
        assert v2_output["results"]["single_speaker_mode"] is True

    def test_no_fabricated_percentages_in_themes(self, v2_output):
        for theme in v2_output["results"]["key_themes"]:
            assert "~" not in theme, f"Fabricated percentage found: {theme[:80]}"
            # Allow % only in direct quotes
            if "%" in theme and '"' not in theme and "'" not in theme:
                pytest.fail(f"Possible fabricated percentage: {theme[:80]}")

    def test_confidence_range_uses_lower_values(self, v2_output):
        confidences = [c["confidence"] for c in v2_output["results"]["codes_identified"]]
        assert min(confidences) < 0.75, f"Confidence floor too high: {min(confidences)}"

    def test_code_count_reasonable(self, v2_output):
        count = len(v2_output["results"]["codes_identified"])
        assert 5 <= count <= 25, f"Code count {count} outside reasonable range"
