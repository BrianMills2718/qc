# Evidence: Code Extraction Pipeline Disconnect Investigation
Date: 2025-08-14
Status: Investigation Complete

## Executive Summary
The extraction pipeline has a fundamental architecture flaw: Phase 1 creates taxonomy codes with structured IDs (e.g., "AI_IMPACT_RESEARCH_TASKS"), but Phase 4 only passes code names to the LLM without IDs. The LLM is expected to return matching code names, but without IDs in the prompt, it creates its own names, resulting in completely disconnected coding systems.

## The Problem Chain

### 1. Phase 1: Taxonomy Creation
```python
# Line 856-865 in code_first_extractor.py
codes.append(HierarchicalCode(
    id=f"code_{len(codes)}",  # Initially creates "code_0", "code_1", etc.
    name=parsed_code.name,
    description=parsed_code.description,
    # ...
))
```

**Actual taxonomy.json output:**
```json
{
  "codes": [
    {
      "id": "AI_IMPACT_RESEARCH_TASKS",  // Structured ID
      "name": "AI's Impact on Research Tasks",
      "description": "How researchers perceive AI's influence..."
    }
  ]
}
```

### 2. Phase 4 Prompt Building - THE CRITICAL FLAW
```python
# Line 503-509 in code_first_extractor.py
def _format_codes_for_prompt(self) -> str:
    """Format code taxonomy for prompt"""
    lines = []
    for code in self.code_taxonomy.codes:
        indent = "  " * code.level
        lines.append(f"{indent}- {code.name}: {code.description}")  # ❌ NO ID!
    return "\n".join(lines)
```

**What the LLM sees in the prompt:**
```
AVAILABLE CODES (from Phase 1):
  - AI's Impact on Research Tasks: How researchers perceive AI's influence...
    - AI for Transcription: The use and perceived accuracy of AI tools...
    - AI for Qualitative Coding: Perceptions of AI's utility...
```

### 3. LLM Response Schema - NO ID FIELD
```python
# Line 298-304 in code_first_schemas.py
class SimpleQuote(BaseModel):
    """Simplified quote for Phase 4A extraction"""
    text: str
    speaker_name: str
    code_names: List[str]  # ❌ Only names, no IDs!
    line_start: int
    line_end: int
```

### 4. LLM Returns Different Names
Since the LLM only sees names like "AI's Impact on Research Tasks" without the ID "AI_IMPACT_RESEARCH_TASKS", it might return:
- "AI for Literature Reviews"
- "AI Impact on Research" 
- "Research Task Automation"
- Or even empty lists (as seen in output)

### 5. Pipeline Creates Fake IDs
```python
# Line 1283 in code_first_extractor.py
code_ids=[f"CODE_{code}" for code in simple_quote.code_names],
```

If LLM returns `code_names=["AI for Literature Reviews"]`, this creates:
- `code_ids=["CODE_AI for Literature Reviews"]`

But the taxonomy has:
- `id="AI_IMPACT_RESEARCH_TASKS"`

**Result: Zero matches between quotes and taxonomy codes!**

## Evidence from Actual Outputs

### Output Analysis
```bash
# Checking for codes in optimized output
grep -r "code_names.*\[.*\".*\".*\]" output_performance_optimized/interviews/
# Result: No matches found

# Checking baseline output
grep -r "code_names.*\[.*\".*\".*\]" test_output_stats/interviews/
# Result: No matches found

# All quotes have empty code arrays:
"code_ids": [],
"code_names": [],
```

### Why Are Code Arrays Empty?
The LLM is likely confused because:
1. It sees code names without IDs in the prompt
2. The SimpleQuote schema asks for `code_names` (plural list)
3. Without clear ID mapping, it defaults to empty lists

## Root Cause Summary

**The fundamental issue:** The extraction pipeline has a "write-only" taxonomy. Phase 1 creates it, but Phase 4 can't use it properly because:
1. Code IDs are never passed to the LLM
2. The LLM schema doesn't support code IDs
3. The pipeline artificially creates wrong IDs from LLM responses
4. There's no validation that applied codes match the taxonomy

## Solution Requirements

To fix this disconnect, the pipeline needs:
1. Pass BOTH code IDs and names to the LLM in Phase 4
2. Update SimpleQuote schema to include `code_ids` field
3. Instruct LLM to return the exact code IDs from the taxonomy
4. Validate that returned code IDs exist in the taxonomy
5. Remove the artificial ID creation in `_combine_extraction_results`

## Next Steps
1. ✅ Investigation complete
2. ⏳ Map the exact divergence points
3. ⏹️ Design the solution architecture
4. ⏹️ Implement the fix
5. ⏹️ Test with validation