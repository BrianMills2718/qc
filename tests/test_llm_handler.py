"""
Tests for LLM handler provider inference.
"""

import os
import pytest
from unittest.mock import patch

from qc_clean.core.llm.llm_handler import LLMHandler


class TestProviderInference:
    """Test _infer_api_key picks the right env var for each model."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-openai"}, clear=True)
    def test_gpt_model_uses_openai(self):
        assert LLMHandler._infer_api_key("gpt-5-mini") == "sk-openai"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-openai"}, clear=True)
    def test_o1_model_uses_openai(self):
        assert LLMHandler._infer_api_key("o1-preview") == "sk-openai"

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-anthropic"}, clear=True)
    def test_claude_model_uses_anthropic(self):
        assert LLMHandler._infer_api_key("claude-3-opus") == "sk-anthropic"

    @patch.dict(os.environ, {"GEMINI_API_KEY": "sk-gemini"}, clear=True)
    def test_gemini_model_uses_gemini(self):
        assert LLMHandler._infer_api_key("gemini-pro") == "sk-gemini"

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-anthropic"}, clear=True)
    def test_unknown_model_falls_back(self):
        """Unknown model tries each provider in order."""
        result = LLMHandler._infer_api_key("llama-3-70b")
        assert result == "sk-anthropic"

    @patch.dict(os.environ, {}, clear=True)
    def test_no_keys_returns_none(self):
        assert LLMHandler._infer_api_key("gpt-5-mini") is None
