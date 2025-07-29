# Framework Specifications for Qualitative Coding System

Based on comprehensive review of documentation and preserved code, here are the solid framework specifications:

---

## 📊 Token Management Strategy (RESOLVED)

### Key Decisions from Migration Analysis:
From `migrate_to_simple_gemini.py` and `simple_gemini_client.py`:

**1. NO CHUNKING for Gemini 2.5 Flash**
- **Context Window**: 1M tokens input capacity (not 900K artificial limit)
- **Output Capacity**: 60K tokens (not 4K artificial limit)
- **Strategy**: Send complete interviews without chunking
- **Rationale**: "NO artificial limits, NO unnecessary chunking, FULL observability"

```python
# From simple_gemini_client.py:
self.generation_config = types.GenerateContentConfig(
    temperature=float(os.getenv('GEMINI_TEMPERATURE', '0.3')),
    max_output_tokens=int(os.getenv('GEMINI_MAX_OUTPUT_TOKENS', '60000')),  # Use full capacity!
    response_mime_type='application/json'  # Force JSON output
)
```

### Token Handling Approach:
1. **Single-Pass Extraction**: Complete interview in one LLM call
2. **No Chunking Logic**: Removed complex token_manager.py 
3. **Full Context Usage**: Leverage 1M token window
4. **Large Output Support**: 60K tokens for comprehensive theme extraction

---

## 🚨 Comprehensive Error Handling Framework

### Error Types (from `robust_error_handling.py`):
```python
class ErrorType(Enum):
    LLM_TIMEOUT = "llm_timeout"
    LLM_MALFORMED_JSON = "llm_malformed_json"
    LLM_EMPTY_RESPONSE = "llm_empty_response"
    SCHEMA_VALIDATION = "schema_validation"
    DATA_CORRUPTION = "data_corruption"
    TOKEN_LIMIT_EXCEEDED = "token_limit_exceeded"
    PARSING_ERROR = "parsing_error"
    UNKNOWN_ERROR = "unknown_error"
```

### Error Severity Levels:
```python
class ErrorSeverity(Enum):
    LOW = "low"           # Continue processing with fallback
    MEDIUM = "medium"     # Warn user but continue
    HIGH = "high"         # Stop current operation, try recovery
    CRITICAL = "critical" # Stop all processing
```

### Error Handling Strategy:
1. **Structured Error Results**:
   ```python
   @dataclass
   class OperationResult:
       success: bool
       data: Any = None
       errors: List[ErrorDetails] = field(default_factory=list)
       warnings: List[str] = field(default_factory=list)
       metadata: Dict[str, Any] = field(default_factory=dict)
   ```

2. **Retry Logic with Exponential Backoff**:
   ```python
   # From robust_error_handling.py
   max_retries = 3
   retry_delay = 2.0
   await asyncio.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
   ```

3. **JSON Parsing Recovery**:
   - Direct JSON parsing
   - Extract from markdown blocks
   - Find JSON-like objects
   - Manual structure extraction

### Additional Error Scenarios to Handle:

**File Processing Errors**:
- `FileNotFoundError`: Interview file doesn't exist
- `CorruptFileError`: DOCX file unreadable
- `EncodingError`: Text encoding issues
- `FileTooLargeError`: File exceeds reasonable size

**LLM Integration Errors**:
- `APIKeyError`: Missing or invalid API key
- `RateLimitError`: API rate limits exceeded
- `ServiceDownError`: Gemini service unavailable
- `ResponseTimeoutError`: LLM takes too long

**Processing Errors**:
- `MemoryError`: Out of memory during processing
- `DiskSpaceError`: Insufficient space for outputs
- `PermissionError`: Can't write to output directory
- `ConfigurationError`: Invalid configuration settings

---

## 📄 Output Format Specifications

### Core Output Formats (from `cli_config.py`):
```python
output_format: str = "markdown"  # markdown, json, csv
```

### 1. Markdown Output Format
**Purpose**: Human-readable analysis reports

```markdown
# Qualitative Analysis Report

**Session**: Remote Work Study - Wave 1
**Date**: 2025-01-29
**Model**: gemini-2.5-flash
**Interviews Processed**: 5

## Executive Summary
[High-level findings and key themes]

## Theme Analysis

### Theme 1: Trust in Remote Work
**Prevalence**: 85% of interviews
**Confidence**: 0.92

#### Categories:
1. **Trust Building Mechanisms**
   - Code: Virtual team bonding (12 mentions)
     - "We do virtual coffee breaks..." [Interview 1, line 45]
     - "Regular check-ins help..." [Interview 3, line 127]
   
   - Code: Transparent communication (8 mentions)
     - "Over-communicating is key..." [Interview 2, line 89]

2. **Trust Breakdown Factors**
   - Code: Lack of visibility (6 mentions)
     - "Can't see if people are working..." [Interview 4, line 234]

#### Analytical Memo:
Trust emerges as fundamental to remote work success...

### Theme 2: Technology Challenges
[Similar structure]

## Cross-Interview Analysis
- Contradictions identified: 3
- Saturation reached at: Interview 4
- Emerging themes: 2

## Policy Recommendations
[If enabled in config]

## Appendices
- A. Methodology
- B. Codebook Evolution
- C. Raw Data Tables
```

