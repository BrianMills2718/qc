"""
Schema Bridge for LLM Speaker Detection
Bridges src/ sophisticated schemas to qc_clean/ architecture
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

# Import sophisticated schemas from src/
try:
    from src.qc.extraction.code_first_schemas import (
        SpeakerPropertySchema,
        DiscoveredSpeakerProperty,
        QuotesAndSpeakers
    )
    SOPHISTICATED_SCHEMAS_AVAILABLE = True
except ImportError:
    SOPHISTICATED_SCHEMAS_AVAILABLE = False
    # Fallback lightweight schemas
    class SpeakerPropertySchema(BaseModel):
        properties: List[Dict[str, Any]] = []
        discovery_method: str = "fallback"
        extraction_confidence: float = 0.0

class SimpleSpeakerResult(BaseModel):
    """Fixed schema based on actual LLM response format"""
    speaker_name: Optional[str] = None
    confidence: Optional[float] = 0.8  # Allow None - LLM may return None
    detection_method: Optional[str] = "llm"  # Allow None - LLM may return None

class SpeakerDetectionBridge:
    """Bridge between sophisticated src/ and simple qc_clean/ speaker detection"""
    
    def __init__(self, llm_handler):
        self.llm_handler = llm_handler
        self.schemas_available = SOPHISTICATED_SCHEMAS_AVAILABLE
    
    async def detect_speaker_simple(self, text: str) -> Optional[str]:
        """Simple interface matching current regex approach"""
        try:
            prompt = self._build_simple_speaker_prompt(text)
            result = await self.llm_handler.extract_structured(
                prompt=prompt,
                schema=SimpleSpeakerResult
            )
            return result.speaker_name
        except Exception as e:
            # Critical: Don't hide errors, but log for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"LLM speaker detection failed: {e}")
            raise  # Re-raise for fail-fast behavior
    
    def _build_simple_speaker_prompt(self, text: str) -> str:
        """Build prompt for simple speaker detection with structured JSON output"""
        return f"""
You are an expert at identifying speakers in interview transcripts.

Analyze this text and identify who is speaking: "{text}"

Return a JSON object with exactly this format:
{{"speaker_name": "detected_name_or_null", "confidence": 0.8, "detection_method": "llm"}}

Rules:
1. If text starts with "Name:" set speaker_name to that name
2. If text contains "Name said" set speaker_name to that name  
3. If first person ("I", "We") set speaker_name to "Participant"
4. If unclear, set speaker_name to null
5. Set confidence between 0.0 and 1.0 based on your certainty
6. Always set detection_method to "llm"

Return only the JSON object, no other text.
"""