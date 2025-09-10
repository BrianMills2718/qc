# Evidence: Ultra-Deep Schema-Prompt Misalignment Analysis
Date: 2025-08-18T14:45:00Z

## Executive Summary

Critical breaking issues identified in the 4-phase extraction pipeline that will cause immediate failures or data corruption. These are NOT quality issues but fundamental schema-prompt misalignments that prevent proper functioning.

## CRITICAL BREAKING ISSUE #1: Phase 2 Schema Design Flaw

### Problem: `total_speakers_found` Field Mismatch
**Schema Requirements** (line 154 in `code_first_schemas.py`):
```python
class SpeakerPropertySchema(BaseModel):
    properties: List[DiscoveredSpeakerProperty]
    total_speakers_found: int  # REQUIRED FIELD
    discovery_method: str
    extraction_confidence: float = 0.8
```

**Prompt Purpose** (Phase 2 discovery prompts):
- Prompts discover PROPERTY TYPES, not individual speakers
- Phase 2 prompt says: "You are NOT identifying individual speakers, just discovering their property TYPES"
- No capability to count speakers since Phase 2 processes all interviews concatenated

**Breaking Impact**: 
- LLM cannot provide `total_speakers_found` during Phase 2 (property discovery)
- Will likely return 0 or fail validation
- Phase 2 schema expects speaker count but prompt explicitly avoids speaker identification

**Evidence Location**: 
- Schema: `src/qc/extraction/code_first_schemas.py:154`
- Prompt: `src/qc/prompts/phase2/open_speaker_discovery.txt:7`

## CRITICAL BREAKING ISSUE #2: Phase 4B Circular Dependency

### Problem: "must be an extracted entity" Constraint
**Phase 4B Prompt Requirements** (lines 25-27 in `entities_relationships.txt`):
```
* source_entity: Name of the source entity (must be an extracted entity)
* target_entity: Name of the target entity (must be an extracted entity)
```

**Schema Design Problem**:
- Phase 4B extracts entities AND relationships in single call
- Relationships require "must be an extracted entity" for source/target
- But entities are being extracted in the SAME LLM call
- Creates logical impossibility: relationships depend on entities not yet finalized

**Breaking Impact**:
- LLM must extract entities first, then validate all relationships against those entities
- High probability of relationship extraction failures
- May create incomplete relationship networks

**Evidence Location**:
- Prompt: `src/qc/prompts/phase4/entities_relationships.txt:25-27`
- Schema: `src/qc/extraction/code_first_schemas.py:224-234`

## CRITICAL BREAKING ISSUE #3: Line Number Dependencies

### Problem: Line Numbers Required But Not Always Available
**Schema Requirements** (lines 253-254 in `code_first_schemas.py`):
```python
line_start: int
line_end: int
```

**Document Format Reality**:
- Pipeline processes DOCX and TXT files
- DOCX files don't have meaningful line numbers
- `_read_interview_file()` method may not provide line-by-line processing
- Some documents are paragraph-based, not line-based

**Prompt Assumptions** (line 37 in `quotes_speakers.txt`):
```
Record location if available (line number, paragraph number, or section)
```

**Breaking Impact**:
- Schema requires `int` for line numbers but prompt says "if available"
- DOCX processing may not generate line numbers
- Will cause validation failures or force arbitrary line numbers

**Evidence Location**:
- Schema: `src/qc/extraction/code_first_schemas.py:253-254`
- Prompt: `src/qc/prompts/phase4/quotes_speakers.txt:37`

## CRITICAL BREAKING ISSUE #4: Code ID Format Validation Gap

### Problem: No Validation for Code ID Format
**Phase 1 Prompt Requirements** (line 10 in `open_code_discovery.txt`):
```
Unique ID in CAPS_WITH_UNDERSCORES format (e.g., AI_CHALLENGES, DATA_QUALITY_ISSUES)
```

**Schema Definition** (line 115 in `code_first_schemas.py`):
```python
id: str  # No format validation
```

**Phase 4A Critical Dependency** (line 21 in `quotes_speakers.txt`):
```
CRITICAL: Use the EXACT CODE IDs shown in brackets [CODE_ID] above
```

**Breaking Impact**:
- If Phase 1 generates invalid IDs (spaces, lowercase, special chars), Phase 4A will use them
- No Pydantic validation to catch format violations
- May break downstream Neo4j imports or analysis tools
- Inconsistent ID formats across extractions

**Evidence Location**:
- Schema: `src/qc/extraction/code_first_schemas.py:115`
- Phase 1 Prompt: `src/qc/prompts/phase1/open_code_discovery.txt:10`
- Phase 4A Prompt: `src/qc/prompts/phase4/quotes_speakers.txt:21`

## CRITICAL BREAKING ISSUE #5: Entity Type Validation Gap

