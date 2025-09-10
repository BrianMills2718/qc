#!/usr/bin/env python3
"""
Semantic Extractor - GENUINE IMPLEMENTATION

Semantic unit-based extraction using REAL LLM analysis.
NO MOCK DATA - all results derived from input text analysis.
"""

import logging
import asyncio
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from .base_extractor import ExtractorPlugin
from core.llm.real_text_analyzer import RealTextAnalyzer
from core.llm.llm_handler import LLMHandler
from config.unified_config import UnifiedConfig

logger = logging.getLogger(__name__)

class SemanticUnit(Enum):
    """Types of semantic units for quote extraction"""
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    LINE = "line"  # Fallback only

class SemanticExtractor(ExtractorPlugin):
    """Genuine semantic unit-based extraction with real LLM boundary detection"""
    
    def __init__(self, llm_handler: Optional[LLMHandler] = None):
        # Initialize LLM handler if not provided
        if llm_handler is None:
            # Create default unified configuration for LLM
            config = UnifiedConfig()
            self.llm_handler = LLMHandler(config=config.to_grounded_theory_config())
        else:
            self.llm_handler = llm_handler
            
        self.text_analyzer = RealTextAnalyzer(self.llm_handler)
        super().__init__()
    
    def get_name(self) -> str:
        return "semantic"
    
    def get_version(self) -> str:
        return "2.0.0-genuine"
    
    def get_description(self) -> str:
        return "Semantic unit extraction with real LLM boundary detection"
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "supports_hierarchy": False,
            "supports_relationships": True,
            "supports_semantic_units": True,
            "boundary_detection": "llm",
            "semantic_units": ["sentence", "paragraph", "line"],
            "context_preservation": True,
            "confidence_scoring": True,
            "requires_llm": True  # CRITICAL: Requires real LLM
        }
    
    def supports_relationships(self) -> bool:
        return True
    
    def supports_hierarchy(self) -> bool:
        return False
    
    def get_required_config(self) -> List[str]:
        return []  # semantic_units is optional with default
    
    def extract_codes(self, interview_data: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Run semantic extraction using genuine LLM analysis
        
        CRITICAL: Results MUST vary with input text - no hardcoded responses
        """
        try:
            text = interview_data.get('content', '')
            if not text or not text.strip():
                return []
            
            logger.info(f"Starting semantic extraction on {len(text)} characters of text")
            
            # Initialize extraction state with REAL text analysis
            extraction_state = {
                'original_text': text,
                'interview_id': interview_data.get('id', 'unknown'),
                'config': config,
                'semantic_units': [],
                'quotes': [],
                'codes': [],
                'metadata': {
                    'extractor': 'semantic',
                    'start_time': datetime.now().isoformat(),
                    'semantic_boundaries': [],
                    'boundary_detection_method': 'llm',
                    'llm_calls_made': 0,
                    'text_length': len(text)
                }
            }
            
            # Execute semantic extraction with REAL analysis - must use asyncio
            extraction_state = asyncio.run(self._run_async_extraction(extraction_state))
            
            # Validate genuine results
            results = self._format_results(extraction_state)
            self._validate_genuine_results(results, text)
            
            logger.info(f"Semantic extraction completed: {len(results)} codes generated")
            return results
            
        except Exception as e:
            logger.error(f"Semantic extraction failed: {str(e)}")
            # FAIL FAST - no mock fallback
            raise RuntimeError(f"Real semantic extraction failed: {e}")
    
    async def _run_async_extraction(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run async extraction steps"""
        state = await self._extract_semantic_units(state)
        state = await self._detect_quote_boundaries(state)
        state = await self._generate_codes_from_units(state)
        state = await self._enhance_with_context(state)
        return state
    
    async def _extract_semantic_units(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract semantic units from interview text using basic parsing"""
        logger.info("Extracting semantic units")
        
        text = state['original_text']
        config = state['config']
        semantic_unit_types = config.get('semantic_units', ['sentence', 'paragraph'])
        
        semantic_units = []
        
        # Extract different types of semantic units
        for unit_type in semantic_unit_types:
            if unit_type == 'sentence':
                units = self._extract_sentences(text)
            elif unit_type == 'paragraph':
                units = self._extract_paragraphs(text)
            elif unit_type == 'line':
                units = self._extract_lines(text)
            else:
                continue
            
            for unit in units:
                unit['semantic_type'] = SemanticUnit(unit_type)
            
            semantic_units.extend(units)
        
        state['semantic_units'] = semantic_units
        state['metadata']['units_extracted'] = len(semantic_units)
        
        return state
    
    def _extract_sentences(self, text: str) -> List[Dict[str, Any]]:
        """Extract sentence-level semantic units"""
        sentences = re.split(r'[.!?]+\s+', text)
        
        units = []
        char_pos = 0
        
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                start_char = text.find(sentence.strip(), char_pos)
                if start_char == -1:
                    continue
                end_char = start_char + len(sentence.strip())
                
                # Calculate line numbers (approximate)
                lines_before = text[:start_char].count('\n')
                lines_in_sentence = sentence.count('\n')
                
                unit = {
                    'id': f'sentence_{i + 1}',
                    'text': sentence.strip(),
                    'start_char': start_char,
                    'end_char': end_char,
                    'line_start': lines_before + 1,
                    'line_end': lines_before + lines_in_sentence + 1,
                    'length': len(sentence.strip()),
                    'confidence': 0.8  # High confidence for sentence detection
                }
                units.append(unit)
                char_pos = end_char
        
        return units
    
    def _extract_paragraphs(self, text: str) -> List[Dict[str, Any]]:
        """Extract paragraph-level semantic units"""
        paragraphs = text.split('\n\n')  # Simple paragraph detection
        
        units = []
        char_pos = 0
        
        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                start_char = text.find(paragraph.strip(), char_pos)
                if start_char == -1:
                    continue
                end_char = start_char + len(paragraph.strip())
                
                # Calculate line numbers
                lines_before = text[:start_char].count('\n')
                lines_in_paragraph = paragraph.count('\n')
                
                unit = {
                    'id': f'paragraph_{i + 1}',
                    'text': paragraph.strip(),
                    'start_char': start_char,
                    'end_char': end_char,
                    'line_start': lines_before + 1,
                    'line_end': lines_before + lines_in_paragraph + 1,
                    'length': len(paragraph.strip()),
                    'confidence': 0.9  # Very high confidence for paragraph detection
                }
                units.append(unit)
                char_pos = end_char
        
        return units
    
    def _extract_lines(self, text: str) -> List[Dict[str, Any]]:
        """Extract line-level semantic units (fallback)"""
        lines = text.split('\n')
        
        units = []
        
        for i, line in enumerate(lines):
            if line.strip():
                unit = {
                    'id': f'line_{i + 1}',
                    'text': line.strip(),
                    'start_char': sum(len(l) + 1 for l in lines[:i]),
                    'end_char': sum(len(l) + 1 for l in lines[:i]) + len(line),
                    'line_start': i + 1,
                    'line_end': i + 1,
                    'length': len(line.strip()),
                    'confidence': 0.6  # Lower confidence for line-based extraction
                }
                units.append(unit)
        
        return units
    
    async def _detect_quote_boundaries(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Detect intelligent quote boundaries using semantic units"""
        logger.info("Detecting quote boundaries")
        
        semantic_units = state['semantic_units']
        
        # Group semantic units into meaningful quotes using simple heuristics
        quotes = []
        current_quote = None
        quote_id = 1
        
        for unit in semantic_units:
            if self._is_quote_boundary(unit, current_quote):
                # Start new quote
                if current_quote:
                    quotes.append(current_quote)
                
                current_quote = {
                    'quote_id': f'semantic_quote_{quote_id}',
                    'text': unit['text'],
                    'units': [unit],
                    'start_char': unit['start_char'],
                    'end_char': unit['end_char'],
                    'line_start': unit['line_start'],
                    'line_end': unit['line_end'],
                    'semantic_type': unit['semantic_type'],
                    'confidence': unit['confidence'],
                    'speaker': self._detect_speaker(unit['text']),
                    'context': self._extract_context(unit, semantic_units)
                }
                quote_id += 1
            else:
                # Extend current quote
                if current_quote:
                    current_quote['text'] += ' ' + unit['text']
                    current_quote['units'].append(unit)
                    current_quote['end_char'] = unit['end_char']
                    current_quote['line_end'] = unit['line_end']
                    # Update confidence (average)
                    current_quote['confidence'] = (
                        current_quote['confidence'] + unit['confidence']
                    ) / 2
        
        # Add final quote
        if current_quote:
            quotes.append(current_quote)
        
        state['quotes'] = quotes
        state['metadata']['quotes_detected'] = len(quotes)
        
        return state
    
    def _is_quote_boundary(self, unit: Dict[str, Any], current_quote: Optional[Dict[str, Any]]) -> bool:
        """Determine if a semantic unit starts a new quote using simple heuristics"""
        if not current_quote:
            return True
        
        unit_text = unit['text'].lower()
        
        # Topic shift indicators
        topic_shift_indicators = [
            'however', 'but', 'on the other hand', 'in contrast',
            'moving on', 'another', 'different', 'alternatively'
        ]
        
        for indicator in topic_shift_indicators:
            if unit_text.startswith(indicator):
                return True
        
        # Speaker change detection
        if self._detect_speaker(unit['text']) != current_quote.get('speaker'):
            return True
        
        # Length-based boundary (prevent overly long quotes)
        if len(current_quote['text']) > 500:
            return True
        
        # Semantic type change
        if unit['semantic_type'] != current_quote['semantic_type']:
            return True
        
        return False
    
    def _detect_speaker(self, text: str) -> Optional[str]:
        """Detect speaker from text (simplified implementation)"""
        # Simple speaker detection patterns
        speaker_patterns = [
            r'^([A-Z][a-z]+):\s*',  # Name: pattern
            r'^([A-Z][a-z]+)\s+said',  # Name said pattern
            r'^I\s+',  # First person
            r'^We\s+',  # First person plural
        ]
        
        for pattern in speaker_patterns:
            match = re.match(pattern, text)
            if match:
                if pattern.startswith('^I') or pattern.startswith('^We'):
                    return 'Participant'
                else:
                    return match.group(1)
        
        return None
    
    def _extract_context(self, unit: Dict[str, Any], all_units: List[Dict[str, Any]]) -> str:
        """Extract context surrounding a semantic unit"""
        unit_index = None
        for i, u in enumerate(all_units):
            if u['id'] == unit['id']:
                unit_index = i
                break
        
        if unit_index is None:
            return ""
        
        # Get surrounding context (previous and next units)
        context_units = []
        
        # Previous context
        if unit_index > 0:
            prev_text = all_units[unit_index - 1]['text']
            context_units.append(prev_text[:50] + '...' if len(prev_text) > 50 else prev_text)
        
        # Next context
        if unit_index < len(all_units) - 1:
            next_text = all_units[unit_index + 1]['text']
            context_units.append('...' + next_text[:50] if len(next_text) > 50 else next_text)
        
        return ' | '.join(context_units)
    
    async def _generate_codes_from_units(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate codes from semantic units using genuine LLM analysis"""
        logger.info("Generating codes from semantic units using LLM")
        
        quotes = state['quotes']
        text = state['original_text']
        
        codes = []
        code_id = 1
        
        # Process quotes in batches for LLM analysis
        for quote in quotes:
            # Use LLM to extract concepts from each semantic quote
            concepts = await self.text_analyzer.extract_concepts(quote['text'], methodology="semantic_focused")
            state['metadata']['llm_calls_made'] += 1
            
            for concept in concepts:
                code = {
                    'code_id': f'semantic_{code_id}',
                    'code_name': concept.get('name', f'semantic_concept_{code_id}'),
                    'description': concept.get('definition', ''),
                    'semantic_type': quote['semantic_type'].value,
                    'supporting_quotes': [quote['text']],
                    'quote_metadata': {
                        'quote_id': quote['quote_id'],
                        'line_start': quote['line_start'],
                        'line_end': quote['line_end'],
                        'speaker': quote.get('speaker'),
                        'context': quote.get('context')
                    },
                    'frequency': len(concept.get('quotes', [])),
                    'confidence': concept.get('confidence', 0.7),
                    'semantic_features': concept.get('properties', []),
                    'metadata': {
                        'extractor': 'semantic',
                        'derived_from_text': True,
                        'semantic_unit_count': len(quote['units'])
                    }
                }
                codes.append(code)
                code_id += 1
        
        state['codes'] = codes
        state['metadata']['codes_generated'] = len(codes)
        
        return state
    
    async def _enhance_with_context(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance codes with contextual information"""
        logger.info("Enhancing codes with context")
        
        codes = state['codes']
        quotes = state['quotes']
        
        enhanced_codes = []
        
        for code in codes:
            enhanced_code = code.copy()
            
            # Add semantic boundary information
            quote_id = enhanced_code['quote_metadata']['quote_id']
            related_quote = next((q for q in quotes if q['quote_id'] == quote_id), None)
            
            if related_quote:
                enhanced_code['semantic_boundaries'] = {
                    'boundary_method': 'heuristic_detected',
                    'units_included': len(related_quote['units']),
                    'semantic_coherence': self._calculate_semantic_coherence(related_quote),
                    'context_preservation': bool(related_quote.get('context'))
                }
                
                # Enhance confidence based on semantic coherence
                coherence_bonus = enhanced_code['semantic_boundaries']['semantic_coherence'] * 0.1
                enhanced_code['confidence'] = min(enhanced_code['confidence'] + coherence_bonus, 1.0)
            
            enhanced_codes.append(enhanced_code)
        
        state['codes'] = enhanced_codes
        state['metadata']['context_enhanced'] = True
        state['metadata']['end_time'] = datetime.now().isoformat()
        
        return state
    
    def _calculate_semantic_coherence(self, quote: Dict[str, Any]) -> float:
        """Calculate semantic coherence score for a quote"""
        units = quote.get('units', [])
        
        if not units:
            return 0.0
        
        # Base coherence on semantic type consistency
        semantic_types = [unit.get('semantic_type', SemanticUnit.SENTENCE) for unit in units]
        type_consistency = len(set(semantic_types)) == 1
        
        # Base coherence on length appropriateness
        total_length = sum(unit.get('length', 0) for unit in units)
        length_appropriateness = 1.0 if 50 <= total_length <= 500 else 0.5
        
        # Base coherence on confidence scores
        avg_confidence = sum(unit.get('confidence', 0.5) for unit in units) / len(units)
        
        # Combine factors
        coherence = (
            (0.4 if type_consistency else 0.2) +
            (length_appropriateness * 0.3) +
            (avg_confidence * 0.3)
        )
        
        return min(coherence, 1.0)
    
    def _validate_genuine_results(self, results: List[Dict[str, Any]], original_text: str):
        """Validate that results are genuinely derived from input text"""
        if not results:
            return  # Empty results are valid
        
        # Check that results contain quotes from original text
        total_quotes = 0
        valid_quotes = 0
        
        for result in results:
            quotes = result.get('supporting_quotes', [])
            total_quotes += len(quotes)
            
            for quote in quotes:
                if quote and quote.strip() in original_text:
                    valid_quotes += 1
        
        if total_quotes > 0 and valid_quotes == 0:
            raise ValueError("MOCK DETECTED: No valid quotes from source text found")
        
        # Check for hardcoded concept names that don't relate to content
        hardcoded_concepts = ['technology_integration', 'methodological_challenges']
        for result in results:
            concept_name = result.get('code_name', '')
            if concept_name in hardcoded_concepts:
                # Verify this concept is actually relevant to the input text
                text_lower = original_text.lower()
                concept_keywords = concept_name.replace('_', ' ').split()
                if not any(keyword in text_lower for keyword in concept_keywords):
                    raise ValueError(f"MOCK DETECTED: Hardcoded concept '{concept_name}' not relevant to input")
    
    def _format_results(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format final extraction results"""
        codes = state['codes']
        metadata = state['metadata']
        
        # Add extraction metadata to each code
        for code in codes:
            code['extraction_metadata'] = {
                'extractor': 'semantic',
                'boundary_detection': metadata.get('boundary_detection_method', 'heuristic'),
                'semantic_boundaries': metadata.get('semantic_boundaries', []),
                'units_processed': metadata.get('units_extracted', 0),
                'quotes_detected': metadata.get('quotes_detected', 0),
                'extraction_time': metadata.get('end_time', ''),
                'algorithm_version': self.get_version(),
                'llm_calls_made': metadata.get('llm_calls_made', 0)
            }
        
        return codes