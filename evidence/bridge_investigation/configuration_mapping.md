# Configuration Schema Mapping Analysis

**Investigation Date**: 2025-09-05  
**Objective**: Map fields between `UnifiedConfig` and `ExtractionConfig` to determine compatibility

## Schema Comparison

### Current UnifiedConfig Schema
From `qc_clean/config/unified_config.py`:

```python
@dataclass
class UnifiedConfig:
    # Provider settings
    api_provider: str
    model: str
    temperature: float
    
    # Research methodology 
    methodology: str
    validation_level: str
    coding_approach: str
    
    # Analysis parameters
    confidence_threshold: float
    min_code_frequency: int
    enable_hierarchy: bool
    max_hierarchy_levels: int
    
    # Data processing
    chunk_size: int
    max_tokens: Optional[int]
    
    # LLM reliability
    max_llm_retries: int
    base_retry_delay: float
    circuit_breaker_threshold: int
    
    # Dynamic API key resolution
    @property
    def api_key(self) -> str: ...
```

### Required ExtractionConfig Schema  
From `archive/old_system/qc/extraction/code_first_schemas.py`:

```python
class ExtractionConfig(BaseModel):
    # Core configuration
    analytic_question: str                    # Research question
    interview_files_dir: str                  # Directory path
    
    # Code configuration
    coding_approach: ExtractionApproach       # OPEN, CLOSED, MIXED
    predefined_codes_file: Optional[str]      # Path to codes file
    code_hierarchy_depth: int = 2             # Hierarchy depth
    
    # Speaker configuration  
    speaker_approach: ExtractionApproach      # OPEN, CLOSED, MIXED
    predefined_speaker_schema_file: Optional[str]
    
    # Entity/Relationship configuration
    entity_approach: ExtractionApproach       # OPEN, CLOSED, MIXED  
    predefined_entity_schema_file: Optional[str]
    
    # Output configuration
    output_dir: str = "output"                # Output directory
    auto_import_neo4j: bool = True            # Neo4j import
    
    # Neo4j connection settings
    neo4j_uri: Optional[str]                  # Neo4j connection
    neo4j_user: Optional[str]
    neo4j_password: Optional[str]
    
    # LLM configuration
    llm_model: str = "gemini/gemini-2.5-flash"  # Model name
    temperature: float = 0.1                    # LLM temperature
    
    # Performance configuration
    max_concurrent_interviews: int = 5          # Parallel processing
    
    # Analysis paradigm  
    paradigm: str = "expert_qualitative_coder"  # Analysis lens
```

## Field Mapping Analysis

**STATUS**: ✅ COMPLETED

| ExtractionConfig Field | UnifiedConfig Equivalent | Mapping Strategy | Compatibility |
|----------------------|--------------------------|------------------|---------------|
| `analytic_question` | ❌ NOT PRESENT | Default/env var | ⚠️ MISSING |
| `interview_files_dir` | ❌ NOT PRESENT | Default/env var | ⚠️ MISSING |
| `coding_approach` | ✅ `coding_approach` | Direct enum map | ✅ COMPATIBLE |
| `predefined_codes_file` | ❌ NOT PRESENT | Default None | ⚠️ MISSING |
| `code_hierarchy_depth` | ❌ NOT PRESENT | Default 2 | ⚠️ MISSING |
| `speaker_approach` | ❌ NOT PRESENT | Map from coding_approach | ⚠️ MISSING |
| `entity_approach` | ❌ NOT PRESENT | Map from coding_approach | ⚠️ MISSING |
| `output_dir` | ❌ NOT PRESENT | Default "output" | ⚠️ MISSING |
| `auto_import_neo4j` | ❌ NOT PRESENT | Default True | ⚠️ MISSING |
| `neo4j_uri` | ❌ NOT PRESENT | From env/default | ⚠️ MISSING |
| `neo4j_user` | ❌ NOT PRESENT | From env/default | ⚠️ MISSING |
| `neo4j_password` | ❌ NOT PRESENT | From env/default | ⚠️ MISSING |
| `llm_model` | ✅ `model_preference` + `api_provider` | Format as "provider/model" | ✅ COMPATIBLE |
| `temperature` | ✅ `temperature` | Direct map | ✅ COMPATIBLE |
| `max_concurrent_interviews` | ❌ NOT PRESENT | Default 5 | ⚠️ MISSING |
| `paradigm` | ✅ `methodology` (partial) | Map methodology enum | ⚠️ PARTIAL |

