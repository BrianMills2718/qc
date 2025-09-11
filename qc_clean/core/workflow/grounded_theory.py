#!/usr/bin/env python3
"""
Grounded Theory Workflow Implementation

Implements the complete grounded theory analysis methodology following established frameworks
(Strauss & Corbin, Charmaz) with LLM-assisted analysis and theoretical memo generation.

Workflow stages:
1. Open Coding - Identify concepts and categories from data
2. Axial Coding - Identify relationships between categories  
3. Selective Coding - Develop core category and integrate theory
4. Theoretical Integration - Generate theoretical model and memos
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from pydantic import BaseModel, Field
from .prompt_templates import ConfigurablePromptGenerator

class ProcessingError(Exception):
    """Error raised during processing that should halt execution"""
    pass

logger = logging.getLogger(__name__)


# Grounded Theory Data Structures
class OpenCode(BaseModel):
    """A concept identified during open coding with hierarchical structure support"""
    code_name: str = Field(description="Name of the open code")
    description: str = Field(description="Description of what this code represents")
    properties: List[str] = Field(description="Properties of this concept")
    dimensions: List[str] = Field(description="Dimensional variations")
    supporting_quotes: List[str] = Field(description="Quotes that support this code")
    frequency: int = Field(description="Number of occurrences")
    confidence: float = Field(description="Confidence in this code 0-1")
    
    # Hierarchical structure fields (NVivo-style)
    parent_id: Optional[str] = Field(default=None, description="String ID of parent code if this is a sub-code (use parent's code_name with underscores)")
    level: int = Field(default=0, description="Hierarchy level (0 for top-level codes)")
    child_codes: List[str] = Field(default_factory=list, description="List of string IDs of child codes (use child code_names with underscores, not numbers)")
    
    def to_hierarchical_dict(self) -> Dict[str, Any]:
        """Convert to dictionary preserving hierarchy information"""
        return {
            "code_name": self.code_name,
            "description": self.description,
            "properties": self.properties,
            "dimensions": self.dimensions,
            "supporting_quotes": self.supporting_quotes,
            "frequency": self.frequency,
            "confidence": self.confidence,
            "parent_id": self.parent_id,
            "level": self.level,
            "child_codes": self.child_codes
        }


class AxialRelationship(BaseModel):
    """A relationship identified during axial coding"""
    central_category: str = Field(description="The central category")
    related_category: str = Field(description="Related category")
    relationship_type: str = Field(description="Type of relationship (causal, contextual, intervening, etc.)")
    conditions: List[str] = Field(description="Conditions that influence this relationship")
    consequences: List[str] = Field(description="Consequences of this relationship")
    supporting_evidence: List[str] = Field(description="Evidence supporting this relationship")
    strength: float = Field(description="Strength of relationship 0-1")


class CoreCategory(BaseModel):
    """The core category identified during selective coding"""
    category_name: str = Field(description="Name of the core category")
    definition: str = Field(description="Clear definition of the core category")
    central_phenomenon: str = Field(description="The central phenomenon this category explains")
    related_categories: List[str] = Field(description="Categories that relate to this core category")
    theoretical_properties: List[str] = Field(description="Theoretical properties")
    explanatory_power: str = Field(description="How this category explains the phenomenon")
    integration_rationale: str = Field(description="Why this is the core category")


class TheoreticalModel(BaseModel):
    """The final theoretical model from grounded theory analysis"""
    model_name: str = Field(description="Name of the theoretical model")
    core_categories: List[str] = Field(description="The core categories that explain the phenomenon")
    theoretical_framework: str = Field(description="The theoretical framework developed")
    propositions: List[str] = Field(description="Theoretical propositions")
    conceptual_relationships: List[str] = Field(description="Key conceptual relationships")
    scope_conditions: List[str] = Field(description="Conditions under which theory applies")
    implications: List[str] = Field(description="Implications of the theory")
    future_research: List[str] = Field(description="Suggested future research directions")
    
    @property
    def core_category(self) -> str:
        """Backward compatibility: return first core category as string"""
        return self.core_categories[0] if self.core_categories else ""


@dataclass
class GroundedTheoryResults:
    """Complete results of grounded theory analysis"""
    open_codes: List[OpenCode]
    axial_relationships: List[AxialRelationship]  
    core_categories: List[CoreCategory]  # Changed to support multiple core categories
    theoretical_model: TheoreticalModel
    supporting_memos: List[Dict[str, Any]]
    analysis_metadata: Dict[str, Any]
    
    @property
    def core_category(self) -> Optional[CoreCategory]:
        """Backward compatibility: return first core category"""
        return self.core_categories[0] if self.core_categories else None


class GroundedTheoryWorkflow:
    """
    Complete Grounded Theory Analysis Workflow
    
    Implements the systematic grounded theory methodology with LLM assistance
    for concept identification, relationship mapping, and theory development.
    """
    
    def __init__(self, robust_operations, config=None):
        """Initialize with robust CLI operations and optional configuration"""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from ..cli.robust_cli_operations import RobustCLIOperations
        from qc_clean.config.methodology_config import GroundedTheoryConfig
        
        if not isinstance(robust_operations, RobustCLIOperations):
            raise ValueError("robust_operations must be a RobustCLIOperations instance")
        
        self.operations = robust_operations
        self.config = config  # Configuration controls all analysis decisions
        self._generated_memos = []
        self._analysis_log = []
        self.audit_trail = None  # Will be initialized when workflow starts
        
        # Initialize prompt generator with configuration
        self.prompt_generator = ConfigurablePromptGenerator(config) if config else None
        
        # Initialize extractor plugin system
        self.extractor_plugin = self._initialize_extractor_plugin()
        
        if self.config:
            logger.info(f"Grounded Theory Workflow initialized with {self.config.coding_depth} depth, "
                       f"{self.config.theoretical_sensitivity} sensitivity")
            logger.info(f"Using extractor: {self.extractor_plugin.get_name() if self.extractor_plugin else 'none'}")
        else:
            logger.info("Grounded Theory Workflow initialized without configuration")
    
    def _initialize_extractor_plugin(self):
        """Initialize the appropriate extractor plugin based on configuration"""
        try:
            from plugins.extractors import get_extractor_plugin
            
            # Determine extractor from configuration
            extractor_name = "hierarchical"  # default
            use_llm_speaker_detection = False
            
            if self.config:
                # Check for enhanced speaker detection configuration
                if hasattr(self.config, 'speaker_detection'):
                    if getattr(self.config.speaker_detection, 'method', 'regex') == 'llm':
                        extractor_name = "enhanced_semantic"
                        use_llm_speaker_detection = True
                
                # Check for comprehensive config first
                if hasattr(self.config, 'extraction') and hasattr(self.config.extraction, 'extractor'):
                    extractor_name = self.config.extraction.extractor
                elif hasattr(self.config, 'extraction') and hasattr(self.config.extraction, 'coding_approach'):
                    # Map coding approach to extractor
                    approach_mapping = {
                        'open': 'hierarchical',
                        'closed': 'validated',
                        'mixed': 'relationship'
                    }
                    approach_value = self.config.extraction.coding_approach
                    if hasattr(approach_value, 'value'):  # Handle enum
                        approach_value = approach_value.value
                    extractor_name = approach_mapping.get(approach_value, 'hierarchical')
                elif hasattr(self.config, 'extractor'):
                    extractor_name = self.config.extractor
                elif hasattr(self.config, 'coding_approach'):
                    # Map coding approach to extractor (legacy config)
                    approach_mapping = {
                        'open': 'hierarchical',
                        'closed': 'validated',
                        'mixed': 'relationship'
                    }
                    extractor_name = approach_mapping.get(self.config.coding_approach, 'hierarchical')
            
            # Get the appropriate extractor
            if extractor_name == "enhanced_semantic":
                from plugins.extractors.enhanced_semantic_extractor import EnhancedSemanticExtractor
                from core.llm.llm_handler import LLMHandler
                
                # Create LLM handler if not available
                if not hasattr(self, 'operations') or not hasattr(self.operations, 'llm_handler'):
                    from config.unified_config import UnifiedConfig
                    config = UnifiedConfig()
                    llm_handler = LLMHandler(config=config.to_grounded_theory_config())
                else:
                    llm_handler = self.operations.llm_handler
                
                extractor = EnhancedSemanticExtractor(
                    llm_handler=llm_handler,
                    use_llm_speaker_detection=use_llm_speaker_detection
                )
                logger.info(f"Initialized enhanced_semantic extractor plugin with LLM detection: {use_llm_speaker_detection}")
                return extractor
            else:
                # Use standard plugin system
                extractor = get_extractor_plugin(extractor_name)
                if extractor:
                    logger.info(f"Initialized {extractor_name} extractor plugin")
                    return extractor
                else:
                    logger.warning(f"Extractor {extractor_name} not found, using hierarchical as fallback")
                    return get_extractor_plugin('hierarchical')
                
        except ImportError as e:
            logger.warning(f"Failed to load extractor plugins: {e}")
            return None
    
    async def execute_complete_workflow(self, interviews: List[Dict[str, Any]]) -> GroundedTheoryResults:
        """
        Execute complete grounded theory analysis workflow
        
        Args:
            interviews: List of interview data dictionaries
            
        Returns:
            GroundedTheoryResults with complete analysis
        """
        start_time = datetime.now()
        
        # Initialize audit trail
        from ..audit.audit_trail import GTAuditTrail, AnalysisStep
        self.audit_trail = GTAuditTrail(
            methodology="grounded_theory",
            analysis_config=self.config.to_dict() if self.config else None,
            start_time=start_time,
            input_summary={
                "interview_count": len(interviews),
                "total_quotes": sum(len(interview.get('quotes', [])) for interview in interviews)
            }
        )
        
        self._log_step("Starting Grounded Theory Analysis Workflow")
        
        try:
            # Phase 1: Open Coding
            self._log_step("Phase 1: Open Coding - Identifying concepts and categories")
            open_codes = await self._open_coding_phase(interviews)
            
            # Phase 2: Axial Coding  
            self._log_step("Phase 2: Axial Coding - Identifying relationships between categories")
            axial_relationships = await self._axial_coding_phase(open_codes, interviews)
            
            # Phase 3: Selective Coding
            self._log_step("Phase 3: Selective Coding - Developing core categories")
            core_categories = await self._selective_coding_phase(open_codes, axial_relationships, interviews)
            
            # Phase 4: Theoretical Integration
            self._log_step("Phase 4: Theoretical Integration - Generating theoretical model")
            theoretical_model = await self._theory_integration_phase(
                open_codes, axial_relationships, core_categories, interviews
            )
            
            # Generate analysis metadata
            end_time = datetime.now()
            analysis_metadata = {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": (end_time - start_time).total_seconds(),
                "interview_count": len(interviews),
                "open_codes_identified": len(open_codes),
                "axial_relationships_found": len(axial_relationships),
                "memos_generated": len(self._generated_memos),
                "analysis_steps": self._analysis_log
            }
            
            results = GroundedTheoryResults(
                open_codes=open_codes,
                axial_relationships=axial_relationships,
                core_categories=core_categories,
                theoretical_model=theoretical_model,
                supporting_memos=self._generated_memos,
                analysis_metadata=analysis_metadata
            )
            
            # Finalize audit trail
            # Get first core category for compatibility
            first_core_category = core_categories[0] if core_categories else None
            
            final_results_summary = {
                "core_categories": [c.category_name for c in core_categories] if core_categories else [],
                "core_category": first_core_category.category_name if first_core_category else "None",
                "theoretical_model": theoretical_model.model_name if theoretical_model else "None",
                "open_codes_count": len(open_codes),
                "relationships_count": len(axial_relationships),
                "memos_generated": len(self._generated_memos)
            }
            self.audit_trail.finalize_workflow(final_results_summary)
            
            core_cat_names = ', '.join([c.category_name for c in core_categories[:3]]) if core_categories else "None"
            self._log_step(f"Grounded Theory Analysis Complete: {len(open_codes)} codes, "
                         f"{len(axial_relationships)} relationships, core categories: {core_cat_names}")
            
            return results
            
        except Exception as e:
            logger.error(f"Grounded Theory workflow failed: {e}")
            # Log failure in audit trail
            if self.audit_trail:
                self.audit_trail.finalize_workflow({"error": str(e), "status": "failed"})
            raise
    
    async def _open_coding_phase(self, interviews: List[Dict[str, Any]]) -> List[OpenCode]:
        """
        Phase 1: Open Coding - Identify concepts and categories from data
        
        Uses extractor plugins to systematically analyze interview data and identify initial concepts,
        their properties, and dimensional variations following open coding principles.
        """
        try:
            all_open_codes = []
            
            # Process each interview with the extractor plugin
            for i, interview in enumerate(interviews):
                logger.info(f"Processing interview {i + 1}/{len(interviews)} with {self.extractor_plugin.get_name() if self.extractor_plugin else 'default'} extractor")
                
                if self.extractor_plugin:
                    # Use extractor plugin with enhanced configuration
                    interview_config = {
                        'llm_handler': self.operations.llm_handler,  
                        'coding_approach': self._get_coding_approach(),
                        'relationship_threshold': self._get_relationship_threshold(),
                        'semantic_units': self._get_semantic_units(),
                        'validation_level': self._get_validation_level(),
                        'consolidation_enabled': self._get_consolidation_enabled(),
                        'hierarchy_depth': self._get_hierarchy_depth(),  # ADD THIS LINE
                        'extractor': self._get_extractor_name()
                    }
                    
                    # Extract codes using plugin
                    extracted_codes = await self.extractor_plugin.extract_codes(interview, interview_config)
                    
                    # Convert extracted codes to OpenCode objects
                    for code_data in extracted_codes:
                        open_code = self._convert_extracted_code_to_open_code(code_data, interview.get('id', f'interview_{i}'))
                        all_open_codes.append(open_code)
                        
                else:
                    # Fallback to original LLM-based method
                    interview_text = interview.get('content', '') or str(interview)
                    fallback_codes = await self._fallback_open_coding(interview_text, i)
                    all_open_codes.extend(fallback_codes)
            
            # Log results
            logger.info(f"Open coding phase completed. Identified {len(all_open_codes)} codes using {self.extractor_plugin.get_name() if self.extractor_plugin else 'fallback'} method")
            self._log_step(f"Open coding completed: {len(all_open_codes)} codes identified")
            
            # Record in audit trail
            if self.audit_trail:
                self.audit_trail.add_step(
                    step="open_coding",
                    description=f"Extracted {len(all_open_codes)} open codes using {self.extractor_plugin.get_name() if self.extractor_plugin else 'fallback'} extractor",
                    input_summary={"interview_count": len(interviews)},
                    output_summary={"codes_identified": len(all_open_codes)},
                    metadata={
                        "extractor": self.extractor_plugin.get_name() if self.extractor_plugin else "fallback",
                        "extractor_capabilities": self.extractor_plugin.get_capabilities() if self.extractor_plugin else {}
                    }
                )
            
            # Entity-relationship extraction and Neo4j storage
            if hasattr(self.operations, '_neo4j_manager') and self.operations._neo4j_manager:
                try:
                    for i, interview in enumerate(interviews):
                        interview_text = interview.get('content', '') or str(interview)
                        interview_file = interview.get('id', f'interview_{i}')
                        await self._process_entities_and_relationships(
                            interview_file, all_open_codes, interview_text
                        )
                except Exception as e:
                    logger.error(f"Entity-relationship processing failed: {e}")
                    raise ProcessingError(f"Neo4j graph storage failed: {e}")
            
            return all_open_codes
            
        except Exception as e:
            logger.error(f"Open coding phase failed: {str(e)}")
            self._log_step(f"Open coding failed: {str(e)}")
            
            # Record failure in audit trail
            if self.audit_trail:
                self.audit_trail.add_step(
                    step="open_coding",
                    description="Open coding phase failed",
                    input_summary={"interview_count": len(interviews) if interviews else 0},
                    output_summary={"error": str(e)},
                    metadata={"status": "failed"}
                )
            raise
    
    def _get_coding_approach(self) -> str:
        """Get coding approach from configuration"""
        if not self.config:
            return 'open'
        
        # Check comprehensive config first
        if hasattr(self.config, 'extraction') and hasattr(self.config.extraction, 'coding_approach'):
            approach = self.config.extraction.coding_approach
            return approach.value if hasattr(approach, 'value') else approach
        elif hasattr(self.config, 'coding_approach'):
            return self.config.coding_approach
        
        return 'open'
    
    def _get_relationship_threshold(self) -> float:
        """Get relationship threshold from configuration"""
        if not self.config:
            return 0.7
        
        if hasattr(self.config, 'extraction') and hasattr(self.config.extraction, 'relationship_threshold'):
            return self.config.extraction.relationship_threshold
        
        return 0.7
    
    def _get_semantic_units(self) -> List[str]:
        """Get semantic units from configuration"""
        if not self.config:
            return ['sentence', 'paragraph']
        
        # Get from plugin config if available
        if hasattr(self.config, 'plugin_configs'):
            semantic_config = self.config.plugin_configs.get('extractors', {}).get('semantic_extractor', {})
            units = semantic_config.get('semantic_units', ['sentence', 'paragraph'])
            return units
        
        return ['sentence', 'paragraph']
    
    def _get_validation_level(self) -> str:
        """Get validation level from configuration"""
        if not self.config:
            return 'standard'
        
        if hasattr(self.config, 'validation') and hasattr(self.config.validation, 'validation_level'):
            level = self.config.validation.validation_level
            return level.value if hasattr(level, 'value') else level
        elif hasattr(self.config, 'validation_level'):
            return self.config.validation_level
        
        return 'standard'
    
    def _get_consolidation_enabled(self) -> bool:
        """Get consolidation enabled from configuration"""
        if not self.config:
            return True
        
        if hasattr(self.config, 'validation') and hasattr(self.config.validation, 'consolidation_enabled'):
            return self.config.validation.consolidation_enabled
        
        return True
    
    def _get_extractor_name(self) -> str:
        """Get extractor name from configuration"""
        if not self.config:
            return 'hierarchical'
        
        if hasattr(self.config, 'extraction') and hasattr(self.config.extraction, 'extractor'):
            return self.config.extraction.extractor
        elif hasattr(self.config, 'extractor'):
            return self.config.extractor
        
        return 'hierarchical'
    
    def _get_hierarchy_depth(self) -> Union[int, str]:
        """Get hierarchy depth from configuration"""
        if not self.config:
            return 'auto'
        
        # Check comprehensive config first  
        if hasattr(self.config, 'extraction') and hasattr(self.config.extraction, 'hierarchy_depth'):
            depth = self.config.extraction.hierarchy_depth
            return depth if depth != 0 else 'auto'
        elif hasattr(self.config, 'hierarchy_depth'):
            return self.config.hierarchy_depth
        
        return 'auto'  # Let LLM determine optimal depth
    
    def _convert_extracted_code_to_open_code(self, code_data: Dict[str, Any], source_id: str) -> OpenCode:
        """Convert extracted code data to OpenCode object"""
        return OpenCode(
            code_name=code_data.get('code_name', 'unknown_code'),
            description=code_data.get('description', 'No description available'),
            properties=code_data.get('properties', []),
            dimensions=code_data.get('dimensions', []),
            supporting_quotes=code_data.get('supporting_quotes', []),
            frequency=code_data.get('frequency', 1),
            confidence=code_data.get('confidence', 0.7),
            parent_id=code_data.get('parent_id'),
            level=code_data.get('level', 0),
            child_codes=code_data.get('child_codes', [])
        )
    
    async def _fallback_open_coding(self, interview_text: str, interview_index: int) -> List[OpenCode]:
        """Fallback open coding method when extractor plugins are not available"""
        try:
            # Generate configuration-driven prompt or use fallback
            if self.prompt_generator:
                open_coding_prompt = self.prompt_generator.generate_open_coding_prompt(interview_text)
            else:
                # Fallback static prompt
                open_coding_prompt = f'''
                You are an expert qualitative researcher conducting open coding analysis following grounded theory methodology.
                
                Analyze the following interview data and identify key concepts and categories. For each concept identified:
                4. Note dimensional variations (different ways this concept appears)
                5. Provide supporting quotes that demonstrate this concept
                6. Assess frequency and confidence
                7. ORGANIZE HIERARCHICALLY with MULTIPLE LEVELS:
                   - Create a MULTI-LEVEL hierarchy (at least 3 levels deep where appropriate)
                   - Level 0: Top-level parent codes (3-5 major themes)
                   - Level 1: Child codes under each parent (2-4 per parent)
                   - Level 2: Grandchild codes under Level 1 codes (1-3 per child where relevant)
                   - Level 3+: Further sub-codes if the data supports it
                   - Use parent_id to link each code to its parent (use parent's code_name with underscores)
                   - List child_codes for any code that has children
                
                Follow open coding principles:
                - Stay close to the data
                - Use participants' language when possible
                - Look for actions, interactions, and meanings
                - Ask: What is happening here? What are people doing?
                - Organize related concepts into MULTI-LEVEL hierarchical groups
                - Build deep hierarchies: parent → child → grandchild → great-grandchild where the data supports it
                
                Interview Data:
                {interview_data}
                
                Generate comprehensive open codes that capture the key concepts in this data, organizing them into a MULTI-LEVEL hierarchical structure (at least 3 levels deep) where natural groupings emerge.
                '''.format(interview_data=interview_text)
            phase_start_time = datetime.now()
            
            # Create audit step for open coding
            from ..audit.audit_trail import AnalysisStep
            audit_step = AnalysisStep(
                step_name="open_coding",
                input_data_summary={
                    "interview_count": len(interviews),
                    "quote_count": sum(len(interview.get('quotes', [])) for interview in interviews)
                },
                configuration_used=self.config.to_dict() if self.config else {},
                llm_prompt=open_coding_prompt,
                decision_rationale=f"Open coding with {self.config.theoretical_sensitivity if self.config else 'default'} theoretical sensitivity to identify initial concepts",
                alternatives_considered=["manual coding", "pre-defined coding scheme", "inductive thematic analysis"]
            )
            
            # Generate open codes using LLM
            if hasattr(self.operations, '_llm_handler') and self.operations._llm_handler:
                # Use prompt directly (ConfigurablePromptGenerator already formatted it)
                final_prompt = open_coding_prompt if self.prompt_generator else open_coding_prompt.format(interview_data=interview_text)
                
                llm_response = await self.operations._llm_handler.extract_structured(
                    prompt=final_prompt,
                    schema=self._create_open_codes_schema(),
                    instructions="Analyze interview data using grounded theory open coding methodology"
                )
                
                open_codes = llm_response.open_codes
                
                # Apply configuration-based filtering to open codes
                if self.config:
                    original_count = len(open_codes)
                    # Filter by minimum frequency
                    open_codes = [code for code in open_codes if code.frequency >= self.config.minimum_code_frequency]
                    filtered_by_frequency = original_count - len(open_codes)
                    logger.info(f"Filtered {filtered_by_frequency} codes below minimum frequency threshold ({self.config.minimum_code_frequency})")
                
                # Update audit step with results
                phase_end_time = datetime.now()
                audit_step.execution_time_seconds = (phase_end_time - phase_start_time).total_seconds()
                audit_step.llm_response = {"open_codes_count": len(open_codes)}
                audit_step.output_summary = {
                    "codes_identified": len(open_codes),
                    "average_confidence": sum(code.confidence for code in open_codes) / len(open_codes) if open_codes else 0,
                    "most_frequent_code": max(open_codes, key=lambda x: x.frequency).code_name if open_codes else None
                }
                audit_step.confidence_metrics = {
                    "code_confidence_avg": sum(code.confidence for code in open_codes) / len(open_codes) if open_codes else 0,
                    "analysis_completeness": 1.0 if len(open_codes) >= (self.config.minimum_code_frequency if self.config else 3) else 0.7
                }
                
                if self.audit_trail:
                    self.audit_trail.add_step(audit_step)
                
                open_codes = open_codes
                
                # Generate theoretical memo for open coding phase
                # Add the generated codes to the interviews data for memo generation
                # Only add to first interview to avoid duplication
                interviews_with_codes = []
                for i, interview in enumerate(interviews):
                    import copy
                    enhanced_interview = copy.deepcopy(interview)  # Deep copy to avoid modifying original
                    if 'quotes' not in enhanced_interview:
                        enhanced_interview['quotes'] = []
                    
                    # Only add codes to first interview to avoid massive duplication
                    if i == 0:
                        for code in open_codes:
                            for quote in code.supporting_quotes:
                                enhanced_interview['quotes'].append({
                                    'text': quote,
                                    'code': code.code_name,
                                    'frequency': code.frequency,
                                    'confidence': code.confidence
                                })
                    interviews_with_codes.append(enhanced_interview)
                
                memo_result = await self.operations.generate_analytical_memo_from_data(
                    interviews_with_codes, 
                    memo_type="theoretical_memo",
                    focus_codes=[code.code_name for code in open_codes[:5]],  # Focus on top codes
                    memo_title="Open Coding - Initial Conceptual Analysis"
                )
                
                if memo_result.get('success'):
                    self._generated_memos.append(memo_result)
                
                logger.info(f"Open coding phase complete: {len(open_codes)} codes identified")
                return open_codes
            else:
                # Fallback: Create sample open codes for testing
                logger.warning("LLM not available, using fallback open coding")
                return self._create_fallback_open_codes(interviews)
                
        except Exception as e:
            logger.error(f"Open coding phase failed: {e}")
            raise
    
    async def _axial_coding_phase(self, open_codes: List[OpenCode], interviews: List[Dict[str, Any]]) -> List[AxialRelationship]:
        """
        Phase 2: Axial Coding - Identify relationships between categories
        
        Analyzes relationships between the open codes to understand causal conditions,
        context, intervening conditions, and consequences.
        """
        try:
            # METHODOLOGY VALIDATION: Ensure we have codes to build relationships from
            if not open_codes or len(open_codes) == 0:
                logger.warning("Axial coding phase skipped: No open codes identified to build relationships from")
                logger.info("This follows proper grounded theory methodology - relationships require existing codes")
                return []  # Return empty relationships - methodologically correct
            
            logger.info(f"Axial coding proceeding with {len(open_codes)} open codes")
            # Prepare codes and interview data
            codes_text = self._format_codes_for_analysis(open_codes)
            interview_text = self._prepare_interview_text(interviews)
            
            # Generate configuration-driven prompt or use fallback
            if self.prompt_generator:
                axial_coding_prompt = self.prompt_generator.generate_axial_coding_prompt(codes_text, interview_text)
            else:
                # Fallback static prompt
                axial_coding_prompt = '''
                You are conducting axial coding analysis in grounded theory methodology.
                
                Given these open codes from the previous phase, identify relationships between categories:
                
                Open Codes:
                {open_codes}
                
                IMPORTANT: In addition to identifying relationships, also:
                - Create CODE FAMILIES by grouping related codes hierarchically
                - Ensure parent-child relationships are preserved
                - Maintain both hierarchical structure AND axial relationships
                
                For each significant relationship, identify:
                1. The central category in this relationship
                2. Related categories that connect to it
                3. Type of relationship (causal, contextual, intervening, etc.)
                4. Conditions that influence this relationship
                5. Consequences that result from this relationship
                6. Supporting evidence from the data
                7. Strength of the relationship
                
                Focus on the paradigm model:
                - Causal conditions (what leads to the phenomenon)
                - Context (specific conditions) 
                - Intervening conditions (broad conditions)
                - Action/interaction strategies (responses)
                - Consequences (outcomes)
                
                Original Interview Data:
                {interview_data}
                
                Identify the key relationships that help explain the phenomena in the data.
                '''.format(open_codes=codes_text, interview_data=interview_text)
            
            # Generate axial relationships using LLM
            if hasattr(self.operations, '_llm_handler') and self.operations._llm_handler:
                llm_response = await self.operations._llm_handler.extract_structured(
                    prompt=axial_coding_prompt,
                    schema=self._create_axial_relationships_schema(),
                    instructions="Identify relationships between categories using grounded theory axial coding methodology"
                )
                
                axial_relationships = llm_response.axial_relationships
                
                # Apply configuration-based filtering to axial relationships
                if self.config:
                    original_count = len(axial_relationships)
                    # Filter by relationship confidence threshold
                    axial_relationships = [rel for rel in axial_relationships if rel.strength >= self.config.relationship_confidence_threshold]
                    filtered_by_confidence = original_count - len(axial_relationships)
                    logger.info(f"Filtered {filtered_by_confidence} relationships below confidence threshold ({self.config.relationship_confidence_threshold})")
                
                # Generate theoretical memo for axial coding phase
                # Add the axial relationships to the interviews data for memo generation
                interviews_with_axial = []
                for i, interview in enumerate(interviews):
                    import copy
                    enhanced_interview = copy.deepcopy(interview)  # Deep copy to avoid modifying original
                    if 'quotes' not in enhanced_interview:
                        enhanced_interview['quotes'] = []
                    
                    # Only add to first interview to avoid massive duplication
                    if i == 0:
                        # Add original codes
                        for code in open_codes:
                            for quote in code.supporting_quotes:
                                enhanced_interview['quotes'].append({
                                    'text': quote,
                                    'code': code.code_name,
                                    'frequency': code.frequency,
                                    'confidence': code.confidence
                                })
                        
                        # Add axial relationships
                        for rel in axial_relationships:
                            # Use first supporting evidence or relationship description
                            evidence_text = rel.supporting_evidence[0] if rel.supporting_evidence else f"{rel.central_category} relates to {rel.related_category}"
                            enhanced_interview['quotes'].append({
                                'text': evidence_text,
                                'code': f"RELATIONSHIP: {rel.central_category} → {rel.related_category}",
                                'frequency': 1,
                                'confidence': rel.strength
                            })
                    
                    interviews_with_axial.append(enhanced_interview)
                
                memo_result = await self.operations.generate_analytical_memo_from_data(
                    interviews_with_axial,
                    memo_type="theoretical_memo", 
                    focus_codes=[rel.central_category for rel in axial_relationships[:3]],
                    memo_title="Axial Coding - Conceptual Relationships Analysis"
                )
                
                if memo_result.get('success'):
                    self._generated_memos.append(memo_result)
                
                logger.info(f"Axial coding phase complete: {len(axial_relationships)} relationships identified")
                return axial_relationships
            else:
                # Fallback: Create sample relationships
                logger.warning("LLM not available, using fallback axial coding")
                return self._create_fallback_relationships(open_codes)
                
        except Exception as e:
            logger.error(f"Axial coding phase failed: {e}")
            raise
    
    async def _selective_coding_phase(self, open_codes: List[OpenCode], axial_relationships: List[AxialRelationship], interviews: List[Dict[str, Any]]) -> List[CoreCategory]:
        """
        Phase 3: Selective Coding - Develop core categories that integrate the theory
        
        Identifies one or more core categories that have the most explanatory power and 
        can integrate the other categories into a coherent theoretical framework.
        Complex phenomena may require multiple core categories for full explanation.
        """
        try:
            # Prepare data for analysis
            codes_text = self._format_codes_for_analysis(open_codes)
            relationships_text = self._format_relationships_for_analysis(axial_relationships)
            
            # Generate configuration-driven prompt or use fallback
            if self.prompt_generator:
                selective_coding_prompt = self.prompt_generator.generate_selective_coding_prompt(codes_text, relationships_text)
            else:
                # Fallback static prompt
                selective_coding_prompt = '''
                You are conducting selective coding in grounded theory methodology to identify the core categories.
                
                Given these open codes and axial relationships, identify the CORE CATEGORY or CATEGORIES that:
                1. Have the most analytical power and explanatory capability
                2. Appear frequently and significantly in the data
                3. Relate meaningfully to other major categories
                4. Can integrate and explain the central phenomenon
                
                Note: Complex phenomena may require multiple core categories for complete explanation.
                Identify one or more core categories based on the data complexity.
                
                Open Codes:
                {open_codes}
                
                Axial Relationships:
                {axial_relationships}
                
                For each core category, provide:
                1. Clear name and definition
                2. The central phenomenon it explains
                3. How it relates to other major categories
                4. Its theoretical properties
                5. Why it has explanatory power
                6. Rationale for why this is a core integrating category
                
                The core categories should be the central organizing concepts for your emerging theory.
                '''.format(open_codes=codes_text, axial_relationships=relationships_text)
            
            # Generate core categories using LLM
            if hasattr(self.operations, '_llm_handler') and self.operations._llm_handler:
                # Create a response schema for multiple core categories
                from typing import List as ListType
                class CoreCategoriesResponse(BaseModel):
                    core_categories: ListType[CoreCategory] = Field(description="List of core categories identified")
                
                llm_response = await self.operations._llm_handler.extract_structured(
                    prompt=selective_coding_prompt,
                    schema=CoreCategoriesResponse,
                    instructions="Identify one or more core categories using grounded theory selective coding methodology"
                )
                
                core_categories = llm_response.core_categories
                
                logger.info(f"Selective coding phase complete: {len(core_categories)} core categories identified")
                for category in core_categories:
                    logger.info(f"  - Core category: '{category.category_name}'")
                return core_categories
            else:
                # Fallback: Create sample core category (return as list for consistency)
                logger.warning("LLM not available, using fallback selective coding")
                return [self._create_fallback_core_category(open_codes)]
                
        except Exception as e:
            logger.error(f"Selective coding phase failed: {e}")
            raise
    
    async def _theory_integration_phase(self, 
                                       open_codes: List[OpenCode],
                                       axial_relationships: List[AxialRelationship], 
                                       core_categories: List[CoreCategory],
                                       interviews: List[Dict[str, Any]]) -> TheoreticalModel:
        """
        Phase 4: Theoretical Integration - Generate final theoretical model
        
        Integrates all analysis phases into a coherent theoretical model with
        propositions, relationships, and implications.
        """
        try:
            # Prepare comprehensive summary for theory integration
            codes_summary = self._create_codes_summary(open_codes)
            relationships_summary = self._create_relationships_summary(axial_relationships)
            core_categories_text = "\n".join([
                f"- {cat.category_name}: {cat.definition}" 
                for cat in core_categories
            ])
            
            # Generate configuration-driven prompt or use fallback
            if self.prompt_generator:
                theory_integration_prompt = self.prompt_generator.generate_theory_integration_prompt(
                    core_categories_text, codes_summary, relationships_summary)
            else:
                # Fallback static prompt
                theory_integration_prompt = '''
                You are completing grounded theory analysis by integrating all phases into a coherent theoretical model.
                
                Based on the complete analysis:
                
                Core Categories: {core_categories}
                
                Open Codes: {open_codes_summary}
                
                Axial Relationships: {relationships_summary}
                
                Develop a comprehensive theoretical model that includes:
                1. Name for the theoretical model
                2. The core category and its central role
                3. Theoretical framework that explains the phenomenon
                4. Key theoretical propositions (if-then statements)
                5. Major conceptual relationships
                6. Scope conditions (when/where theory applies)
                7. Implications of the theory
                8. Suggested future research directions
                
                Create a theory that is:
                - Grounded in the data analyzed
                - Conceptually clear and well-integrated
                - Has explanatory and predictive power
                - Connects to broader theoretical understanding
                '''.format(
                    core_categories=core_categories_text,
                    open_codes_summary=codes_summary,
                    relationships_summary=relationships_summary
                )
            
            # Generate theoretical model using LLM
            if hasattr(self.operations, '_llm_handler') and self.operations._llm_handler:
                llm_response = await self.operations._llm_handler.extract_structured(
                    prompt=theory_integration_prompt,
                    schema=TheoreticalModel,
                    instructions="Integrate all analysis phases into a coherent theoretical model using grounded theory methodology"
                )
                
                theoretical_model = llm_response
                
                # Generate final theoretical memo
                # Add the complete GT results to the interviews data for memo generation
                interviews_with_theory = []
                for i, interview in enumerate(interviews):
                    import copy
                    enhanced_interview = copy.deepcopy(interview)  # Deep copy to avoid modifying original
                    if 'quotes' not in enhanced_interview:
                        enhanced_interview['quotes'] = []
                    
                    # Only add to first interview to avoid massive duplication
                    if i == 0:
                        # Add original codes
                        for code in open_codes:
                            for quote in code.supporting_quotes:
                                enhanced_interview['quotes'].append({
                                    'text': quote,
                                    'code': code.code_name,
                                    'frequency': code.frequency,
                                    'confidence': code.confidence
                                })
                        
                        # Add axial relationships
                        for rel in axial_relationships:
                            # Use first supporting evidence or relationship description
                            evidence_text = rel.supporting_evidence[0] if rel.supporting_evidence else f"{rel.central_category} relates to {rel.related_category}"
                            enhanced_interview['quotes'].append({
                                'text': evidence_text,
                                'code': f"RELATIONSHIP: {rel.central_category} → {rel.related_category}",
                                'frequency': 1,
                                'confidence': rel.strength
                            })
                        
                        # Add core category (use first one for compatibility)
                        first_core = core_categories[0] if core_categories else None
                        if first_core:
                            enhanced_interview['quotes'].append({
                                'text': first_core.definition,
                                'code': f"CORE CATEGORY: {first_core.category_name}",
                                'frequency': 1,
                                'confidence': 0.9  # High confidence for core category
                            })
                        
                        # Add theoretical model propositions
                        for prop in theoretical_model.propositions[:3]:  # First 3 propositions
                            enhanced_interview['quotes'].append({
                                'text': prop,
                                'code': f"THEORETICAL PROPOSITION",
                                'frequency': 1,
                                'confidence': 0.9
                            })
                    
                    interviews_with_theory.append(enhanced_interview)
                
                # Use first core category for memo focus
                focus_codes_list = [core_categories[0].category_name] if core_categories else []
                
                memo_result = await self.operations.generate_analytical_memo_from_data(
                    interviews_with_theory,
                    memo_type="theoretical_memo",
                    focus_codes=focus_codes_list,
                    memo_title=f"Theoretical Integration - {theoretical_model.model_name}"
                )
                
                if memo_result.get('success'):
                    self._generated_memos.append(memo_result)
                
                logger.info(f"Theory integration phase complete: Model '{theoretical_model.model_name}' developed")
                return theoretical_model
            else:
                # Fallback: Create sample theoretical model
                logger.warning("LLM not available, using fallback theory integration")
                return self._create_fallback_theoretical_model(core_categories)
                
        except Exception as e:
            logger.error(f"Theory integration phase failed: {e}")
            raise
    
    # Helper methods
    def _log_step(self, message: str):
        """Log analysis step with timestamp"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}"
        self._analysis_log.append(log_entry)
        logger.info(message)
    
    def _prepare_interview_text(self, interviews: List[Dict[str, Any]]) -> str:
        """Prepare interview data for LLM analysis"""
        interview_texts = []
        for i, interview in enumerate(interviews):
            interview_id = interview.get('interview_id', f'interview_{i+1}')
            
            # Handle both data formats: text field (current) and quotes array (legacy)
            if 'text' in interview and interview['text']:
                # Current format: direct text content
                interview_text = f"Interview {interview_id}:\n{interview['text']}"
                interview_texts.append(interview_text)
            elif 'quotes' in interview and interview['quotes']:
                # Legacy format: quotes array with speaker info
                quotes = interview.get('quotes', [])
                quote_texts = []
                for quote in quotes:
                    quote_text = quote.get('text', '')
                    speaker = quote.get('speaker', {}).get('name', 'Unknown')
                    quote_texts.append(f"{speaker}: {quote_text}")
                
                interview_text = f"Interview {interview_id}:\n" + "\n".join(quote_texts)
                interview_texts.append(interview_text)
            else:
                # Fallback: no usable content
                logger.warning(f"Interview {interview_id} has no usable text content")
                interview_texts.append(f"Interview {interview_id}:\n[No content available]")
        
        return "\n\n".join(interview_texts)
    
    def _format_codes_for_analysis(self, open_codes: List[OpenCode]) -> str:
        """Format open codes for LLM analysis"""
        formatted_codes = []
        for code in open_codes:
            code_text = f"- {code.code_name}: {code.description}\n"
            code_text += f"  Properties: {', '.join(code.properties)}\n"
            code_text += f"  Frequency: {code.frequency}, Confidence: {code.confidence:.2f}"
            formatted_codes.append(code_text)
        return "\n\n".join(formatted_codes)
    
    def _format_relationships_for_analysis(self, relationships: List[AxialRelationship]) -> str:
        """Format axial relationships for LLM analysis"""
        formatted_rels = []
        for rel in relationships:
            rel_text = f"- {rel.central_category} → {rel.related_category}\n"
            rel_text += f"  Type: {rel.relationship_type}\n"
            rel_text += f"  Conditions: {', '.join(rel.conditions)}\n"
            rel_text += f"  Consequences: {', '.join(rel.consequences)}\n"
            rel_text += f"  Strength: {rel.strength:.2f}"
            formatted_rels.append(rel_text)
        return "\n\n".join(formatted_rels)
    
    def _create_codes_summary(self, open_codes: List[OpenCode]) -> str:
        """Create summary of open codes for theory integration"""
        top_codes = sorted(open_codes, key=lambda x: x.frequency, reverse=True)[:10]
        summary_parts = []
        for code in top_codes:
            summary_parts.append(f"{code.code_name} (freq: {code.frequency}): {code.description}")
        return "; ".join(summary_parts)
    
    def _create_relationships_summary(self, relationships: List[AxialRelationship]) -> str:
        """Create summary of axial relationships for theory integration"""
        strong_rels = sorted(relationships, key=lambda x: x.strength, reverse=True)[:5]
        summary_parts = []
        for rel in strong_rels:
            summary_parts.append(f"{rel.central_category} → {rel.related_category} ({rel.relationship_type})")
        return "; ".join(summary_parts)
    
    def _create_open_codes_schema(self) -> type:
        """Create schema for open codes LLM extraction"""
        from pydantic import BaseModel
        
        class OpenCodesResponse(BaseModel):
            open_codes: List[OpenCode] = Field(description="List of open codes identified")
            
        return OpenCodesResponse
    
    def _create_axial_relationships_schema(self) -> type:
        """Create schema for axial relationships LLM extraction"""
        from pydantic import BaseModel
        
        class AxialRelationshipsResponse(BaseModel):
            axial_relationships: List[AxialRelationship] = Field(description="List of axial relationships identified")
            
        return AxialRelationshipsResponse
    
    # Fallback methods for testing without LLM
    def _create_fallback_open_codes(self, interviews: List[Dict[str, Any]]) -> List[OpenCode]:
        """Create sample open codes for testing"""
        return [
            OpenCode(
                code_name="Communication Challenges",
                description="Difficulties in effective communication within teams",
                properties=["frequency", "impact", "context"],
                dimensions=["formal-informal", "verbal-written", "internal-external"],
                supporting_quotes=["Sample quote about communication"],
                frequency=5,
                confidence=0.8
            ),
            OpenCode(
                code_name="Adaptation Strategies", 
                description="Methods used to adapt to changing circumstances",
                properties=["flexibility", "timing", "effectiveness"],
                dimensions=["proactive-reactive", "individual-collective"],
                supporting_quotes=["Sample quote about adaptation"],
                frequency=3,
                confidence=0.7
            )
        ]
    
    def _create_fallback_relationships(self, open_codes: List[OpenCode]) -> List[AxialRelationship]:
        """Create sample axial relationships for testing"""
        if len(open_codes) >= 2:
            return [
                AxialRelationship(
                    central_category=open_codes[0].code_name,
                    related_category=open_codes[1].code_name,
                    relationship_type="causal",
                    conditions=["organizational context", "time pressure"],
                    consequences=["reduced efficiency", "increased stress"],
                    supporting_evidence=["Sample evidence"],
                    strength=0.8
                )
            ]
        return []
    
    def _create_fallback_core_category(self, open_codes: List[OpenCode]) -> CoreCategory:
        """Create sample core category for testing"""
        primary_code = open_codes[0] if open_codes else None
        return CoreCategory(
            category_name="Organizational Adaptation" if primary_code else "Sample Core Category",
            definition="The process of adapting to organizational changes and challenges",
            central_phenomenon="organizational change management",
            related_categories=[code.code_name for code in open_codes[:3]],
            theoretical_properties=["processual", "contextual", "strategic"],
            explanatory_power="Explains how organizations navigate change through adaptive processes",
            integration_rationale="Most frequently occurring and connects to all major categories"
        )
    
    def _create_fallback_theoretical_model(self, core_categories: List[CoreCategory]) -> TheoreticalModel:
        """Create sample theoretical model for testing"""
        first_category = core_categories[0] if core_categories else None
        category_names = [cat.category_name for cat in core_categories]
        
        return TheoreticalModel(
            model_name=f"Theory of {' and '.join(category_names)}",
            core_categories=category_names,
            theoretical_framework=f"A framework explaining {first_category.central_phenomenon if first_category else 'the phenomenon'}",
            propositions=[
                f"When {first_category.category_name if first_category else 'the phenomenon'} occurs, adaptation strategies are activated",
                "Contextual conditions influence the effectiveness of adaptation processes"
            ],
            conceptual_relationships=[
                f"{first_category.category_name if first_category else 'The core phenomenon'} leads to strategic responses",
                "Environmental conditions moderate adaptive processes"
            ],
            scope_conditions=["organizational contexts", "change situations"],
            implications=["Organizations need adaptive capacity", "Context matters for strategy"],
            future_research=["Test theory in different contexts", "Examine long-term outcomes"]
        )
    
    async def _process_entities_and_relationships(self, interview_file: str, 
                                                codes: List[OpenCode], 
                                                text: str) -> None:
        """Extract and store entities and relationships in Neo4j"""
        logger.info("Starting entity-relationship extraction and storage")
        
        # Extract entities from text using existing patterns
        entities = await self._extract_entities_from_text(text, codes)
        logger.info(f"Extracted {len(entities)} entities")
        
        # Extract relationships between entities  
        relationships = await self._extract_relationships_from_entities(entities, text)
        logger.info(f"Extracted {len(relationships)} relationships")
        
        # Store in Neo4j
        stored_entities = 0
        stored_relationships = 0
        
        try:
            # Store entities
            for entity in entities:
                entity_node = self._create_entity_node(entity, interview_file)
                await self.operations._neo4j_manager.create_entity(entity_node)
                stored_entities += 1
            
            # Store relationships based on entity content analysis
            if len(entities) > 1:  # Need at least 2 entities for relationships
                try:
                    relationships_created = await self._create_content_relationships(entities)
                    logger.info(f"Created {relationships_created} content-based relationships")
                    stored_relationships += relationships_created
                except Exception as e:
                    logger.error(f"Relationship creation failed: {e}")
                    raise ProcessingError(f"Content relationship creation failed: {e}")
            
            # Store original LLM relationships
            for relationship in relationships:
                relationship_edge = self._create_relationship_edge(relationship)
                await self.operations._neo4j_manager.create_relationship(relationship_edge)
                stored_relationships += 1
                
            logger.info(f"Stored {stored_entities} entities and {stored_relationships} relationships in Neo4j")
            
        except Exception as e:
            logger.error(f"Neo4j storage failed: {e}")
            raise

    async def _extract_entities_from_text(self, text: str, codes: List[OpenCode]) -> List[Dict[str, Any]]:
        """Extract entities from interview text"""
        # Use existing LLM handler for entity extraction
        prompt = f"""
Extract entities from this interview text. Focus on:
- People (speakers, participants, mentioned individuals)
- Organizations (companies, institutions)
- Concepts (key ideas, themes from codes: {[c.code_name for c in codes[:5]]})
- Locations (places mentioned)

Text: {text[:2000]}...

Return JSON with entities array containing: name, type, description, quotes
"""
        
        try:
            response = await self.operations.llm_handler.complete_raw(prompt, temperature=0.1)
            # Parse response similar to existing code extraction
            entities = self._parse_entity_response(response)
            return entities
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []

    async def _extract_relationships_from_entities(self, entities: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """Extract relationships between entities"""
        if len(entities) < 2:
            return []
            
        entity_names = [e['name'] for e in entities]
        prompt = f"""
Analyze relationships between these entities from the interview text:
Entities: {entity_names}

Text: {text[:2000]}...

Identify relationships such as:
- WORKS_WITH, MANAGES, COLLABORATES_WITH (for people)
- BELONGS_TO, OPERATES_IN (for organizations/locations)
- INFLUENCES, CAUSES, RELATES_TO (for concepts)

Return JSON with relationships array containing: source, target, type, description
"""
        
        try:
            response = await self.operations.llm_handler.complete_raw(prompt, temperature=0.1)
            relationships = self._parse_relationship_response(response)
            return relationships
        except Exception as e:
            logger.error(f"Relationship extraction failed: {e}")
            return []

    def _create_entity_node(self, entity: Dict[str, Any], interview_file: str) -> 'EntityNode':
        """Create EntityNode for Neo4j storage"""
        from ..data.neo4j_manager import EntityNode
        
        return EntityNode(
            id=f"{entity['type']}_{entity['name'][:50]}".replace(' ', '_'),
            name=entity['name'],
            entity_type=entity['type'],
            properties={
                'description': entity.get('description', ''),
                'source_interview': interview_file,
                'quotes': entity.get('quotes', []),
                'extracted_at': str(datetime.now())
            }
        )

    def _create_relationship_edge(self, relationship: Dict[str, Any]) -> 'RelationshipEdge':
        """Create RelationshipEdge for Neo4j storage"""
        from ..data.neo4j_manager import RelationshipEdge
        
        return RelationshipEdge(
            source_id=f"{relationship['source']}".replace(' ', '_'),
            target_id=f"{relationship['target']}".replace(' ', '_'),
            relationship_type=relationship['type'],
            properties={
                'description': relationship.get('description', ''),
                'extracted_at': str(datetime.now())
            }
        )

    def _parse_entity_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM entity extraction response"""
        # Implement similar to existing code parsing
        try:
            import json
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response
            
            parsed = json.loads(json_str)
            return parsed.get('entities', [])
        except Exception as e:
            logger.error(f"Entity response parsing failed: {e}")
            return []

    def _parse_relationship_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM relationship extraction response"""
        try:
            import json
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response
            
            parsed = json.loads(json_str)
            return parsed.get('relationships', [])
        except Exception as e:
            logger.error(f"Relationship response parsing failed: {e}")
            return []

    async def _create_content_relationships(self, entities: List[Dict[str, Any]]) -> int:
        """Create relationships based on entity content analysis using working algorithm"""
        logger.info("Creating content-based relationships between entities")
        created_relationships = 0
        
        # Convert to list for indexing
        entity_list = list(entities)
        
        for i, entity1 in enumerate(entity_list):
            name1 = entity1['name'].lower() if entity1.get('name') else ''
            desc1 = entity1.get('description', '').lower()
            entity1_id = entity1.get('id', '')
            
            if not entity1_id or not name1:
                continue
                
            for j, entity2 in enumerate(entity_list):
                if i >= j:  # Avoid duplicates and self-references
                    continue
                    
                name2 = entity2['name'].lower() if entity2.get('name') else ''
                desc2 = entity2.get('description', '').lower()
                entity2_id = entity2.get('id', '')
                
                if not entity2_id or not name2:
                    continue
                
                # Content analysis: Check if entities mention each other
                relationship_found = False
                rel_type = "MENTIONS"
                
                if name1 in desc2:
                    logger.debug(f"Found mention: {entity2['name']} mentions {entity1['name']}")
                    relationship_found = True
                elif name2 in desc1:
                    logger.debug(f"Found mention: {entity1['name']} mentions {entity2['name']}")
                    relationship_found = True
                
                if relationship_found:
                    try:
                        from ..data.neo4j_manager import RelationshipEdge
                        
                        edge = RelationshipEdge(
                            source_id=entity1_id,
                            target_id=entity2_id,
                            relationship_type=rel_type,
                            properties={
                                'created_by': 'content_analysis',
                                'confidence': 0.8,
                                'method': 'entity_mention_detection',
                                'extracted_at': str(datetime.now())
                            }
                        )
                        
                        success = await self.operations._neo4j_manager.create_relationship(edge)
                        if success:
                            created_relationships += 1
                            logger.debug(f"Created relationship: {entity1['name']} --{rel_type}--> {entity2['name']}")
                        else:
                            logger.warning(f"Failed to create relationship: {entity1['name']} --{rel_type}--> {entity2['name']}")
                            
                    except Exception as e:
                        logger.error(f"Relationship creation error: {e}")
        
        return created_relationships