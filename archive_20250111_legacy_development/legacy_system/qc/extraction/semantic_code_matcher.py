"""
Semantic Code Matcher

LLM-based semantic matching for quote-code relationships.
Replaces naive keyword matching with intelligent semantic analysis
as specified in CLAUDE.md critical fixes.
"""

import logging
import asyncio
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

# Conditional imports for testing vs production
try:
    from ..core.llm_client import UniversalModelClient as LLMClient
    from .semantic_quote_extractor import ExtractedQuote
except ImportError:
    # For standalone testing
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from qc.core.llm_client import UniversalModelClient as LLMClient
    from qc.extraction.semantic_quote_extractor import ExtractedQuote

logger = logging.getLogger(__name__)


@dataclass
class CodeMatch:
    """Result of semantic code matching"""
    quote_id: str
    code_name: str
    confidence: float
    reasoning: str
    semantic_relationship: str  # "supports", "contradicts", "mentions", "exemplifies"


class SemanticCodeMatcher:
    """
    LLM-based semantic matching between quotes and codes.
    
    This addresses the critical flaw identified in CLAUDE.md where naive keyword 
    matching would fail in production due to the complexity of semantic relationships
    between quotes and qualitative codes.
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.confidence_threshold = 0.6
        
    async def match_quotes_to_codes(self, quotes: List[ExtractedQuote], 
                                  codes: List[Dict[str, Any]]) -> List[CodeMatch]:
        """
        Semantically match quotes to codes using LLM analysis
        
        Args:
            quotes: List of extracted quotes
            codes: List of code definitions with name and definition
            
        Returns:
            List of confident semantic matches
        """
        logger.info(f"Semantically matching {len(quotes)} quotes to {len(codes)} codes")
        
        matches = []
        
        # Process quotes in batches for efficiency
        batch_size = 5
        for i in range(0, len(quotes), batch_size):
            batch_quotes = quotes[i:i + batch_size]
            batch_matches = await self._process_quote_batch(batch_quotes, codes)
            matches.extend(batch_matches)
        
        # Filter by confidence threshold
        confident_matches = [m for m in matches if m.confidence >= self.confidence_threshold]
        
        logger.info(f"Found {len(confident_matches)} confident semantic matches")
        return confident_matches
    
    async def _process_quote_batch(self, quotes: List[ExtractedQuote], 
                                 codes: List[Dict[str, Any]]) -> List[CodeMatch]:
        """Process a batch of quotes for semantic matching"""
        
        # Prepare structured prompt for LLM analysis
        prompt = self._build_semantic_matching_prompt(quotes, codes)
        
        # Debug logging for troubleshooting safety issues
        logger.info(f"DEBUG: Sending prompt to LLM (length: {len(prompt)} chars)")
        logger.info(f"DEBUG: Processing {len(quotes)} quotes with {len(codes)} codes")
        logger.info(f"DEBUG: First 500 chars of prompt: {prompt[:500]}...")
        
        try:
            # Get LLM analysis
            response = await self.llm_client.generate(
                prompt,
                max_tokens=2000,
                temperature=0.1  # Low temperature for consistent analysis
            )
            
            # Parse LLM response into matches
            matches = self._parse_matching_response(response, quotes, codes)
            return matches
            
        except Exception as e:
            logger.error(f"LLM semantic matching failed: {e}")
            # Fallback to basic keyword matching with low confidence
            return self._fallback_keyword_matching(quotes, codes)
    
    def _build_semantic_matching_prompt(self, quotes: List[ExtractedQuote], 
                                      codes: List[Dict[str, Any]]) -> str:
        """Build structured prompt for semantic quote-code matching"""
        
        # Format quotes
        quotes_text = "\\n".join([
            f"QUOTE_{i+1}: \"{quote.text}\" (ID: {quote.id or f'memory_{id(quote)}'})"
            for i, quote in enumerate(quotes)
        ])
        
        # Format codes - use actual names to avoid confusion
        codes_text = "\\n".join([
            f"{code['name']}: {code['definition']}"
            for code in codes
        ])
        
        prompt = f"""This is an academic research analysis task for qualitative data coding.

RESEARCH CONTEXT: You are analyzing interview transcript excerpts to identify which quotes relate to specific research themes (codes). This is standard qualitative research methodology used in academic studies.

RESEARCH CODES (themes to identify):
{codes_text}

INTERVIEW QUOTES (text excerpts to analyze):
{quotes_text}

ANALYSIS TASK:
1. For each quote, determine if it relates to any of the research codes above
2. Focus on semantic meaning and content relevance
3. Rate confidence level from 0.0 to 1.0 for each potential match
4. Specify relationship type: supports, mentions, exemplifies, or contradicts

Please provide your analysis in this JSON format:
{{
  "matches": [
    {{
      "quote_id": "quote_identifier",
      "code_name": "theme_name",
      "confidence": 0.85,
      "reasoning": "explanation of relevance",
      "relationship_type": "supports"
    }}
  ]
}}

