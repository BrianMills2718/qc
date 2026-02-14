"""
Tests for the LLM handler (qc_clean.core.llm.llm_handler).

The handler is now a thin adapter over llm_client.acall_llm_structured.
Tests mock llm_client — no real API calls are made.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel, Field
from typing import List

from qc_clean.core.utils.error_handler import LLMError


# ---------------------------------------------------------------------------
# Test schemas
# ---------------------------------------------------------------------------

class SimpleSchema(BaseModel):
    name: str
    count: int


class NestedItem(BaseModel):
    label: str
    score: float = 0.0


class NestedSchema(BaseModel):
    title: str
    items: List[NestedItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_handler(model_name="gpt-5-mini", **kwargs):
    """Create an LLMHandler (no API key needed — llm_client handles keys)."""
    from qc_clean.core.llm.llm_handler import LLMHandler
    return LLMHandler(model_name=model_name, **kwargs)


def _mock_meta(cost=0.001):
    """Build a mock LLMCallResult for the meta return value."""
    meta = MagicMock()
    meta.cost = cost
    meta.usage = {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    return meta


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

class TestInit:
    def test_default_init(self):
        handler = _make_handler()
        assert handler.model_name == "gpt-5-mini"
        assert handler.temperature == 1.0
        assert handler.max_retries == 4
        assert handler.base_delay == 1.0
        assert handler.default_max_tokens is None

    def test_custom_params(self):
        handler = _make_handler(
            model_name="gpt-5-mini", temperature=0.5, max_retries=2, base_delay=0.5
        )
        assert handler.temperature == 0.5
        assert handler.max_retries == 2
        assert handler.base_delay == 0.5


# ---------------------------------------------------------------------------
# Config-based init
# ---------------------------------------------------------------------------

class TestConfigInit:
    def test_init_with_unified_config(self):
        from qc_clean.config.unified_config import UnifiedConfig
        cfg = UnifiedConfig(
            api_provider="openai",
            model_preference="gpt-5-mini",
            temperature=0.3,
            max_tokens=2000,
            max_llm_retries=3,
            base_retry_delay=0.5,
        )
        from qc_clean.core.llm.llm_handler import LLMHandler
        handler = LLMHandler(config=cfg)

        assert handler.model_name == "gpt-5-mini"
        assert handler.temperature == 0.3
        assert handler.default_max_tokens == 2000
        assert handler.max_retries == 3
        assert handler.base_delay == 0.5

    def test_init_with_grounded_theory_config(self):
        from qc_clean.config.methodology_config import GroundedTheoryConfig
        cfg = GroundedTheoryConfig(
            methodology="grounded_theory",
            theoretical_sensitivity="high",
            coding_depth="focused",
            memo_generation_frequency="each_phase",
            report_formats=["academic_report"],
            include_audit_trail=True,
            include_supporting_quotes=True,
            minimum_code_frequency=2,
            relationship_confidence_threshold=0.7,
            validation_level="standard",
            temperature=0.1,
            max_tokens=None,
            model_preference="gpt-5-mini",
            max_llm_retries=2,
        )
        from qc_clean.core.llm.llm_handler import LLMHandler
        handler = LLMHandler(config=cfg)

        assert handler.model_name == "gpt-5-mini"
        assert handler.max_retries == 2

    def test_config_without_retry_settings(self):
        """Config without max_llm_retries should use constructor defaults."""
        cfg = MagicMock()
        cfg.model_preference = "gpt-5-mini"
        cfg.temperature = 0.5
        cfg.max_tokens = None
        del cfg.max_llm_retries  # Simulate missing attribute
        del cfg.base_retry_delay

        from qc_clean.core.llm.llm_handler import LLMHandler
        handler = LLMHandler(config=cfg, max_retries=7, base_delay=2.0)

        assert handler.max_retries == 7
        assert handler.base_delay == 2.0


# ---------------------------------------------------------------------------
# extract_structured
# ---------------------------------------------------------------------------

class TestExtractStructured:
    def test_returns_validated_model(self):
        handler = _make_handler()
        parsed = SimpleSchema(name="Test", count=42)
        meta = _mock_meta()

        with patch(
            "qc_clean.core.llm.llm_handler.acall_llm_structured",
            new_callable=AsyncMock,
            return_value=(parsed, meta),
        ) as mock_call:
            result = asyncio.run(
                handler.extract_structured("Some text", SimpleSchema)
            )

        assert isinstance(result, SimpleSchema)
        assert result.name == "Test"
        assert result.count == 42
        mock_call.assert_called_once()

    def test_nested_schema(self):
        handler = _make_handler()
        parsed = NestedSchema(
            title="Report",
            items=[NestedItem(label="A", score=0.9), NestedItem(label="B", score=0.5)],
        )
        meta = _mock_meta()

        with patch(
            "qc_clean.core.llm.llm_handler.acall_llm_structured",
            new_callable=AsyncMock,
            return_value=(parsed, meta),
        ):
            result = asyncio.run(
                handler.extract_structured("Some text", NestedSchema)
            )

        assert result.title == "Report"
        assert len(result.items) == 2

    def test_temperature_passed_in_kwargs(self):
        handler = _make_handler(temperature=0.3)
        parsed = SimpleSchema(name="X", count=1)
        meta = _mock_meta()

        with patch(
            "qc_clean.core.llm.llm_handler.acall_llm_structured",
            new_callable=AsyncMock,
            return_value=(parsed, meta),
        ) as mock_call:
            asyncio.run(handler.extract_structured("text", SimpleSchema))

        _, kwargs = mock_call.call_args
        assert kwargs["temperature"] == 0.3

    def test_explicit_max_tokens(self):
        handler = _make_handler()
        parsed = SimpleSchema(name="X", count=1)
        meta = _mock_meta()

        with patch(
            "qc_clean.core.llm.llm_handler.acall_llm_structured",
            new_callable=AsyncMock,
            return_value=(parsed, meta),
        ) as mock_call:
            asyncio.run(
                handler.extract_structured("text", SimpleSchema, max_tokens=500)
            )

        _, kwargs = mock_call.call_args
        assert kwargs["max_tokens"] == 500

    def test_no_max_tokens_by_default(self):
        handler = _make_handler()
        parsed = SimpleSchema(name="X", count=1)
        meta = _mock_meta()

        with patch(
            "qc_clean.core.llm.llm_handler.acall_llm_structured",
            new_callable=AsyncMock,
            return_value=(parsed, meta),
        ) as mock_call:
            asyncio.run(handler.extract_structured("text", SimpleSchema))

        _, kwargs = mock_call.call_args
        assert "max_tokens" not in kwargs

    def test_instructions_appended_to_user_content(self):
        handler = _make_handler()
        parsed = SimpleSchema(name="X", count=1)
        meta = _mock_meta()

        with patch(
            "qc_clean.core.llm.llm_handler.acall_llm_structured",
            new_callable=AsyncMock,
            return_value=(parsed, meta),
        ) as mock_call:
            asyncio.run(
                handler.extract_structured(
                    "text", SimpleSchema, instructions="Be precise"
                )
            )

        args = mock_call.call_args[0]
        messages = args[1]
        user_content = messages[1]["content"]
        assert "Be precise" in user_content
        assert "ADDITIONAL INSTRUCTIONS" in user_content

    def test_system_prompt_present(self):
        handler = _make_handler()
        parsed = SimpleSchema(name="X", count=1)
        meta = _mock_meta()

        with patch(
            "qc_clean.core.llm.llm_handler.acall_llm_structured",
            new_callable=AsyncMock,
            return_value=(parsed, meta),
        ) as mock_call:
            asyncio.run(handler.extract_structured("text", SimpleSchema))

        args = mock_call.call_args[0]
        messages = args[1]
        assert messages[0]["role"] == "system"
        assert "structured information" in messages[0]["content"]

    def test_num_retries_and_base_delay_passed(self):
        handler = _make_handler(max_retries=6, base_delay=2.0)
        parsed = SimpleSchema(name="X", count=1)
        meta = _mock_meta()

        with patch(
            "qc_clean.core.llm.llm_handler.acall_llm_structured",
            new_callable=AsyncMock,
            return_value=(parsed, meta),
        ) as mock_call:
            asyncio.run(handler.extract_structured("text", SimpleSchema))

        _, kwargs = mock_call.call_args
        assert kwargs["num_retries"] == 6
        assert kwargs["base_delay"] == 2.0

    def test_response_model_passed(self):
        handler = _make_handler()
        parsed = SimpleSchema(name="X", count=1)
        meta = _mock_meta()

        with patch(
            "qc_clean.core.llm.llm_handler.acall_llm_structured",
            new_callable=AsyncMock,
            return_value=(parsed, meta),
        ) as mock_call:
            asyncio.run(handler.extract_structured("text", SimpleSchema))

        _, kwargs = mock_call.call_args
        assert kwargs["response_model"] is SimpleSchema

    def test_error_raises_llm_error(self):
        handler = _make_handler()

        with patch(
            "qc_clean.core.llm.llm_handler.acall_llm_structured",
            new_callable=AsyncMock,
            side_effect=Exception("API down"),
        ):
            with pytest.raises(LLMError, match="Failed to extract SimpleSchema"):
                asyncio.run(handler.extract_structured("text", SimpleSchema))

    def test_model_name_passed_as_first_arg(self):
        handler = _make_handler(model_name="claude-3-opus")
        parsed = SimpleSchema(name="X", count=1)
        meta = _mock_meta()

        with patch(
            "qc_clean.core.llm.llm_handler.acall_llm_structured",
            new_callable=AsyncMock,
            return_value=(parsed, meta),
        ) as mock_call:
            asyncio.run(handler.extract_structured("text", SimpleSchema))

        args = mock_call.call_args[0]
        assert args[0] == "claude-3-opus"
