"""
Tests for the LLM handler (qc_clean.core.llm.llm_handler).

All LiteLLM calls are mocked — no real API calls are made.
"""

import asyncio
import json
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

def _make_response(content):
    """Build a mock LiteLLM response with the given content dict or string."""
    if isinstance(content, dict):
        content = json.dumps(content)
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def _make_handler(model_name="gpt-5-mini", **kwargs):
    """Create an LLMHandler with a fake API key."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
        from qc_clean.core.llm.llm_handler import LLMHandler
        return LLMHandler(model_name=model_name, **kwargs)


# ---------------------------------------------------------------------------
# Init & API key inference
# ---------------------------------------------------------------------------

class TestInit:
    def test_default_init(self):
        handler = _make_handler()
        assert handler.model_name == "gpt-5-mini"
        assert handler.max_retries == 4
        assert handler.api_key == "sk-test-key"

    def test_custom_params(self):
        handler = _make_handler(model_name="gpt-5-mini", temperature=0.5, max_retries=2, base_delay=0.5)
        assert handler.temperature == 0.5
        assert handler.max_retries == 2
        assert handler.base_delay == 0.5

    def test_missing_api_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            from qc_clean.core.llm.llm_handler import LLMHandler
            with pytest.raises(ValueError, match="No API key"):
                LLMHandler(model_name="gpt-5-mini")


class TestInferApiKey:
    def _infer(self, model_name):
        from qc_clean.core.llm.llm_handler import LLMHandler
        return LLMHandler._infer_api_key(model_name)

    def test_gpt_model(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-openai"}):
            assert self._infer("gpt-5-mini") == "sk-openai"

    def test_o1_model(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-openai"}):
            assert self._infer("o1-preview") == "sk-openai"

    def test_o3_model(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-openai"}):
            assert self._infer("o3-mini") == "sk-openai"

    def test_openai_prefixed(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-openai"}):
            assert self._infer("openai/gpt-5") == "sk-openai"

    def test_claude_model(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant"}):
            assert self._infer("claude-3-opus") == "sk-ant"

    def test_anthropic_prefixed(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant"}):
            assert self._infer("anthropic/claude-3-opus") == "sk-ant"

    def test_gemini_model(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "gem-key"}):
            assert self._infer("gemini-2.5-flash") == "gem-key"

    def test_vertex_prefixed(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "gem-key"}):
            assert self._infer("vertex_ai/gemini-2.5-flash") == "gem-key"

    def test_unknown_model_fallback(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-fb"}, clear=True):
            assert self._infer("custom-model") == "sk-fb"

    def test_unknown_model_no_keys(self):
        with patch.dict("os.environ", {}, clear=True):
            assert self._infer("custom-model") is None


# ---------------------------------------------------------------------------
# Backoff & retry helpers
# ---------------------------------------------------------------------------

class TestBackoff:
    def test_delay_increases_exponentially(self):
        handler = _make_handler(base_delay=1.0)
        d0 = handler._calculate_backoff_delay(0)
        d1 = handler._calculate_backoff_delay(1)
        d2 = handler._calculate_backoff_delay(2)
        # Even with jitter, higher attempts should produce larger average ranges
        # d0 base=1, d1 base=2, d2 base=4
        assert 0.5 <= d0 <= 1.5
        assert 1.0 <= d1 <= 3.0
        assert 2.0 <= d2 <= 6.0

    def test_delay_capped_at_30(self):
        handler = _make_handler(base_delay=1.0)
        d = handler._calculate_backoff_delay(10)  # 2^10 = 1024
        assert d <= 30.0


class TestRetryableError:
    def setup_method(self):
        self.handler = _make_handler()

    def test_retryable_errors(self):
        retryable = [
            "HTTP 500 Internal Server Error",
            "Service unavailable",
            "Request timeout",
            "Rate limit exceeded",
            "Server overloaded",
            "Empty content returned",
            "No JSON found in response",
            "JSON parse error",
            "Expecting ',' delimiter",
        ]
        for msg in retryable:
            assert self.handler._is_retryable_error(Exception(msg)), f"Should be retryable: {msg}"

    def test_non_retryable_errors(self):
        non_retryable = [
            "Invalid API key",
            "Model not found",
            "Permission denied",
            "Quota exceeded",
        ]
        for msg in non_retryable:
            assert not self.handler._is_retryable_error(Exception(msg)), f"Should not be retryable: {msg}"


# ---------------------------------------------------------------------------
# extract_structured
# ---------------------------------------------------------------------------

class TestExtractStructured:
    def test_basic_extraction(self):
        handler = _make_handler()
        mock_resp = _make_response({"name": "Test", "count": 42})

        with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp):
            result = asyncio.run(
                handler.extract_structured("Some text", SimpleSchema)
            )

        assert isinstance(result, SimpleSchema)
        assert result.name == "Test"
        assert result.count == 42

    def test_nested_schema(self):
        handler = _make_handler()
        data = {"title": "Report", "items": [{"label": "A", "score": 0.9}, {"label": "B", "score": 0.5}]}
        mock_resp = _make_response(data)

        with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp):
            result = asyncio.run(
                handler.extract_structured("Some text", NestedSchema)
            )

        assert result.title == "Report"
        assert len(result.items) == 2
        assert result.items[0].label == "A"

    def test_string_json_response(self):
        """LLM can return content as a JSON string (most common)."""
        handler = _make_handler()
        mock_resp = _make_response(json.dumps({"name": "FromStr", "count": 7}))

        with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp):
            result = asyncio.run(
                handler.extract_structured("text", SimpleSchema)
            )

        assert result.name == "FromStr"

    def test_dict_response(self):
        """LLM can return content already parsed as a dict."""
        handler = _make_handler()
        msg = MagicMock()
        msg.content = {"name": "FromDict", "count": 3}
        choice = MagicMock()
        choice.message = msg
        resp = MagicMock()
        resp.choices = [choice]

        with patch("litellm.acompletion", new_callable=AsyncMock, return_value=resp):
            result = asyncio.run(
                handler.extract_structured("text", SimpleSchema)
            )

        assert result.name == "FromDict"

    def test_gpt5_skips_temperature(self):
        """GPT-5 models should not receive a temperature parameter."""
        handler = _make_handler(model_name="gpt-5-mini")

        mock_resp = _make_response({"name": "X", "count": 1})
        mock_acomp = AsyncMock(return_value=mock_resp)

        with patch("litellm.acompletion", mock_acomp):
            asyncio.run(
                handler.extract_structured("text", SimpleSchema)
            )

        call_kwargs = mock_acomp.call_args[1]
        assert "temperature" not in call_kwargs

    def test_non_gpt5_sends_temperature(self):
        """Non-GPT-5 models should include temperature."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant"}):
            from qc_clean.core.llm.llm_handler import LLMHandler
            handler = LLMHandler(model_name="claude-3-opus", temperature=0.2)

        mock_resp = _make_response({"name": "X", "count": 1})
        mock_acomp = AsyncMock(return_value=mock_resp)

        with patch("litellm.acompletion", mock_acomp):
            asyncio.run(
                handler.extract_structured("text", SimpleSchema)
            )

        call_kwargs = mock_acomp.call_args[1]
        assert call_kwargs["temperature"] == 0.2

    def test_explicit_max_tokens(self):
        handler = _make_handler()
        mock_resp = _make_response({"name": "X", "count": 1})
        mock_acomp = AsyncMock(return_value=mock_resp)

        with patch("litellm.acompletion", mock_acomp):
            asyncio.run(
                handler.extract_structured("text", SimpleSchema, max_tokens=500)
            )

        assert mock_acomp.call_args[1]["max_tokens"] == 500

    def test_no_max_tokens_by_default(self):
        handler = _make_handler()
        mock_resp = _make_response({"name": "X", "count": 1})
        mock_acomp = AsyncMock(return_value=mock_resp)

        with patch("litellm.acompletion", mock_acomp):
            asyncio.run(
                handler.extract_structured("text", SimpleSchema)
            )

        assert "max_tokens" not in mock_acomp.call_args[1]

    def test_json_mode_requested(self):
        handler = _make_handler()
        mock_resp = _make_response({"name": "X", "count": 1})
        mock_acomp = AsyncMock(return_value=mock_resp)

        with patch("litellm.acompletion", mock_acomp):
            asyncio.run(
                handler.extract_structured("text", SimpleSchema)
            )

        assert mock_acomp.call_args[1]["response_format"] == {"type": "json_object"}

    def test_instructions_included_in_prompt(self):
        handler = _make_handler()
        mock_resp = _make_response({"name": "X", "count": 1})
        mock_acomp = AsyncMock(return_value=mock_resp)

        with patch("litellm.acompletion", mock_acomp):
            asyncio.run(
                handler.extract_structured("text", SimpleSchema, instructions="Be precise")
            )

        messages = mock_acomp.call_args[1]["messages"]
        user_prompt = messages[1]["content"]
        assert "Be precise" in user_prompt

    def test_empty_response_raises(self):
        handler = _make_handler(max_retries=0)
        resp = MagicMock()
        resp.choices = []

        with patch("litellm.acompletion", new_callable=AsyncMock, return_value=resp):
            with pytest.raises(LLMError, match="Failed to extract"):
                asyncio.run(
                    handler.extract_structured("text", SimpleSchema)
                )

    def test_empty_content_raises(self):
        handler = _make_handler(max_retries=0)
        msg = MagicMock()
        msg.content = None
        choice = MagicMock()
        choice.message = msg
        resp = MagicMock()
        resp.choices = [choice]

        with patch("litellm.acompletion", new_callable=AsyncMock, return_value=resp):
            with pytest.raises(LLMError, match="Failed to extract"):
                asyncio.run(
                    handler.extract_structured("text", SimpleSchema)
                )

    def test_invalid_json_raises(self):
        handler = _make_handler(max_retries=0)
        msg = MagicMock()
        msg.content = "not valid json {{"
        choice = MagicMock()
        choice.message = msg
        resp = MagicMock()
        resp.choices = [choice]

        with patch("litellm.acompletion", new_callable=AsyncMock, return_value=resp):
            with pytest.raises(LLMError):
                asyncio.run(
                    handler.extract_structured("text", SimpleSchema)
                )


