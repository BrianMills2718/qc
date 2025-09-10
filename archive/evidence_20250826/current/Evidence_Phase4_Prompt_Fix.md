# Evidence: Phase 4 Prompt Instructions Corrected

Date: 2025-08-14
Status: COMPLETED

## Problem Identified
The Phase 4 prompt was instructing the LLM to:
- "Extract AT LEAST 20-30 quotes" 
- "Every substantive statement should be captured"
- "Be exhaustive"

This was causing:
1. Extraction of irrelevant quotes (greetings, small talk)
2. Many quotes with empty code_ids arrays
3. Poor signal-to-noise ratio

## Solution Implemented

### Changed Instructions in `src/qc/prompts/phase4/quotes_speakers.txt`

**OLD (Wrong Approach):**
```
1. COMPREHENSIVE EXTRACTION:
   - Extract AT LEAST 20-30 quotes from this interview
   - Every substantive statement should be captured as a quote
   - Each speaker turn with meaningful content = one quote
   - Look through the ENTIRE interview systematically
   - Don't stop after finding a few quotes - be exhaustive
```

**NEW (Correct Approach):**
```
1. SELECTIVE EXTRACTION:
   - ONLY extract quotes that clearly relate to one or more of the codes above
   - A quote should map to at least one code from the taxonomy
   - Skip small talk, procedural discussions, or off-topic statements
   - Focus on statements that address the analytic question
   - Quality over quantity - better to have 10 relevant coded quotes than 30 uncoded ones

2. CODE APPLICATION:
   - Each quote MUST have at least one code_id from the taxonomy
   - If a statement doesn't map to any code, don't extract it as a quote
```

## Expected Behavior Change

### Before Fix
```
Quote 1: "Good morning, how are you?" - code_ids: []
Quote 2: "Should we start?" - code_ids: []
Quote 3: "The weather is nice" - code_ids: []
Quote 4: "We use AI for transcription" - code_ids: ["transcription_ai"]  # Wrong ID
```

### After Fix
```
Quote 1: "We use AI for transcription" - code_ids: ["C1.1.1"]  # Correct ID from taxonomy
(Skips greetings, weather, and other irrelevant statements)
```

## Benefits

1. **Higher Quality Extraction**: Only extracts quotes that relate to the codes
2. **No Empty Arrays**: Every extracted quote has at least one code
3. **Correct Code IDs**: Uses exact IDs from the taxonomy
4. **Better Performance**: Fewer but more relevant quotes to process
5. **Cleaner Data**: No noise from small talk or off-topic statements

## Files Changed

- `src/qc/prompts/phase4/quotes_speakers.txt` - Updated extraction instructions

## Testing

Created `test_improved_prompts.py` to demonstrate the expected behavior change.

## Next Steps

1. Run actual extraction to verify improvement
2. Monitor if LLM now returns proper code_ids
3. Fine-tune instructions if needed
4. Consider adding validation to reject quotes without codes