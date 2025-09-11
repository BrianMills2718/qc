#!/usr/bin/env python3
"""
Hierarchical Extractor - GENUINE IMPLEMENTATION

Implements 4-phase hierarchical code extraction using REAL LLM analysis.
NO MOCK DATA - all results derived from input text analysis.
"""

from typing import Dict, Any, List, Optional, Union
import logging
import asyncio
from .base_extractor import ExtractorPlugin, ExtractionPhase
from core.llm.real_text_analyzer import RealTextAnalyzer
from core.llm.llm_handler import LLMHandler
from config.unified_config import UnifiedConfig

logger = logging.getLogger(__name__)

class HierarchicalExtractor(ExtractorPlugin):
    """Genuine 4-phase hierarchical extraction algorithm"""
    
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
        return "hierarchical"
    
    def get_version(self) -> str:
        return "2.0.0-genuine"
    
    def get_description(self) -> str:
        return "4-phase hierarchical extraction using real LLM analysis"
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            'supports_hierarchy': True,
            'supports_relationships': True,
            'phases': ['initial', 'relationship', 'taxonomy', 'refinement'],
            'methodology_focus': 'grounded_theory',
            'requires_llm': True  # CRITICAL: Requires real LLM
        }
    
    def supports_relationships(self) -> bool:
        return True
    
    def supports_hierarchy(self) -> bool:
        return True
    
    def get_required_config(self) -> List[str]:
        return ["minimum_confidence", "hierarchy_depth"]
    
    async def extract_codes(self, interview_data: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract codes using genuine 4-phase hierarchical algorithm
        
        CRITICAL: Results MUST vary with input text - no hardcoded responses
        """
        try:
            text = interview_data.get('content', '')
            if not text or not text.strip():
                return []
            
            logger.info(f"Starting hierarchical extraction on {len(text)} characters of text")
            
            # Initialize extraction state with REAL text analysis
            extraction_state = {
                'original_text': text,
                'interview_id': interview_data.get('id', 'unknown'),
                'config': config,
                'codes': [],
                'relationships': [],
                'hierarchy': {},
                'metadata': {
                    'extractor': 'hierarchical',
                    'phases_completed': [],
                    'llm_calls_made': 0,
                    'text_length': len(text)
                }
            }
            
            # Execute 4 phases with REAL analysis - must use await
            extraction_state = await self._run_async_extraction(extraction_state)
            
            # Validate genuine results
            results = self._format_results(extraction_state)
            self._validate_genuine_results(results, text)
            
            logger.info(f"Hierarchical extraction completed: {len(results)} codes generated")
            return results
            
        except Exception as e:
            logger.error(f"Hierarchical extraction failed: {str(e)}")
            # FAIL FAST - no mock fallback
            raise RuntimeError(f"Real hierarchical extraction failed: {e}")
    
    async def _run_async_extraction(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run async extraction phases"""
        state = await self._run_phase_1_initial(state)
        state = await self._run_phase_2_relationships(state)
        state = await self._run_phase_3_taxonomy(state)
        state = await self._run_phase_4_refinement(state)
        return state
    
    async def _run_phase_1_initial(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 1: Hierarchical concept discovery using configuration-driven prompts"""
        logger.info("Phase 1: Real hierarchical concept discovery")
        
        text = state['original_text']
        config = state['config']
        hierarchy_depth = config.get('hierarchy_depth', 'auto')
        
        # Build hierarchical prompt based on configuration
        hierarchical_concepts = await self._extract_hierarchical_concepts_structured(
            text, hierarchy_depth
        )
        state['metadata']['llm_calls_made'] += 1
        
        # Convert to proper hierarchical codes format
        initial_codes = self._convert_hierarchical_response_to_codes(hierarchical_concepts)
        
        state['codes'] = initial_codes
        state['metadata']['phases_completed'].append('initial')
        state['metadata']['initial_codes_found'] = len(initial_codes)
        
        logger.info(f"Phase 1 complete: {len(initial_codes)} hierarchical codes extracted")
        return state

    async def _extract_hierarchical_concepts_structured(self, text: str, hierarchy_depth: Union[int, str]) -> List[Dict[str, Any]]:
        """Extract concepts with explicit hierarchical structure"""
        
        # Build depth instruction
        if hierarchy_depth == 'auto':
            depth_instruction = "Determine optimal hierarchy depth (2-5 levels) based on data complexity"
        else:
            depth_instruction = f"Create exactly {hierarchy_depth} levels of hierarchy"
        
        prompt = f"""
Analyze this interview text using grounded theory methodology with EXPLICIT HIERARCHICAL STRUCTURE.

Interview Text:
{text}

Create a MULTI-LEVEL hierarchical code structure following these requirements:

1. HIERARCHY STRUCTURE:
   {depth_instruction}
   - Level 0: Top-level parent codes (3-5 major themes)
   - Level 1: Child codes under each parent (2-4 per parent)  
   - Level 2+: Additional sub-levels as data supports

2. REQUIRED FIELDS for each code:
   - code_name: Descriptive name from participant language
   - description: Definition based on text content
   - parent_id: Name of parent code (null for level 0)
   - level: Hierarchy level (0, 1, 2, ...)
   - child_codes: Array of child code names (empty if no children)
   - quotes: Exact quotes from text supporting this code
   - properties: Characteristics/attributes found in text
   - dimensions: Variations along properties
   - confidence: 0.0-1.0 based on evidence strength

3. HIERARCHY LINKING:
   - Use parent_id to link each child to its parent's code_name
   - Populate child_codes arrays for parent codes
   - Ensure level numbering is consistent

Return JSON with "concepts" array containing properly structured hierarchical codes.

CRITICAL: All codes must be derived from THIS SPECIFIC TEXT with exact quotes.
"""
        
        response = await self.llm_handler.complete_raw(prompt, temperature=0.1)
        return self._parse_hierarchical_response(response, text)

    def _parse_hierarchical_response(self, response: str, original_text: str) -> List[Dict[str, Any]]:
        """Parse LLM response ensuring hierarchical structure"""
        try:
            # Parse JSON response
            import json
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "{" in response:
                json_str = response[response.find("{"):]
                # Find matching closing brace
                brace_count = 0
                end_pos = 0
                for i, char in enumerate(json_str):
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = i + 1
                            break
                json_str = json_str[:end_pos]
            else:
                logger.error("No JSON found in LLM response")
                return []
            
            parsed = json.loads(json_str)
            concepts = parsed.get("concepts", [])
            
            # Validate hierarchy structure
            self._validate_hierarchy_structure(concepts)
            
            return concepts
            
        except Exception as e:
            logger.error(f"Failed to parse hierarchical response: {e}")
            raise RuntimeError(f"Hierarchical response parsing failed: {e}")

    def _validate_hierarchy_structure(self, concepts: List[Dict[str, Any]]) -> None:
        """Validate that hierarchical structure is properly formed"""
        if not concepts:
            return
        
        # Check for required hierarchy fields
        hierarchy_fields = ['parent_id', 'level', 'child_codes']
        missing_fields = []
        
        for concept in concepts:
            for field in hierarchy_fields:
                if field not in concept:
                    missing_fields.append(field)
        
        if missing_fields:
            logger.warning(f"Missing hierarchy fields in concepts: {set(missing_fields)}")
        
        # Validate level consistency
        levels = [c.get('level', 0) for c in concepts]
        max_level = max(levels) if levels else 0
        
        logger.info(f"Hierarchy validation: {len(concepts)} concepts, {max_level + 1} levels detected")

    def _convert_hierarchical_response_to_codes(self, concepts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert hierarchical concepts to code dictionary format"""
        codes = []
        for concept in concepts:
            code = {
                'code_name': concept.get('name') or concept.get('code_name', 'unnamed'),
                'description': concept.get('definition') or concept.get('description', ''),
                'quotes': concept.get('quotes', []),
                'confidence': concept.get('confidence', 0.0),
                'properties': concept.get('properties', []),
                'dimensions': concept.get('dimensions', []),
                # HIERARCHY FIELDS - Previously missing:
                'parent_id': concept.get('parent_id'),
                'level': concept.get('level', 0),
                'child_codes': concept.get('child_codes', [])
            }
            codes.append(code)
        return codes
    
    async def _run_phase_2_relationships(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: Build hierarchical relationships using REAL analysis"""
        logger.info("Phase 2: Real relationship analysis")
        
        codes = state['codes']
        text = state['original_text']
        
        if len(codes) < 2:
            logger.info("Phase 2 skipped: insufficient codes for relationships")
            state['metadata']['phases_completed'].append('relationship')
            return state
        
        # GENUINE relationship identification
        relationships = await self.text_analyzer.identify_relationships(codes, text)
        state['metadata']['llm_calls_made'] += 1
        
        # Build hierarchical structure from relationships
        hierarchy = self._build_hierarchy_from_relationships(codes, relationships)
        
        state['relationships'] = relationships
        state['hierarchy'] = hierarchy
        state['metadata']['phases_completed'].append('relationship')
        state['metadata']['relationships_found'] = len(relationships)
        
        logger.info(f"Phase 2 complete: {len(relationships)} relationships identified")
        return state
    
    async def _run_phase_3_taxonomy(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3: Create formal taxonomy structure"""
        logger.info("Phase 3: Taxonomy creation")
        
        codes = state['codes']
        hierarchy = state['hierarchy']
        
        # Build formal taxonomy from hierarchical relationships
        taxonomy_structure = self._build_formal_taxonomy(codes, hierarchy)
        
        # Update codes with taxonomy information
        taxonomical_codes = self._apply_taxonomy_to_codes(codes, taxonomy_structure)
        
        state['codes'] = taxonomical_codes
        state['taxonomy'] = taxonomy_structure
        state['metadata']['phases_completed'].append('taxonomy')
        state['metadata']['taxonomy_levels'] = len(taxonomy_structure.get('levels', []))
        
        logger.info(f"Phase 3 complete: taxonomy with {state['metadata']['taxonomy_levels']} levels")
        return state
    
    async def _run_phase_4_refinement(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 4: Code refinement and quality enhancement"""
        logger.info("Phase 4: Code refinement")
        
        codes = state['codes']
        config = state['config']
        
        # Apply configuration-based refinement
        min_confidence = config.get('minimum_confidence', 0.3)
        refined_codes = [code for code in codes if code.get('confidence', 0) >= min_confidence]
        
        # Consolidate similar codes if enabled
        if config.get('consolidation_enabled', False):
            refined_codes = self._consolidate_similar_codes(refined_codes)
        
        state['codes'] = refined_codes
        state['metadata']['phases_completed'].append('refinement')
        state['metadata']['codes_after_refinement'] = len(refined_codes)
        
        logger.info(f"Phase 4 complete: {len(refined_codes)} codes after refinement")
        return state
    
    def _build_hierarchy_from_relationships(self, codes: List[Dict[str, Any]], 
                                          relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build hierarchical structure from identified relationships"""
        hierarchy = {
            'parent_child': {},
            'categories': {},
            'subcategories': {}
        }
        
        # Build parent-child relationships
        for rel in relationships:
            if rel.get('relationship_type') in ['influences', 'contains', 'causes']:
                parent = rel.get('concept1')
                child = rel.get('concept2')
                if parent and child:
                    if parent not in hierarchy['parent_child']:
                        hierarchy['parent_child'][parent] = []
                    hierarchy['parent_child'][parent].append(child)
        
        return hierarchy
    
    def _build_formal_taxonomy(self, codes: List[Dict[str, Any]], 
                              hierarchy: Dict[str, Any]) -> Dict[str, Any]:
        """Build formal taxonomy structure"""
        taxonomy = {
            'levels': [],
            'categories': {},
            'root_concepts': []
        }
        
        # Find root concepts (those not children of others)
        all_children = set()
        for parent, children in hierarchy.get('parent_child', {}).items():
            all_children.update(children)
        
        all_concept_names = set(code.get('code_name') for code in codes)
        root_concepts = all_concept_names - all_children
        taxonomy['root_concepts'] = list(root_concepts)
        
        # Build levels based on hierarchy depth
        levels = []
        current_level = list(root_concepts)
        while current_level:
            levels.append(current_level[:])
            next_level = []
            for concept in current_level:
                children = hierarchy.get('parent_child', {}).get(concept, [])
                next_level.extend(children)
            current_level = next_level
        
        taxonomy['levels'] = levels
        return taxonomy
    
    def _apply_taxonomy_to_codes(self, codes: List[Dict[str, Any]], 
                                taxonomy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply taxonomy information to codes"""
        taxonomical_codes = []
        
        for code in codes:
            enhanced_code = code.copy()
            concept_name = code.get('code_name')
            
            # Find which level this concept belongs to
            for level_idx, level_concepts in enumerate(taxonomy.get('levels', [])):
                if concept_name in level_concepts:
                    enhanced_code['taxonomy_level'] = level_idx
                    enhanced_code['is_root_concept'] = concept_name in taxonomy.get('root_concepts', [])
                    break
            
            taxonomical_codes.append(enhanced_code)
        
        return taxonomical_codes
    
    def _consolidate_similar_codes(self, codes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Consolidate similar or duplicate codes"""
        consolidated = []
        processed_names = set()
        
        for code in codes:
            code_name = code.get('code_name', '').lower()
            
            # Simple similarity check - could be enhanced with semantic similarity
            similar_found = False
            for processed_name in processed_names:
                if self._are_similar_concepts(code_name, processed_name):
                    similar_found = True
                    break
            
            if not similar_found:
                consolidated.append(code)
                processed_names.add(code_name)
        
        return consolidated
    
    def _are_similar_concepts(self, name1: str, name2: str) -> bool:
        """Check if two concept names are similar enough to consolidate"""
        # Simple word-based similarity
        words1 = set(name1.replace('_', ' ').split())
        words2 = set(name2.replace('_', ' ').split())
        
        if len(words1) == 0 or len(words2) == 0:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union) if len(union) > 0 else 0
        return similarity > 0.7
    
    def _format_results(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format extraction results for output"""
        codes = state.get('codes', [])
        formatted_results = []
        
        for code in codes:
            formatted_code = {
                'code_name': code.get('code_name', 'unnamed'),
                'description': code.get('description', ''),
                'quotes': code.get('quotes', []),
                'confidence': code.get('confidence', 0.0),
                'properties': code.get('properties', []),
                'dimensions': code.get('dimensions', []),
                # HIERARCHY FIELDS - Critical for hierarchical structure:
                'parent_id': code.get('parent_id'),
                'level': code.get('level', 0),
                'child_codes': code.get('child_codes', []),
                'extraction_metadata': {
                    'extractor': 'hierarchical',
                    'phase': code.get('phase', 'unknown'),
                    'derived_from_text': code.get('metadata', {}).get('derived_from_text', True),
                    'taxonomy_level': code.get('taxonomy_level'),
                    'is_root_concept': code.get('is_root_concept', False)
                }
            }
            formatted_results.append(formatted_code)
        
        return formatted_results
    
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