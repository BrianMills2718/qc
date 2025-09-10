# Evidence: All Prompt Improvements Implemented

Date: 2025-08-14
Status: COMPLETED

## Summary
Implemented comprehensive improvements to all extraction prompts based on systematic review. The prompts are now more precise, less ambiguous, and provide clear formatting guidelines.

## Key Improvements Implemented

### 1. Standardized ID Formats Across All Phases

| Phase | Type | Format | Example |
|-------|------|--------|---------|
| Phase 1 | Code IDs | CAPS_WITH_UNDERSCORES | `AI_CHALLENGES` |
| Phase 2 | Property names | snake_case | `years_experience` |
| Phase 3 | Entity type IDs | CAPS_SNAKE_CASE | `AI_TOOL` |
| Phase 3 | Relationship IDs | CAPS | `USES` |

### 2. Phase-Specific Improvements

#### Phase 1: Code Discovery
- ✅ Added ID format specification: "CAPS_WITH_UNDERSCORES format"
- ✅ Specified description length: "2-3 sentences"
- ✅ Clarified code quality: "minimize overlap between codes"
- ✅ Required example quotes: "1-3 example quotes"

#### Phase 2: Speaker Properties
- ✅ **Critical fix**: Clarified "You are NOT identifying individual speakers, just discovering their property TYPES"
- ✅ Added format: "snake_case format (e.g., years_experience)"
- ✅ Specified frequency tracking: "rare, common, very common"
- ✅ Clarified focus: "properties that are actually mentioned (not assumed)"

#### Phase 3: Entity/Relationship Discovery
- ✅ Removed biasing examples that could limit discovery
- ✅ Added ID formats for both entities and relationships
- ✅ Specified relationship direction: "one-way (→) or bidirectional (↔)"
- ✅ Required concrete examples from interviews

#### Phase 4A: Quote Extraction
- ✅ Added minimum length: "minimum ~10 words unless exceptionally relevant"
- ✅ Clarified null handling: "null if not mentioned" vs "Unknown if mentioned but unclear"
- ✅ Improved selective extraction: "ONLY extract quotes that clearly relate to codes"
- ✅ Specified location tracking: "line number, paragraph number, or section"

#### Phase 4B: Entity Extraction
- ✅ Defined confidence scale: "1.0 if explicitly named... 0.0 = total guess"
- ✅ Specified naming convention: "Use the most complete/formal name"
- ✅ Required exact schema matching: "Must exactly match a type ID from the schema"
- ✅ Clarified relationship extraction requirements

### 3. Removed Ambiguity

**Before:**
- "important" concepts
- "useful" for understanding
- "comprehensive" extraction
- "confidence scores" (undefined)

**After:**
- "directly relate to the analytic question"
- "appear multiple times or are emphasized"
- "ONLY extract quotes that clearly relate to codes"
- "1.0 if explicitly stated... 0.0 = total guess"

### 4. Clarified Task Boundaries

**Phases 1-3**: Discover TYPES/SCHEMAS/CATEGORIES
- What types of codes exist?
- What properties do speakers have?
- What entity and relationship types exist?

**Phase 4**: Extract INSTANCES using discovered schemas
- Which specific quotes map to which codes?
- What are the actual property values for each speaker?
- Which specific entities and relationships appear?

## Test Results

```
>>> Phase 1: Code Discovery
  OK: ID format specified
  OK: Example format shown
  OK: 2-3 sentences specified
  OK: Minimize overlap mentioned

>>> Phase 2: Speaker Properties
  OK: Clarifies NOT identifying speakers
  OK: snake_case format specified
  OK: Example shown
  OK: Frequency mentioned

>>> Phase 3: Entity/Relationship Discovery
  OK: Entity ID format
  OK: Relationship ID format
  OK: No biasing examples
  OK: Direction specified

>>> Phase 4A: Quote Extraction
  OK: Minimum quote length
  OK: Null handling specified
  OK: Unknown vs null clarified
  OK: Selective extraction

>>> Phase 4B: Entity Extraction
  OK: Entity naming convention
  OK: Confidence scale defined
  OK: Total guess = 0.0
  OK: Must match schema IDs
```

## Files Modified

1. `src/qc/prompts/phase1/open_code_discovery.txt`
2. `src/qc/prompts/phase1/mixed_code_discovery.txt`
3. `src/qc/prompts/phase2/open_speaker_discovery.txt`
4. `src/qc/prompts/phase3/open_entity_discovery.txt`
5. `src/qc/prompts/phase4/quotes_speakers.txt`
6. `src/qc/prompts/phase4/entities_relationships.txt`

## Expected Benefits

1. **Better Code IDs**: Consistent format should reduce made-up IDs
2. **Clearer Extraction**: Phase 4 now knows exactly what format to use
3. **Less Noise**: Selective extraction means fewer irrelevant quotes
4. **Better Data Quality**: Clear confidence scales and null handling
5. **Reduced Ambiguity**: Specific instructions replace vague terms

## Next Steps

1. Run extraction with improved prompts
2. Verify code IDs now match taxonomy format
3. Check that quotes have proper code assignments
4. Confirm entities/relationships use schema IDs

The prompts are now significantly more precise and should produce better quality extractions.