# Data Flow Specifications

## 🔄 Complete Data Transformation Pipeline

### 1. Input Stage: Document to Text
```
DOCX File (Binary)
    ↓ [python-docx library]
Raw Document Object
    ↓ [Text extraction]
Unstructured Text (with metadata)
    ↓ [Validation & cleaning]
Interview Object
```

**Data Structure Evolution**:
```python
# Stage 1: File Path
file_path = Path("interviews/RAND_Methods_Alice_Huguet.docx")

# Stage 2: Raw Document
doc = docx.Document(file_path)
# Contains: paragraphs, tables, styles, properties

# Stage 3: Extracted Content
raw_text = "\n".join([p.text for p in doc.paragraphs])
metadata = {
    "title": doc.core_properties.title,
    "author": doc.core_properties.author,
    "created": doc.core_properties.created,
    "modified": doc.core_properties.modified,
    "word_count": len(raw_text.split())
}

# Stage 4: Interview Object
interview = Interview(
    id=generate_uuid(),
    file_path=file_path,
    title=metadata.get("title", file_path.stem),
    content=clean_text(raw_text),
    metadata=metadata,
    word_count=metadata["word_count"],
    estimated_tokens=int(metadata["word_count"] * 1.3),
    participant_id=extract_participant_id(metadata),
    interview_type=detect_interview_type(raw_text)
)
```

### 2. Processing Stage: Text to LLM Prompt
```
Interview Object
    ↓ [Prompt construction]
Structured Prompt (with schema)
    ↓ [Gemini API call]
JSON Response (up to 60K tokens)
    ↓ [Response parsing]
Theme Extraction Result
```

**Data Transformation**:
```python
# Stage 1: Interview Object
interview = Interview(content="[500K tokens of interview text]")

# Stage 2: Prompt Construction
prompt = f"""
You are an expert qualitative researcher. Extract themes, categories, and codes from this interview.

Interview Content:
{interview.content}

Output Format:
Provide a JSON object with this structure:
{schema_definition}

Requirements:
- Identify major themes (broad patterns)
- Group related concepts into categories
- Extract specific codes with supporting quotes
- Include confidence scores (0-1) for each element
- Preserve participant voice in quotes
"""

# Stage 3: API Call (NO CHUNKING!)
response = await gemini_client.generate_content(
    prompt,
    generation_config={
        "response_mime_type": "application/json",
        "max_output_tokens": 60000,
        "temperature": 0.3
    }
)

# Stage 4: Parse Response
raw_json = response.text  # Already JSON due to mime_type
theme_data = json.loads(raw_json)

# Stage 5: Create Result Objects
themes = [
    Theme(
        id=f"theme_{uuid4()}",
        name=t["name"],
        description=t["description"],
        categories=[
            Category(
                id=f"cat_{uuid4()}",
                name=c["name"],
                codes=[
                    Code(
                        id=f"code_{uuid4()}",
                        name=code["name"],
                        quotes=[
                            Quote(
                                text=q["text"],
                                context=q.get("context", ""),
                                line_number=find_line_number(q["text"], interview.content)
                            )
                            for q in code["quotes"]
                        ]
                    )
                    for code in c["codes"]
                ]
            )
            for c in t["categories"]
        ]
    )
    for t in theme_data["themes"]
]
```

### 3. Aggregation Stage: Multiple Interviews
```
List[ThemeExtractionResult]
    ↓ [Theme merging]
Unified Theme Hierarchy
    ↓ [Deduplication]
Consolidated Themes
    ↓ [Statistical analysis]
Aggregated Results with Metrics
```

**Aggregation Logic**:
```python
def aggregate_themes(results: List[ThemeExtractionResult]) -> AggregatedThemes:
    # 1. Collect all themes
    all_themes = []
    for result in results:
        all_themes.extend(result.themes)
    
    # 2. Group similar themes (semantic similarity)
    theme_groups = group_by_similarity(all_themes, threshold=0.85)
    
    # 3. Merge each group
    merged_themes = []
    for group in theme_groups:
        merged_theme = Theme(
            id=f"merged_theme_{uuid4()}",
            name=most_common_name(group),
            description=synthesize_descriptions(group),
            prevalence=len(group) / len(results),  # How many interviews
            categories=merge_categories(group),
            confidence=average_confidence(group)
        )
        merged_themes.append(merged_theme)
    
    # 4. Calculate statistics
    return AggregatedThemes(
        themes=merged_themes,
        total_interviews=len(results),
        saturation_point=find_saturation_point(results),
        inter_rater_reliability=calculate_irr(merged_themes)
    )
```

### 4. Output Stage: Results to Files
```
Aggregated Results
    ├─→ [Markdown formatter] → report.md
    ├─→ [JSON serializer] → results.json
    └─→ [CSV generator] → Multiple CSV files
```

