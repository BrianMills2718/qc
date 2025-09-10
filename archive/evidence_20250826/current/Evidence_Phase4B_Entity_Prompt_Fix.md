# Evidence: Phase 4B Entity Extraction Prompt Corrected

Date: 2025-08-14
Status: COMPLETED

## Problems Identified

The Phase 4B entities_relationships.txt prompt had several issues:

1. **Hardcoded entity definition**: "Entities are important concepts, tools, methods, people, or organizations" - This should come from Phase 3 schema, not be hardcoded
2. **Unnecessary counting**: "Track how many times each entity is mentioned" - This is programmatic work, not LLM's job
3. **Vague instructions**: "Note different contexts where entities appear" - Unclear what to do with this
4. **Hardcoded examples**: Examples like "Researcher USES ChatGPT" might not match the discovered schema

## Solutions Implemented

### Changes to `src/qc/prompts/phase4/entities_relationships.txt`

**OLD (Problematic):**
```
1. ENTITY EXTRACTION:
   - Search for ALL entity types defined in the schema
   - Entities are important concepts, tools, methods, people, or organizations
   - Extract specific instances (e.g., "ChatGPT" as type "AI Tool")
   - Track how many times each entity is mentioned
   - Note different contexts where entities appear

2. RELATIONSHIP EXTRACTION:
   - Examples of relationships:
     * "Researcher" USES "ChatGPT"
     * "AI Tool" CHALLENGES "Traditional Methods"
```

**NEW (Corrected):**
```
1. ENTITY EXTRACTION:
   - ONLY extract entities that match the types defined in the schema above
   - Extract specific instances with their correct type from the schema
   - For example, if schema has "AI_TOOL" type, extract "ChatGPT" as type "AI_TOOL"
   - Focus on entities relevant to the analytic question

2. RELATIONSHIP EXTRACTION:
   - ONLY use relationship types defined in the schema above
   - Identify when extracted entities interact or connect
   - Each relationship needs: source entity, relationship type, target entity
```

## Key Improvements

1. **Schema-driven extraction**: Now strictly follows Phase 3 discovered types
2. **Removed unnecessary work**: No more counting or context noting
3. **Clear instructions**: Extract instances that match schema types only
4. **No hardcoded examples**: Examples now reference the actual schema

## Expected Behavior

### Before Fix
LLM might:
- Extract entities not in the schema
- Waste tokens counting mentions
- Generate vague "context notes"
- Use relationship types not in schema

### After Fix
LLM will:
- Only extract entities matching Phase 3 types
- Focus on extraction, not counting
- Use only defined relationship types
- Stay within schema boundaries

## Benefits

1. **Better alignment**: Phase 4B now properly uses Phase 3 output
2. **Cleaner data**: No unexpected entity/relationship types
3. **Efficiency**: LLM focuses on extraction, not analysis
4. **Consistency**: All entities and relationships match the schema

## Files Changed

- `src/qc/prompts/phase4/entities_relationships.txt` - Corrected extraction instructions

## Division of Labor

**Phase 3 (Discovery)**: Discovers what TYPES of entities and relationships exist
**Phase 4B (Extraction)**: Extracts specific INSTANCES of those types
**Post-processing**: Count mentions, analyze patterns (programmatically, not via LLM)