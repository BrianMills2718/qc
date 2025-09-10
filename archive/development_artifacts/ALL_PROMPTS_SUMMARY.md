# All Prompts in Code-First Extractor

## Phase 1: Code Discovery Prompt
Location: `code_first_extractor.py` line 364-390

### Open Coding Approach
```python
def _build_open_code_discovery_prompt(self, combined_text: str) -> str:
    return f"""
    You are analyzing {len(self.config.interview_files)} interviews to discover thematic codes.
    
    ANALYTIC QUESTION: {self.config.analytic_question}
    
    INSTRUCTIONS:
    1. Read through ALL interviews comprehensively
    2. Identify major themes and sub-themes related to the analytic question
    3. Create a hierarchical code structure with up to {self.config.code_hierarchy_depth} levels
    4. Each code should have:
       - Clear name
       - Detailed description
       - Semantic definition of what it represents
       - Example quotes that illustrate this code
    
    INTERVIEW CONTENT:
    {combined_text}
    
    Generate a comprehensive code taxonomy that captures all major themes.
    """
```

### Mixed Coding Approach (with existing codes)
Location: line 900-928
```python
def _build_mixed_code_discovery_prompt(self, combined_text: str, existing_taxonomy: CodeTaxonomy) -> str:
    existing_codes = "\n".join([f"- {code.name}: {code.description}" 
                               for code in existing_taxonomy.codes])
    
    return f"""
    You are analyzing {len(self.config.interview_files)} interviews to discover thematic codes.
    
    ANALYTIC QUESTION: {self.config.analytic_question}
    
    EXISTING CODES (keep these):
    {existing_codes}
    
    INSTRUCTIONS:
    1. Keep all existing codes exactly as defined
    2. Discover ADDITIONAL codes from the interviews that are not covered by existing codes
    3. New codes should complement, not duplicate, existing codes
    4. Create hierarchical structure up to {self.config.code_hierarchy_depth} levels
    5. Provide clear descriptions and example quotes for new codes
    
    INTERVIEW CONTENT:
    {combined_text}
    
    Generate additional codes that complement the existing taxonomy.
    """
```

## Phase 2: Speaker Schema Discovery Prompt
Location: line 930-955

### Open Speaker Discovery
```python
def _build_open_speaker_discovery_prompt(self, combined_text: str) -> str:
    return f"""
    You are analyzing {len(self.config.interview_files)} interviews to discover speaker properties.
    
    IMPORTANT: You are discovering the SCHEMA (what properties to track), not extracting actual speaker data.
    
    INSTRUCTIONS:
    1. Identify what properties/attributes are mentioned about speakers
    2. Determine the nature of each property:
       - Text properties (names, titles, organizations)
       - Categorical properties (limited set of values like department, role)
       - List properties (multiple values like skills, responsibilities)
       - Numeric properties (years of experience, age if relevant)
    3. Note how frequently each property appears
    4. Provide example values for each property
    
    Focus on properties that are:
    - Mentioned multiple times across interviews
    - Relevant to the research context
    - Useful for analysis
    
    INTERVIEW CONTENT:
    {combined_text}
    
    Discover the speaker property schema from these interviews.
    """
```

### Mixed Speaker Discovery (with existing schema)
Location: line 992-1026
```python
def _build_mixed_speaker_discovery_prompt(self, combined_text: str, existing_schema: SpeakerPropertySchema) -> str:
    existing_props = "\n".join([
        f"- {prop.name} ({prop.property_type}): {prop.description or 'No description'}"
        for prop in existing_schema.properties
    ])
    
    return f"""
    You are analyzing {len(self.config.interview_files)} interviews to discover speaker properties.
    
    EXISTING PROPERTIES (preserve these and find additional):
    {existing_props}
    
    INSTRUCTIONS:
    1. Keep all existing properties exactly as defined
    2. Discover ADDITIONAL properties from the interviews not covered by existing ones
    3. New properties should complement, not duplicate, existing properties
    4. Focus on properties that appear frequently and add analytical value
    
    Property types to consider:
    - Text (names, titles, organizations)
    - Categorical (limited values like department, role)
    - List (multiple values like skills)
    - Numeric (years of experience, counts)
    
    INTERVIEW CONTENT:
    {combined_text}
    
    Discover additional speaker properties to complement the existing schema.
    """
```