Include only matches with confidence 0.6 or higher. Focus on clear thematic connections."""
        
        return prompt
    
    def _parse_matching_response(self, response: str, quotes: List[ExtractedQuote],
                               codes: List[Dict[str, Any]]) -> List[CodeMatch]:
        """Parse LLM response into CodeMatch objects with robust error handling"""
        matches = []
        
        try:
            import json
            import re
            
            # Extract JSON from response with more robust parsing
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning("No JSON found in LLM response")
                return matches
            
            json_str = response[json_start:json_end]
            
            # Clean up common JSON formatting issues
            json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
            json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
            
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}")
                logger.debug(f"Problematic JSON: {json_str[:500]}...")
                return matches
            
            # Create quote ID mapping - CRITICAL FIX: Use actual database IDs
            quote_id_map = {}
            for quote in quotes:
                # Use database ID if available, otherwise fall back to memory ID
                if quote.id:
                    quote_id_map[quote.id] = quote
                quote_id_map[f'memory_{id(quote)}'] = quote
            
            # Create flexible code name mapping to handle variations
            code_name_map = {}
            for code in codes:
                original_name = code['name']
                code_name_map[original_name] = code
                # Add variations to handle LLM formatting
                code_name_map[original_name.upper()] = code
                code_name_map[original_name.lower()] = code
                code_name_map[f"CODE_{original_name.upper()}"] = code
                code_name_map[f"CODE-{original_name.upper()}"] = code
                code_name_map[original_name.replace(' ', '_').upper()] = code
            
            # Process matches
            for match_data in data.get('matches', []):
                quote_id = str(match_data.get('quote_id', ''))
                code_name = match_data.get('code_name', '')
                
                # Try to find the quote
                quote_match = quote_id_map.get(quote_id)
                if not quote_match:
                    logger.warning(f"Quote not found for ID: {quote_id}")
                    continue
                
                # Try to find the code with flexible matching
                code_match = code_name_map.get(code_name)
                if not code_match:
                    logger.warning(f"Code not found for name: {code_name}")
                    continue
                
                # CRITICAL FIX: Use the actual database quote ID if available
                actual_quote_id = quote_match.id if quote_match.id else quote_id
                actual_code_name = code_match['name']  # Use the original code name
                
                match = CodeMatch(
                    quote_id=actual_quote_id,
                    code_name=actual_code_name,
                    confidence=float(match_data.get('confidence', 0.0)),
                    reasoning=match_data.get('reasoning', ''),
                    semantic_relationship=match_data.get('relationship_type', 'mentions')
                )
                matches.append(match)
            
        except Exception as e:
            logger.error(f"Error parsing matching response: {e}")
        
        return matches
    
    def _fallback_keyword_matching(self, quotes: List[ExtractedQuote],
                                 codes: List[Dict[str, Any]]) -> List[CodeMatch]:
        """
        Fallback keyword matching with low confidence scores
        
        This is the old approach that would fail in production, but serves
        as a safety net if LLM analysis fails.
        """
        logger.info("Using fallback keyword matching (low confidence)")
        
        matches = []
        
        for quote in quotes:
            quote_text_lower = quote.text.lower()
            
            for code in codes:
                code_name = code['name']
                code_definition = code['definition'].lower()
                
                # Simple keyword presence check
                keywords = code_name.lower().split('_')
                keywords.extend(code_definition.split())
                
                keyword_matches = sum(1 for keyword in keywords 
                                    if len(keyword) > 3 and keyword in quote_text_lower)
                
                if keyword_matches > 0:
                    # Low confidence for fallback matching
                    confidence = min(0.5, keyword_matches * 0.1)
                    
                    match = CodeMatch(
                        quote_id=str(id(quote)),
                        code_name=code_name,
                        confidence=confidence,
                        reasoning=f"Keyword matching fallback ({keyword_matches} matches)",
                        semantic_relationship="mentions"
                    )
                    matches.append(match)
        
        return matches
    
    async def analyze_quote_entity_relationships(self, quotes: List[ExtractedQuote],
                                               entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze semantic relationships between quotes and entities
        
        Args:
            quotes: List of extracted quotes
            entities: List of entity definitions
            
        Returns:
            List of entity relationships with confidence scores
        """
        logger.info(f"Analyzing quote-entity relationships for {len(quotes)} quotes and {len(entities)} entities")
        
        relationships = []
        
        # Build entity analysis prompt
        entity_prompt = self._build_entity_matching_prompt(quotes, entities)
        
        try:
            response = await self.llm_client.generate(
                entity_prompt,
                max_tokens=2000,
                temperature=0.1
            )
            
            relationships = self._parse_entity_response(response, quotes, entities)
            
        except Exception as e:
            logger.error(f"Entity relationship analysis failed: {e}")
        
        return relationships
    
    def _build_entity_matching_prompt(self, quotes: List[ExtractedQuote],
                                    entities: List[Dict[str, Any]]) -> str:
        """Build prompt for entity-quote relationship analysis"""
        
        quotes_text = "\\n".join([
            f"QUOTE_{i+1}: \"{quote.text}\" (ID: {id(quote)})"
            for i, quote in enumerate(quotes)
        ])
        
        entities_text = "\\n".join([
            f"ENTITY_{entity['name'].upper()} ({entity['type']}): {entity.get('description', 'N/A')}"
            for entity in entities
        ])
        
        prompt = f"""This is an academic research analysis task for entity identification in interview data.

RESEARCH CONTEXT: You are analyzing interview transcript excerpts to identify mentions of specific entities (people, organizations, methods, tools). This is standard qualitative research analysis.

ENTITIES TO IDENTIFY:
{entities_text}

INTERVIEW QUOTES TO ANALYZE:
{quotes_text}

ANALYSIS TASK: For each quote, identify if it mentions or refers to any of the entities listed above, including:
1. Direct mentions by name
2. Indirect references or descriptions  
3. Contextual relationships

Please provide your analysis in this JSON format:
{{
  "relationships": [
    {{
      "quote_id": "quote_identifier", 
      "entity_name": "entity_name",
      "confidence": 0.85,
      "relationship_type": "mentions"
    }}
  ]
}}

Include only clear relationships with confidence 0.6 or higher."""
        
        return prompt
    
    def _parse_entity_response(self, response: str, quotes: List[ExtractedQuote],
                             entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse entity relationship response"""
        relationships = []
        
        try:
            import json
            
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > 0:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                quote_id_map = {str(id(quote)): quote for quote in quotes}
                entity_name_map = {entity['name']: entity for entity in entities}
                
                for rel_data in data.get('relationships', []):
                    quote_id = str(rel_data.get('quote_id', ''))
                    entity_name = rel_data.get('entity_name', '')
                    
                    if quote_id in quote_id_map and entity_name in entity_name_map:
                        relationships.append({
                            'quote_id': quote_id,
                            'entity_name': entity_name,
                            'confidence': float(rel_data.get('confidence', 0.0)),
                            'relationship_type': rel_data.get('relationship_type', 'mentions')
                        })
        
        except Exception as e:
            logger.error(f"Error parsing entity relationships: {e}")
        
        return relationships


async def test_semantic_code_matcher():
    """Test the semantic code matcher"""
    print("Testing Semantic Code Matcher")
    print("=" * 50)
    
    # Mock LLM client for testing
    class MockLLMClient:
        async def generate(self, prompt, max_tokens=1000, temperature=0.1):
            # Simulate LLM response
            return '''
            {
              "matches": [
                {
                  "quote_id": "123456789",
                  "code_name": "leadership",
                  "confidence": 0.85,
                  "reasoning": "Quote directly mentions leadership role and influence",
                  "relationship_type": "supports"
                },
                {
                  "quote_id": "987654321", 
                  "code_name": "training",
                  "confidence": 0.90,
                  "reasoning": "Quote discusses training programs and methods",
                  "relationship_type": "exemplifies"
                }
              ]
            }
            '''
    
    # Test data
    try:
        from .semantic_quote_extractor import ExtractedQuote, SemanticUnit
    except ImportError:
        from semantic_quote_extractor import ExtractedQuote, SemanticUnit
    
    quotes = [
        ExtractedQuote(
            text="Mouho was the force behind the CA training",
            line_start=11,
            line_end=11,
            semantic_type=SemanticUnit.SENTENCE,
            confidence=0.85
        ),
        ExtractedQuote(
            text="The training program was comprehensive and effective",
            line_start=15,
            line_end=15,
            semantic_type=SemanticUnit.SENTENCE,
            confidence=0.80
        )
    ]
    
    codes = [
        {
            'name': 'leadership',
            'definition': 'References to leadership roles, influence, and decision-making authority'
        },
        {
            'name': 'training',
            'definition': 'Discussion of training programs, methods, and effectiveness'
        }
    ]
    
    # Initialize matcher
    mock_llm = MockLLMClient()
    matcher = SemanticCodeMatcher(mock_llm)
    
    # Test matching
    print("Testing semantic code matching...")
    
    # Mock the id() function to return predictable values
    original_id = id
    def mock_id(obj):
        if obj.text == "Mouho was the force behind the CA training":
            return "123456789"
        elif obj.text == "The training program was comprehensive and effective":
            return "987654321"
        return original_id(obj)
    
    # Temporarily override id
    import builtins
    builtins.id = mock_id
    
    try:
        matches = await matcher.match_quotes_to_codes(quotes, codes)
        
        print(f"Found {len(matches)} semantic matches:")
        for match in matches:
            print(f"  Quote: {match.quote_id}")
            print(f"  Code: {match.code_name}")
            print(f"  Confidence: {match.confidence}")
            print(f"  Relationship: {match.semantic_relationship}")
            print(f"  Reasoning: {match.reasoning}")
            print()
    finally:
        # Restore original id function
        builtins.id = original_id
    
    print("Semantic Code Matcher test completed!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_semantic_code_matcher())