# Evidence: Code Divergence Mapping
Date: 2025-08-14
Status: Complete Divergence Analysis

## Code Flow Through the Pipeline

### Phase 1: Taxonomy Creation
**Location:** `code_first_extractor.py:124-165`
```
Input: All interviews concatenated
Output: CodeTaxonomy with structured codes
Example Code:
  - id: "AI_IMPACT_RESEARCH_TASKS"
  - name: "AI's Impact on Research Tasks"
  - description: "How researchers perceive AI's influence..."
```

### Phase 4A: Quote Extraction Request
**Location:** `code_first_extractor.py:453-509`

#### What Gets Formatted for Prompt:
```python
# _format_codes_for_prompt() outputs:
- AI's Impact on Research Tasks: How researchers perceive AI's influence...
  - AI for Transcription: The use and perceived accuracy...
  - AI for Qualitative Coding: Perceptions of AI's utility...
```
**❌ DIVERGENCE POINT 1: IDs stripped from taxonomy**

#### What LLM is Asked to Return:
```python
class SimpleQuote(BaseModel):
    code_names: List[str]  # Expects names only
```
**❌ DIVERGENCE POINT 2: Schema can't accept IDs**

### Phase 4A: LLM Response
**Location:** Response from `llm.extract_structured()`

#### What LLM Actually Returns:
```python
SimpleQuote(
    text="...",
    speaker_name="Molly Dunnigan",
    code_names=[],  # Empty because unclear what names to use
    # OR
    code_names=["AI Research Impact", "Tool Usage"]  # Makes up new names
)
```
**❌ DIVERGENCE POINT 3: LLM creates new names or returns empty**

### Phase 4: Result Combination
**Location:** `code_first_extractor.py:1283`

#### Artificial ID Creation:
```python
code_ids=[f"CODE_{code}" for code in simple_quote.code_names]
# If LLM returned ["AI Research Impact"]
# Creates: ["CODE_AI Research Impact"]
```
**❌ DIVERGENCE POINT 4: Wrong IDs fabricated**

### Final Output
**Location:** `interviews/*.json`

#### What Gets Saved:
```json
{
  "quotes": [{
    "code_ids": [],  // Empty or wrong IDs
    "code_names": [],  // Empty or wrong names
    // Quote has no connection to taxonomy codes
  }]
}
```
**❌ DIVERGENCE POINT 5: Complete disconnect**

## The Two Parallel Universes

### Universe 1: Taxonomy Codes
```
AI_IMPACT_RESEARCH_TASKS -> "AI's Impact on Research Tasks"
AI_IMPACT_TRANSCRIPTION -> "AI for Transcription"
AI_IMPACT_QUAL_CODING -> "AI for Qualitative Coding"
```

### Universe 2: Quote Codes (if any)
```
CODE_AI Research Impact -> "AI Research Impact"
CODE_Tool Usage -> "Tool Usage"
(or more commonly: nothing at all)
```

**These two universes never connect!**

## Critical Code Locations

| Component | File | Lines | Issue |
|-----------|------|-------|-------|
| Taxonomy Creation | code_first_extractor.py | 124-165 | Creates proper IDs |
| Code Formatting | code_first_extractor.py | 503-509 | **Strips IDs** |
| Quote Schema | code_first_schemas.py | 298-304 | **No ID field** |
| LLM Call | code_first_extractor.py | 334-338 | Uses broken schema |
| ID Fabrication | code_first_extractor.py | 1283 | **Creates wrong IDs** |
| Validation | (none) | - | **No validation exists** |

## Why Quotes Have No Codes

The LLM returns empty `code_names` because:
1. It sees: "AI's Impact on Research Tasks" (name only)
2. It needs to return exact matches in `code_names`
3. It's unsure if it should return:
   - "AI's Impact on Research Tasks" (exact name)
   - "AI_IMPACT_RESEARCH_TASKS" (the ID it never saw)
   - Something else
4. Faced with ambiguity, it returns empty arrays

## Validation

**Test Command:**
```bash
python -c "
import json
with open('output_performance_optimized/taxonomy.json') as f:
    taxonomy = json.load(f)
    code_ids = {c['id'] for c in taxonomy['codes']}
    print(f'Taxonomy has {len(code_ids)} codes')
    print(f'First 3 IDs: {list(code_ids)[:3]}')

with open('output_performance_optimized/interviews/AI assessment Arroyo SDR.json') as f:
    interview = json.load(f)
    all_code_ids = []
    for quote in interview['quotes']:
        all_code_ids.extend(quote.get('code_ids', []))
    print(f'Interview has {len(all_code_ids)} code applications')
    print(f'Unique codes used: {set(all_code_ids)}')
"
```

**Expected Output:**
```
Taxonomy has 33 codes
First 3 IDs: ['AI_IMPACT_RESEARCH_TASKS', 'AI_IMPACT_TRANSCRIPTION', ...]
Interview has 0 code applications
Unique codes used: set()
```

## Conclusion

The divergence is complete and systemic. The taxonomy and quote coding exist in parallel universes that never intersect. This is not a bug in one location but a fundamental architectural flaw where the pipeline creates data it can never use.