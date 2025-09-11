# Evidence: Complete Schema Compatibility Analysis
Date: 2025-08-14
Status: Analysis Complete

## Executive Summary
All schemas are structurally compatible between phases. The fix implemented for code IDs is correct at the schema level. However, actual outputs show that the LLM is still not returning the correct code IDs in many cases.

## Schema Compatibility Results

### ✅ Phase 1: Code Taxonomy
**Schema:** `HierarchicalCode` and `CodeTaxonomy`
- **Fields:** id, name, description, semantic_definition, parent_id, level, example_quotes, discovery_confidence
- **Output:** Produces codes with structured IDs (e.g., "AI_IMPACT_RESEARCH_TASKS")
- **Status:** ✅ COMPATIBLE

### ✅ Phase 2: Speaker Schema  
**Schema:** `DiscoveredSpeakerProperty` and `SpeakerPropertySchema`
- **Fields:** name, description, property_type, frequency, example_values, is_categorical, possible_values, confidence
- **Output:** Produces speaker properties for extraction guidance
- **Status:** ✅ COMPATIBLE

### ✅ Phase 3: Entity/Relationship Schema
**Schema:** `DiscoveredEntityType`, `DiscoveredRelationshipType`, `EntityRelationshipSchema`
- **Fields:** Entity types, relationship types with examples and contexts
- **Output:** Produces schemas to guide entity/relationship extraction
- **Status:** ✅ COMPATIBLE

### ✅ Phase 4A: Quote Extraction (FIXED)
**Schema:** `SimpleQuote` and `QuotesAndSpeakers`
- **Critical Change:** Now uses `code_ids: List[str]` instead of `code_names: List[str]`
- **Input:** Receives formatted codes with IDs in brackets: `[AI_IMPACT_RESEARCH_TASKS] AI's Impact on Research Tasks`
- **Expected Output:** Should return exact code IDs from taxonomy
- **Status:** ✅ SCHEMA FIXED

### ✅ Phase 4B: Entity Extraction
**Schema:** `ExtractedEntity`, `ExtractedRelationship`, `EntitiesAndRelationships`
- **Fields:** Entities with types, relationships with source/target
- **Output:** Extracts entities and relationships based on Phase 3 schemas
- **Status:** ✅ COMPATIBLE

### ✅ Final Output: CodedInterview
**Schema:** `EnhancedQuote` and `CodedInterview`
- **Fields:** Contains both code_ids and code_names for compatibility
- **Process:** Combines Phase 4A and 4B results
- **Status:** ✅ COMPATIBLE

## Data Flow Analysis

### Phase 1 → Phase 4
```
Phase 1 Output: CodeTaxonomy
  └─> codes: List[HierarchicalCode]
       └─> Each code has: id="AI_IMPACT_RESEARCH_TASKS", name="AI's Impact on Research Tasks"

Phase 4 Input (via prompt):
  └─> Formatted as: "[AI_IMPACT_RESEARCH_TASKS] AI's Impact on Research Tasks: description"

Phase 4 Expected Output:
  └─> SimpleQuote.code_ids = ["AI_IMPACT_RESEARCH_TASKS"]
```
**Status:** ✅ COMPATIBLE (after fix)

### Phase 2 → Phase 4
```
Phase 2 Output: SpeakerPropertySchema
  └─> properties: List[DiscoveredSpeakerProperty]

Phase 4 Usage:
  └─> Properties formatted in prompt to guide speaker extraction
  └─> Creates SpeakerInfo objects
```
**Status:** ✅ COMPATIBLE

### Phase 3 → Phase 4B
```
Phase 3 Output: EntityRelationshipSchema
  └─> entity_types: List[DiscoveredEntityType]
  └─> relationship_types: List[DiscoveredRelationshipType]

Phase 4B Usage:
  └─> Types formatted in prompt to guide extraction
  └─> Creates ExtractedEntity and ExtractedRelationship objects
```
**Status:** ✅ COMPATIBLE

## Actual Output Analysis

### output_performance_optimized
- **Taxonomy IDs:** AI_IMPACT_RESEARCH_TASKS, AI_IMPACT_TRANSCRIPTION, etc.
- **Quote code_ids:** [] (empty)
- **Issue:** LLM not returning any codes

### test_output_stats  
- **Taxonomy IDs:** A1, C1, C1.3, etc.
- **Quote code_ids:** [] (empty)
- **Issue:** LLM not returning any codes

### test_output_full
- **Taxonomy IDs:** C1, C1.1, C1.1.1, etc.
- **Quote code_ids:** ['qualitative_data_analysis_challenges', 'recruitment_challenges']
- **Issue:** LLM returning made-up code IDs that don't exist in taxonomy

## Root Cause Analysis

### Schema Level: ✅ FIXED
The schemas are now properly structured to pass and receive code IDs.

### Implementation Level: ✅ FIXED
The code properly formats prompts with IDs and expects IDs back.

### LLM Behavior: ⚠️ NEEDS ATTENTION
The LLM is either:
1. Not understanding the instruction to use exact code IDs
2. Creating its own code names instead of using provided IDs
3. Returning empty arrays when uncertain

## Recommendations

### 1. Improve LLM Instructions
Make the instructions even more explicit:
```python
"CRITICAL: You MUST use the EXACT code IDs shown in brackets.
DO NOT create new code names.
Example: For a quote about AI transcription, use code_ids: ['AI_IMPACT_TRANSCRIPTION']
NOT code_names like 'transcription_challenges' or 'AI_for_transcription'"
```

### 2. Add Validation
Add a validation step that checks if returned code IDs exist in the taxonomy:
```python
def validate_code_ids(self, code_ids: List[str]) -> List[str]:
    valid_ids = {code.id for code in self.code_taxonomy.codes}
    validated = [cid for cid in code_ids if cid in valid_ids]
    if len(validated) < len(code_ids):
        invalid = set(code_ids) - set(validated)
        logger.warning(f"Invalid code IDs from LLM: {invalid}")
    return validated
```

### 3. Add Examples to Prompt
Include concrete examples in the prompt:
```python
"Example quote: 'We use AI for transcribing our interviews'
Correct response: code_ids: ['AI_IMPACT_TRANSCRIPTION']
WRONG response: code_ids: ['transcription', 'AI_transcription', 'interview_transcription']"
```

### 4. Consider Fallback Matching
If LLM returns names instead of IDs, try to match them:
```python
def fuzzy_match_code(self, code_text: str) -> Optional[str]:
    # Try exact ID match first
    if code_text in self.valid_code_ids:
        return code_text
    # Try matching by name
    for code in self.code_taxonomy.codes:
        if code.name.lower() == code_text.lower():
            return code.id
    return None
```

## Conclusion

The schema compatibility is fully resolved and working correctly. The remaining issue is ensuring the LLM consistently returns the correct code IDs from the taxonomy. This requires:
1. Clearer instructions in the prompt
2. Validation of returned code IDs
3. Possibly some fuzzy matching as a fallback
4. Testing with different prompt formulations to find what works best

The architecture is sound; it's now a matter of fine-tuning the LLM interaction.