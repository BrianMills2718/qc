#!/usr/bin/env python3
"""
Relationship Extractor - GENUINE IMPLEMENTATION

3-pass relationship-focused extraction using REAL LLM analysis.
NO MOCK DATA - all results derived from input text analysis.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from .base_extractor import ExtractorPlugin, ExtractionPhase
from core.llm.real_text_analyzer import RealTextAnalyzer
from core.llm.llm_handler import LLMHandler
from config.unified_config import UnifiedConfig

logger = logging.getLogger(__name__)

class RelationshipExtractor(ExtractorPlugin):
    """Genuine 3-pass relationship-focused extraction algorithm"""
    
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
        return "relationship"
    
    def get_version(self) -> str:
        return "2.0.0-genuine"
    
    def get_description(self) -> str:
        return "3-pass relationship discovery using real LLM analysis"
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "supports_hierarchy": False,
            "supports_relationships": True,
            "supports_entities": True,
            "passes": ["entity", "relationship", "gap_filling"],
            "relationship_types": ["RELATES_TO", "CAUSES", "EXEMPLIFIES", "INFLUENCES"],
            "confidence_scoring": True,
            "gap_filling": True,
            "requires_llm": True  # CRITICAL: Requires real LLM
        }
    
    def supports_relationships(self) -> bool:
        return True
    
    def supports_hierarchy(self) -> bool:
        return False
    
    def get_required_config(self) -> List[str]:
        return []  # relationship_threshold is optional with default
    
    def extract_codes(self, interview_data: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Run 3-pass relationship extraction using genuine LLM analysis
        
        CRITICAL: Results MUST vary with input text - no hardcoded responses
        """
        try:
            text = interview_data.get('content', '')
            if not text or not text.strip():
                return []
            
            logger.info(f"Starting relationship extraction on {len(text)} characters of text")
            
            # Initialize extraction state with REAL text analysis
            extraction_state = {
                'original_text': text,
                'interview_id': interview_data.get('id', 'unknown'),
                'config': config,
                'entities': {},
                'codes': [],
                'relationships': [],
                'pass_results': [],
                'metadata': {
                    'extractor': 'relationship',
                    'start_time': datetime.now().isoformat(),
                    'passes_completed': [],
                    'llm_calls_made': 0,
                    'text_length': len(text)
                }
            }
            
            # Execute 3 passes with REAL analysis - must use asyncio
            extraction_state = asyncio.run(self._run_async_extraction(extraction_state))
            
            # Validate genuine results
            results = self._format_results(extraction_state)
            self._validate_genuine_results(results, text)
            
            logger.info(f"Relationship extraction completed: {len(results)} codes generated")
            return results
            
        except Exception as e:
            logger.error(f"Relationship extraction failed: {str(e)}")
            # FAIL FAST - no mock fallback
            raise RuntimeError(f"Real relationship extraction failed: {e}")
    
    async def _run_async_extraction(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run async extraction passes"""
        state = await self._run_pass_1_entities(state)
        state = await self._run_pass_2_relationships(state)
        state = await self._run_pass_3_gap_filling(state)
        return state
    
    async def _run_pass_1_entities(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Pass 1: Real entity extraction using LLM analysis"""
        logger.info("Pass 1: Real entity extraction")
        
        text = state['original_text']
        
        # GENUINE LLM-based concept extraction focused on entities
        concepts = await self.text_analyzer.extract_concepts(text, methodology="relationship_focused")
        state['metadata']['llm_calls_made'] += 1
        
        # Convert concepts to entity-focused codes format
        entity_codes = []
        for i, concept in enumerate(concepts):
            code = {
                'code_id': f"rel_ent_{i+1}",
                'code_name': concept.get('name', f'entity_{i+1}'),
                'description': concept.get('definition', ''),
                'quotes': concept.get('quotes', []),
                'confidence': concept.get('confidence', 0.0),
                'properties': concept.get('properties', []),
                'dimensions': concept.get('dimensions', []),
                'entity_type': self._classify_entity_type(concept),
                'frequency': len(concept.get('quotes', [])),
                'relationships': [],  # Will be populated in pass 2
                'pass': 'entity',
                'metadata': {
                    'extractor': 'relationship',
                    'pass': 'entity',
                    'derived_from_text': True
                }
            }
            entity_codes.append(code)
        
        state['codes'] = entity_codes
        state['metadata']['passes_completed'].append('entity')
        state['metadata']['entities_found'] = len(entity_codes)
        
        logger.info(f"Pass 1 complete: {len(entity_codes)} entity codes extracted")
        return state
    
    def _classify_entity_type(self, concept: Dict[str, Any]) -> str:
        """Classify entity type based on concept properties"""
        name = concept.get('name', '').lower()
        definition = concept.get('definition', '').lower()
        properties = [prop.lower() for prop in concept.get('properties', [])]
        
        # Simple classification based on concept characteristics
        if any(term in name or term in definition for term in ['person', 'individual', 'participant', 'actor']):
            return 'person'
        elif any(term in name or term in definition for term in ['technology', 'tool', 'system', 'software']):
            return 'technology'
        elif any(term in name or term in definition for term in ['process', 'method', 'approach', 'technique']):
            return 'method'
        elif any(term in name or term in definition for term in ['challenge', 'problem', 'issue', 'difficulty']):
            return 'challenge'
        elif any(term in name or term in definition for term in ['outcome', 'result', 'benefit', 'impact']):
            return 'outcome'
        else:
            return 'concept'
    
    async def _run_pass_2_relationships(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Pass 2: Real relationship discovery using LLM analysis"""
        logger.info("Pass 2: Real relationship discovery")
        
        codes = state['codes']
        text = state['original_text']
        
        if len(codes) < 2:
            logger.info("Pass 2 skipped: insufficient codes for relationships")
            state['metadata']['passes_completed'].append('relationship')
            return state
        
        # GENUINE relationship identification using LLM
        relationships = await self.text_analyzer.identify_relationships(codes, text)
        state['metadata']['llm_calls_made'] += 1
        
        # Build relationship network and enhance codes
        enhanced_codes = self._enhance_codes_with_relationships(codes, relationships)
        
        state['relationships'] = relationships
        state['codes'] = enhanced_codes
        state['metadata']['passes_completed'].append('relationship')
        state['metadata']['relationships_found'] = len(relationships)
        
        logger.info(f"Pass 2 complete: {len(relationships)} relationships identified")
        return state
    
    async def _run_pass_3_gap_filling(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Pass 3: Gap filling and validation"""
        logger.info("Pass 3: Gap filling and validation")
        
        codes = state['codes']
        relationships = state['relationships']
        config = state['config']
        
        # Fill relationship gaps using simple heuristics
        filled_relationships = self._fill_relationship_gaps(relationships, codes)
        
        # Validate and strengthen relationships
        validated_relationships = self._validate_relationships(filled_relationships, codes)
        
        # Final code enhancement with relationship network information
        final_codes = self._final_code_enhancement(codes, validated_relationships)
        
        state['relationships'] = validated_relationships
        state['codes'] = final_codes
        state['metadata']['passes_completed'].append('gap_filling')
        state['metadata']['final_relationships'] = len(validated_relationships)
        state['metadata']['end_time'] = datetime.now().isoformat()
        
        logger.info(f"Pass 3 complete: {len(final_codes)} codes after relationship analysis")
        return state
    
    def _enhance_codes_with_relationships(self, codes: List[Dict[str, Any]], 
                                        relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance codes with relationship information"""
        enhanced_codes = []
        
        # Create relationship lookup
        code_relationships = {}
        for rel in relationships:
            source = rel.get('concept1', rel.get('source_code', ''))
            target = rel.get('concept2', rel.get('target_code', ''))
            
            if source not in code_relationships:
                code_relationships[source] = []
            if target not in code_relationships:
                code_relationships[target] = []
            
            code_relationships[source].append({
                'related_code': target,
                'relationship_type': rel.get('relationship_type', 'RELATES_TO'),
                'strength': rel.get('strength', 0.5)
            })
            code_relationships[target].append({
                'related_code': source,
                'relationship_type': f"INVERSE_{rel.get('relationship_type', 'RELATES_TO')}",
                'strength': rel.get('strength', 0.5)
            })
        
        # Enhance codes
        for code in codes:
            enhanced_code = code.copy()
            code_name = code.get('code_name', code.get('name', ''))
            
            if code_name in code_relationships:
                enhanced_code['relationships'] = code_relationships[code_name]
                enhanced_code['relationship_count'] = len(code_relationships[code_name])
                
                # Boost confidence for well-connected codes
                connection_bonus = min(len(code_relationships[code_name]) * 0.05, 0.2)
                enhanced_code['confidence'] = min(enhanced_code['confidence'] + connection_bonus, 1.0)
            else:
                enhanced_code['relationships'] = []
                enhanced_code['relationship_count'] = 0
            
            enhanced_codes.append(enhanced_code)
        
        return enhanced_codes
    
    def _fill_relationship_gaps(self, relationships: List[Dict[str, Any]], 
                               codes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fill gaps in relationship network using simple heuristics"""
        # For now, return relationships as-is since LLM analysis should provide complete relationships
        # This could be enhanced with additional gap-filling logic in the future
        return relationships
    
    def _validate_relationships(self, relationships: List[Dict[str, Any]], 
                               codes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and filter relationships"""
        validated_relationships = []
        code_names = set(code.get('code_name', code.get('name', '')) for code in codes)
        
        for rel in relationships:
            # Validate relationship exists between valid codes
            concept1 = rel.get('concept1', '')
            concept2 = rel.get('concept2', '')
            
            if concept1 in code_names and concept2 in code_names:
                validated_rel = rel.copy()
                
                # Ensure minimum confidence
                validated_rel['confidence'] = max(validated_rel.get('strength', 0.5), 0.3)
                
                validated_relationships.append(validated_rel)
        
        return validated_relationships
    
    def _final_code_enhancement(self, codes: List[Dict[str, Any]], 
                               relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Final enhancement of codes with validated relationships"""
        enhanced_codes = []
        
        # Update relationship counts
        relationship_counts = {}
        for rel in relationships:
            concept1 = rel.get('concept1', '')
            concept2 = rel.get('concept2', '')
            relationship_counts[concept1] = relationship_counts.get(concept1, 0) + 1
            relationship_counts[concept2] = relationship_counts.get(concept2, 0) + 1
        
        for code in codes:
            enhanced_code = code.copy()
            code_name = code.get('code_name', code.get('name', ''))
            
            # Update relationship count
            enhanced_code['relationship_count'] = relationship_counts.get(code_name, 0)
            
            # Calculate network centrality score
            centrality = min(relationship_counts.get(code_name, 0) / max(len(codes) - 1, 1), 1.0)
            enhanced_code['network_centrality'] = centrality
            
            # Final confidence adjustment based on network position
            network_bonus = centrality * 0.1
            enhanced_code['confidence'] = min(enhanced_code['confidence'] + network_bonus, 1.0)
            
            enhanced_codes.append(enhanced_code)
        
        return enhanced_codes
    
    def _validate_genuine_results(self, results: List[Dict[str, Any]], original_text: str):
        """Validate that results are genuinely derived from input text"""
        if not results:
            return  # Empty results are valid
        
        # Check that results contain quotes from original text
        total_quotes = 0
        valid_quotes = 0
        
        for result in results:
            quotes = result.get('quotes', [])
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
        relationships = state['relationships']
        
        # Add extraction metadata to each code
        for code in codes:
            code['extraction_metadata'] = {
                'extractor': 'relationship',
                'passes_completed': metadata['passes_completed'],
                'total_relationships': len(relationships),
                'extraction_time': metadata.get('end_time', ''),
                'algorithm_version': self.get_version(),
                'llm_calls_made': metadata.get('llm_calls_made', 0)
            }
            
            # Include relationship summary
            code['relationship_summary'] = {
                'total_relationships': code.get('relationship_count', 0),
                'network_centrality': code.get('network_centrality', 0.0),
                'entity_type': code.get('entity_type', 'unknown')
            }
        
        return codes