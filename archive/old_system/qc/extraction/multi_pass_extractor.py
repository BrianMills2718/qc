"""
Multi-Pass LLM Extraction Pipeline

This module implements the core extraction system that takes interview text and
dynamically extracts entities and relationships based on schema configurations.

Architecture:
1. Pass 1: Basic entity and code extraction
2. Pass 2: Relationship discovery and linking
3. Pass 3: Gap filling and validation
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from difflib import SequenceMatcher

from ..core.schema_config import SchemaConfiguration, EntityDefinition, PropertyDefinition, PropertyType
from ..core.neo4j_manager import EnhancedNeo4jManager, EntityNode, RelationshipEdge
from ..core.native_gemini_client import NativeGeminiClient
from .extraction_schemas import ComprehensiveExtractionResult, ExtractedEntity, ExtractedRelationship, ExtractedCode, CodeDrivenExtractionResult, ExtractedTheme, ThemeQuote, QuoteRelationship
from .semantic_quote_extractor import SemanticQuoteExtractor, ExtractedQuote
from .semantic_code_matcher import SemanticCodeMatcher
from ..utils.token_manager import TokenManager, TokenLimitError
from ..utils.error_handler import (
    LLMError, RateLimitError, ExtractionError, ValidationError,
    retry_with_backoff, ErrorHandler
)

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result from a single extraction pass"""
    pass_number: int
    entities_found: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    relationships_found: List[Dict[str, Any]] = field(default_factory=list)
    codes_found: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None
    raw_response: Optional[str] = None


@dataclass
class InterviewContext:
    """Context for a single interview extraction"""
    interview_id: str
    interview_text: str
    session_id: str
    speaker_info: Optional[Dict[str, Any]] = None
    filename: Optional[str] = None
    extraction_timestamp: datetime = field(default_factory=datetime.utcnow)


class PromptBuilder:
    """Builds dynamic prompts based on schema configuration"""
    
    @staticmethod
    def build_entity_extraction_prompt(schema: SchemaConfiguration, 
                                     interview_text: str,
                                     pass_number: int = 1) -> str:
        """Build prompt for entity extraction"""
        
        # Build entity definitions for prompt
        entity_definitions = []
        for entity_type, entity_def in schema.entities.items():
            properties = []
            for prop_name, prop_def in entity_def.properties.items():
                prop_desc = f"  - {prop_name}: {prop_def.description or 'No description'}"
                if prop_def.type == PropertyType.ENUM and prop_def.values:
                    prop_desc += f" (options: {', '.join(prop_def.values)})"
                elif prop_def.type == PropertyType.LIST:
                    prop_desc += " (list format)"
                properties.append(prop_desc)
            
            entity_def_text = f"""
{entity_type}: {entity_def.description}
Properties:
{chr(10).join(properties)}
Extraction hints: {entity_def.extraction_hints or 'Look for mentions in the text'}
Examples: {', '.join(entity_def.examples) if entity_def.examples else 'None provided'}
"""
            entity_definitions.append(entity_def_text)
        
        if pass_number == 1:
            prompt = f"""
You are analyzing an interview transcript to extract entities and thematic codes. 

INTERVIEW TEXT:
{interview_text}

ENTITY TYPES TO EXTRACT:
{chr(10).join(entity_definitions)}

TASK:
1. Extract all instances of the above entity types mentioned in the interview
2. For each entity, extract its properties based on the definitions above
3. Identify thematic codes (topics, themes, patterns) discussed in the interview
4. For each code, find supporting quotes from the interview text

Extract entities and codes with supporting evidence from the text.

Be thorough but accurate. Only extract entities that are clearly mentioned or strongly implied in the text.
"""
        else:
            prompt = f"""
You are analyzing an interview transcript to find ADDITIONAL entities and relationships that may have been missed in the initial extraction.

INTERVIEW TEXT:
{interview_text}

ENTITY TYPES TO FIND:
{chr(10).join(entity_definitions)}

TASK: Look for any entities that may have been missed, including:
- Implicit references (e.g., "the company" referring to a previously mentioned organization)
- Entities mentioned in passing or context
- Additional properties for already identified entities

Extract additional entities and codes that may have been missed in the initial extraction.

Focus on completeness while maintaining accuracy.
"""
        
        return prompt
    
    @staticmethod
    def build_focused_entity_extraction_prompt(schema: SchemaConfiguration,
                                             interview_text: str,
                                             entity_types: List[str],
                                             pass_number: int = 1) -> str:
        """Build prompt for extracting specific entity types only"""
        
        # Build entity definitions for specified types only
        entity_definitions = []
        for entity_type in entity_types:
            if entity_type in schema.entities:
                entity_def = schema.entities[entity_type]
                properties = []
                for prop_name, prop_def in entity_def.properties.items():
                    prop_desc = f"  - {prop_name}: {prop_def.description or 'No description'}"
                    if prop_def.type == PropertyType.ENUM and prop_def.values:
                        prop_desc += f" (options: {', '.join(prop_def.values)})"
                    elif prop_def.type == PropertyType.LIST:
                        prop_desc += " (list format)"
                    properties.append(prop_desc)
                
                entity_def_text = f"""
{entity_type}: {entity_def.description}
Properties:
{chr(10).join(properties)}
Extraction hints: {entity_def.extraction_hints or 'Look for mentions in the text'}
Examples: {', '.join(entity_def.examples) if entity_def.examples else 'None provided'}
"""
                entity_definitions.append(entity_def_text)
        
        codes_section = ''
        if pass_number == 1:
            codes_section = ''',
  "codes": [
    {
      "name": "code_name",
      "definition": "what this code represents",
      "quotes": ["supporting quote 1", "supporting quote 2", ...],
      "confidence": 0.0-1.0
    }
  ]'''
        
        prompt = f"""
You are analyzing an interview transcript to extract specific entity types and thematic codes.

INTERVIEW TEXT:
{interview_text}

FOCUS ON THESE ENTITY TYPES (Pass {pass_number}):
{chr(10).join(entity_definitions)}

TASK:
1. Extract ONLY instances of the specified entity types above
2. For each entity, extract its properties based on the definitions
3. {"Identify thematic codes (topics, themes, patterns) discussed" if pass_number == 1 else "Do NOT extract codes in this pass - focus on entities only"}

CRITICAL NAMING REQUIREMENTS:
- Use UNAMBIGUOUS, DESCRIPTIVE entity names that are globally unique
- NEVER use pronouns, generic terms, or ambiguous references like "I", "my husband", "the organization", "husband", "sister", "researchers"
- For people mentioned as relatives: "Kandice Kapinos's Husband", "Kandice Kapinos's Sister" 
- For generic roles: "RAND Librarian", "Health Economics Researchers", "Federal Agency Officials"
- For "I" references: Use the actual interviewee's name (e.g., "Kandice Kapinos")
- For organizations: Use full names not abbreviations when possible
- Test: Each entity name should make sense without any context from the interview

Extract entities with unambiguous descriptive names (no pronouns or 'my/the' references).

Be thorough but focused on the specified entity types only. Remember: entity names must be unambiguous and not require context to understand.
"""
        return prompt
    
    @staticmethod
    def build_secondary_entity_relationship_prompt(schema: SchemaConfiguration,
                                                 interview_text: str,
                                                 secondary_entity_types: List[str],
                                                 primary_entities: List[Dict[str, Any]]) -> str:
        """Build prompt for extracting secondary entities and relationships with primary entities"""
        
        # Build entity definitions for secondary types
        secondary_entity_definitions = []
        for entity_type in secondary_entity_types:
            if entity_type in schema.entities:
                entity_def = schema.entities[entity_type]
                properties = []
                for prop_name, prop_def in entity_def.properties.items():
                    prop_desc = f"  - {prop_name}: {prop_def.description or 'No description'}"
                    if prop_def.type == PropertyType.ENUM and prop_def.values:
                        prop_desc += f" (options: {', '.join(prop_def.values)})"
                    properties.append(prop_desc)
                
                entity_def_text = f"""
{entity_type}: {entity_def.description}
Properties:
{chr(10).join(properties)}
"""
                secondary_entity_definitions.append(entity_def_text)
        
        # Build relationship definitions
        relationship_definitions = []
        for entity_type, entity_def in schema.entities.items():
            for rel_name, rel_def in entity_def.relationships.items():
                rel_text = f"""
{entity_type} -> {rel_def.relationship_type} -> {rel_def.target_entity}
Description: {rel_def.description or 'No description'}
Direction: {rel_def.direction}
"""
                relationship_definitions.append(rel_text)
        
        # List primary entities for reference
        primary_entity_list = []
        for entity in primary_entities:
            primary_entity_list.append(f"- {entity['name']} ({entity['entity_type']})")
        
        prompt = f"""
You are analyzing an interview transcript to find secondary entities and their relationships with primary entities.

INTERVIEW TEXT:
{interview_text}

PRIMARY ENTITIES FOUND (from Pass 1):
{chr(10).join(primary_entity_list)}

SECONDARY ENTITY TYPES TO EXTRACT:
{chr(10).join(secondary_entity_definitions)}

POSSIBLE RELATIONSHIPS:
{chr(10).join(relationship_definitions)}

TASK:
1. Extract instances of secondary entity types (Methods, Tools, etc.)
2. Find relationships between ALL entities (primary + secondary)

Find secondary entities and their relationships with the primary entities listed above.

Focus on completeness while maintaining accuracy.
"""
        return prompt
    
    @staticmethod
    def build_relationship_extraction_prompt(schema: SchemaConfiguration,
                                           interview_text: str,
                                           extracted_entities: List[Dict[str, Any]]) -> str:
        """Build prompt for relationship extraction"""
        
        # Build relationship definitions
        relationship_definitions = []
        for entity_type, entity_def in schema.entities.items():
            for rel_name, rel_def in entity_def.relationships.items():
                rel_text = f"""
{entity_type} -> {rel_def.relationship_type} -> {rel_def.target_entity}
Description: {rel_def.description or 'No description'}
Direction: {rel_def.direction}
Extraction hints: {rel_def.extraction_hints or 'Look for connections in the text'}
"""
                relationship_definitions.append(rel_text)
        
        # List extracted entities for reference
        entity_list = []
        for entity in extracted_entities:
            entity_list.append(f"- {entity['name']} ({entity['entity_type']})")
        
        prompt = f"""
You are analyzing an interview transcript to find relationships between entities.

INTERVIEW TEXT:
{interview_text}

EXTRACTED ENTITIES:
{chr(10).join(entity_list)}

POSSIBLE RELATIONSHIPS:
{chr(10).join(relationship_definitions)}

TASK:
Find relationships between the extracted entities based on what is mentioned or implied in the interview text.

Find relationships between entities that are clearly stated or strongly implied in the text.

Only extract relationships that are clearly stated or strongly implied in the text.
"""
        
        return prompt
    
    @staticmethod
    def build_code_driven_extraction_prompt(schema: SchemaConfiguration, interview_text: str) -> str:
        """
        Build code-driven extraction prompt that extracts themes with supporting quotes.
        
        This implements true qualitative coding methodology where thematic codes drive
        quote extraction, ensuring 100% coding rate by design.
        
        Args:
            schema: Schema configuration with entity definitions
            interview_text: Interview text to analyze
            
        Returns:
            Code-driven extraction prompt that prioritizes themes → quotes → entities
        """
        
        # Build entity definitions for context
        entity_definitions = []
        for entity_type, entity_def in schema.entities.items():
            properties = []
            for prop_name, prop_def in entity_def.properties.items():
                prop_desc = f"  - {prop_name}: {prop_def.description or 'No description'}"
                if prop_def.type == PropertyType.ENUM and prop_def.values:
                    prop_desc += f" (options: {', '.join(prop_def.values)})"
                elif prop_def.type == PropertyType.LIST:
                    prop_desc += " (list format)"
                properties.append(prop_desc)
            
            entity_definition = f"{entity_type}: {entity_def.description}\n" + "\n".join(properties)
            entity_definitions.append(entity_definition)
        
        # Build relationship definitions for context
        relationship_definitions = []
        for entity_type, entity_def in schema.entities.items():
            for rel_name, rel_def in entity_def.relationships.items():
                rel_desc = f"- {rel_name}: {entity_type} -> {rel_def.target_entity} ({rel_def.relationship_type})"
                if rel_def.description:
                    rel_desc += f" - {rel_def.description}"
                relationship_definitions.append(rel_desc)
        
        prompt = f"""Extract thematic codes with supporting quotes from this interview text using true qualitative coding methodology.

INTERVIEW TEXT:
{interview_text}

QUALITATIVE CODING METHODOLOGY:
This is CODE-DRIVEN extraction where themes drive data collection, ensuring 100% coding rate.
Follow this exact process:

PHASE 1: THEMATIC ANALYSIS
- Identify 3-8 main themes/concepts/patterns in the interview
- Each theme represents a key insight, pattern, or concept from the participant
- Themes should capture the essence of what the participant is communicating

PHASE 2: EVIDENCE EXTRACTION  
- For EACH theme, extract 2-5 supporting quotes from the interview
- MANDATORY JSON STRUCTURE: All quotes MUST be returned as JSON objects, NEVER as strings
- REQUIRED FIELDS for each supporting_quote:
  * "text": exact quote text from interview (string)
  * "line_start": starting line number (integer, not string)
  * "line_end": ending line number (integer, not string)  
  * "entities": array of entity names found in this quote (REQUIRED, cannot be empty)
  * "confidence": confidence score between 0.0 and 1.0 (float)
  * "relationships": array of relationship objects (can be empty array)
- ABSOLUTE REQUIREMENT: Every quote MUST include populated "entities" array
- PROCESSING WILL FAIL if any quote is returned as a simple string
- PROCESSING WILL FAIL if "entities" field is missing or empty

PHASE 3: ENTITY EXTRACTION
- For each quote, extract entities/relationships mentioned within that quote
- Entities must be grounded in the specific quote text
- Only extract what is explicitly mentioned in the quote

ENTITY TYPES FOR REFERENCE:
{chr(10).join(entity_definitions)}

RELATIONSHIP TYPES FOR REFERENCE:
{chr(10).join(relationship_definitions)}

CRITICAL REQUIREMENTS:
1. THEMES DRIVE EXTRACTION: Extract quotes BECAUSE they support themes, not due to linguistic boundaries
2. 100% CODING RATE: Every extracted quote MUST link to a thematic code by design
3. SUPPORTING EVIDENCE: Quotes must actually illustrate or support their assigned theme
4. LINE NUMBER ACCURACY: Preserve exact line numbers for research citations
5. COMPLETE PROVENANCE: Every entity must trace back to a specific quote that mentions it
6. CONFIDENCE SCORING: Include confidence scores (0.1-1.0) for all extractions

JSON STRUCTURE REQUIREMENT - MUST FOLLOW EXACTLY:
{{"themes": [
  {{"name": "AI Integration", 
    "description": "How AI tools are integrated into research", 
    "supporting_quotes": [
      {{"text": "We use AI tools to enhance our research methodology",
        "line_start": 42,
        "line_end": 42,
        "entities": ["AI tools", "research methodology"],
        "confidence": 0.8,
        "relationships": []}}
    ]}}
]}}

❌ INVALID FORMAT (will be rejected): 
{{"themes": [
  {{"name": "AI Integration",
    "supporting_quotes": ["We use AI tools..."]  // STRINGS NOT ALLOWED
  }}
]}}

VALIDATION CHECKLIST:
- ✓ Every theme has supporting quotes that actually illustrate the theme
- ✓ Every quote is linked to a theme (no orphaned quotes)
- ✓ All quotes are in structured JSON format with required fields
- ✓ Line numbers are accurate for research citations
- ✓ Entities are grounded in specific quotes that mention them
- ✓ Confidence scores reflect extraction certainty

Extract comprehensively using the themes-first, evidence-driven approach for maximum research value."""
        
        return prompt

    @staticmethod
    def build_comprehensive_extraction_prompt(schema: SchemaConfiguration, interview_text: str) -> str:
        """
        Build a comprehensive extraction prompt that extracts entities, relationships, and codes
        in a single LLM call for Phase 2.2 single-pass architecture.
        """
        
        # Build entity definitions
        entity_definitions = []
        for entity_type, entity_def in schema.entities.items():
            properties = []
            for prop_name, prop_def in entity_def.properties.items():
                prop_desc = f"  - {prop_name}: {prop_def.description or 'No description'}"
                if prop_def.type == PropertyType.ENUM and prop_def.values:
                    prop_desc += f" (options: {', '.join(prop_def.values)})"
                elif prop_def.type == PropertyType.LIST:
                    prop_desc += " (list format)"
                properties.append(prop_desc)
            
            entity_definition = f"{entity_type}: {entity_def.description}\n" + "\n".join(properties)
            entity_definitions.append(entity_definition)
        
        # Build relationship definitions
        relationship_definitions = []
        for entity_type, entity_def in schema.entities.items():
            for rel_name, rel_def in entity_def.relationships.items():
                rel_desc = f"- {rel_name}: {entity_type} -> {rel_def.target_entity} ({rel_def.relationship_type})"
                if rel_def.description:
                    rel_desc += f" - {rel_def.description}"
                relationship_definitions.append(rel_desc)
        
        prompt = f"""Extract entities, relationships, and thematic codes from this interview text in a single comprehensive analysis.

INTERVIEW TEXT:
{interview_text}

ENTITY TYPES TO EXTRACT:
{chr(10).join(entity_definitions)}

RELATIONSHIP TYPES TO EXTRACT:
{chr(10).join(relationship_definitions)}

CRITICAL VALIDATION REQUIREMENTS FOR RELATIONSHIPS:
1. source_entity and target_entity must NEVER be empty or null
2. Use EXACT entity names (case-sensitive matching)
3. Only create relationships explicitly mentioned or strongly implied in the text
4. Each relationship must have supporting context from the interview
5. Confidence must be between 0.1 and 1.0

INSTRUCTIONS:
1. Extract ALL entities of the specified types with their properties
2. Identify ALL relationships between entities that are mentioned or implied
3. Extract thematic codes (themes, concepts, ideas) with supporting quotes
4. Assign unique IDs to all entities, relationships, and codes
5. For codes, associate them with relevant entity IDs when applicable

RELATIONSHIP VALIDATION CHECKLIST:
- ✓ source_entity contains exact entity name (not empty, not "unknown")
- ✓ target_entity contains exact entity name (not empty, not "unknown")
- ✓ relationship_type is appropriate and clear
- ✓ Supporting context explains the relationship

REJECT relationships where source_entity or target_entity are empty, null, or don't match extracted entity names.
Extract comprehensively - use the full output capacity to capture all relevant information."""
        
        return prompt