## Missing Fields Analysis

**Fields in ExtractionConfig but NOT in UnifiedConfig** (8 missing):
- `analytic_question` - Core research question driving analysis
- `interview_files_dir` - Input data directory path  
- `predefined_codes_file` - Closed/mixed approach schema files
- `code_hierarchy_depth` - Hierarchy structure depth
- `speaker_approach` - Speaker detection approach (open/closed/mixed)
- `entity_approach` - Entity extraction approach (open/closed/mixed)  
- `output_dir` - Output directory path
- `auto_import_neo4j` - Neo4j integration flag
- `neo4j_uri/user/password` - Database connection settings
- `max_concurrent_interviews` - Performance tuning

**Fields in UnifiedConfig but NOT in ExtractionConfig** (15+ extra):
- All extractor_type, validation_level, theoretical_sensitivity etc.
- Quality control parameters
- Reliability settings

## Adapter Function Requirements

**Adapter Strategy**: 
```python
def adapt_unified_to_extraction_config(
    unified: UnifiedConfig, 
    analytic_question: str = None,
    interview_files_dir: str = None
) -> ExtractionConfig:
    """Adapt UnifiedConfig to ExtractionConfig with sensible defaults"""
    
    return ExtractionConfig(
        # Required fields (need defaults or parameters)
        analytic_question=analytic_question or os.getenv('ANALYTIC_QUESTION', 'Default research question'),
        interview_files_dir=interview_files_dir or os.getenv('INTERVIEW_FILES_DIR', 'data/interviews'),
        
        # Direct mappings
        coding_approach=ExtractionApproach(unified.coding_approach.value),
        temperature=unified.temperature,
        llm_model=f"{unified.api_provider}/{unified.model_preference}",
        
        # Derived mappings
        speaker_approach=ExtractionApproach(unified.coding_approach.value),  # Use same as coding
        entity_approach=ExtractionApproach(unified.coding_approach.value),   # Use same as coding
        paradigm=unified.methodology.value,  # Map methodology to paradigm
        
        # Environment-based defaults
        output_dir=os.getenv('OUTPUT_DIR', 'output'),
        auto_import_neo4j=os.getenv('AUTO_IMPORT_NEO4J', 'true').lower() == 'true',
        neo4j_uri=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        neo4j_user=os.getenv('NEO4J_USER', 'neo4j'),
        neo4j_password=os.getenv('NEO4J_PASSWORD', 'password'),
        
        # Performance defaults
        max_concurrent_interviews=int(os.getenv('MAX_CONCURRENT_INTERVIEWS', '5')),
        
        # Optional defaults
        predefined_codes_file=os.getenv('PREDEFINED_CODES_FILE'),
        code_hierarchy_depth=int(os.getenv('CODE_HIERARCHY_DEPTH', '2')),
    )
```

## Risk Assessment

**COMPATIBILITY RISK**: ⚠️ **MEDIUM** 

**Key Findings**:
- ✅ Core LLM parameters (model, temperature) are compatible
- ✅ Coding approach enum maps correctly
- ⚠️ 8 critical fields missing from UnifiedConfig
- ⚠️ Requires additional environment variables or function parameters
- ✅ All missing fields have reasonable defaults

**Missing Field Strategy**: **Use environment variables + function parameters for critical fields**