### 2. JSON Output Format
**Purpose**: Machine-readable for further analysis

```json
{
  "session": {
    "name": "Remote Work Study - Wave 1",
    "date": "2025-01-29T10:30:00Z",
    "model": "gemini-2.5-flash",
    "version": "2.1.0"
  },
  "results": {
    "interviews_processed": 5,
    "total_themes": 8,
    "total_codes": 47,
    "confidence_average": 0.87
  },
  "themes": [
    {
      "id": "theme_001",
      "name": "Trust in Remote Work",
      "description": "Factors affecting trust in distributed teams",
      "prevalence": 0.85,
      "confidence": 0.92,
      "categories": [
        {
          "id": "cat_001",
          "name": "Trust Building Mechanisms",
          "codes": [
            {
              "id": "code_001",
              "name": "Virtual team bonding",
              "definition": "Activities to build team cohesion remotely",
              "frequency": 12,
              "quotes": [
                {
                  "text": "We do virtual coffee breaks...",
                  "interview_id": "interview_001",
                  "line_number": 45,
                  "participant_id": "P001"
                }
              ]
            }
          ]
        }
      ],
      "memos": [
        {
          "id": "memo_001",
          "type": "theoretical",
          "content": "Trust emerges as fundamental...",
          "timestamp": "2025-01-29T10:45:00Z"
        }
      ]
    }
  ],
  "contradictions": [
    {
      "theme1_id": "theme_001",
      "theme2_id": "theme_003",
      "description": "Conflicting views on remote productivity",
      "evidence": ["quote_id_1", "quote_id_2"]
    }
  ],
  "metadata": {
    "codebook_version": "1.2.0",
    "saturation_point": "interview_004",
    "processing_time_seconds": 234.5,
    "token_usage": {
      "total": 487650,
      "prompt": 427650,
      "completion": 60000
    }
  }
}
```

### 3. CSV Output Format
**Purpose**: Statistical analysis in Excel/SPSS/R

**Main Analysis File** (`analysis_results.csv`):
```csv
theme_id,theme_name,prevalence,confidence,total_codes,total_quotes
theme_001,"Trust in Remote Work",0.85,0.92,8,47
theme_002,"Technology Challenges",0.72,0.88,6,32
```

**Code Frequency File** (`code_frequencies.csv`):
```csv
theme_id,category_id,code_id,code_name,frequency,interviews_mentioned
theme_001,cat_001,code_001,"Virtual team bonding",12,4
theme_001,cat_001,code_002,"Transparent communication",8,3
```

**Quote Evidence File** (`quote_evidence.csv`):
```csv
quote_id,interview_id,participant_id,theme_id,code_id,quote_text,line_number
q_001,interview_001,P001,theme_001,code_001,"We do virtual coffee breaks...",45
q_002,interview_003,P003,theme_001,code_001,"Regular check-ins help...",127
```

---

## 🔄 Processing Pipeline Specifications

### Three-Phase Qualitative Coding Process:
```python
async def process_interview(file_path: Path, existing_codebook: Optional[Codebook] = None) -> QCResult:
    # 1. Parse document
    interview = parse_docx(file_path)  # Extract text and metadata
    
    # 2. Validate content
    validation = validate_interview(interview)
    if not validation.is_valid:
        raise InvalidInterviewError(validation.issues)
    
    # 3. PHASE 1: Open Coding - Initial code discovery
    open_codes = await gemini_client.open_coding(
        interview.content,
        research_question=config.research_question,
        max_output_tokens=60000
    )
    
    # 4. PHASE 2: Axial Coding - Find relationships and categories
    categories = await gemini_client.axial_coding(
        interview.content,
        open_codes=open_codes,
        existing_codebook=existing_codebook,
        max_output_tokens=60000
    )
    
    # 5. PHASE 3: Selective Coding - Identify core category and themes
    themes = await gemini_client.selective_coding(
        interview.content,
        categories=categories,
        existing_codebook=existing_codebook,
        max_output_tokens=60000
    )
    
    # 6. Update codebook with new discoveries
    current_codebook.evolve(themes)
    
    # 7. Generate outputs
    return QCResult(
        interview_id=interview.id,
        open_codes=open_codes,
        categories=categories,
        themes=themes,
        metadata=extraction_metadata
    )
```

