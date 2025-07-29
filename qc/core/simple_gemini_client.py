#!/usr/bin/env python3
"""
Simple Gemini 2.5 Flash Client for Qualitative Coding Extraction

NO artificial limits, NO unnecessary chunking, FULL observability.
Uses Gemini 2.5 Flash's massive context window and structured output capabilities.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import uuid
from dataclasses import dataclass, asdict

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai
from google.generativeai import types
from pydantic import BaseModel, Field
from qc.core.error_recovery import DataFixer


# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class StructuredLogger:
    """JSON-structured logging for complete observability"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
    def log(self, level: str, event: str, **kwargs):
        """Log with structured data"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'event': event,
            'trace_id': kwargs.pop('trace_id', str(uuid.uuid4())),
            **kwargs
        }
        self.logger.log(
            getattr(logging, level.upper()),
            json.dumps(log_entry)
        )


logger = StructuredLogger(__name__)


@dataclass
class ExtractionMetrics:
    """Metrics for extraction performance"""
    trace_id: str
    interview_id: str
    model: str
    prompt_tokens: int
    response_tokens: int
    total_tokens: int
    duration_ms: float
    success: bool
    entities_count: int = 0
    codes_count: int = 0
    relationships_count: int = 0
    error: Optional[str] = None


class SimpleGeminiClient:
    """
    Simple, direct Gemini 2.5 Flash extractor.
    No chunking, no artificial limits, full observability.
    """
    
    def __init__(self, debug_dir: Optional[Path] = None):
        """
        Initialize Gemini client with environment configuration.
        
        Args:
            debug_dir: Directory to save all responses for debugging
        """
        # Get configuration from environment
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
            
        # Model configuration from environment
        self.model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        
        # Initialize client
        genai.configure(api_key=self.api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel(self.model_name)
        
        # Generation config - NO artificial limits!
        self.generation_config = genai.GenerationConfig(
            temperature=float(os.getenv('GEMINI_TEMPERATURE', '0.0')),
            max_output_tokens=int(os.getenv('GEMINI_MAX_OUTPUT_TOKENS', '60000')),  # Use full capacity!
            response_mime_type='application/json'  # Force JSON output
        )
        
        # Debug directory for saving ALL responses
        self.debug_dir = debug_dir or Path('debug_responses')
        self.debug_dir.mkdir(exist_ok=True)
        
        # Initialize data fixer for JSON repair
        self.data_fixer = DataFixer()
        
        logger.log('info', 'Initialized SimpleGeminiClient',
                  model=self.model_name,
                  max_output_tokens=self.generation_config.max_output_tokens,
                  debug_dir=str(self.debug_dir))
    
    async def generate_text(self, prompt: str, temperature: float = 0.1, 
                          max_tokens: int = 2000) -> str:
        """Simple text generation without JSON structure."""
        try:
            config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            
            response = self.model.generate_content(
                contents=prompt,
                generation_config=config
            )
            
            return response.text.strip() if response.text else ""
        except Exception as e:
            logger.log('error', 'text_generation_failed', error=str(e))
            return ""
    
    async def extract_themes(self,
                           prompt: str,
                           generation_config: Optional[Dict[str, Any]] = None,
                           max_retries: int = 3) -> Dict[str, Any]:
        """
        General-purpose theme extraction with custom prompts and configs.
        
        Args:
            prompt: The complete prompt to send to Gemini
            generation_config: Optional custom generation config
            max_retries: Number of retries on failure
            
        Returns:
            Extracted data as dict or JSON string
        """
        trace_id = str(uuid.uuid4())
        
        # Use provided config or defaults
        config = generation_config or {
            'temperature': self.generation_config.temperature,
            'max_output_tokens': self.generation_config.max_output_tokens,
            'response_mime_type': 'application/json'
        }
        
        # Create config copy for logging (without non-serializable response_schema)
        log_config = {k: v for k, v in config.items() if k != 'response_schema'}
        if 'response_schema' in config:
            log_config['response_schema'] = str(config['response_schema'].__name__ if hasattr(config['response_schema'], '__name__') else 'Schema')
        
        logger.log('info', 'theme_extraction_started',
                  trace_id=trace_id,
                  prompt_length=len(prompt),
                  config=log_config)
        
        for attempt in range(max_retries):
            try:
                # Build GenerationConfig
                if 'response_schema' in config:
                    schema = config.pop('response_schema')
                    gemini_config = genai.GenerationConfig(
                        temperature=config.get('temperature', 0.0),
                        max_output_tokens=config.get('max_output_tokens', 60000),
                        response_mime_type=config.get('response_mime_type', 'application/json'),
                        response_schema=schema
                    )
                else:
                    gemini_config = genai.GenerationConfig(**config)
                
                # Make the API call
                response = self.model.generate_content(
                    contents=prompt,
                    generation_config=gemini_config
                )
                
                # Save original config for later checks
                original_config = dict(config)
                
                # Handle structured response - Gemini's structured output
                if 'response_schema' in original_config and hasattr(response, 'parsed') and response.parsed:
                    # With structured output, response.parsed is already a Pydantic model
                    logger.log('info', 'using_structured_response',
                              trace_id=trace_id,
                              parsed_type=type(response.parsed).__name__)
                    return response.parsed.model_dump()
                else:
                    # Check response mime type
                    text = response.text.strip() if response.text else ""
                    
                    # Check for empty response
                    if not text:
                        logger.log('warning', 'empty_response_received',
                                  trace_id=trace_id,
                                  attempt=attempt + 1)
                        if attempt < max_retries - 1:
                            # Retry with a shorter prompt
                            logger.log('info', 'retrying_with_shorter_prompt', trace_id=trace_id)
                            continue
                        else:
                            # Return empty structure on final attempt
                            return {"quotes": []} if "quote" in prompt.lower() else {}
                    
                    if original_config.get('response_mime_type') == 'text/plain':
                        # Return plain text as-is
                        logger.log('info', 'returning_plain_text',
                                  trace_id=trace_id,
                                  response_length=len(text))
                        return text
                    else:
                        # Fallback: Parse JSON response, handling markdown code blocks
                        logger.log('info', 'parsing_json_response',
                                  trace_id=trace_id,
                                  response_length=len(text))
                        
                        # Remove markdown code block if present
                        if text.startswith('```json'):
                            text = text[7:]  # Remove ```json
                        elif text.startswith('```'):
                            text = text[3:]  # Remove ```
                        
                        if text.endswith('```'):
                            text = text[:-3]  # Remove trailing ```
                        
                        # Additional cleanup for common JSON issues
                        text = text.strip()
                        
                        # Try to repair JSON if needed
                        try:
                            return json.loads(text)
                        except json.JSONDecodeError as e:
                            logger.log('warning', 'attempting_json_repair',
                                      trace_id=trace_id,
                                      error=str(e))
                            # Attempt to repair the JSON
                            repaired_text = self.data_fixer.repair_json_string(text)
                            return json.loads(repaired_text)
                    
            except Exception as e:
                logger.log('error', 'theme_extraction_error',
                          trace_id=trace_id,
                          attempt=attempt + 1,
                          error=str(e))
                
                if attempt == max_retries - 1:
                    raise
        
        raise Exception(f"Failed after {max_retries} attempts")
    
    async def extract(self,
                     interview_text: str,
                     schema: BaseModel,
                     interview_id: Optional[str] = None,
                     max_retries: int = 3) -> Dict[str, Any]:
        """
        Extract entities and codes from interview using Gemini 2.5 Flash.
        
        NO CHUNKING - uses full context window
        NO TRUNCATION - sends complete interview
        FULL OBSERVABILITY - saves all responses
        
        Args:
            interview_text: Complete interview text
            schema: Pydantic model defining expected output structure
            interview_id: Identifier for tracking
            max_retries: Number of retries on failure
            
        Returns:
            Extracted data matching schema
            
        Raises:
            Exception: If all retries fail
        """
        trace_id = str(uuid.uuid4())
        interview_id = interview_id or f"interview_{trace_id[:8]}"
        
        # Track metrics
        metrics = ExtractionMetrics(
            trace_id=trace_id,
            interview_id=interview_id,
            model=self.model_name,
            prompt_tokens=0,
            response_tokens=0,
            total_tokens=0,
            duration_ms=0,
            success=False
        )
        
        # Log extraction start
        logger.log('info', 'extraction_started',
                  trace_id=trace_id,
                  interview_id=interview_id,
                  text_length=len(interview_text),
                  text_preview=interview_text[:200] + '...' if len(interview_text) > 200 else interview_text)
        
        # Build clear, direct prompt
        prompt = f"""Extract ALL entities, relationships, and thematic codes from this interview.

