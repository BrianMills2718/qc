"""
Advanced Speaker Analysis using Sophisticated Schemas
Optional enhancement for rich speaker property discovery
"""
from typing import Dict, List, Any, Optional
import logging

try:
    from src.qc.extraction.code_first_schemas import SpeakerPropertySchema
    ADVANCED_SCHEMAS_AVAILABLE = True
except ImportError:
    ADVANCED_SCHEMAS_AVAILABLE = False

logger = logging.getLogger(__name__)

class AdvancedSpeakerAnalyzer:
    """Advanced speaker analysis using sophisticated src/ schemas"""
    
    def __init__(self, llm_handler):
        self.llm_handler = llm_handler
        self.available = ADVANCED_SCHEMAS_AVAILABLE
        
        if not self.available:
            logger.warning("Advanced speaker schemas not available - feature disabled")
    
    async def analyze_speaker_properties(
        self, 
        interview_text: str,
        interview_id: str = "unknown"
    ) -> Optional[Dict[str, Any]]:
        """Rich speaker property analysis"""
        
        if not self.available:
            return None
        
        try:
            prompt = self._build_speaker_analysis_prompt(interview_text, interview_id)
            result = await self.llm_handler.extract_structured(
                prompt=prompt,
                schema=SpeakerPropertySchema
            )
            
            return {
                "interview_id": interview_id,
                "speaker_properties": result.properties,
                "discovery_method": result.discovery_method,
                "confidence": result.extraction_confidence
            }
            
        except Exception as e:
            logger.error(f"Advanced speaker analysis failed: {e}")
            return None
    
    def _build_speaker_analysis_prompt(self, text: str, interview_id: str) -> str:
        """Build comprehensive speaker analysis prompt"""
        return f"""
You are an expert qualitative researcher analyzing speaker characteristics in interview data.

Interview ID: {interview_id}

Analyze this interview transcript and identify speaker properties:

{text}

Instructions:
1. Identify recurring speaker characteristics (roles, attitudes, expertise)
2. Note communication patterns and styles
3. Determine relationship dynamics between speakers
4. Extract demographic or contextual indicators
5. Assess confidence levels for each identified property

Focus on properties that help distinguish speakers and understand their perspectives.
"""