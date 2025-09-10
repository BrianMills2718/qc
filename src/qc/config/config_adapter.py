"""
Configuration Adapter for Bridge Architecture
Maps UnifiedConfig (qc_clean) to ExtractionConfig (sophisticated system)
"""

import os
from pathlib import Path
from qc_clean.config.unified_config import UnifiedConfig
from src.qc.extraction.code_first_schemas import ExtractionConfig, ExtractionApproach


def map_coding_approach(unified_approach):
    """Map UnifiedConfig.CodingApproach to ExtractionConfig.ExtractionApproach"""
    mapping = {
        'open': ExtractionApproach.OPEN,
        'closed': ExtractionApproach.CLOSED,
        'mixed': ExtractionApproach.MIXED
    }
    return mapping.get(unified_approach.value if hasattr(unified_approach, 'value') else str(unified_approach), 
                      ExtractionApproach.OPEN)


def create_extraction_config_from_unified(
    unified_config: UnifiedConfig = None,
    analytic_question: str = None,
    interview_files_dir: str = None,
    output_dir: str = "output"
) -> ExtractionConfig:
    """
    Create ExtractionConfig from UnifiedConfig with adapter layer
    
    Args:
        unified_config: UnifiedConfig instance (created if None)
        analytic_question: Research question (required for sophisticated system)
        interview_files_dir: Directory containing interview files (required)
        output_dir: Output directory
    
    Returns:
        ExtractionConfig configured with adapted values
    """
    
    if unified_config is None:
        unified_config = UnifiedConfig()
    
    # Required parameters with defaults based on investigation findings
    if analytic_question is None:
        analytic_question = os.getenv('ANALYTIC_QUESTION', 
                                    "What are the key themes and relationships in these qualitative interviews?")
    
    if interview_files_dir is None:
        interview_files_dir = os.getenv('INTERVIEW_FILES_DIR', 'data/interviews')
    
    # Map model preference to sophisticated system format
    llm_model = unified_config.model_preference
    if not llm_model.startswith(('gemini/', 'gpt-', 'claude-')):
        # Add provider prefix for litellm compatibility
        if 'gemini' in llm_model.lower():
            llm_model = f"gemini/{llm_model}"
        elif 'gpt' in llm_model.lower():
            llm_model = f"openai/{llm_model}"
    
    # Create ExtractionConfig with mapped values
    extraction_config = ExtractionConfig(
        # Core configuration (required)
        analytic_question=analytic_question,
        interview_files_dir=interview_files_dir,
        
        # Code configuration (mapped from unified)
        coding_approach=map_coding_approach(unified_config.coding_approach),
        predefined_codes_file=os.getenv('PREDEFINED_CODES_FILE'),
        code_hierarchy_depth=int(os.getenv('CODE_HIERARCHY_DEPTH', '2')),
        
        # Speaker configuration (defaults with environment overrides) 
        speaker_approach=ExtractionApproach(os.getenv('SPEAKER_APPROACH', 'open')),
        predefined_speaker_schema_file=os.getenv('PREDEFINED_SPEAKER_SCHEMA_FILE'),
        
        # Entity/Relationship configuration (defaults with environment overrides)
        entity_approach=ExtractionApproach(os.getenv('ENTITY_APPROACH', 'open')),
        predefined_entity_schema_file=os.getenv('PREDEFINED_ENTITY_SCHEMA_FILE'),
        
        # Output configuration
        output_dir=output_dir,
        auto_import_neo4j=os.getenv('AUTO_IMPORT_NEO4J', 'true').lower() == 'true',
        
        # Neo4j configuration (from environment)
        neo4j_uri=os.getenv('NEO4J_URI'),
        neo4j_user=os.getenv('NEO4J_USER'),
        neo4j_password=os.getenv('NEO4J_PASSWORD'),
        
        # LLM configuration (mapped from unified)
        llm_model=llm_model,
        temperature=unified_config.temperature,
        
        # Performance configuration
        max_concurrent_interviews=int(os.getenv('MAX_CONCURRENT_INTERVIEWS', '5')),
        
        # Analysis paradigm
        paradigm=os.getenv('ANALYSIS_PARADIGM', 'expert_qualitative_coder')
    )
    
    return extraction_config


def create_default_extraction_config(
    analytic_question: str,
    interview_files_dir: str,
    output_dir: str = "output"
) -> ExtractionConfig:
    """
    Create ExtractionConfig with reasonable defaults for quick testing
    
    Args:
        analytic_question: Research question
        interview_files_dir: Directory containing interview files
        output_dir: Output directory
        
    Returns:
        ExtractionConfig with defaults
    """
    
    return ExtractionConfig(
        analytic_question=analytic_question,
        interview_files_dir=interview_files_dir,
        output_dir=output_dir,
        coding_approach=ExtractionApproach.OPEN,
        speaker_approach=ExtractionApproach.OPEN,
        entity_approach=ExtractionApproach.OPEN,
        auto_import_neo4j=True,
        llm_model="gemini/gemini-2.5-flash",
        temperature=0.1,
        max_concurrent_interviews=5,
        paradigm="expert_qualitative_coder"
    )