# ---------------------------------------------------------------------------
# Retry logic
# ---------------------------------------------------------------------------

class TestRetryLogic:
    def test_retries_on_retryable_error(self):
        handler = _make_handler(max_retries=2, base_delay=0.01)
        good_resp = _make_response({"name": "OK", "count": 1})

        call_count = 0

        async def flaky_call(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("HTTP 500 Internal Server Error")
            return good_resp

        with patch("litellm.acompletion", side_effect=flaky_call):
            result = asyncio.run(
                handler.extract_structured("text", SimpleSchema)
            )

        assert result.name == "OK"
        assert call_count == 3  # 2 failures + 1 success

    def test_no_retry_on_non_retryable_error(self):
        handler = _make_handler(max_retries=3, base_delay=0.01)
        call_count = 0

        async def fatal_call(**kwargs):
            nonlocal call_count
            call_count += 1
            raise Exception("Invalid API key")

        with patch("litellm.acompletion", side_effect=fatal_call):
            with pytest.raises(LLMError):
                asyncio.run(
                    handler.extract_structured("text", SimpleSchema)
                )

        assert call_count == 1  # No retries

    def test_exhausts_retries(self):
        handler = _make_handler(max_retries=2, base_delay=0.01)
        call_count = 0

        async def always_fail(**kwargs):
            nonlocal call_count
            call_count += 1
            raise Exception("HTTP 500 keeps failing")

        with patch("litellm.acompletion", side_effect=always_fail):
            with pytest.raises(LLMError, match="Failed to extract"):
                asyncio.run(
                    handler.extract_structured("text", SimpleSchema)
                )

        assert call_count == 3  # initial + 2 retries


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

class TestPromptBuilding:
    def test_schema_info_in_prompt(self):
        handler = _make_handler()
        prompt = handler._build_extraction_prompt("input text", SimpleSchema)
        assert "SimpleSchema" in prompt
        assert "name" in prompt
        assert "count" in prompt
        assert "input text" in prompt

    def test_instructions_in_prompt(self):
        handler = _make_handler()
        prompt = handler._build_extraction_prompt("input", SimpleSchema, instructions="Focus on quality")
        assert "Focus on quality" in prompt

    def test_nested_schema_info(self):
        handler = _make_handler()
        info = handler._format_schema_for_prompt(NestedSchema)
        assert "NestedSchema" in info
        assert "title" in info
        assert "items" in info


# ---------------------------------------------------------------------------
# Config-based init
# ---------------------------------------------------------------------------

class TestConfigInit:
    def test_init_with_unified_config(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
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
        # GT config has no api_provider attr, defaults to 'google' -> GEMINI_API_KEY
        with patch.dict("os.environ", {"GEMINI_API_KEY": "gem-test"}):
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
