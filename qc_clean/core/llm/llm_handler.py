"""LLM Handler — thin adapter over llm_client for QC-specific concerns."""

import logging
from typing import Optional, Type

from pydantic import BaseModel

from llm_client import acall_llm_structured
from qc_clean.core.utils.error_handler import LLMError

logger = logging.getLogger(__name__)


class LLMHandler:
    """Thin adapter over llm_client.acall_llm_structured.

    Handles QC-specific concerns:
    - UnifiedConfig / GroundedTheoryConfig → model/temperature extraction
    - LLMError wrapping (QC error type)
    - System prompt for structured extraction
    - QC-specific logging format
    """

    def __init__(
        self,
        model_name: str = "gpt-5-mini",
        temperature: float = 1.0,
        config=None,
        max_retries: int = 4,
        base_delay: float = 1.0,
    ):
        if config:
            self.model_name = config.model_preference
            self.temperature = config.temperature
            self.max_retries = getattr(config, "max_llm_retries", max_retries)
            self.base_delay = getattr(config, "base_retry_delay", base_delay)
        else:
            self.model_name = model_name
            self.temperature = temperature
            self.max_retries = max_retries
            self.base_delay = base_delay
        self.default_max_tokens = getattr(config, "max_tokens", None) if config else None

    async def extract_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        instructions: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> BaseModel:
        """Extract structured data from text using LLM.

        Args:
            prompt: The prompt/text to process
            schema: Pydantic model class for the expected output
            instructions: Additional instructions for extraction
            max_tokens: Maximum tokens (None = use maximum available)

        Returns:
            Validated instance of the schema model
        """
        user_content = prompt
        if instructions:
            user_content += f"\n\nADDITIONAL INSTRUCTIONS:\n{instructions}"

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert at extracting structured information from text. "
                    "Return your response as valid JSON that matches the provided schema."
                ),
            },
            {"role": "user", "content": user_content},
        ]

        kwargs = {"temperature": self.temperature}
        effective_max_tokens = max_tokens or self.default_max_tokens
        if effective_max_tokens:
            kwargs["max_tokens"] = effective_max_tokens

        logger.info(
            "LLM call: model=%s, schema=%s, prompt_len=%d",
            self.model_name,
            schema.__name__,
            len(prompt),
        )
        try:
            result, meta = await acall_llm_structured(
                self.model_name,
                messages,
                response_model=schema,
                num_retries=self.max_retries,
                base_delay=self.base_delay,
                **kwargs,
            )
            logger.info(
                "LLM response: model=%s, schema=%s, cost=$%.6f, tokens=%s",
                self.model_name,
                schema.__name__,
                meta.cost,
                meta.usage,
            )
            return result
        except Exception as e:
            logger.error(
                "Structured extraction failed: model=%s, schema=%s, error=%s",
                self.model_name,
                schema.__name__,
                e,
            )
            raise LLMError(f"Failed to extract {schema.__name__}: {e}") from e