### Iterative Batch Processing with Codebook Evolution:
```python
async def process_batch_iteratively(interview_files: List[Path]) -> BatchQCResult:
    """
    Process interviews in batches, evolving codebook with each batch
    until theoretical saturation is reached.
    """
    batch_size = config.batch_size  # e.g., 3-5 interviews per batch
    current_codebook = Codebook()
    all_results = []
    batch_num = 1
    
    for batch_start in range(0, len(interview_files), batch_size):
        batch_files = interview_files[batch_start:batch_start + batch_size]
        
        logger.info(f"Processing batch {batch_num} with {len(batch_files)} interviews")
        
        # Process current batch with existing codebook context
        batch_results = []
        for file_path in batch_files:
            result = await process_interview(file_path, existing_codebook=current_codebook)
            batch_results.append(result)
        
        # Aggregate and evolve codebook using LLM
        new_codebook = await gemini_client.evolve_codebook(
            current_codebook=current_codebook,
            new_results=batch_results,
            all_previous_results=all_results
        )
        
        # Check for theoretical saturation using LLM
        saturation_check = await gemini_client.assess_saturation(
            current_codebook=current_codebook,
            new_codebook=new_codebook,
            batch_results=batch_results
        )
        
        all_results.extend(batch_results)
        current_codebook = new_codebook
        batch_num += 1
        
        # Stop if saturation reached or limits hit
        if saturation_check.is_saturated or batch_num > config.max_batches:
            break
    
    # Final aggregation and analysis using LLM
    final_analysis = await gemini_client.final_analysis(
        all_results=all_results,
        final_codebook=current_codebook
    )
    
    return BatchQCResult(
        all_results=all_results,
        final_codebook=current_codebook,
        final_analysis=final_analysis,
        batches_processed=batch_num,
        saturation_reached=saturation_check.is_saturated
    )
```

---

## 📋 Configuration Management

### Environment Variables (from analysis):
```bash
# Required
GEMINI_API_KEY=your-api-key-here

# Optional with defaults
GEMINI_MODEL=gemini-2.5-flash  # or gemini-1.5-pro
GEMINI_TEMPERATURE=0.3
GEMINI_MAX_OUTPUT_TOKENS=60000
```

### CLI Configuration (from `cli_config.py`):
```python
@dataclass
class AnalysisConfig:
    # Input/Output
    input_dir: Optional[str] = None
    input_file: Optional[str] = None
    output_dir: str = "./output"
    output_format: str = "markdown"  # markdown, json, csv
    
    # Analysis Settings
    model: str = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    confidence_threshold: float = 0.7
    max_quotes_per_code: int = 5
    
    # Qualitative Coding Settings
    coding_mode: str = "HYBRID"  # OPEN, CLOSED, HYBRID
    generate_policy_brief: bool = True
    detect_contradictions: bool = True
```

---

## 🏗️ Component Interface Specifications

### 1. Interview Parser Interface (IMPLEMENTED)
```python
class DOCXParser:
    def parse_interview_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Returns:
            {
                'content': str,  # Full text
                'metadata': {
                    'file_name': str,
                    'word_count': int,
                    'parsed_timestamp': str
                },
                'estimated_tokens': int,  # ~word_count * 1.3
                'parsing_info': {'success': bool}
            }
        
        Raises:
            FileNotFoundError
            ValueError (wrong file type)
            Exception (corrupt DOCX)
        """
```

### 2. Theme Extractor Interface
```python
class QualitativeCodingExtractor:
    async def extract_themes(
        self,
        interview_content: str,
        existing_codebook: Optional[Codebook] = None,
        confidence_threshold: float = 0.7
    ) -> ThemeExtractionResult:
        """
        Single-pass extraction using full Gemini capacity.
        
        Returns:
            ThemeExtractionResult(
                themes: List[Theme],
                processing_time: float,
                token_usage: dict,
                confidence_metrics: dict
            )
        
        Raises:
            LLMTimeoutError
            TokenLimitExceeded (only if >1M tokens)
            InvalidResponseFormat
        """
```

### 3. Report Generator Interface
```python
class ReportGenerator:
    def generate_report(
        self,
        results: QCResult,
        format: Literal["markdown", "json", "csv"]
    ) -> Union[str, dict, List[Path]]:
        """
        Generate analysis report in specified format.
        
        Returns:
            - markdown: Single string with formatted report
            - json: Dictionary with complete results
            - csv: List of Paths to generated CSV files
        """
```

---

## ✅ Framework Decisions Summary

1. **Token Strategy**: NO CHUNKING - Use Gemini's full 1M/60K capacity for global context
2. **Error Handling**: Comprehensive with severity levels and recovery
3. **Output Formats**: Markdown (human), JSON (machine), CSV (analysis)
4. **Processing Flow**: LLM-native global analysis (2 calls) with systematic fallback if needed
5. **Configuration**: Environment-based with sensible defaults
6. **Storage**: Neo4j Desktop for graph queries, JSON for backup/portability
7. **Architecture**: Research tool leveraging LLM's global context advantage

**Key Innovation**: Instead of mimicking human sequential processing, leverage LLM's ability to analyze all 103 interviews simultaneously for better pattern recognition and theoretical development.

These specifications provide a solid foundation focused on research needs while maximizing LLM capabilities.