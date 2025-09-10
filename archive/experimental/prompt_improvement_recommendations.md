# Prompt Improvement Recommendations

After reviewing all prompts, here are my suggestions for further improvements:

## Phase 1: Code Discovery (`phase1/open_code_discovery.txt`)

### Current Issues:
1. **Vague ID generation**: Doesn't specify how to create code IDs
2. **No naming convention**: Should specify format for IDs (e.g., CAPS_WITH_UNDERSCORES)
3. **"Example quotes" unclear**: How many? From which interviews?

### Suggested Improvements:
```
4. Each code should have:
   - Unique ID in CAPS_WITH_UNDERSCORES format (e.g., AI_CHALLENGES)
   - Clear name (human-readable)
   - Detailed description (2-3 sentences)
   - Semantic definition of what qualifies for this code
   - 1-3 example quotes that best illustrate this code

5. Codes should be:
   - Mutually distinct (minimize overlap)
   - Directly relevant to the analytic question
   - Grounded in actual interview content (not theoretical)
```

## Phase 2: Speaker Discovery (`phase2/open_speaker_discovery.txt`)

### Current Issues:
1. **Line 6 confusion**: "Identify all distinct speakers" - but this is schema discovery, not extraction
2. **Mixed instructions**: Combines schema discovery with speaker identification
3. **Examples too generic**: "Role or position" might not apply to all domains

### Suggested Improvements:
```
INSTRUCTIONS:
1. Discover what properties/attributes are mentioned about speakers
   (You are NOT identifying individual speakers, just their property types)
2. Properties should help distinguish speakers or be relevant to analysis
3. For each property, specify:
   - Property name (snake_case format, e.g., years_experience)
   - Description of what this property captures
   - Data type: categorical (fixed options), numerical, text, or boolean
   - If categorical: list all possible values found
   - Frequency: How often is this property mentioned?
```

## Phase 3: Entity Discovery (`phase3/open_entity_discovery.txt`)

### Current Issues:
1. **Examples in parentheses** (line 7): Could bias the discovery
2. **"Common patterns"** (line 12): These examples might not fit all domains
3. **No ID format specified**: Should entities have specific ID format?

### Suggested Improvements:
```
1. ENTITY TYPES: Identify categories of things discussed
   - Each type needs:
     * Type ID in CAPS_SNAKE_CASE (e.g., AI_TOOL, ORGANIZATION)
     * Clear definition of what qualifies as this type
     * 2-3 concrete examples from the interviews
     * Why this type matters for the analytic question

2. RELATIONSHIP TYPES: Identify how entities connect
   - Each relationship needs:
     * Type ID in CAPS (e.g., USES, MANAGES, BELONGS_TO)
     * Clear definition of this relationship
     * Valid source entity type(s)
     * Valid target entity type(s)
     * Direction: one-way (→) or bidirectional (↔)
     * 1-2 examples from the interviews
```

## Phase 4A: Quote Extraction (`phase4/quotes_speakers.txt`)

### Current Issues:
1. **Line 37**: "Include line numbers" - but line numbers might not exist in all formats
2. **Speaker properties extraction**: Unclear what to do if property value unknown
3. **No minimum quote length**: Could extract single words

### Suggested Improvements:
```
3. QUOTE BOUNDARIES:
   - Capture complete thoughts (minimum ~10 words unless exceptionally relevant)
   - Include enough context for standalone understanding
   - Use natural semantic boundaries
   - Record location if available (line number, paragraph, or section)

4. SPEAKER IDENTIFICATION:
   - Identify speaker from available cues
   - For each speaker property from schema:
     * Extract value if clearly stated
     * Use null if not mentioned
     * Use "Unknown" only if explicitly unclear
```

## Phase 4B: Entity Extraction (`phase4/entities_relationships.txt`)

### Current Issues:
1. **Quote context provided but not used**: Why show quotes if not referencing them?
2. **"Confidence scores"** mentioned but not explained**: What scale? When to use?
3. **No guidance on entity naming**: Should "Dr. Smith" be "Dr. Smith" or "Smith" or "John Smith"?

### Suggested Improvements:
```
ENTITY EXTRACTION:
- Extract specific instances matching the schema types
- Entity naming: Use the most complete/formal name mentioned
- Each entity needs:
  * name: The specific instance (e.g., "ChatGPT", "Dr. Jane Smith")
  * type: Must match a type from the schema
  * confidence: 0.0-1.0 (1.0 = explicitly named, 0.5 = inferred)

RELATIONSHIP EXTRACTION:
- Only extract relationships you can identify with confidence
- Each relationship needs:
  * source_entity: Name of source entity
  * relationship_type: Must match a type from schema
  * target_entity: Name of target entity
  * confidence: 0.0-1.0 (1.0 = explicit, 0.5 = implied)
```

## General Recommendations

### 1. Add Format Specifications
- Specify ID formats consistently (CAPS_SNAKE_CASE)
- Define what null/unknown/missing means
- Clarify number formats (integers vs. decimals)

### 2. Remove Ambiguous Instructions
- Replace "comprehensive" with specific criteria
- Define "important" and "relevant" more precisely
- Remove subjective terms like "useful"

### 3. Add Validation Rules
- Minimum/maximum counts where appropriate
- Required vs. optional fields
- Valid value ranges (e.g., confidence 0.0-1.0)

### 4. Improve Examples
- Use dynamic examples from actual data
- Show both correct and incorrect examples
- Include edge cases

### 5. Clarify Task Boundaries
- Phase 1-3: Schema discovery (types/categories)
- Phase 4: Instance extraction (specific occurrences)
- Make this distinction clearer in each prompt

## Priority Fixes

1. **HIGH**: Phase 1 - Add ID format specification
2. **HIGH**: Phase 2 - Clarify it's schema discovery, not speaker identification  
3. **MEDIUM**: Phase 3 - Remove biasing examples
4. **MEDIUM**: Phase 4B - Clarify confidence scoring
5. **LOW**: All phases - Standardize terminology

These improvements would make the prompts more precise, reduce ambiguity, and likely improve the quality of extraction.