## Phase 3: Entity/Relationship Discovery Prompt
Location: line 957-990

### Open Entity Discovery
```python
def _build_open_entity_discovery_prompt(self, combined_text: str) -> str:
    return f"""
    You are analyzing {len(self.config.interview_files)} interviews to discover entity and relationship types.
    
    ANALYTIC QUESTION: {self.config.analytic_question}
    
    IMPORTANT: You are discovering TYPES/CATEGORIES, not extracting specific instances.
    
    INSTRUCTIONS:
    1. ENTITY TYPES - Identify categories of things mentioned:
       - People categories (roles, positions, stakeholders)
       - Organization types (companies, departments, institutions)
       - Technology/Tool types (software, platforms, systems)
       - Concept types (methodologies, theories, frameworks)
       - Document/Artifact types (reports, datasets, publications)
       - Process/Activity types (workflows, procedures, tasks)
    
    2. RELATIONSHIP TYPES - Identify how entities relate:
       - Action relationships (uses, creates, manages, implements)
       - Hierarchical relationships (belongs_to, supervises, contains)
       - Collaborative relationships (works_with, partners_with)
       - Impact relationships (affects, influences, depends_on)
       - Information flow (provides_to, receives_from, shares_with)
    
    3. For each type provide:
       - Clear name and description
       - What entities can participate (source and target types)
       - How frequently it appears
       - Example instances
    
    INTERVIEW CONTENT:
    {combined_text}
    
    Discover entity and relationship types that capture the knowledge structure.
    """
```

### Mixed Entity Discovery (with existing schema)
Location: line 1028-1073
```python
def _build_mixed_entity_discovery_prompt(self, combined_text: str, existing_schema: EntityRelationshipSchema) -> str:
    existing_entities = "\n".join([
        f"- {et.name}: {et.description}"
        for et in existing_schema.entity_types
    ])
    
    existing_relationships = "\n".join([
        f"- {rt.name}: {rt.description} ({' -> '.join(rt.source_types)} -> {' -> '.join(rt.target_types)})"
        for rt in existing_schema.relationship_types
    ])
    
    return f"""
    You are analyzing {len(self.config.interview_files)} interviews to discover entity and relationship types.
    
    ANALYTIC QUESTION: {self.config.analytic_question}
    
    EXISTING ENTITY TYPES (preserve these):
    {existing_entities}
    
    EXISTING RELATIONSHIP TYPES (preserve these):
    {existing_relationships}
    
    INSTRUCTIONS:
    1. Keep all existing entity and relationship types exactly as defined
    2. Discover ADDITIONAL types not covered by existing schema
    3. New types should complement, not duplicate, existing ones
    4. Focus on types that appear frequently and capture important domain knowledge
    
    INTERVIEW CONTENT:
    {combined_text}
    
    Discover additional entity and relationship types to complement the existing schema.
    """
```

## Phase 4: Application Prompt (THE PROBLEMATIC ONE)
Location: line 392-448