### Problem: Entity Type Mismatch Between Phases
**Phase 3 Schema Output** (lines 164-171 in `code_first_schemas.py`):
```python
class DiscoveredEntityType(BaseModel):
    name: str  # e.g., "Researcher", "AI_TOOL", "Organization"
```

**Phase 4B Prompt Requirement** (line 18 in `entities_relationships.txt`):
```
* type: Must exactly match a type ID from the schema (e.g., "AI_TOOL")
```

**Breaking Impact**:
- Phase 3 discovers entity types with `name` field
- Phase 4B prompt refers to "type ID from the schema" but schema uses `name`
- Inconsistent terminology between "name" vs "type ID"
- May cause entity type mismatches and validation failures

**Evidence Location**:
- Schema: `src/qc/extraction/code_first_schemas.py:164`
- Prompt: `src/qc/prompts/phase4/entities_relationships.txt:18`

## CRITICAL BREAKING ISSUE #6: Speaker Property Schema Mismatch

### Problem: Property Type Values Don't Match Schema
**Phase 2 Prompt Instructions** (line 12 in `open_speaker_discovery.txt`):
```
Data type: categorical (fixed options), numerical, text, or boolean
```

**Phase 2 Schema Definition** (line 143 in `code_first_schemas.py`):
```python
property_type: str  # "string", "list", "number", "categorical"
```

**Breaking Impact**:
- Prompt suggests: "text", "boolean", "numerical"
- Schema expects: "string", "list", "number"
- Type mapping mismatch will cause validation errors
- "text" != "string", "numerical" != "number", missing "boolean" handling

**Evidence Location**:
- Schema: `src/qc/extraction/code_first_schemas.py:143`
- Prompt: `src/qc/prompts/phase2/open_speaker_discovery.txt:12`

## CRITICAL BREAKING ISSUE #7: Missing Total Field Calculations

### Problem: Phase 4 Split Creates Calculation Dependencies
**QuotesAndSpeakers Schema** (lines 310-311 in `code_first_schemas.py`):
```python
total_quotes: int
total_codes_applied: int
```

**EntitiesAndRelationships Schema** (lines 321-322 in `code_first_schemas.py`):
```python
total_entities: int
total_relationships: int
```

**Breaking Impact**:
- Phase 4A and 4B are split into separate LLM calls
- Each must calculate totals independently
- No validation that totals match actual list lengths
- May create inconsistent metadata

**Evidence Location**:
- Schema: `src/qc/extraction/code_first_schemas.py:310-311, 321-322`
- Implementation: `src/qc/extraction/code_first_extractor.py:336-357`

## CRITICAL BREAKING ISSUE #8: Null Value Handling Inconsistency

### Problem: Null Guidance Mismatch
**Phase 4A Prompt Instructions** (line 42-44 in `quotes_speakers.txt`):
```
* Extract the value if clearly stated in the interview
* Use null if the property is not mentioned for this speaker
* Use "Unknown" only if the property is mentioned but unclear
```

**Schema Reality**:
- Most schema fields are required (not Optional)
- No explicit null handling in Pydantic models
- Mixed guidance between null and "Unknown" string values

**Breaking Impact**:
- LLM instructed to use null but schema may reject nulls
- Inconsistent handling of missing data
- String "Unknown" vs null semantic differences

**Evidence Location**:
- Prompt: `src/qc/prompts/phase4/quotes_speakers.txt:42-44`
- Schema: All BaseModel fields without Optional typing

## Immediate Fix Priorities

### Priority 1 - Will Cause Pipeline Failures:
1. **Issue #1**: Remove `total_speakers_found` from Phase 2 schema or change Phase 2 to count speakers
2. **Issue #3**: Make line_start/line_end Optional or handle DOCX line numbering
3. **Issue #6**: Align property type values between prompt and schema

### Priority 2 - Data Quality Issues:
4. **Issue #2**: Restructure Phase 4B to extract entities first, then relationships
5. **Issue #4**: Add Pydantic field validators for code ID format
6. **Issue #5**: Clarify entity type naming consistency

### Priority 3 - Robustness Issues:
7. **Issue #7**: Add validation for total field calculations
8. **Issue #8**: Standardize null vs "Unknown" handling

## Test Commands to Reproduce Issues

```bash
# Test Phase 2 speaker counting issue
cd /c/Users/Brian/projects/qualitative_coding
python test_phase_2_only.py

# Test line number handling with DOCX
python test_phase4_line_numbers.py

# Test property type validation
python test_speaker_property_types.py
```

## Validation Status
- [x] Schema files analyzed for type definitions
- [x] Prompt files analyzed for LLM instructions  
- [x] Cross-referenced schemas with actual output files
- [x] Identified breaking vs quality issues
- [ ] Created test cases to reproduce issues
- [ ] Proposed specific fixes for each issue