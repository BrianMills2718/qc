# Evidence: Solution Design for Code Connection Fix
Date: 2025-08-14
Status: Solution Architecture Complete

## Problem Summary
The extraction pipeline strips code IDs when formatting prompts for Phase 4, making it impossible for the LLM to apply the correct codes to quotes. The system creates two disconnected coding systems that never link.

## Solution Architecture

### Option 1: Minimal Fix (Recommended)
**Effort:** Low (2-3 hours)
**Risk:** Low
**Impact:** Immediate fix

#### Changes Required:

1. **Update Code Formatting (code_first_extractor.py:503-509)**
```python
def _format_codes_for_prompt(self) -> str:
    """Format code taxonomy for prompt WITH IDs"""
    lines = []
    for code in self.code_taxonomy.codes:
        indent = "  " * code.level
        # Include both ID and name
        lines.append(f"{indent}- [{code.id}] {code.name}: {code.description}")
    return "\n".join(lines)
```

2. **Update SimpleQuote Schema (code_first_schemas.py:298-304)**
```python
class SimpleQuote(BaseModel):
    """Quote with proper code IDs"""
    text: str
    speaker_name: str
    code_ids: List[str]  # Use IDs directly
    line_start: int
    line_end: int
```

3. **Update Prompt Instructions (code_first_extractor.py:464-472)**
```python
"""
1. QUOTE EXTRACTION WITH MANY-TO-MANY CODING:
   - Apply codes using the EXACT CODE IDs shown in brackets [CODE_ID]
   - Each quote should be assigned relevant code IDs from the taxonomy
   - Example: If a quote discusses AI transcription, assign ["AI_IMPACT_TRANSCRIPTION"]
   - A quote can have multiple code IDs: ["AI_IMPACT_RESEARCH_TASKS", "AI_TRUST_RELIABILITY"]
"""
```

4. **Fix Result Combination (code_first_extractor.py:1283-1284)**
```python
# Remove artificial ID creation
code_ids=simple_quote.code_ids,  # Use IDs directly from LLM
code_names=[self._get_code_name(code_id) for code_id in simple_quote.code_ids],
```

5. **Add Helper Method**
```python
def _get_code_name(self, code_id: str) -> str:
    """Get code name from ID"""
    for code in self.code_taxonomy.codes:
        if code.id == code_id:
            return code.name
    return code_id  # Fallback to ID if not found
```

### Option 2: Robust Fix with Validation
**Effort:** Medium (4-6 hours)
**Risk:** Low
**Impact:** Better long-term solution

All changes from Option 1, plus:

1. **Add Code Validation**
```python
def _validate_code_ids(self, code_ids: List[str]) -> List[str]:
    """Validate that code IDs exist in taxonomy"""
    valid_ids = {code.id for code in self.code_taxonomy.codes}
    validated = []
    for code_id in code_ids:
        if code_id in valid_ids:
            validated.append(code_id)
        else:
            logger.warning(f"Invalid code ID returned by LLM: {code_id}")
    return validated
```

2. **Add Fuzzy Matching Fallback**
```python
def _fuzzy_match_code(self, code_text: str) -> Optional[str]:
    """Try to match a code by name if ID matching fails"""
    # Use string similarity to find closest matching code
    # Useful if LLM returns names instead of IDs
    pass
```

3. **Add Extraction Metrics**
```python
def _calculate_coding_metrics(self, coded_interview: CodedInterview) -> dict:
    """Calculate metrics for extraction quality"""
    return {
        "quotes_with_codes": sum(1 for q in coded_interview.quotes if q.code_ids),
        "quotes_without_codes": sum(1 for q in coded_interview.quotes if not q.code_ids),
        "avg_codes_per_quote": ...,
        "taxonomy_coverage": ...  # What % of taxonomy codes were used
    }
```

### Option 3: Complete Redesign
**Effort:** High (2-3 days)
**Risk:** Medium
**Impact:** Best long-term architecture

Redesign Phase 4 to be code-centric rather than quote-centric:
1. For each code in taxonomy, find relevant quotes
2. Build a code-to-quotes mapping
3. Invert to create quote-to-codes mapping
4. More accurate but requires significant refactoring

## Implementation Plan

### Step 1: Create Test to Verify Problem
```python
# test_code_connection.py
def test_codes_are_connected():
    """Verify that quotes reference valid taxonomy codes"""
    # Load taxonomy
    with open('output_performance_optimized/taxonomy.json') as f:
        taxonomy = json.load(f)
    code_ids = {c['id'] for c in taxonomy['codes']}
    
    # Load interview
    with open('output_performance_optimized/interviews/AI assessment Arroyo SDR.json') as f:
        interview = json.load(f)
    
    # Check code connections
    for quote in interview['quotes']:
        for code_id in quote.get('code_ids', []):
            assert code_id in code_ids, f"Code {code_id} not in taxonomy!"
```

### Step 2: Implement Minimal Fix
1. Backup current extractor
2. Update _format_codes_for_prompt()
3. Update SimpleQuote schema
4. Update prompt instructions
5. Fix _combine_extraction_results()
6. Add _get_code_name() helper

### Step 3: Test Fix
```bash
# Run extraction with fixed code
python run_code_first_extraction.py

# Verify codes are connected
python test_code_connection.py

# Check that quotes have codes
python -c "
import json
with open('output_fixed/interviews/AI assessment Arroyo SDR.json') as f:
    interview = json.load(f)
    quotes_with_codes = sum(1 for q in interview['quotes'] if q['code_ids'])
    print(f'Quotes with codes: {quotes_with_codes}/{len(interview['quotes'])}')
"
```

### Step 4: Validate Quality
- Ensure >80% of quotes have at least one code
- Verify code IDs match taxonomy exactly
- Check that code names are correctly resolved
- Confirm viewer can now display connected data

## Risk Assessment

### Risks:
1. **LLM Confusion:** LLM might still return names instead of IDs
   - Mitigation: Clear prompt instructions with examples
   
2. **Backward Compatibility:** Existing outputs won't work with viewer
   - Mitigation: Create migration script or version flag
   
3. **Performance:** No performance impact expected
   - Same number of LLM calls, just better structured

### Benefits:
1. **Immediate Fix:** Codes will actually connect to quotes
2. **Viewer Works:** All viewers will show proper connections
3. **Data Integrity:** Proper foreign key relationships
4. **Future Proof:** Can add validation and metrics

## Recommendation

Implement **Option 1 (Minimal Fix)** immediately to unblock the viewer functionality. This is a surgical fix that addresses the root cause with minimal risk. Once validated, consider adding Option 2 enhancements for better robustness.

The fix is straightforward:
1. Pass code IDs to the LLM
2. Have LLM return code IDs
3. Use those IDs directly

This will finally connect the two parallel universes of codes and quotes.