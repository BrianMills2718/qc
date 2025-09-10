"""
Enhanced Semantic Extractor with LLM Speaker Detection
Extends current SemanticExtractor with optional LLM capabilities
"""
import logging
from typing import Optional, Union, Dict, Any
from .semantic_extractor import SemanticExtractor
from core.speaker_detection.schema_bridge import SpeakerDetectionBridge
from core.speaker_detection.circuit_breaker import SpeakerDetectionCircuitBreaker

logger = logging.getLogger(__name__)

class EnhancedSemanticExtractor(SemanticExtractor):
    """Semantic extractor with optional LLM-based speaker detection"""
    
    def __init__(self, llm_handler=None, use_llm_speaker_detection=False):
        super().__init__(llm_handler)
        self.use_llm_detection = use_llm_speaker_detection
        
        if self.use_llm_detection and llm_handler:
            self.speaker_bridge = SpeakerDetectionBridge(llm_handler)
            self.circuit_breaker = SpeakerDetectionCircuitBreaker(
                failure_threshold=5,
                timeout_seconds=30
            )
        else:
            self.speaker_bridge = None
            self.circuit_breaker = None
        
        logger.info(f"EnhancedSemanticExtractor initialized - LLM detection: {self.use_llm_detection}")
    
    def get_name(self) -> str:
        return "enhanced_semantic"
    
    def get_version(self) -> str:
        return "3.0.0-llm-bridge"
    
    def get_description(self) -> str:
        mode = "LLM" if self.use_llm_detection else "regex"
        return f"Enhanced semantic extraction with {mode} speaker detection"
    
    async def _detect_speaker(self, text: str) -> Union[str, Dict[str, Any]]:
        """Hybrid speaker detection with transparent method reporting"""
        if self.use_llm_detection and self.speaker_bridge and self.circuit_breaker:
            # Check circuit breaker state for transparency
            cb_state = self.circuit_breaker.state
            if cb_state == "OPEN":
                print(f"WARNING: Circuit breaker OPEN - using regex fallback for {self.circuit_breaker.timeout_seconds}s")
                speaker = await self._detect_speaker_regex(text)
                print(f"FALLBACK: Detection used - Method: regex, Result: {speaker}")
                return {
                    'speaker_name': speaker,
                    'detection_method': 'regex_fallback',
                    'circuit_breaker_status': 'OPEN',
                    'reason': 'Circuit breaker protection active'
                }
            
            # Try LLM detection with circuit breaker
            try:
                speaker = await self.circuit_breaker.call_with_circuit_breaker(
                    self.speaker_bridge.detect_speaker_simple,
                    self._detect_speaker_regex,
                    text
                )
                
                # Determine which method was actually used
                if self.circuit_breaker.state == "OPEN":
                    method = 'regex_fallback'
                    print(f"FALLBACK: LLM failed, fallback used - Method: regex, Result: {speaker}")
                else:
                    method = 'llm'
                    print(f"LLM: Detection used - Method: llm, Result: {speaker}")
                
                return {
                    'speaker_name': speaker,
                    'detection_method': method,
                    'circuit_breaker_status': self.circuit_breaker.state,
                    'reason': 'Hybrid detection with circuit breaker'
                }
                
            except Exception as e:
                print(f"ERROR: Detection failed - Error: {e}")
                speaker = await self._detect_speaker_regex(text)
                print(f"EMERGENCY: Fallback used - Method: regex, Result: {speaker}")
                return {
                    'speaker_name': speaker,
                    'detection_method': 'regex_emergency',
                    'circuit_breaker_status': getattr(self.circuit_breaker, 'state', 'UNKNOWN'),
                    'reason': 'Emergency fallback due to exception'
                }
        else:
            # Pure regex mode with transparency
            speaker = await self._detect_speaker_regex(text)
            print(f"REGEX: Detection used - Method: regex, Result: {speaker}")
            return {
                'speaker_name': speaker,
                'detection_method': 'regex',
                'circuit_breaker_status': 'DISABLED',
                'reason': 'LLM detection disabled'
            }

    async def _detect_speaker_regex(self, text: str) -> Optional[str]:
        """Explicit regex implementation for fallback"""
        return super()._detect_speaker(text)