class MultiPassExtractor:
    """Main extraction pipeline coordinator"""
    
    def __init__(self, neo4j_manager: EnhancedNeo4jManager, 
                 schema: SchemaConfiguration, llm_client: NativeGeminiClient = None,
                 use_code_driven: bool = False):
        """
        Initialize the multi-pass extractor
        
        Args:
            neo4j_manager: Neo4j database manager
            schema: Schema configuration for extraction
            llm_client: Native Gemini client with real structured output (auto-created if not provided)
            use_code_driven: Use code-driven extraction for 100% coding rate (default: False for backwards compatibility)
        """
        # FAIL-FAST: Runtime parameter validation
        if not isinstance(neo4j_manager, EnhancedNeo4jManager):
            raise TypeError(f"neo4j_manager must be EnhancedNeo4jManager, got {type(neo4j_manager)}")
        if not isinstance(schema, SchemaConfiguration):
            raise TypeError(f"schema must be SchemaConfiguration, got {type(schema)}")
        if llm_client is not None and not isinstance(llm_client, NativeGeminiClient):
            raise TypeError(f"llm_client must be NativeGeminiClient, got {type(llm_client)}")
        
        self.neo4j = neo4j_manager
        self.schema = schema
        self.use_code_driven = use_code_driven
        self.prompt_builder = PromptBuilder()
        
        # Initialize LLM client
        if llm_client is None:
            self.llm = NativeGeminiClient()
        else:
            self.llm = llm_client
        
        # Initialize quote-centric extraction components
        self.quote_extractor = SemanticQuoteExtractor()
        self.semantic_matcher = SemanticCodeMatcher(self.llm)
            
        # Initialize token manager
        self.token_manager = TokenManager(max_tokens=1000000)  # 1M input token limit
        self.error_handler = ErrorHandler()
        
        # Session state management for isolation
        self._current_session_id = None
        self._extraction_cache = {}  # Clear between sessions
    
    def _clear_extraction_state(self):
        """Clear extraction state to prevent contamination between sessions"""
        self._current_session_id = None
        self._extraction_cache.clear()
        logger.info("Cleared extraction state for session isolation")
    
    def _ensure_session_isolation(self, context: InterviewContext):
        """Ensure proper session isolation for batch processing"""
        if self._current_session_id != context.session_id:
            # New session detected, clear previous state
            self._clear_extraction_state()
            self._current_session_id = context.session_id
            logger.info(f"Session changed to {context.session_id}, state cleared")
    
    def _validate_and_fix_relationship(self, rel_data: Dict[str, Any], entity_names: List[str], 
                                     fuzzy_threshold: float = 0.8) -> Tuple[bool, Dict[str, Any], List[str]]:
        """
        Validate and fix a single relationship
        
        Args:
            rel_data: Relationship data dict
            entity_names: List of valid entity names for matching
            fuzzy_threshold: Minimum similarity score for fuzzy matching
            
        Returns:
            Tuple of (is_valid, corrected_data, issues)
        """
        issues = []
        corrected_data = rel_data.copy()
        
        # Extract source and target entities (handle both field name conventions)
        source_entity = rel_data.get("source_entity") or rel_data.get("source_id", "")
        target_entity = rel_data.get("target_entity") or rel_data.get("target_id", "")
        
        # Critical validation: check for empty entities
        if not source_entity or not isinstance(source_entity, str) or not source_entity.strip():
            issues.append("Empty or invalid source_entity")
            return False, corrected_data, issues
        
        if not target_entity or not isinstance(target_entity, str) or not target_entity.strip():
            issues.append("Empty or invalid target_entity")
            return False, corrected_data, issues
        
        # Clean entity names
        source_entity = source_entity.strip()
        target_entity = target_entity.strip()
        
        # Check relationship type
        relationship_type = rel_data.get("relationship_type", "").strip()
        if not relationship_type:
            issues.append("Empty relationship_type")
            return False, corrected_data, issues
        
        # Try to match entities
        source_match = self._find_entity_match(source_entity, entity_names, fuzzy_threshold)
        target_match = self._find_entity_match(target_entity, entity_names, fuzzy_threshold)
        
        if source_match != source_entity:
            if source_match:
                issues.append(f"Fixed source entity: '{source_entity}' -> '{source_match}'")
                corrected_data["source_entity"] = source_match
                # Reduce confidence for fuzzy matches
                original_confidence = rel_data.get("confidence", 0.8)
                corrected_data["confidence"] = max(0.1, original_confidence - 0.1)
            else:
                issues.append(f"No match found for source entity: '{source_entity}'")
                return False, corrected_data, issues
        
        if target_match != target_entity:
            if target_match:
                issues.append(f"Fixed target entity: '{target_entity}' -> '{target_match}'")
                corrected_data["target_entity"] = target_match
                # Reduce confidence for fuzzy matches
                original_confidence = corrected_data.get("confidence", 0.8)
                corrected_data["confidence"] = max(0.1, original_confidence - 0.1)
            else:
                issues.append(f"No match found for target entity: '{target_entity}'")
                return False, corrected_data, issues
        
        return True, corrected_data, issues
    
    def _find_entity_match(self, entity_name: str, entity_names: List[str], 
                          fuzzy_threshold: float = 0.8) -> Optional[str]:
        """
        Find exact or fuzzy match for entity name
        
        Args:
            entity_name: Entity name to match
            entity_names: List of valid entity names
            fuzzy_threshold: Minimum similarity for fuzzy matching
            
        Returns:
            Matched entity name or original if exact match found
        """
        entity_name_clean = entity_name.strip()
        
        # Try exact match (case sensitive)
        if entity_name_clean in entity_names:
            return entity_name_clean
        
        # Try case insensitive match
        for name in entity_names:
            if name.lower() == entity_name_clean.lower():
                return name
        
        # Try fuzzy matching
        best_match = None
        best_score = 0.0
        
        entity_name_lower = entity_name_clean.lower()
        
        for candidate in entity_names:
            candidate_lower = candidate.lower()
            
            # Calculate similarity score
            score = SequenceMatcher(None, entity_name_lower, candidate_lower).ratio()
            
            # Boost score for substring matches
            if entity_name_lower in candidate_lower or candidate_lower in entity_name_lower:
                score = max(score, 0.85)
            
            if score > best_score:
                best_score = score
                best_match = candidate
        
        # Return fuzzy match if above threshold
        if best_score >= fuzzy_threshold:
            return best_match
        
        return None
    
    async def extract_from_interview(self, context: InterviewContext) -> List[ExtractionResult]:
        """
        Run complete multi-pass extraction on an interview.
        
        If the interview is too large, it will be chunked automatically.
        """
        # Check if we need to chunk the interview
        chunks_needed = self.token_manager.estimate_interview_chunks(context.interview_text)
        
        if chunks_needed > 1:
            logger.info(f"Interview too large, splitting into {chunks_needed} chunks")
            return await self._extract_from_chunked_interview(context)
        
        # Choose extraction method based on configuration
        if self.use_code_driven:
            return await self._code_driven_extraction(context)
        else:
            # Use single-pass extraction (Phase 2.2)
            return await self._single_pass_extraction(context)
    
    async def _single_pass_extraction(self, context: InterviewContext) -> List[ExtractionResult]:
        """
        Phase 2.2: Single-pass extraction that combines all entities, relationships, and codes in one LLM call.
        
        This replaces the inefficient 3-pass system with a single comprehensive extraction using
        the full 60K token output capacity of modern LLMs.
        
        Args:
            context: Interview context with text and metadata
            
        Returns:
            List containing single extraction result
        """
        # Ensure session isolation first
        self._ensure_session_isolation(context)
        
        logger.info(f"Starting single-pass extraction for interview {context.interview_id}")
        
        # Build comprehensive extraction prompt that includes all entity types, relationships, and codes
        prompt = self.prompt_builder.build_comprehensive_extraction_prompt(
            self.schema, context.interview_text
        )
        
        # Retry mechanism for reliability
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Extraction attempt {attempt + 1}/{max_retries} for interview {context.interview_id}")
                
                # Single LLM call with native Gemini structured output
                result = self.llm.structured_output(
                    prompt=prompt,
                    schema=ComprehensiveExtractionResult
                )
                
                # Extract the content from the native Gemini response
                if result['success']:
                    extraction_data = result['response']  # Already parsed JSON dict
                    logger.info(f"Extraction successful on attempt {attempt + 1}")
                    break  # Success, exit retry loop
                else:
                    last_error = result.get('error', 'Native Gemini extraction failed')
                    logger.warning(f"Extraction attempt {attempt + 1} failed: {last_error}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)  # Brief delay before retry
                        continue
                    else:
                        logger.error(f"All {max_retries} extraction attempts failed")
                        raise ExtractionError(f"All {max_retries} extraction attempts failed. Last error: {last_error}")
                        
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Extraction attempt {attempt + 1} exception: {last_error}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)  # Brief delay before retry
                    continue
                else:
                    logger.error(f"All {max_retries} extraction attempts failed with exceptions")
                    raise ExtractionError(f"All {max_retries} extraction attempts failed with exceptions. Last error: {last_error}")
        
        # If we get here, extraction was successful
        try:
            # Parse the comprehensive extraction result
            extraction_result = self._parse_single_pass_result_from_dict(extraction_data, context)
            
            # Store result in Neo4j FIRST (this creates the code_id_map needed for semantic matching)
            await self._store_extraction_results(context, [extraction_result])
            
            # QUOTE-CENTRIC ARCHITECTURE: Extract and store quotes with semantic relationships
            # This MUST happen after storing codes so code_id_map is available
            logger.info(f"Starting quote-centric extraction for interview {context.interview_id}")
            await self._extract_and_store_quotes(context, extraction_result)
            
            logger.info(f"Completed single-pass extraction for interview {context.interview_id}")
            return [extraction_result]
        
        except Exception as e:
            logger.error(f"Failed to parse or store extraction results: {e}")
            raise ExtractionError(f"Failed to parse or store extraction results: {str(e)}") from e
    
    async def _code_driven_extraction(self, context: InterviewContext) -> List[ExtractionResult]:
        """
        Code-driven extraction that ensures 100% quote-to-code linkage.
        
        Implementation Flow:
        1. Extract themes with supporting quotes (themes drive quote selection)
        2. For each quote, extract entities/relationships mentioned
        3. Store with complete provenance chain: themes → quotes → entities
        
        Returns 100% coding rate by design since quotes extracted FOR themes.
        
        Args:
            context: Interview context with text and metadata
            
        Returns:
            List containing single extraction result with complete provenance
        """
        # Ensure session isolation first
        self._ensure_session_isolation(context)
        
        logger.info(f"Starting code-driven extraction for interview {context.interview_id}")
        
        # Build code-driven extraction prompt
        prompt = self.prompt_builder.build_code_driven_extraction_prompt(
            self.schema, context.interview_text
        )
        
        # Retry mechanism for reliability
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Code-driven extraction attempt {attempt + 1}/{max_retries} for interview {context.interview_id}")
                
                # Single LLM call with code-driven structured output
                result = self.llm.structured_output(
                    prompt=prompt,
                    schema=CodeDrivenExtractionResult
                )
                
                # Extract the content from the native Gemini response
                if result['success']:
                    extraction_data = result['response']  # Already parsed JSON dict
                    
                    # VALIDATION AND PARSING: Convert JSON string quotes to structured format
                    validation_errors = []
                    if 'themes' in extraction_data:
                        for theme_idx, theme in enumerate(extraction_data['themes']):
                            if 'supporting_quotes' in theme:
                                parsed_quotes = []
                                for quote_idx, quote in enumerate(theme['supporting_quotes']):
                                    if isinstance(quote, str):
                                        # Try to parse as JSON string first
                                        try:
                                            parsed_quote = json.loads(quote)
                                            if isinstance(parsed_quote, dict):
                                                # Validate required fields
                                                if 'entities' not in parsed_quote:
                                                    validation_errors.append(f"Theme {theme_idx}, Quote {quote_idx}: Parsed JSON missing 'entities' field")
                                                elif not isinstance(parsed_quote.get('line_start'), int):
                                                    validation_errors.append(f"Theme {theme_idx}, Quote {quote_idx}: 'line_start' must be integer")
                                                elif not isinstance(parsed_quote.get('line_end'), int):
                                                    validation_errors.append(f"Theme {theme_idx}, Quote {quote_idx}: 'line_end' must be integer")
                                                else:
                                                    # Normalize entities - extract names from complex objects if needed
                                                    entities_list = parsed_quote.get('entities', [])
                                                    normalized_entities = []
                                                    for entity in entities_list:
                                                        if isinstance(entity, dict) and 'name' in entity:
                                                            normalized_entities.append(entity['name'])
                                                        elif isinstance(entity, str):
                                                            normalized_entities.append(entity)
                                                        else:
                                                            logger.warning(f"Skipping invalid entity format: {entity}")
                                                    
                                                    parsed_quote['entities'] = normalized_entities
                                                    parsed_quotes.append(parsed_quote)
                                                    logger.info(f"Successfully parsed JSON string quote with {len(normalized_entities)} entities")
                                            else:
                                                validation_errors.append(f"Theme {theme_idx}, Quote {quote_idx}: JSON string did not parse to dictionary")
                                        except json.JSONDecodeError as e:
                                            validation_errors.append(f"Theme {theme_idx}, Quote {quote_idx}: String format not valid JSON: {e}")
                                    elif isinstance(quote, dict):
                                        # Already structured format
                                        if 'entities' not in quote:
                                            validation_errors.append(f"Theme {theme_idx}, Quote {quote_idx}: Missing 'entities' field")
                                        elif not isinstance(quote.get('line_start'), int):
                                            validation_errors.append(f"Theme {theme_idx}, Quote {quote_idx}: 'line_start' must be integer")
                                        elif not isinstance(quote.get('line_end'), int):
                                            validation_errors.append(f"Theme {theme_idx}, Quote {quote_idx}: 'line_end' must be integer")
                                        else:
                                            # Normalize entities - extract names from complex objects if needed
                                            entities_list = quote.get('entities', [])
                                            normalized_entities = []
                                            for entity in entities_list:
                                                if isinstance(entity, dict) and 'name' in entity:
                                                    normalized_entities.append(entity['name'])
                                                elif isinstance(entity, str):
                                                    normalized_entities.append(entity)
                                                else:
                                                    logger.warning(f"Skipping invalid entity format: {entity}")
                                            
                                            quote['entities'] = normalized_entities
                                            parsed_quotes.append(quote)
                                # Replace with parsed quotes
                                theme['supporting_quotes'] = parsed_quotes
                    
                    if validation_errors:
                        validation_error_msg = "LLM response format validation failed:\n" + "\n".join(validation_errors)
                        logger.warning(f"Format validation failed on attempt {attempt + 1}: {validation_error_msg}")
                        if attempt < max_retries - 1:
                            continue  # Retry with corrected prompt
                        else:
                            raise ExtractionError(f"Format validation failed after {max_retries} attempts: {validation_error_msg}")
                    
                    logger.info(f"Code-driven extraction successful on attempt {attempt + 1}")
                    break  # Success, exit retry loop
                else:
                    last_error = result.get('error', 'Native Gemini code-driven extraction failed')
                    logger.warning(f"Code-driven extraction attempt {attempt + 1} failed: {last_error}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)  # Brief delay before retry
                        continue
                    else:
                        logger.error(f"All {max_retries} code-driven extraction attempts failed")
                        raise ExtractionError(f"All {max_retries} code-driven extraction attempts failed. Last error: {last_error}")
                        
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Code-driven extraction attempt {attempt + 1} exception: {last_error}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)  # Brief delay before retry
                    continue
                else:
                    logger.error(f"All {max_retries} code-driven extraction attempts failed with exceptions")
                    raise ExtractionError(f"All {max_retries} code-driven extraction attempts failed with exceptions. Last error: {last_error}")
        
        # If we get here, extraction was successful
        try:
            # Parse the code-driven extraction result and convert to standard format
            extraction_result = self._parse_code_driven_result_from_dict(extraction_data, context)
            
            # Store result in Neo4j with complete provenance chains
            await self._store_code_driven_results(context, extraction_result, extraction_data)
            
            logger.info(f"Completed code-driven extraction for interview {context.interview_id}")
            return [extraction_result]
        
        except Exception as e:
            logger.error(f"Failed to parse or store code-driven extraction results: {e}")
            raise ExtractionError(f"Failed to parse or store code-driven extraction results: {str(e)}") from e
    
    async def _extract_from_single_interview(self, context: InterviewContext) -> List[ExtractionResult]:
        """
        Run complete multi-pass extraction on an interview
        
        Args:
            context: Interview context with text and metadata
            
        Returns:
            List of extraction results from each pass
        """
        logger.info(f"Starting multi-pass extraction for interview {context.interview_id}")
        
        results = []
        
        # Pass 1: Extract primary entities (Person, Organization) and codes
        logger.info("Pass 1: Primary entities (Person, Organization) and codes")
        pass1_result = await self._extraction_pass_1(context)
        results.append(pass1_result)
        
        # Pass 2: Extract secondary entities (Method, Tool) and relationships
        logger.info("Pass 2: Secondary entities (Method, Tool) and relationships")
        pass2_result = await self._extraction_pass_2(context, pass1_result)
        results.append(pass2_result)
        
        # Pass 3: Gap filling, validation, and additional entities
        logger.info("Pass 3: Gap filling, validation, and additional entities")
        pass3_result = await self._extraction_pass_3(context, results)
        results.append(pass3_result)
        
        # Store results in Neo4j
        await self._store_extraction_results(context, results)
        
        logger.info(f"Completed multi-pass extraction for interview {context.interview_id}")
        return results
    
    async def _extract_from_chunked_interview(self, context: InterviewContext) -> List[ExtractionResult]:
        """
        Extract from large interviews by processing chunks.
        
        Args:
            context: Interview context with large text
            
        Returns:
            Combined extraction results from all chunks
        """
        chunks = self.token_manager.chunk_text(context.interview_text, overlap=1000)
        logger.info(f"Processing {len(chunks)} chunks for interview {context.interview_id}")
        
        all_entities = []
        all_relationships = []
        all_codes = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            
            # Create a context for this chunk
            chunk_context = InterviewContext(
                interview_id=f"{context.interview_id}_chunk_{i}",
                interview_text=chunk,
                session_id=context.session_id,
                speaker_info=context.speaker_info,
                filename=context.filename
            )
            
            # Run extraction on the chunk
            chunk_results = await self._extract_from_single_interview(chunk_context)
            
            # Aggregate results
            for result in chunk_results:
                all_entities.extend(result.entities_found)
                all_relationships.extend(result.relationships_found)
                all_codes.extend(result.codes_found)
        
        # Deduplicate entities and codes
        unique_entities = self._deduplicate_entities(all_entities)
        unique_codes = self._deduplicate_codes(all_codes)
        
        # Return combined results
        return [
            ExtractionResult(
                pass_number=1,
                entities_found=unique_entities,
                relationships_found=all_relationships,
                codes_found=unique_codes,
                confidence_scores={},
                metadata={
                    "chunks_processed": len(chunks),
                    "total_entities": len(unique_entities),
                    "total_relationships": len(all_relationships),
                    "total_codes": len(unique_codes)
                }
            )
        ]
    
    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate entities based on name and type"""
        seen = set()
        unique = []
        for entity in entities:
            key = (entity.get('name', ''), entity.get('entity_type', ''))
            if key not in seen:
                seen.add(key)
                unique.append(entity)
        return unique
    
    def _deduplicate_codes(self, codes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate codes based on name"""
        seen = set()
        unique = []
        for code in codes:
            name = code.get('name', '')
            if name not in seen:
                seen.add(name)
                unique.append(code)
        return unique
    
    async def _extraction_pass_1(self, context: InterviewContext) -> ExtractionResult:
        """Pass 1: Extract primary entities (Person, Organization) and codes"""
        
        # Create focused schema for primary entities only
        primary_entity_types = ["Person", "Organization"]
        prompt = self.prompt_builder.build_focused_entity_extraction_prompt(
            self.schema, context.interview_text, entity_types=primary_entity_types, pass_number=1
        )
        
        try:
            # Call LLM (placeholder - needs actual LLM integration)
            llm_response = await self._call_llm(prompt, structured_output=True)
            
            # Parse response
            # Try to parse JSON with error handling
            if isinstance(llm_response, str):
                try:
                    parsed_data = json.loads(llm_response)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parsing failed: {e}. Response: {llm_response[:200]}...")
                    # This will trigger fallback to next model in the chain
                    raise LLMError(f"JSON parsing failed: {e}")
            else:
                parsed_data = llm_response
            
            return ExtractionResult(
                pass_number=1,
                entities_found=parsed_data.get("entities", []),
                relationships_found=[],  # No relationships in pass 1
                codes_found=parsed_data.get("codes", []),
                confidence_scores=self._calculate_confidence_scores(parsed_data),
                metadata={
                    "prompt_length": len(prompt),
                    "response_length": len(str(llm_response)) if llm_response is not None else 0,
                    "extraction_time": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Pass 1 extraction failed: {e}")
            raise ExtractionError(f"Pass 1 extraction failed: {e}") from e
    
    async def _extraction_pass_2(self, context: InterviewContext, 
                                pass1_result: ExtractionResult) -> ExtractionResult:
        """Pass 2: Extract relationships between entities from Pass 1"""
        
        # Get entities from Pass 1
        entities = pass1_result.entities_found
        if not entities:
            return ExtractionResult(
                pass_number=2,
                entities_found=[],
                relationships_found=[],
                codes_found=[],
                confidence_scores={},
                metadata={"note": "No entities from Pass 1"}
            )
        
        # Build simple relationship extraction prompt
        entity_list = [f"- {e['name']} ({e['entity_type']})" for e in entities]
        
        prompt = f"""Find relationships between these entities in the interview text.

INTERVIEW TEXT:
{context.interview_text}

ENTITIES (use these EXACT names):
{chr(10).join(entity_list)}

CRITICAL INSTRUCTIONS:
- You MUST use the EXACT entity names from the list above
- If the text says "I", "my husband", "the organization", etc., map them to the correct entity names from the list
- Example: If text says "My husband uses Claude" and the entity list has "Kandice Kapinos's Husband", use "Kandice Kapinos's Husband"
- NEVER create new entity names - only use names from the ENTITIES list above

Find relationships like:
- Person WORKS_AT Organization
- Person MANAGES Person/Team  
- Organization PART_OF Organization
- Person USES Method/Tool

Find relationships between the entities listed above using EXACT entity names.

Focus only on clear, explicit relationships in the text. Remember: use ONLY the exact entity names provided in the list above."""
        
        try:
            llm_response = await self._call_llm(prompt, structured_output=False)
            
            # Clean markdown and parse JSON
            llm_response = self._clean_llm_response(llm_response)
            if llm_response is None:
                raise ValueError("LLM returned None response")
                
            parsed_data = json.loads(llm_response)
            
            return ExtractionResult(
                pass_number=2,
                entities_found=[],  # No new entities in Pass 2
                relationships_found=parsed_data.get("relationships", []),
                codes_found=[],  # No new codes in Pass 2
                confidence_scores=self._calculate_confidence_scores(parsed_data),
                metadata={
                    "prompt_length": len(prompt),
                    "response_length": len(str(llm_response)) if llm_response is not None else 0,
                    "extraction_time": datetime.utcnow().isoformat(),
                    "method": "simplified_relationships_only"
                }
            )
            
        except Exception as e:
            logger.error(f"Pass 2 extraction failed: {e}")
            raise ExtractionError(f"Pass 2 extraction failed: {e}") from e
    
    async def _extraction_pass_3(self, context: InterviewContext,
                                previous_results: List[ExtractionResult]) -> ExtractionResult:
        """Pass 3: Gap filling and additional entity discovery"""
        
        prompt = self.prompt_builder.build_entity_extraction_prompt(
            self.schema, context.interview_text, pass_number=3
        )
        
        try:
            llm_response = await self._call_llm(prompt, structured_output=True)
            
            # Clean markdown from response
            llm_response = self._clean_llm_response(llm_response)
            
            # Try to parse JSON with error handling
            if isinstance(llm_response, str):
                try:
                    parsed_data = json.loads(llm_response)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parsing failed: {e}. Response: {llm_response[:200]}...")
                    # This will trigger fallback to next model in the chain
                    raise LLMError(f"JSON parsing failed: {e}")
            else:
                parsed_data = llm_response
            
            # Handle None response
            if parsed_data is None:
                parsed_data = {"entities": [], "codes": []}
            
            return ExtractionResult(
                pass_number=3,
                entities_found=parsed_data.get("entities", []),
                relationships_found=[],
                codes_found=parsed_data.get("codes", []),  # Could add code refinement here
                confidence_scores=self._calculate_confidence_scores(parsed_data),
                metadata={
                    "prompt_length": len(prompt),
                    "response_length": len(str(llm_response)) if llm_response is not None else 0,
                    "extraction_time": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Pass 3 extraction failed: {e}")
            raise ExtractionError(f"Pass 3 extraction failed: {e}") from e
    
    @retry_with_backoff(max_tries=3, exceptions=(LLMError, Exception))
    async def _call_llm(self, prompt: str, structured_output: bool = False) -> str:
        """
        Call the LLM with error handling, token management, and retries
        
        Args:
            prompt: The prompt to send to the LLM
            structured_output: Whether to request structured JSON output
            
        Returns:
            JSON string response from the LLM
        """
        try:
            # Check token count before making the call
            try:
                self.token_manager.validate_prompt_size(prompt, max_response_tokens=4096)
            except TokenLimitError as e:
                logger.warning(f"Prompt too large: {e}. Attempting to optimize...")
                prompt = self.token_manager.optimize_prompt(prompt)
            
            # Prepare messages for the LLM
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            # Generate JSON schema dynamically from YAML configuration
            schema = None
            if structured_output:
                schema = self._generate_json_schema_from_config(prompt)
            
            # Call the universal model client with default fallback chain
            result = self.llm.complete(
                messages=messages,
                # Use UniversalModelClient default with fallbacks (gemini_2_5_flash -> o4_mini -> claude_sonnet_4)
                schema=schema,
                max_tokens=60000,
                temperature=0.3
            )
            
            # Extract the content from the response
            response_content = result.get('response', {})
            
            # Handle different response structures
            if hasattr(response_content, 'choices'):
                # It's a ModelResponse object from litellm
                if len(response_content.choices) > 0:
                    content = response_content.choices[0].message.content
                else:
                    raise ValueError("No choices in LLM response")
            elif isinstance(response_content, dict) and 'choices' in response_content:
                # It's a dict with choices
                if len(response_content['choices']) > 0:
                    content = response_content['choices'][0]['message']['content']
                else:
                    raise ValueError("No choices in LLM response")
            elif isinstance(response_content, str):
                # Direct string response
                content = response_content
            else:
                # Try to convert to string
                content = str(response_content)
            
            # Check if content is None
            if content is None:
                raise ValueError("LLM returned None content")
            
            # Log successful LLM call with token usage
            prompt_tokens = self.token_manager.count_tokens(prompt)
            response_tokens = self.token_manager.count_tokens(content)
            logger.info(
                f"LLM call successful - model: {result.get('model_used', 'unknown')}, "
                f"attempts: {result.get('attempts', 1)}, "
                f"tokens: {prompt_tokens} prompt + {response_tokens} response = {prompt_tokens + response_tokens} total"
            )
            
            return content
            
        except Exception as e:
            # Use error handler for proper logging
            self.error_handler.handle_llm_error(e, "multi-pass extraction")
            
            # Convert to appropriate error type if needed
            if "rate_limit" in str(e).lower():
                raise RateLimitError(str(e)) from e
            elif "token" in str(e).lower():
                raise TokenLimitError(str(e)) from e
            
            # Re-raise for retry logic
            raise LLMError(f"LLM call failed: {e}") from e
    
    def _clean_llm_response(self, content: str) -> str:
        """Clean markdown code blocks from LLM response and fix common JSON issues"""
        if not content or not isinstance(content, str):
            return content
            
        content = content.strip()
        
        # Remove markdown code blocks
        if content.startswith('```'):
            lines = content.split('\n')
            # Find start (after ```json or ```)
            start_idx = 1
            # Find end (before closing ```)
            end_idx = len(lines)
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip() == '```':
                    end_idx = i
                    break
            content = '\n'.join(lines[start_idx:end_idx])
        
        # Fix common JSON issues
        # Fix unescaped quotes in strings
        import re
        # This is a basic fix - could be improved
        content = re.sub(r'(?<!\\)"(?=.*")', '\\"', content)
        
        return content

    def _generate_json_schema_from_config(self, prompt: str) -> Dict[str, Any]:
        """
        Generate JSON schema dynamically from YAML configuration
        
        Args:
            prompt: The prompt to determine schema type
            
        Returns:
            JSON schema dictionary
        """
        if "relationships" in prompt.lower():
            # This is either pass 2 (secondary entities + relationships) or old relationship-only extraction
            if "secondary entities" in prompt.lower():
                return self._generate_secondary_entity_relationship_schema()
            else:
                return self._generate_relationship_schema()
        else:
            # This is entity extraction (pass 1 or pass 3)
            include_codes = "codes" in prompt.lower() and "do not extract codes" not in prompt.lower()
            return self._generate_entity_and_code_schema(include_codes=include_codes)
    
    def _generate_relationship_schema(self) -> Dict[str, Any]:
        """Generate JSON schema for relationship extraction"""
        # Generate property schema for all entity types
        all_properties = {}
        for entity_def in self.schema.entities.values():
            for prop_name, prop_def in entity_def.properties.items():
                if prop_name not in all_properties:
                    all_properties[prop_name] = self._property_to_json_schema(prop_def)
        
        return {
            "type": "object",
            "properties": {
                "relationships": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source_entity": {"type": "string"},
                            "target_entity": {"type": "string"},
                            "relationship_type": {"type": "string"},
                            "properties": {
                                "type": "object",
                                "properties": all_properties,
                                "additionalProperties": True
                            },
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "source_quotes": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["source_entity", "target_entity", "relationship_type"]
                    }
                }
            },
            "required": ["relationships"]
        }
    
    def _generate_secondary_entity_relationship_schema(self) -> Dict[str, Any]:
        """Generate JSON schema for secondary entity and relationship extraction (Pass 2)"""
        # Generate property schema for all entity types
        all_properties = {}
        for entity_def in self.schema.entities.values():
            for prop_name, prop_def in entity_def.properties.items():
                if prop_name not in all_properties:
                    all_properties[prop_name] = self._property_to_json_schema(prop_def)
        
        return {
            "type": "object",
            "properties": {
                "entities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "entity_type": {"type": "string"},
                            "name": {"type": "string"},
                            "properties": {
                                "type": "object",
                                "properties": all_properties,
                                "additionalProperties": True
                            },
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "source_quotes": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["entity_type", "name"]
                    }
                },
                "relationships": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source_entity": {"type": "string"},
                            "target_entity": {"type": "string"},
                            "relationship_type": {"type": "string"},
                            "properties": {
                                "type": "object",
                                "properties": all_properties,
                                "additionalProperties": True
                            },
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "source_quotes": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["source_entity", "target_entity", "relationship_type"]
                    }
                }
            },
            "required": ["entities", "relationships"]
        }
    
    def _generate_entity_and_code_schema(self, include_codes: bool = True) -> Dict[str, Any]:
        """Generate JSON schema for entity and code extraction"""
        # Generate property schema for all entity types
        all_properties = {}
        for entity_def in self.schema.entities.values():
            for prop_name, prop_def in entity_def.properties.items():
                if prop_name not in all_properties:
                    all_properties[prop_name] = self._property_to_json_schema(prop_def)
        
        schema = {
            "type": "object",
            "properties": {
                "entities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "entity_type": {"type": "string"},
                            "name": {"type": "string"},
                            "properties": {
                                "type": "object",
                                "properties": all_properties,
                                "additionalProperties": True
                            },
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "source_quotes": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["entity_type", "name"]
                    }
                }
            },
            "required": ["entities"]
        }
        
        if include_codes:
            schema["properties"]["codes"] = {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "definition": {"type": "string"},
                        "quotes": {"type": "array", "items": {"type": "string"}},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                    },
                    "required": ["name", "definition", "quotes"]
                }
            }
            schema["required"].append("codes")
        
        return schema
    
    def _property_to_json_schema(self, prop_def: PropertyDefinition) -> Dict[str, Any]:
        """Convert PropertyDefinition to JSON schema property"""
        if prop_def.type == PropertyType.TEXT:
            return {"type": "string"}
        elif prop_def.type == PropertyType.INTEGER:
            return {"type": "integer"}
        elif prop_def.type == PropertyType.FLOAT:
            return {"type": "number"}
        elif prop_def.type == PropertyType.BOOLEAN:
            return {"type": "boolean"}
        elif prop_def.type == PropertyType.DATE:
            # Use date-time format for compatibility with Gemini 2.5 Flash
            return {"type": "string", "format": "date-time"}
        elif prop_def.type == PropertyType.DATETIME:
            return {"type": "string", "format": "date-time"}
        elif prop_def.type == PropertyType.ENUM:
            return {"type": "string", "enum": prop_def.values or []}
        elif prop_def.type == PropertyType.LIST:
            return {"type": "array", "items": {"type": "string"}}
        elif prop_def.type == PropertyType.REFERENCE:
            return {"type": "string"}
        else:
            return {"type": "string"}  # Default fallback
    
    def _calculate_confidence_scores(self, parsed_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence scores for extracted data"""
        scores = {}
        
        # Handle None input
        if parsed_data is None:
            return scores
        
        for entity in parsed_data.get("entities", []):
            if "confidence" in entity:
                scores[f"entity_{entity.get('name', 'unknown')}"] = entity["confidence"]
        
        for relationship in parsed_data.get("relationships", []):
            if "confidence" in relationship:
                rel_key = f"rel_{relationship.get('source_entity', 'unknown')}_to_{relationship.get('target_entity', 'unknown')}"
                scores[rel_key] = relationship["confidence"]
        
        for code in parsed_data.get("codes", []):
            if "confidence" in code:
                scores[f"code_{code.get('name', 'unknown')}"] = code["confidence"]
        
        return scores
    
    async def _store_extraction_results(self, context: InterviewContext,
                                      results: List[ExtractionResult]):
        """Store extraction results in Neo4j"""
        logger.info(f"Storing extraction results for interview {context.interview_id}")
        
        # Collect all entities from all passes
        all_entities = []
        all_relationships = []
        all_codes = []
        
        for result in results:
            # Handle both dict and list formats for entities
            if isinstance(result.entities_found, dict):
                all_entities.extend(result.entities_found.values())
            else:
                all_entities.extend(result.entities_found)
                
            # Relationships are always lists
            all_relationships.extend(result.relationships_found)
            
            # Handle both dict and list formats for codes
            if isinstance(result.codes_found, dict):
                all_codes.extend(result.codes_found.values())
            else:
                all_codes.extend(result.codes_found)
        
        # Store entities
        entity_id_map = {}  # Map entity names/original IDs to Neo4j IDs
        for entity_data in all_entities:
            # Handle both 'type' and 'entity_type' field names
            entity_type = entity_data.get('entity_type') or entity_data.get('type', 'Unknown')
            entity_id = f"{context.interview_id}_{entity_type}_{uuid.uuid4().hex[:8]}"
            
            entity_node = EntityNode(
                id=entity_id,
                name=entity_data["name"],
                entity_type=entity_type,
                properties={
                    **entity_data.get("properties", {}),
                    "interview_id": context.interview_id,
                    "session_id": context.session_id,
                    "confidence": entity_data.get("confidence", 0.0),
                    "source_quotes": entity_data.get("source_quotes", []),
                    "type_definition": entity_data.get("type_definition", "")  # NEW: Include type definition
                }
            )
            
            await self.neo4j.create_entity(entity_node)
            # Map both by name and by original ID (if present)
            entity_id_map[entity_data["name"]] = entity_id
            if "id" in entity_data:
                entity_id_map[entity_data["id"]] = entity_id
            logger.debug(f"Stored entity: {entity_data['name']} -> {entity_id}")
        
        # Enhanced relationship validation and storage
        entity_names = [entity_data["name"] for entity_data in all_entities if entity_data.get("name")]
        
        valid_relationships = []
        validation_stats = {
            'total': len(all_relationships),
            'valid': 0,
            'fixed': 0,
            'rejected': 0
        }
        
        logger.info(f"Validating {len(all_relationships)} relationships against {len(entity_names)} entities")
        
        for i, rel_data in enumerate(all_relationships):
            is_valid, corrected_data, issues = self._validate_and_fix_relationship(
                rel_data, entity_names, fuzzy_threshold=0.8
            )
            
            if is_valid:
                valid_relationships.append(corrected_data)
                if issues:
                    validation_stats['fixed'] += 1
                    logger.debug(f"Fixed relationship {i}: {'; '.join(issues)}")
                else:
                    validation_stats['valid'] += 1
            else:
                validation_stats['rejected'] += 1
                logger.warning(f"Rejected relationship {i}: {'; '.join(issues)}")
        
        # Log validation results
        logger.info(f"Relationship validation completed: "
                   f"{validation_stats['valid']} valid, "
                   f"{validation_stats['fixed']} fixed, "
                   f"{validation_stats['rejected']} rejected")
        
        # Store validated relationships
        for rel_data in valid_relationships:
            source_entity = rel_data["source_entity"]
            target_entity = rel_data["target_entity"]
            
            # Map entity names to Neo4j IDs
            source_id = entity_id_map.get(source_entity) or source_entity
            target_id = entity_id_map.get(target_entity) or target_entity
            
            if source_id and target_id:
                relationship = RelationshipEdge(
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type=rel_data["relationship_type"],
                    properties={
                        **rel_data.get("properties", {}),
                        "interview_id": context.interview_id,
                        "confidence": rel_data.get("confidence", 0.0),
                        "source_quotes": rel_data.get("source_quotes", []),
                        "relationship_definition": rel_data.get("relationship_definition", "")  # NEW: Include relationship definition
                    }
                )
                
                await self.neo4j.create_relationship(relationship)
                logger.debug(f"Stored relationship: {source_entity} -> {target_entity}")
            else:
                logger.error(f"Entity mapping failed for validated relationship: {source_entity} -> {target_entity}")
                # This should not happen after validation, but log it for debugging
        
        # Store codes (using existing base Neo4j manager methods)
        code_id_map = {}  # Map code names to Neo4j IDs  
        for code_data in all_codes:
            code_id = f"{context.interview_id}_code_{uuid.uuid4().hex[:8]}"
            
            # Use base manager's create_code method
            await self.neo4j.create_code({
                'id': code_id,
                'name': code_data["name"],
                'definition': code_data.get("definition", ""),
                'confidence': code_data.get("confidence", 0.0),
                'session_id': context.session_id,
                'quotes': code_data.get("quotes", [])
            })
            
            # CRITICAL FIX: Map code name to database ID for semantic matching
            # Include multiple variations that LLM might return
            original_name = code_data["name"]
            code_id_map[original_name] = code_id
            
            # Add common LLM transformations
            code_id_map[original_name.upper()] = code_id
            code_id_map[original_name.lower()] = code_id
            code_id_map[f"code-{original_name.lower().replace(' ', '-')}"] = code_id
            code_id_map[f"code_{original_name.upper().replace(' ', '_')}"] = code_id
            code_id_map[original_name.replace(' ', '_').upper()] = code_id
            code_id_map[original_name.replace(' ', '-').lower()] = code_id
            
            logger.debug(f"Stored code: {original_name} -> {code_id} (with variations)")
            
        # Store the code ID mapping for use in quote-centric extraction
        context.code_id_map = code_id_map
        
        logger.info(f"Successfully stored {len(all_entities)} entities, {len(all_relationships)} relationships, {len(all_codes)} codes")

    async def _store_code_driven_results(self, context: InterviewContext, 
                                       extraction_result: ExtractionResult, 
                                       raw_extraction_data: dict):
        """
        Store code-driven extraction results with complete provenance chains
        
        Args:
            context: Interview context
            extraction_result: Parsed extraction result
            raw_extraction_data: Raw extraction data with theme hierarchy
        """
        logger.info(f"Storing code-driven results for interview {context.interview_id}")
        
        # Store entities with quote provenance
        entity_id_map = {}
        for entity_id, entity_data in extraction_result.entities_found.items():
            neo4j_entity_id = f"{context.interview_id}_{entity_data['type']}_{uuid.uuid4().hex[:8]}"
            
            entity_node = EntityNode(
                id=neo4j_entity_id,
                name=entity_data["name"],
                entity_type=entity_data["type"],
                properties={
                    **entity_data.get("properties", {}),
                    "interview_id": context.interview_id,
                    "session_id": context.session_id,
                    "confidence": entity_data.get("confidence", 0.8),
                    "quote_id": entity_data.get("quote_id", ""),  # Link to source quote
                    "theme_id": entity_data.get("theme_id", ""),  # Link to theme
                    "extraction_method": "code_driven"
                }
            )
            
            await self.neo4j.create_entity(entity_node)
            entity_id_map[entity_data["name"]] = neo4j_entity_id
            entity_id_map[entity_id] = neo4j_entity_id
            logger.debug(f"Stored code-driven entity: {entity_data['name']} -> {neo4j_entity_id}")
            
            # RELATIONSHIP FIX: Store entity for later relationship creation
            # (Will create relationships after quotes are stored and mapped)
        
        # Store relationships with quote provenance
        for rel_data in extraction_result.relationships_found:
            source_entity = rel_data.get('source_entity', '')
            target_entity = rel_data.get('target_entity', '')
            
            # Map entity names to Neo4j IDs
            source_id = entity_id_map.get(source_entity)
            target_id = entity_id_map.get(target_entity)
            
            if source_id and target_id:
                rel_id = f"{context.interview_id}_rel_{uuid.uuid4().hex[:8]}"
                
                relationship = RelationshipEdge(
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type=rel_data.get('relationship_type', 'RELATED'),
                    properties={
                        **rel_data.get("properties", {}),
                        "confidence": rel_data.get("confidence", 0.8),
                        "quote_id": rel_data.get("quote_id", ""),  # Link to source quote
                        "theme_id": rel_data.get("theme_id", ""),  # Link to theme
                        "context": rel_data.get("context", ""),
                        "extraction_method": "code_driven"
                    }
                )
                
                await self.neo4j.create_relationship(relationship)
                logger.debug(f"Stored code-driven relationship: {source_entity} -> {target_entity}")
        
        # Store themes as codes with complete quote linkage (100% coding rate)
        code_id_map = {}
        quote_id_map = {}
        
        for code_id, code_data in extraction_result.codes_found.items():
            neo4j_code_id = f"{context.interview_id}_theme_{uuid.uuid4().hex[:8]}"
            
            # Store theme as code
            await self.neo4j.create_code({
                'id': neo4j_code_id,
                'name': code_data["name"],
                'definition': code_data.get("description", ""),
                'confidence': code_data.get("confidence", 0.8),
                'session_id': context.session_id,
                'quotes': code_data.get("quotes", []),
                'extraction_method': 'code_driven',
                'theme_frequency': code_data.get("frequency", 1)
            })
            
            code_id_map[code_data["name"]] = neo4j_code_id
            code_id_map[code_id] = neo4j_code_id
            logger.debug(f"Stored code-driven theme: {code_data['name']} -> {neo4j_code_id}")
        
        # Store quotes with complete theme linkage (ensures 100% coding rate)
        quote_texts = extraction_result.metadata.get('quote_texts', {})
        quote_id_mapping = {}  # Map original quote IDs to Neo4j quote IDs
        
        for quote_id, quote_data in quote_texts.items():
            neo4j_quote_id = f"{context.interview_id}_quote_{uuid.uuid4().hex[:8]}"
            quote_id_mapping[quote_id] = neo4j_quote_id  # Store mapping
            
            # Create quote node with theme linkage
            created_quote_id = await self.neo4j.create_quote_node({
                'id': neo4j_quote_id,
                'text': quote_data['text'],
                'line_start': quote_data.get('line_start', 1),
                'line_end': quote_data.get('line_end', 1),
                'confidence': quote_data.get('confidence', 0.8),
                'interview_id': context.interview_id,
                'session_id': context.session_id,
                'theme_id': quote_data.get('theme_id', ''),
                'theme_name': quote_data.get('theme_name', ''),
                'extraction_method': 'code_driven'
            })
            
            # Create relationship between quote and theme (ensures 100% coding rate)
            theme_neo4j_id = code_id_map.get(quote_data.get('theme_id', ''))
            if theme_neo4j_id:
                await self.neo4j.link_quote_to_code(created_quote_id, theme_neo4j_id)
                logger.debug(f"Linked quote to theme: {created_quote_id} -> {theme_neo4j_id}")
            
            quote_id_map[quote_id] = neo4j_quote_id
        
        # Store code ID mapping for compatibility
        context.code_id_map = code_id_map
        context.quote_id_map = quote_id_map
        
        # CREATE ENTITY-QUOTE RELATIONSHIPS using the correct quote ID mapping
        relationships_created = 0
        for entity_id, entity_data in extraction_result.entities_found.items():
            original_quote_id = entity_data.get("quote_id")
            if original_quote_id and original_quote_id in quote_id_mapping:
                # Get the actual Neo4j quote ID
                neo4j_quote_id = quote_id_mapping[original_quote_id]
                neo4j_entity_id = entity_id_map.get(entity_id)
                
                if neo4j_entity_id:
                    try:
                        await self.neo4j.link_quote_to_entity(
                            quote_id=neo4j_quote_id,
                            entity_id=neo4j_entity_id,
                            relationship_type="MENTIONS"
                        )
                        relationships_created += 1
                        logger.info(f"Created MENTIONS relationship: {neo4j_quote_id} -> {entity_data['name']}")
                    except Exception as e:
                        logger.warning(f"Failed to create MENTIONS relationship for {entity_data['name']}: {e}")
        
        total_themes = len(extraction_result.codes_found)
        total_quotes = len(quote_texts)
        total_entities = len(extraction_result.entities_found)
        total_relationships = len(extraction_result.relationships_found)
        
        logger.info(f"Successfully stored code-driven results: {total_themes} themes, "
                   f"{total_quotes} quotes (100% coding rate), {total_entities} entities, "
                   f"{total_relationships} relationships, {relationships_created} MENTIONS relationships")

    def _build_comprehensive_schema(self) -> Dict[str, Any]:
        """
        Build a comprehensive JSON schema that includes all entity types, relationships, and codes
        for single-pass extraction.
        """
        return {
            "type": "object",
            "properties": {
                "entities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "type": {"type": "string"},
                            "name": {"type": "string"},
                            "properties": {"type": "object"}
                        },
                        "required": ["id", "type", "name"]
                    }
                },
                "relationships": {
                    "type": "array", 
                    "items": {
                        "type": "object",
                        "properties": {
                            "source_id": {"type": "string"},
                            "target_id": {"type": "string"},
                            "relationship_type": {"type": "string"},
                            "properties": {"type": "object"}
                        },
                        "required": ["source_id", "target_id", "relationship_type"]
                    }
                },
                "codes": {
                    "type": "array",
                    "items": {
                        "type": "object", 
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "definition": {"type": "string"},
                            "quote": {"type": "string"},
                            "entity_ids": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "confidence": {"type": "number"}
                        },
                        "required": ["id", "name", "quote"]
                    }
                }
            },
            "required": ["entities", "relationships", "codes"]
        }

    def _parse_single_pass_result(self, content: str, context: InterviewContext) -> ExtractionResult:
        """
        Parse the comprehensive extraction result from single-pass LLM call.
        """
        try:
            if isinstance(content, str):
                parsed_data = json.loads(content)
            else:
                parsed_data = content
            
            # Extract entities
            entities_data = parsed_data.get("entities", [])
            entities_found = {}
            for entity_data in entities_data:
                entity_id = entity_data.get("id", "")
                entities_found[entity_id] = {
                    "id": entity_id,
                    "type": entity_data.get("type", ""),
                    "name": entity_data.get("name", ""),
                    "properties": entity_data.get("properties", {})
                }
            
            # Extract relationships
            relationships_data = parsed_data.get("relationships", [])
            relationships_found = []
            for rel_data in relationships_data:
                relationships_found.append({
                    "source_id": rel_data.get("source_id", ""),
                    "target_id": rel_data.get("target_id", ""),
                    "relationship_type": rel_data.get("relationship_type", ""),
                    "properties": rel_data.get("properties", {})
                })
            
            # Extract codes
            codes_data = parsed_data.get("codes", [])
            codes_found = {}
            for code_data in codes_data:
                code_id = code_data.get("id", "")
                codes_found[code_id] = {
                    "id": code_id,
                    "name": code_data.get("name", ""),
                    "definition": code_data.get("definition", ""),
                    "quote": code_data.get("quote", ""),
                    "entity_ids": code_data.get("entity_ids", []),
                    "confidence": code_data.get("confidence", 0.8)
                }
            
            return ExtractionResult(
                pass_number=1,  # Single pass
                entities_found=entities_found,
                relationships_found=relationships_found,
                codes_found=codes_found,
                raw_response=content,
                success=True,
                error_message=None
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse single-pass extraction result: {e}")
            raise ExtractionError(f"JSON parsing error during extraction: {e}") from e

    def _parse_single_pass_result_from_dict(self, extraction_data: dict, context: InterviewContext) -> ExtractionResult:
        """
        Parse structured extraction result from native Gemini structured output
        
        Args:
            extraction_data: Already parsed dict from native Gemini structured output
            context: Interview context
            
        Returns:
            ExtractionResult with parsed entities, relationships, and codes
        """
        try:
            result = ExtractionResult(pass_number=1)
            
            # Parse entities (now a list)
            entities_list = extraction_data.get('entities', [])
            for entity_data in entities_list:
                entity_id = entity_data.get('id', str(uuid.uuid4()))
                result.entities_found[entity_id] = {
                    'id': entity_id,
                    'type': entity_data.get('type', 'Unknown'),
                    'name': entity_data.get('name', ''),
                    'properties': {},  # Simplified for now
                    'confidence': entity_data.get('confidence', 0.9),
                    'context': entity_data.get('context', ''),
                    'type_definition': entity_data.get('type_definition', '')  # NEW: Include type definition
                }
            
            # Parse relationships (handle both old and new field naming)
            relationships = extraction_data.get('relationships', [])
            for rel_data in relationships:
                # Get source and target entity names, with fallback to lookup by ID
                source_entity = rel_data.get('source_entity') or rel_data.get('source_entity_id', '')
                target_entity = rel_data.get('target_entity') or rel_data.get('target_entity_id', '')
                
                # If source/target are IDs, try to resolve to actual names from entities_found
                if source_entity and source_entity in result.entities_found:
                    source_name = result.entities_found[source_entity].get('name', source_entity)
                else:
                    source_name = source_entity
                    
                if target_entity and target_entity in result.entities_found:
                    target_name = result.entities_found[target_entity].get('name', target_entity)
                else:
                    target_name = target_entity
                
                result.relationships_found.append({
                    'id': rel_data.get('id', str(uuid.uuid4())),
                    'source_entity': source_name,  # Use resolved name
                    'target_entity': target_name,  # Use resolved name
                    'source_entity_id': source_entity,  # Keep original ID for reference
                    'target_entity_id': target_entity,  # Keep original ID for reference
                    'relationship_type': rel_data.get('relationship_type', 'RELATED'),
                    'properties': rel_data.get('properties', {}),
                    'confidence': rel_data.get('confidence', 0.9),
                    'context': rel_data.get('context', ''),
                    'relationship_definition': rel_data.get('relationship_definition', '')  # NEW: Include relationship definition
                })
            
            # Parse codes (now a list)
            codes_list = extraction_data.get('codes', [])
            for code_data in codes_list:
                code_id = code_data.get('id', str(uuid.uuid4()))
                result.codes_found[code_id] = {
                    'id': code_id,
                    'name': code_data.get('name', ''),
                    'description': code_data.get('description', ''),
                    'quotes': code_data.get('quotes', []),
                    'frequency': code_data.get('frequency', 1),
                    'confidence': code_data.get('confidence', 0.9)
                }
            
            # Set metadata
            result.metadata = {
                'interview_id': context.interview_id,
                'extraction_method': 'native_gemini_structured',
                'summary': extraction_data.get('summary', ''),
                'total_entities': extraction_data.get('total_entities', len(result.entities_found)),
                'total_relationships': extraction_data.get('total_relationships', len(result.relationships_found)),
                'total_codes': extraction_data.get('total_codes', len(result.codes_found)),
                'confidence_score': extraction_data.get('confidence_score', 0.9)
            }
            
            result.success = True
            logger.info(f"Successfully parsed single-pass result: {len(result.entities_found)} entities, "
                       f"{len(result.relationships_found)} relationships, {len(result.codes_found)} codes")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse single-pass result: {e}")
            raise ExtractionError(f"Failed to parse single-pass result: {str(e)}") from e

    def _parse_code_driven_result_from_dict(self, extraction_data: dict, context: InterviewContext) -> ExtractionResult:
        """
        Parse code-driven extraction result from native Gemini structured output
        
        Args:
            extraction_data: Already parsed dict from native Gemini structured output
            context: Interview context
            
        Returns:
            ExtractionResult with parsed themes converted to entities, relationships, and codes
        """
        try:
            result = ExtractionResult(pass_number=1)
            
            # Parse themes into codes with 100% coding rate by design
            themes_list = extraction_data.get('themes', [])
            total_quotes = 0
            
            for theme_data in themes_list:
                theme_id = str(uuid.uuid4())
                
                # Create code from theme
                result.codes_found[theme_id] = {
                    'id': theme_id,
                    'name': theme_data.get('name', ''),
                    'description': theme_data.get('description', ''),
                    'quotes': [],  # Will be populated with quote IDs
                    'frequency': theme_data.get('frequency', 1),
                    'confidence': theme_data.get('confidence', 0.8)
                }
                
                # Process supporting quotes for this theme
                supporting_quotes = theme_data.get('supporting_quotes', [])
                for quote_data in supporting_quotes:
                    total_quotes += 1
                    quote_id = str(uuid.uuid4())
                    
                    # Add quote ID to theme's quotes list (ensures 100% coding rate)
                    result.codes_found[theme_id]['quotes'].append(quote_id)
                    
                    # Store quote text for later reference (will be processed by storage method)
                    if not hasattr(result, 'metadata'):
                        result.metadata = {}
                    if 'quote_texts' not in result.metadata:
                        result.metadata['quote_texts'] = {}
                    
                    # Handle both string and dict formats for quotes
                    if isinstance(quote_data, str):
                        # LLM returned simple string format
                        result.metadata['quote_texts'][quote_id] = {
                            'text': quote_data,
                            'line_start': 1,  # Default since not provided
                            'line_end': 1,    # Default since not provided
                            'confidence': 0.8,
                            'theme_id': theme_id,
                            'theme_name': theme_data.get('name', ''),
                            'entities': [],   # Extract from text if needed
                            'relationships': []
                        }
                    else:
                        # LLM returned structured format (expected)
                        result.metadata['quote_texts'][quote_id] = {
                            'text': quote_data.get('text', ''),
                            'line_start': quote_data.get('line_start', 1),
                            'line_end': quote_data.get('line_end', 1),
                            'confidence': quote_data.get('confidence', 0.8),
                            'theme_id': theme_id,
                            'theme_name': theme_data.get('name', ''),
                            'entities': quote_data.get('entities', []),
                            'relationships': quote_data.get('relationships', [])
                        }
                    
                    # Extract entities from this quote (handle both string and dict formats)
                    if isinstance(quote_data, dict):
                        entities_list = quote_data.get('entities', [])
                        quote_text = quote_data.get('text', '')
                        quote_confidence = quote_data.get('confidence', 0.8)
                    else:
                        # FAIL-FAST: String format quotes are not allowed
                        error_msg = f"Quote in string format detected: '{quote_data}'. All quotes must be structured dictionaries with 'entities' field. This indicates LLM prompt validation failed."
                        logger.error(error_msg)
                        raise ExtractionError(error_msg)
                    
                    for entity_name in entities_list:
                        if entity_name:  # Skip empty entity names
                            entity_id = str(uuid.uuid4())
                            result.entities_found[entity_id] = {
                                'id': entity_id,
                                'type': 'Entity',  # Generic type, could be refined
                                'name': entity_name,
                                'properties': {},
                                'confidence': quote_confidence,
                                'context': quote_text,  # Quote provides context
                                'quote_id': quote_id,  # Link back to source quote
                                'theme_id': theme_id   # Link back to theme
                            }
                    
                    # Extract relationships from this quote (handle both string and dict formats)
                    if isinstance(quote_data, dict):
                        relationships_list = quote_data.get('relationships', [])
                    else:
                        relationships_list = []  # No relationships extracted from string format
                    
                    for rel_data in relationships_list:
                        result.relationships_found.append({
                            'id': str(uuid.uuid4()),
                            'source_entity': rel_data.get('source_entity', ''),
                            'target_entity': rel_data.get('target_entity', ''),
                            'relationship_type': rel_data.get('relationship_type', 'RELATED'),
                            'properties': {},
                            'confidence': rel_data.get('confidence', 0.8),
                            'context': rel_data.get('context', quote_text),
                            'quote_id': quote_id,  # Link back to source quote
                            'theme_id': theme_id   # Link back to theme
                        })
            
            # Set metadata with code-driven specific info
            result.metadata = {
                'interview_id': context.interview_id,
                'extraction_method': 'code_driven',
                'summary': extraction_data.get('summary', ''),
                'total_themes': extraction_data.get('total_themes', len(result.codes_found)),
                'total_quotes': extraction_data.get('total_quotes', total_quotes),
                'total_entities': extraction_data.get('total_entities', len(result.entities_found)),
                'confidence_score': extraction_data.get('confidence_score', 0.8),
                'coding_rate': 1.0 if total_quotes > 0 else 0.0,  # 100% by design
                'quote_texts': result.metadata.get('quote_texts', {})
            }
            
            result.success = True
            logger.info(f"Successfully parsed code-driven result: {len(result.codes_found)} themes, "
                       f"{total_quotes} quotes (100% coding rate), {len(result.entities_found)} entities, "
                       f"{len(result.relationships_found)} relationships")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse code-driven result: {e}")
            raise ExtractionError(f"Failed to parse code-driven result: {str(e)}") from e

    async def _extract_and_store_quotes(self, context: InterviewContext, 
                                      extraction_result: ExtractionResult):
        """
        Quote-centric extraction: Extract semantic quotes and create relationships
        
        This implements the critical semantic quote extraction as specified in CLAUDE.md,
        replacing line-based extraction with semantic unit analysis and LLM-based
        relationship matching.
        
        Args:
            context: Interview context with text and metadata
            extraction_result: Results from entity/code extraction
        """
        try:
            # Step 1: Extract semantic quotes from interview text
            logger.info(f"Extracting semantic quotes from interview {context.interview_id}")
            quotes = self.quote_extractor.extract_quotes_from_interview(
                context.interview_text, 
                context.interview_id
            )
            
            logger.info(f"Extracted {len(quotes)} semantic quotes")
            
            # Step 2: Store quotes in Neo4j and update quote objects with database IDs
            quote_ids = []
            for quote in quotes:
                quote_data = quote.to_dict()
                quote_data['interview_id'] = context.interview_id
                
                quote_id = await self.neo4j.create_quote_node(quote_data)
                
                # CRITICAL FIX: Update the ExtractedQuote object with the database ID
                quote.id = quote_id
                quote_ids.append((quote_id, quote))
            
            logger.info(f"Stored {len(quote_ids)} quotes in Neo4j with IDs")
            
            # Step 3: Semantic matching between quotes and codes
            # CRITICAL FIX: Use actual database code IDs from the stored mapping
            code_id_map = getattr(context, 'code_id_map', {})
            logger.info(f"DEBUG: Available code_id_map keys: {list(code_id_map.keys())}")
            logger.info(f"DEBUG: Available code_id_map: {code_id_map}")
            
            # CRITICAL FIX: Build codes_list from actual stored codes in database, not extraction_result
            # Get the actual codes from Neo4j to ensure we have proper names and definitions
            # Use ID prefix matching since session_id/interview_id fields are None
            stored_codes = await self.neo4j.execute_cypher("""
                MATCH (c:Code) 
                WHERE c.id CONTAINS $interview_id
                RETURN c.name as name, c.definition as definition, c.id as id
            """, {"interview_id": context.interview_id})
            
            codes_list = [
                {
                    'name': code['name'],
                    'definition': code['definition'] or '',
                    'id': code['id']
                }
                for code in stored_codes
            ]
            
            logger.info(f"DEBUG: Found {len(stored_codes)} stored codes for semantic matching")
            if stored_codes:
                sample_codes = stored_codes[:3]
                for i, code in enumerate(sample_codes):
                    logger.info(f"DEBUG: Sample code {i+1}: name='{code['name']}', id='{code['id']}', definition='{code.get('definition', 'N/A')[:50]}...'")
            else:
                logger.warning("DEBUG: No stored codes found for semantic matching!")
            
            if codes_list:
                logger.info(f"Performing semantic matching between {len(quotes)} quotes and {len(codes_list)} codes")
                
                code_matches = await self.semantic_matcher.match_quotes_to_codes(quotes, codes_list)
                
                logger.info(f"Found {len(code_matches)} semantic code matches")
                
                # Create quote-code relationships using actual database IDs
                logger.info(f"DEBUG: Processing {len(code_matches)} matches for relationship creation")
                for i, match in enumerate(code_matches):
                    # CRITICAL FIX: Use actual database code ID instead of code name
                    code_db_id = code_id_map.get(match.code_name, match.code_name)
                    logger.info(f"DEBUG: Match {i+1}: quote_id={match.quote_id}, code_name={match.code_name}, code_db_id={code_db_id}")
                    
                    # Enhanced debug: Check if we found the database ID or just got the name back
                    if code_db_id == match.code_name:
                        logger.warning(f"DEBUG: Code ID lookup FAILED for '{match.code_name}' - using name as fallback")
                        logger.warning(f"DEBUG: Available code_id_map keys containing '{match.code_name}': {[k for k in code_id_map.keys() if match.code_name.lower() in k.lower()]}")
                    else:
                        logger.info(f"DEBUG: Code ID lookup SUCCESS: '{match.code_name}' -> '{code_db_id}'")
                    
                    try:
                        success = await self.neo4j.link_quote_to_code(
                            match.quote_id,
                            code_db_id,  # Use database ID not name
                            match.semantic_relationship.upper()
                        )
                        logger.info(f"DEBUG: Relationship creation {'SUCCESS' if success else 'FAILED'}")
                    except Exception as e:
                        logger.error(f"DEBUG: Relationship creation EXCEPTION: {e}")
            
            # Step 4: Semantic matching between quotes and entities
            entities_list = [
                {
                    'name': entity_name,
                    'type': entity_data.get('entity_type', ''),
                    'description': entity_data.get('description', ''),
                    'id': entity_data.get('id', entity_name)
                }
                for entity_name, entity_data in extraction_result.entities_found.items()
            ]
            
            if entities_list:
                logger.info(f"Performing semantic matching between {len(quotes)} quotes and {len(entities_list)} entities")
                
                entity_relationships = await self.semantic_matcher.analyze_quote_entity_relationships(quotes, entities_list)
                
                logger.info(f"Found {len(entity_relationships)} semantic entity relationships")
                
                # Create quote-entity relationships
                for relationship in entity_relationships:
                    await self.neo4j.link_quote_to_entity(
                        relationship['quote_id'],
                        relationship['entity_name'],
                        relationship['relationship_type'].upper(),
                        confidence=relationship['confidence']
                    )
            
            logger.info(f"Completed quote-centric extraction for interview {context.interview_id}")
            
        except Exception as e:
            logger.error(f"Quote extraction failed for {context.interview_id}: {e}")
            # Don't raise - quote extraction failure shouldn't stop the main pipeline
            # But log the issue for debugging


# Test the multi-pass extractor
async def test_multi_pass_extractor():
    """Test the multi-pass extraction system"""
    print("🧪 Testing Multi-Pass LLM Extraction Pipeline")
    print("=" * 60)
    
    # Load schema
    from schema_config import create_research_schema
    schema = create_research_schema()
    
    # Initialize Neo4j manager
    neo4j_manager = EnhancedNeo4jManager(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="qualitative123"
    )
    
    await neo4j_manager.connect()
    
    # Create extractor with real LLM
    extractor = MultiPassExtractor(
        neo4j_manager=neo4j_manager,
        schema=schema  # LLM client will be auto-created
    )
    
    # Create test interview context
    test_interview = """
    I spoke with Dr. Sarah Johnson, a senior researcher in the Methods Division at RAND Corporation. 
    She discussed how her team is adopting AI technologies for policy analysis. The organization, 
    which is a large public sector research institution, has been collaborating with Microsoft 
    on machine learning projects. Dr. Johnson mentioned that the complexity of these new 
    quantitative methods is quite high, but the AI tools they're using are helping with efficiency.
    """
    
    context = InterviewContext(
        interview_id="test_interview_001",
        interview_text=test_interview,
        session_id="test_session_001",
        filename="test_interview.txt"
    )
    
    # Run extraction
    print("\n🚀 Running multi-pass extraction...")
    try:
        results = await extractor.extract_from_interview(context)
        
        print(f"\n✅ Extraction completed with {len(results)} passes")
        
        for i, result in enumerate(results, 1):
            print(f"\n📊 Pass {i} Results:")
            print(f"  - Entities: {len(result.entities_found)}")
            print(f"  - Relationships: {len(result.relationships_found)}")
            print(f"  - Codes: {len(result.codes_found)}")
            print(f"  - Confidence scores: {len(result.confidence_scores)}")
            
            if result.entities_found:
                print("  - Sample entities:")
                for entity in result.entities_found[:2]:  # Show first 2
                    print(f"    • {entity['name']} ({entity['entity_type']})")
        
        # Test querying the stored data
        print("\n🔍 Testing stored data retrieval...")
        
        # Get all entities we just created
        people = await neo4j_manager.get_entities_by_type("Person")
        orgs = await neo4j_manager.get_entities_by_type("Organization")
        
        print(f"✅ Retrieved {len(people)} people and {len(orgs)} organizations from Neo4j")
        
        if people:
            person = people[0]
            print(f"📋 Sample person: {person.get('name')} ({person.get('division')})")
        
        # Clean up test data
        print("\n🧹 Cleaning up test data...")
        await neo4j_manager.execute_custom_cypher("""
            MATCH (e:Entity) 
            WHERE e.interview_id = 'test_interview_001'
            DETACH DELETE e
        """)
        print("✅ Cleaned up test entities")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"❌ Test failed: {e}")
    
    finally:
        await neo4j_manager.close()
    
    print("\n🎉 Multi-Pass Extraction Pipeline test completed!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_multi_pass_extractor())
