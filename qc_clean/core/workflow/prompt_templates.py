#!/usr/bin/env python3
"""
Configuration-Driven Prompt Generation for Grounded Theory Analysis

Provides dynamic prompt generation based on methodology configuration parameters.
Replaces static prompts with configuration-aware prompt templates that modify
analysis behavior based on theoretical sensitivity, coding depth, and other parameters.
"""

import logging
from typing import Dict, Any, Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.methodology_config import GroundedTheoryConfig

logger = logging.getLogger(__name__)


class ConfigurablePromptGenerator:
    """Configuration-driven prompt generation for GT analysis"""
    
    def __init__(self, config: GroundedTheoryConfig):
        """Initialize with grounded theory configuration"""
        self.config = config
        logger.info(f"Prompt generator initialized with {config.theoretical_sensitivity} sensitivity, "
                   f"{config.coding_depth} depth")
    
    def generate_open_coding_prompt(self, interview_data: str) -> str:
        """Generate open coding prompt based on configuration"""
        
        # Base template for open coding
        base_template = """You are an expert qualitative researcher conducting open coding analysis following grounded theory methodology.

{theoretical_sensitivity}

{coding_depth}

Analyze the following interview data and identify key concepts and categories. For each concept identified:

1. Name the concept clearly and concisely
2. Describe what this concept represents in the data
3. Identify properties (characteristics) of this concept
4. Note dimensional variations (different ways this concept appears)
5. Provide supporting quotes that demonstrate this concept
6. Assess frequency and confidence

Follow open coding principles:
- Stay close to the data
- Use participants' language when possible
- Look for actions, interactions, and meanings
- Ask: What is happening here? What are people doing?

{analysis_focus}

Interview Data:
{interview_data}

Generate comprehensive open codes that capture the key concepts in this data."""

        # Configuration-specific instructions
        sensitivity_guidance = self._get_sensitivity_instructions()
        depth_guidance = self._get_depth_instructions()
        analysis_focus = self._get_analysis_focus()
        
        prompt = base_template.format(
            interview_data=interview_data,
            theoretical_sensitivity=sensitivity_guidance,
            coding_depth=depth_guidance,
            analysis_focus=analysis_focus
        )
        
        logger.debug(f"Generated open coding prompt with {len(prompt)} characters")
        return prompt
    
    def generate_axial_coding_prompt(self, open_codes_text: str, interview_data: str) -> str:
        """Generate axial coding prompt based on configuration"""
        
        base_template = """You are conducting axial coding analysis in grounded theory methodology.

{theoretical_sensitivity}

{coding_depth}

Given these open codes from the previous phase, identify relationships between categories:

Open Codes:
{open_codes}

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

{analysis_focus}

Original Interview Data:
{interview_data}

Identify the key relationships that help explain the phenomena in the data."""

        sensitivity_guidance = self._get_sensitivity_instructions()
        depth_guidance = self._get_depth_instructions()
        analysis_focus = self._get_analysis_focus()
        
        prompt = base_template.format(
            open_codes=open_codes_text,
            interview_data=interview_data,
            theoretical_sensitivity=sensitivity_guidance,
            coding_depth=depth_guidance,
            analysis_focus=analysis_focus
        )
        
        logger.debug(f"Generated axial coding prompt with {len(prompt)} characters")
        return prompt
    
    def generate_selective_coding_prompt(self, open_codes_text: str, relationships_text: str) -> str:
        """Generate selective coding prompt based on configuration"""
        
        base_template = """You are conducting selective coding in grounded theory methodology to identify the core category.

{theoretical_sensitivity}

{coding_depth}

Given these open codes and axial relationships, identify the CORE CATEGORY that:
1. Has the most analytical power and explanatory capability
2. Appears frequently and significantly in the data
3. Relates meaningfully to other major categories
4. Can integrate and explain the central phenomenon

Open Codes:
{open_codes}

Axial Relationships:
{axial_relationships}

Identify the core category and provide:
1. Clear name and definition
2. The central phenomenon it explains
3. How it relates to other major categories
4. Its theoretical properties
5. Why it has the most explanatory power
6. Rationale for why this is the core integrating category

{analysis_focus}

The core category should be the central organizing concept for your emerging theory."""

        sensitivity_guidance = self._get_sensitivity_instructions()
        depth_guidance = self._get_depth_instructions()
        analysis_focus = self._get_analysis_focus()
        
        prompt = base_template.format(
            open_codes=open_codes_text,
            axial_relationships=relationships_text,
            theoretical_sensitivity=sensitivity_guidance,
            coding_depth=depth_guidance,
            analysis_focus=analysis_focus
        )
        
        logger.debug(f"Generated selective coding prompt with {len(prompt)} characters")
        return prompt
    
    def generate_theory_integration_prompt(self, core_category_text: str, codes_summary: str, relationships_summary: str) -> str:
        """Generate theory integration prompt based on configuration"""
        
        base_template = """You are completing grounded theory analysis by integrating all phases into a coherent theoretical model.

{theoretical_sensitivity}

{coding_depth}

Based on the complete analysis:

Core Category: {core_category}

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

{analysis_focus}

Create a theory that is:
- Grounded in the data analyzed
- Conceptually clear and well-integrated
- Has explanatory and predictive power
- Connects to broader theoretical understanding"""

        sensitivity_guidance = self._get_sensitivity_instructions()
        depth_guidance = self._get_depth_instructions()
        analysis_focus = self._get_analysis_focus()
        
        prompt = base_template.format(
            core_category=core_category_text,
            open_codes_summary=codes_summary,
            relationships_summary=relationships_summary,
            theoretical_sensitivity=sensitivity_guidance,
            coding_depth=depth_guidance,
            analysis_focus=analysis_focus
        )
        
        logger.debug(f"Generated theory integration prompt with {len(prompt)} characters")
        return prompt
    
    def _get_sensitivity_instructions(self) -> str:
        """Map configuration to theoretical sensitivity instructions"""
        if self.config.theoretical_sensitivity == "high":
            return """THEORETICAL SENSITIVITY: HIGH
Apply maximum theoretical sensitivity. Look for subtle nuances, implicit meanings, and theoretical connections. Consider abstract concepts and theoretical frameworks. Interpret data through theoretical lenses and identify connections to existing theory. Focus on conceptual depth and theoretical abstraction."""
        elif self.config.theoretical_sensitivity == "medium":
            return """THEORETICAL SENSITIVITY: MEDIUM
Apply moderate theoretical sensitivity. Balance concrete observations with theoretical interpretation. Look for both obvious patterns and deeper meanings. Consider theoretical connections while staying grounded in the data."""
        else:  # low
            return """THEORETICAL SENSITIVITY: LOW
Focus on concrete, observable phenomena. Identify clear, directly evident patterns without extensive theoretical interpretation. Stay close to the data and avoid abstract theoretical connections. Emphasize descriptive rather than interpretive analysis."""
    
    def _get_depth_instructions(self) -> str:
        """Map coding depth to analysis instructions"""
        if self.config.coding_depth == "comprehensive":
            return """CODING DEPTH: COMPREHENSIVE
Conduct exhaustive analysis of all aspects. Generate detailed codes for every significant element, including context, relationships, and implications. Analyze nuances, variations, and subtle patterns. Be thorough and include minor themes that may be theoretically relevant."""
        elif self.config.coding_depth == "focused":
            return """CODING DEPTH: FOCUSED  
Focus on central themes and key patterns. Identify important codes while maintaining analytical focus. Balance thoroughness with selectivity. Emphasize major themes and significant patterns while noting important secondary elements."""
        else:  # minimal
            return """CODING DEPTH: MINIMAL
Identify only the most prominent, central themes. Focus on obvious patterns and major concepts. Prioritize the most significant and frequent elements. Keep analysis streamlined and focused on core findings."""
    
    def _get_analysis_focus(self) -> str:
        """Get analysis focus instructions based on validation level"""
        if self.config.validation_level == "rigorous":
            return """ANALYSIS REQUIREMENTS: RIGOROUS VALIDATION
Provide detailed justification for each code or relationship identified. Include confidence scores and supporting evidence. Question your interpretations and consider alternative explanations. Maintain high standards for inclusion criteria."""
        elif self.config.validation_level == "standard":
            return """ANALYSIS REQUIREMENTS: STANDARD VALIDATION
Support your analysis with clear evidence from the data. Provide reasonable justification for codes and relationships. Maintain good analytical standards while being efficient."""
        else:  # minimal
            return """ANALYSIS REQUIREMENTS: MINIMAL VALIDATION
Focus on clear, obvious patterns with basic supporting evidence. Keep analysis efficient while maintaining analytical integrity."""
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of configuration parameters used in prompt generation"""
        return {
            "theoretical_sensitivity": self.config.theoretical_sensitivity,
            "coding_depth": self.config.coding_depth,
            "validation_level": self.config.validation_level,
            "minimum_code_frequency": self.config.minimum_code_frequency,
            "relationship_confidence_threshold": self.config.relationship_confidence_threshold
        }