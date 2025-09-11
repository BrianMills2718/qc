#!/usr/bin/env python3
"""
Real Text Analyzer

Provides genuine LLM-based text analysis for extraction algorithms.
NO MOCKING - actual LLM integration required.
"""

from typing import Dict, Any, List, Optional
import logging
import json
import re
from .llm_handler import LLMHandler

logger = logging.getLogger(__name__)

class RealTextAnalyzer:
    """Genuine text analysis using LLM integration"""
    
    def __init__(self, llm_handler: LLMHandler):
        if llm_handler is None:
            raise ValueError("LLM handler is required - no mock implementations allowed")
        self.llm = llm_handler
    
    async def extract_concepts(self, text: str, methodology: str = "grounded_theory") -> List[Dict[str, Any]]:
        """Extract concepts from text using real LLM analysis"""
        if not text or not text.strip():
            return []
        
        prompt = self._build_concept_extraction_prompt(text, methodology)
        
        try:
            # CRITICAL: Must use actual LLM, not hardcoded responses
            response = await self.llm.complete_raw(prompt, temperature=0.1)
            concepts = self._parse_concept_response(response, text)
            
            # Validate that concepts are derived from input text
            self._validate_concept_authenticity(concepts, text)
            
            logger.info(f"Extracted {len(concepts)} concepts from {len(text)} characters of text")
            return concepts
            
        except Exception as e:
            logger.error(f"Real concept extraction failed: {e}")
            # FAIL FAST - no fallback to mock data
            raise RuntimeError(f"LLM analysis failed: {e}")
    
    async def identify_relationships(self, concepts: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """Identify relationships between concepts using LLM analysis"""
        if len(concepts) < 2:
            return []
        
        prompt = self._build_relationship_prompt(concepts, text)
        
        try:
            response = await self.llm.complete_raw(prompt, temperature=0.2)
            relationships = self._parse_relationship_response(response, concepts)
            
            logger.info(f"Identified {len(relationships)} relationships between {len(concepts)} concepts")
            return relationships
            
        except Exception as e:
            logger.error(f"Relationship analysis failed: {e}")
            raise RuntimeError(f"LLM relationship analysis failed: {e}")
    
    def _build_concept_extraction_prompt(self, text: str, methodology: str) -> str:
        """Build methodology-specific prompt for concept extraction"""
        if methodology == "grounded_theory":
            return f"""
Analyze the following interview text using grounded theory methodology. 
Extract key concepts, categories, and emerging themes from THIS SPECIFIC TEXT.

Interview Text:
{text}

For each concept identified, provide:
1. Concept name (short, descriptive, based on the text)
2. Definition derived from the text content
3. Supporting quotes directly from the text (exact matches)
4. Properties and dimensions found in the text
5. Confidence level (0.0-1.0) based on evidence strength

Return your analysis in JSON format with this structure:
{{
  "concepts": [
    {{
      "name": "concept_name_from_text",
      "definition": "definition based on text content",
      "quotes": ["exact quote from text", "another exact quote"],
      "properties": ["property1", "property2"],
      "dimensions": ["dimension1", "dimension2"],
      "confidence": 0.8
    }}
  ]
}}

CRITICAL: Only extract concepts that are actually present in this specific text. 
Do not use generic or template concepts. All quotes must be exact matches from the text.
"""
        else:
            return f"""
Analyze the following text for key concepts and themes using {methodology} approach.

Text:
{text}

Extract meaningful concepts with supporting evidence from the text provided.
Return analysis in JSON format with concepts array containing name, definition, quotes, and confidence.
All quotes must be exact matches from the provided text.
"""
    
    def _build_relationship_prompt(self, concepts: List[Dict[str, Any]], text: str) -> str:
        """Build prompt for relationship analysis"""
        concept_names = [c.get('name', 'unnamed') for c in concepts]
        concept_list = "\n".join([f"- {name}: {concept.get('definition', 'no definition')}" 
                                 for name, concept in zip(concept_names, concepts)])
        
        return f"""
Analyze the relationships between these concepts found in the text:

Concepts:
{concept_list}

Original Text:
{text}

Identify relationships between these concepts based on how they appear and interact in the text.
Return analysis in JSON format:

{{
  "relationships": [
    {{
      "concept1": "first_concept_name",
      "concept2": "second_concept_name",
      "relationship_type": "causes|influences|relates_to|contradicts|supports",
      "strength": 0.8,
      "evidence": "quote from text showing relationship"
    }}
  ]
}}

Only identify relationships that are actually evident in the text.
"""
    
    def _parse_concept_response(self, response: str, original_text: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured concept data"""
        concepts = []
        
        try:
            # Try to extract JSON from the response
            json_data = self._extract_json_from_response(response)
            
            if 'concepts' in json_data:
                for concept_data in json_data['concepts']:
                    # Validate and clean the concept data
                    concept = {
                        'name': concept_data.get('name', 'unnamed_concept'),
                        'definition': concept_data.get('definition', ''),
                        'quotes': concept_data.get('quotes', []),
                        'properties': concept_data.get('properties', []),
                        'dimensions': concept_data.get('dimensions', []),
                        'confidence': float(concept_data.get('confidence', 0.5))
                    }
                    
                    # Validate quotes are from original text
                    validated_quotes = []
                    for quote in concept.get('quotes', []):
                        if quote and quote.strip() in original_text:
                            validated_quotes.append(quote.strip())
                    concept['quotes'] = validated_quotes
                    
                    concepts.append(concept)
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            # Try to extract concepts from plain text response
            concepts = self._parse_plain_text_concepts(response, original_text)
        
        return concepts
    
    def _parse_relationship_response(self, response: str, concepts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse LLM response into structured relationship data"""
        relationships = []
        
        try:
            json_data = self._extract_json_from_response(response)
            
            if 'relationships' in json_data:
                concept_names = [c.get('name') for c in concepts]
                
                for rel_data in json_data['relationships']:
                    # Validate relationship concepts exist
                    concept1 = rel_data.get('concept1', '')
                    concept2 = rel_data.get('concept2', '')
                    
                    if concept1 in concept_names and concept2 in concept_names:
                        relationship = {
                            'concept1': concept1,
                            'concept2': concept2,
                            'relationship_type': rel_data.get('relationship_type', 'relates_to'),
                            'strength': float(rel_data.get('strength', 0.5)),
                            'evidence': rel_data.get('evidence', '')
                        }
                        relationships.append(relationship)
        
        except Exception as e:
            logger.warning(f"Failed to parse relationship response: {e}")
        
        return relationships
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response text"""
        # Try to find JSON block in response
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        else:
            # Try to find JSON object in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
            else:
                json_text = response
        
        return json.loads(json_text)
    
    def _parse_plain_text_concepts(self, response: str, original_text: str) -> List[Dict[str, Any]]:
        """Fallback parser for plain text responses"""
        concepts = []
        
        # Simple pattern matching for concept extraction
        lines = response.split('\n')
        current_concept = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('Concept:') or line.startswith('Name:'):
                if current_concept:
                    concepts.append(current_concept)
                current_concept = {
                    'name': line.split(':', 1)[1].strip(),
                    'definition': '',
                    'quotes': [],
                    'properties': [],
                    'dimensions': [],
                    'confidence': 0.5
                }
            elif current_concept and line.startswith('Definition:'):
                current_concept['definition'] = line.split(':', 1)[1].strip()
            elif current_concept and line.startswith('Quote:'):
                quote = line.split(':', 1)[1].strip().strip('"\'')
                if quote in original_text:
                    current_concept['quotes'].append(quote)
        
        if current_concept:
            concepts.append(current_concept)
        
        return concepts
    
    def _validate_concept_authenticity(self, concepts: List[Dict[str, Any]], original_text: str):
        """Validate that concepts are genuinely derived from input text"""
        for concept in concepts:
            # Check that quotes exist and come from original text
            quotes = concept.get('quotes', [])
            invalid_quotes = []
            
            for quote in quotes:
                if quote and quote.strip() not in original_text:
                    invalid_quotes.append(quote)
            
            if invalid_quotes:
                logger.warning(f"Concept '{concept.get('name')}' contains invalid quotes: {invalid_quotes}")
                # Remove invalid quotes rather than failing
                concept['quotes'] = [q for q in quotes if q and q.strip() in original_text]
        
        # Check for suspicious hardcoded concept names
        hardcoded_concepts = ['technology_integration', 'methodological_challenges']
        for concept in concepts:
            concept_name = concept.get('name', '').lower()
            if concept_name in hardcoded_concepts:
                # Verify this concept is actually relevant to the input text
                text_lower = original_text.lower()
                concept_keywords = concept_name.replace('_', ' ').split()
                if not any(keyword in text_lower for keyword in concept_keywords):
                    logger.warning(f"Suspicious hardcoded concept detected: '{concept_name}' may not be relevant to input")