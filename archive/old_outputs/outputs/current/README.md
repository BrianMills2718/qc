# Current Analysis Results

**Latest Production Analysis** - AI Research Methods Investigation

## Analysis Details

**Research Question**: "How are researchers experiencing and adapting to the integration of AI tools in qualitative research methods?"

**Generated**: Based on analysis configuration dated from extraction_results.json
**Interviews**: 3 interviews (2 individual + 1 focus group)
**Approach**: Open discovery - all schemas discovered from interview content

## Contents

- `taxonomy.json` - 30+ hierarchical thematic codes discovered from interviews
- `speaker_schema.json` - Speaker properties and characteristics
- `entity_schema.json` - Entity types (Person, Organization, Tool, etc.) and relationships
- `extraction_results.json` - Complete analysis configuration and metadata
- `interviews/` - Individual interview analyses with codes and relationships:
  - `AI assessment Arroyo SDR.json`
  - `Focus Group on AI and Methods 7_7.json` 
  - `Interview Kandice Kapinos.json`

## Key Findings

**Major Themes Discovered**:
- AI Applications and Uses - How researchers use AI tools
- AI Challenges and Risks - Limitations and concerns
- AI Adoption and Integration - Institutional factors
- Efficiency and Productivity - Workflow improvements
- Quality and Validation - Research rigor concerns

**System Performance**: 
- Discovery confidence: 0.9-0.95 (high quality)
- All codes grounded in actual interview quotes
- Complete 4-phase extraction pipeline executed successfully

## System Configuration

- **LLM Model**: gemini/gemini-2.5-flash (temperature: 0.1)
- **Paradigm**: expert_qualitative_coder
- **Processing**: Single concurrent interview, open discovery approach
- **Database**: Neo4j integration available (not auto-imported)

This analysis represents the complete output of the 4-phase code-first extraction system.