**Output Generation**:
```python
# Markdown Generation
def generate_markdown_report(results: AggregatedThemes) -> str:
    sections = [
        generate_header(results),
        generate_executive_summary(results),
        generate_theme_analysis(results),
        generate_cross_interview_analysis(results),
        generate_appendices(results)
    ]
    return "\n\n".join(sections)

# JSON Generation
def generate_json_output(results: AggregatedThemes) -> dict:
    return {
        "session": session_metadata,
        "results": results.to_dict(),
        "themes": [theme.to_dict() for theme in results.themes],
        "metadata": processing_metadata
    }

# CSV Generation
def generate_csv_outputs(results: AggregatedThemes) -> List[Path]:
    files = []
    
    # Main analysis
    files.append(write_csv(
        "analysis_results.csv",
        ["theme_id", "theme_name", "prevalence", "confidence"],
        [[t.id, t.name, t.prevalence, t.confidence] for t in results.themes]
    ))
    
    # Code frequencies
    files.append(write_csv(
        "code_frequencies.csv",
        ["theme_id", "code_id", "code_name", "frequency"],
        flatten_codes(results.themes)
    ))
    
    # Quote evidence
    files.append(write_csv(
        "quote_evidence.csv",
        ["quote_id", "theme_id", "code_id", "quote_text"],
        flatten_quotes(results.themes)
    ))
    
    return files
```

---

## 🔀 Error Flow Specifications

### Error Propagation Map
```
Input Layer Errors
├── FileNotFoundError → User message: "Interview file not found: {path}"
├── CorruptFileError → User message: "Unable to read interview file (corrupted)"
└── EncodingError → User message: "File encoding issue, try saving as UTF-8"
    ↓
Processing Layer Errors  
├── ValidationError → User message: "Interview content invalid: {reason}"
├── TokenLimitExceeded → User message: "Interview too large (>1M tokens)"
└── LLMError
    ├── APIKeyError → User message: "API key invalid or missing"
    ├── RateLimitError → Retry with backoff → User message if fails
    ├── TimeoutError → Retry → User message: "Processing timeout"
    └── InvalidResponseError → Retry → Save raw → User message
        ↓
Output Layer Errors
├── DiskSpaceError → User message: "Insufficient space for output"
├── PermissionError → User message: "Cannot write to output directory"
└── SerializationError → Fallback format → User message
```

### Error Recovery Strategies
```python
class ErrorRecoveryStrategies:
    
    @staticmethod
    async def handle_llm_timeout(error: TimeoutError, context: dict) -> RecoveryAction:
        if context["attempt"] < 3:
            return RecoveryAction.RETRY_WITH_BACKOFF
        elif context["interview_size"] > 500_000:  # tokens
            # For very large interviews, suggest splitting
            return RecoveryAction.SUGGEST_MANUAL_SPLIT
        else:
            return RecoveryAction.FAIL_WITH_MESSAGE
    
    @staticmethod
    def handle_malformed_json(error: JSONDecodeError, raw_response: str) -> RecoveryAction:
        # Try to extract partial results
        partial = extract_partial_json(raw_response)
        if partial and len(partial.get("themes", [])) > 0:
            return RecoveryAction.USE_PARTIAL_RESULTS
        else:
            return RecoveryAction.SAVE_RAW_AND_FAIL
    
    @staticmethod
    def handle_rate_limit(error: RateLimitError) -> RecoveryAction:
        wait_time = extract_wait_time(error) or 60
        return RecoveryAction.WAIT_AND_RETRY(wait_time)
```

---

## 📊 State Management Specifications

### Interview Processing States
```python
class InterviewState(Enum):
    PENDING = "pending"          # Not started
    PARSING = "parsing"          # Extracting text
    VALIDATING = "validating"    # Checking content
    PROCESSING = "processing"    # LLM extraction
    AGGREGATING = "aggregating"  # Merging results
    COMPLETE = "complete"        # Successfully processed
    FAILED = "failed"           # Unrecoverable error
    PARTIAL = "partial"         # Some results available

# State Transitions
STATE_TRANSITIONS = {
    InterviewState.PENDING: [InterviewState.PARSING, InterviewState.FAILED],
    InterviewState.PARSING: [InterviewState.VALIDATING, InterviewState.FAILED],
    InterviewState.VALIDATING: [InterviewState.PROCESSING, InterviewState.FAILED],
    InterviewState.PROCESSING: [InterviewState.AGGREGATING, InterviewState.FAILED, InterviewState.PARTIAL],
    InterviewState.AGGREGATING: [InterviewState.COMPLETE, InterviewState.PARTIAL],
    InterviewState.COMPLETE: [],  # Terminal state
    InterviewState.FAILED: [],    # Terminal state
    InterviewState.PARTIAL: [InterviewState.PROCESSING],  # Can retry
}
```

### Batch Processing States
```python
@dataclass
class BatchState:
    total_interviews: int
    processed: int = 0
    succeeded: int = 0
    failed: int = 0
    partial: int = 0
    current_phase: str = "initialization"
    start_time: float = field(default_factory=time.time)
    
    @property
    def progress_percent(self) -> float:
        return (self.processed / self.total_interviews) * 100 if self.total_interviews > 0 else 0
    
    @property
    def estimated_time_remaining(self) -> float:
        if self.processed == 0:
            return 0
        elapsed = time.time() - self.start_time
        rate = self.processed / elapsed
        remaining = self.total_interviews - self.processed
        return remaining / rate if rate > 0 else 0
```

---

## 🔧 Implementation Checkpoints

### Pre-Implementation Validation
- [x] Token strategy defined (NO CHUNKING)
- [x] Error types enumerated
- [x] Output formats specified
- [x] Data flow mapped
- [x] State transitions defined
- [ ] API contracts finalized
- [ ] Test data prepared
- [ ] Performance benchmarks set

### Implementation Milestones
1. **Week 1**: Core data structures and basic flow
2. **Week 2**: LLM integration and error handling
3. **Week 3**: Batch processing and aggregation
4. **Week 4**: Output generation and polish

This comprehensive specification provides the detailed blueprint needed for implementation.