CRITICAL INSTRUCTIONS:
1. Output ONLY valid JSON - no explanations, no markdown, no comments
2. Extract EVERY entity mentioned (people, organizations, methods, tools, concepts)
3. Extract ALL relationships between entities
4. Identify ALL thematic codes with supporting quotes
5. Include confidence scores for each extraction

Interview Text:
{interview_text}

Output JSON matching this exact structure:
{schema.model_json_schema()}
"""
        
        # Count prompt tokens (approximate)
        metrics.prompt_tokens = len(prompt) // 4  # ~4 chars per token
        
        for attempt in range(max_retries):
            try:
                logger.log('info', 'extraction_attempt',
                          trace_id=trace_id,
                          attempt=attempt + 1,
                          max_retries=max_retries)
                
                # Time the API call
                start_time = datetime.utcnow()
                
                # Make the API call with structured output
                response = self.model.generate_content(
                    prompt,
                    generation_config=self.generation_config
                )
                
                # Calculate duration
                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                metrics.duration_ms = duration_ms
                
                # ALWAYS save raw response for debugging
                debug_file = self.debug_dir / f"{interview_id}_attempt{attempt + 1}_{trace_id}.json"
                debug_data = {
                    'trace_id': trace_id,
                    'interview_id': interview_id,
                    'attempt': attempt + 1,
                    'timestamp': datetime.utcnow().isoformat(),
                    'model': self.model_name,
                    'prompt_length': len(prompt),
                    'response_text': response.text,
                    'duration_ms': duration_ms
                }
                debug_file.write_text(json.dumps(debug_data, indent=2), encoding='utf-8')
                
                # Count response tokens (approximate)
                metrics.response_tokens = len(response.text) // 4
                metrics.total_tokens = metrics.prompt_tokens + metrics.response_tokens
                
                # Log token usage
                logger.log('info', 'token_usage',
                          trace_id=trace_id,
                          prompt_tokens=metrics.prompt_tokens,
                          response_tokens=metrics.response_tokens,
                          total_tokens=metrics.total_tokens,
                          duration_ms=duration_ms)
                
                # Use the parsed response directly (Pydantic model)
                if response.parsed:
                    result = response.parsed.model_dump()
                    
                    # Update metrics with extraction counts
                    metrics.entities_count = len(result.get('entities', []))
                    metrics.codes_count = len(result.get('codes', []))
                    metrics.relationships_count = len(result.get('relationships', []))
                    metrics.success = True
                    
                    logger.log('info', 'extraction_success',
                              trace_id=trace_id,
                              entities=metrics.entities_count,
                              codes=metrics.codes_count,
                              relationships=metrics.relationships_count,
                              debug_file=str(debug_file))
                    
                    # Save metrics
                    self._save_metrics(metrics)
                    
                    return result
                else:
                    # If parsing failed, try to extract JSON manually
                    logger.log('warning', 'pydantic_parse_failed',
                              trace_id=trace_id,
                              attempting_manual_parse=True)
                    
                    result = json.loads(response.text)
                    
                    # Validate against schema manually
                    validated = schema.model_validate(result)
                    result = validated.model_dump()
                    
                    # Update metrics
                    metrics.entities_count = len(result.get('entities', []))
                    metrics.codes_count = len(result.get('codes', []))
                    metrics.relationships_count = len(result.get('relationships', []))
                    metrics.success = True
                    
                    logger.log('info', 'manual_parse_success',
                              trace_id=trace_id,
                              entities=metrics.entities_count,
                              codes=metrics.codes_count,
                              relationships=metrics.relationships_count)
                    
                    self._save_metrics(metrics)
                    return result
                    
            except json.JSONDecodeError as e:
                metrics.error = f"JSON parse error: {str(e)}"
                logger.log('warning', 'json_parse_error',
                          trace_id=trace_id,
                          attempt=attempt + 1,
                          error=str(e),
                          response_preview=response.text[:500] if 'response' in locals() else 'No response')
                
                # On last attempt, try to extract JSON from text
                if attempt == max_retries - 1:
                    extracted = self._extract_json_from_text(response.text if 'response' in locals() else '')
                    if extracted:
                        logger.log('info', 'json_recovery_success', trace_id=trace_id)
                        metrics.success = True
                        self._save_metrics(metrics)
                        return extracted
                        
            except Exception as e:
                metrics.error = f"{type(e).__name__}: {str(e)}"
                logger.log('error', 'extraction_error',
                          trace_id=trace_id,
                          attempt=attempt + 1,
                          error_type=type(e).__name__,
                          error_message=str(e))
                
                if attempt == max_retries - 1:
                    # Save error details
                    error_file = self.debug_dir / f"{interview_id}_error_{trace_id}.json"
                    error_data = {
                        'trace_id': trace_id,
                        'interview_id': interview_id,
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'attempts': max_retries,
                        'timestamp': datetime.utcnow().isoformat(),
                        'metrics': asdict(metrics)
                    }
                    error_file.write_text(json.dumps(error_data, indent=2))
                    
                    self._save_metrics(metrics)
                    raise
        
        # All attempts failed
        metrics.error = f"All {max_retries} attempts failed"
        self._save_metrics(metrics)
        
        logger.log('error', 'all_attempts_failed',
                  trace_id=trace_id,
                  max_retries=max_retries,
                  debug_dir=str(self.debug_dir))
        
        raise Exception(f"Failed to extract after {max_retries} attempts. "
                       f"Check debug files in {self.debug_dir} for trace_id: {trace_id}")
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Try to extract JSON from text that might have extra content"""
        import re
        
        # Try to find JSON object
        patterns = [
            r'\{.*\}',  # Standard JSON object
            r'```json\s*(\{.*?\})\s*```',  # Markdown code block
            r'```\s*(\{.*?\})\s*```',  # Generic code block
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    json_str = match.group(1) if '(' in pattern else match.group()
                    return json.loads(json_str)
                except:
                    continue
        
        return None
    
    def _save_metrics(self, metrics: ExtractionMetrics):
        """Save extraction metrics for analysis"""
        metrics_file = self.debug_dir / 'extraction_metrics.jsonl'
        
        with open(metrics_file, 'a') as f:
            f.write(json.dumps(asdict(metrics)) + '\n')
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all extraction metrics"""
        metrics_file = self.debug_dir / 'extraction_metrics.jsonl'
        
        if not metrics_file.exists():
            return {"message": "No metrics found"}
        
        metrics = []
        with open(metrics_file, 'r') as f:
            for line in f:
                metrics.append(json.loads(line))
        
        if not metrics:
            return {"message": "No metrics found"}
        
        # Calculate summary statistics
        total_extractions = len(metrics)
        successful = sum(1 for m in metrics if m['success'])
        failed = total_extractions - successful
        
        avg_duration = sum(m['duration_ms'] for m in metrics) / total_extractions
        avg_tokens = sum(m['total_tokens'] for m in metrics) / total_extractions
        
        total_entities = sum(m['entities_count'] for m in metrics)
        total_codes = sum(m['codes_count'] for m in metrics)
        total_relationships = sum(m['relationships_count'] for m in metrics)
        
        return {
            'total_extractions': total_extractions,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total_extractions) * 100,
            'avg_duration_ms': avg_duration,
            'avg_total_tokens': avg_tokens,
            'total_entities_extracted': total_entities,
            'total_codes_extracted': total_codes,
            'total_relationships_extracted': total_relationships,
            'avg_entities_per_interview': total_entities / successful if successful > 0 else 0,
            'avg_codes_per_interview': total_codes / successful if successful > 0 else 0,
            'avg_relationships_per_interview': total_relationships / successful if successful > 0 else 0
        }


# Example Pydantic schemas for qualitative coding
class Entity(BaseModel):
    """An entity mentioned in the interview"""
    name: str = Field(description="The name of the entity")
    type: str = Field(description="Type of entity: Person, Organization, Method, Tool, Concept")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")
    confidence: float = Field(ge=0, le=1, description="Confidence score 0-1")


class Relationship(BaseModel):
    """A relationship between entities"""
    source_entity: str = Field(description="Name of source entity")
    target_entity: str = Field(description="Name of target entity")
    relationship_type: str = Field(description="Type of relationship")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")
    confidence: float = Field(ge=0, le=1, description="Confidence score 0-1")


class CodeInstance(BaseModel):
    """A single instance of a code with its quote"""
    quote: str = Field(description="The exact quote from the interview")
    speaker: Optional[str] = Field(default=None, description="Who said this (if identifiable)")
    context: Optional[str] = Field(default=None, description="Additional context around the quote")
    start_position: Optional[int] = Field(default=None, description="Character position where quote starts")
    end_position: Optional[int] = Field(default=None, description="Character position where quote ends")


class Code(BaseModel):
    """A thematic code identified in the interview"""
    name: str = Field(description="Name of the code")
    description: str = Field(description="What this code represents")
    instances: List[CodeInstance] = Field(description="All instances of this code")
    confidence: float = Field(ge=0, le=1, description="Overall confidence score 0-1")


class ExtractionResult(BaseModel):
    """Complete extraction result from an interview"""
    entities: List[Entity] = Field(description="All entities found")
    relationships: List[Relationship] = Field(description="All relationships found")
    codes: List[Code] = Field(description="All thematic codes found")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# Test function
async def test_simple_extractor():
    """Test the simple Gemini extractor"""
    
    # Sample interview text
    interview_text = """
    Interviewer: Can you tell me about your experience with remote work?
    
    Participant: Well, I've been working remotely for TechCorp since 2020. 
    At first, I really struggled with the isolation. I missed the casual 
    conversations with my colleague Sarah from the marketing team.
    
    The biggest challenge was communication. We use Slack and Zoom, but 
    it's not the same as face-to-face interaction. My manager, John, 
    tries to have regular one-on-ones, but sometimes I feel disconnected 
    from the team's goals.
    
    On the positive side, I love the flexibility. I can work from anywhere
    and spend more time with my family. The company provided us with good
    equipment and even pays for our internet.
    
    Interviewer: How has it affected your productivity?
    
    Participant: It's interesting - I'm actually more productive at home
    for focused work. No interruptions from colleagues dropping by my desk.
    But collaborative work is definitely harder. Brainstorming sessions
    on Zoom just aren't the same as being in a room together.
    """
    
    extractor = SimpleGeminiClient()
    
    try:
        result = await extractor.extract(
            interview_text=interview_text,
            schema=ExtractionResult,
            interview_id="test_001"
        )
        
        print(f"Extracted {len(result['entities'])} entities")
        print(f"Extracted {len(result['codes'])} codes")
        print(f"Extracted {len(result['relationships'])} relationships")
        
        # Show metrics summary
        print("\nMetrics Summary:")
        print(json.dumps(extractor.get_metrics_summary(), indent=2))
        
    except Exception as e:
        print(f"Extraction failed: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_simple_extractor())