```python
def _build_application_prompt(self, interview_text: str, interview_id: str, 
                             interview_file: str) -> str:
    return f"""
    You are applying discovered schemas to extract structured data from an interview.
    
    INTERVIEW: {interview_id}
    ANALYTIC QUESTION: {self.config.analytic_question}
    
    AVAILABLE CODES (from Phase 1):
    {self._format_codes_for_prompt()}
    
    SPEAKER PROPERTIES TO EXTRACT (from Phase 2):
    {self._format_speaker_schema_for_prompt()}
    
    ENTITY/RELATIONSHIP TYPES (from Phase 3):
    {self._format_entity_schema_for_prompt()}
    
    INSTRUCTIONS:
    1. QUOTE EXTRACTION WITH MANY-TO-MANY CODING:
       - CRITICAL: Extract AT LEAST 20-30 quotes from this interview (there are many substantive statements)
       - Look through the ENTIRE interview systematically - don't stop after finding a few quotes
       - Each speaker turn that contains substantive content should be a quote
       - Each quote should capture a complete thought or idea (use semantic boundaries)
       - IMPORTANT: Most quotes will relate to MULTIPLE codes - analyze each quote against ALL codes
       - A quote discussing challenges with AI tools might relate to both "Technical Challenges" AND "User Experience" AND "Training Needs"
       - Be comprehensive in code assignment - it's better to over-code than under-code
       
    2. SPEAKER IDENTIFICATION:
       - Identify speakers using all available contextual information
       - Look for explicit labels, document structure, conversational patterns
       - Extract ALL speaker properties defined in the schema for each identified speaker
       - Assign confidence scores based on clarity of identification
       
    3. ENTITY AND RELATIONSHIP EXTRACTION:
       - ACTIVELY SEARCH for all entity types defined in the schema
       - Entities are the important concepts, tools, methods, or actors mentioned
       - Extract entities at multiple levels:
         * Within each quote (what entities are discussed in this specific quote?)
         * Across the interview (what entities appear throughout?)
         * Mark entities that should be tracked globally across all interviews
       - RELATIONSHIPS: When entities co-occur or interact, capture their relationship
       - Look for relationships like: uses, challenges, benefits_from, compares_to, requires, impacts
       - Each relationship should connect two entities with a meaningful relationship type
       
    4. COMPREHENSIVENESS:
       - Every substantive statement should be captured as a quote
       - Every quote should be analyzed for ALL applicable codes (many-to-many is expected)
       - Every mentioned entity from the defined types should be extracted
       - Every meaningful connection between entities should be captured as a relationship
    
    INTERVIEW CONTENT:
    {interview_text}
    
    Extract all quotes, speakers, entities, and relationships according to the schemas.
    Be comprehensive - every relevant quote should be captured.
    """
```

## Helper Format Functions

### Format Codes for Prompt
Location: line 450-456
```python
def _format_codes_for_prompt(self) -> str:
    lines = []
    for code in self.code_taxonomy.codes:
        indent = "  " * code.level
        lines.append(f"{indent}- {code.name}: {code.description}")
    return "\n".join(lines)
```

### Format Speaker Schema for Prompt
Location: line 458-465
```python
def _format_speaker_schema_for_prompt(self) -> str:
    lines = []
    for prop in self.speaker_schema.properties:
        lines.append(f"- {prop.name} ({prop.property_type}): {prop.description or 'No description'}")
        if prop.possible_values:
            lines.append(f"  Possible values: {', '.join(prop.possible_values)}")
    return "\n".join(lines)
```

### Format Entity Schema for Prompt
Location: line 467-483
```python
def _format_entity_schema_for_prompt(self) -> str:
    lines = ["ENTITY TYPES:"]
    for entity_type in self.entity_schema.entity_types:
        lines.append(f"- {entity_type.name}: {entity_type.description}")
    
    lines.append("\nRELATIONSHIP TYPES:")
    for rel_type in self.entity_schema.relationship_types:
        source_str = ", ".join(rel_type.source_types)
        target_str = ", ".join(rel_type.target_types)
        lines.append(f"- {rel_type.name}: {rel_type.description}")
        lines.append(f"  ({source_str} → {target_str})")
    
    return "\n".join(lines)
```

# Analysis

## Key Issues with Phase 4 Prompt:

1. **Too Complex**: Asking for quotes, speakers, entities, and relationships all at once
2. **Conflicting Instructions**: "Extract AT LEAST 20-30 quotes" but also extract entities/relationships
3. **Schema Overload**: The CodedInterview schema has too many nested objects
4. **No Prioritization**: Everything is equally important, model doesn't know what to focus on

## Phase 1-3 Prompts Work Because:
- Single focused task per phase
- Simple output schema
- Processing all interviews at once (pattern finding)
- Clear, specific instructions

## Phase 4 Fails Because:
- Multiple complex tasks in one prompt
- Complex nested output schema
- Processing individual interviews (detail extraction)
- Competing priorities in instructions