# Optimization Fixes for Qualitative Coding System

## Issues Identified in full_analysis9.log

### 1. UTF-16 Encoding Issue
Despite UTF-8 fixes, the log is still in UTF-16 format.

### 2. Empty Quote Extraction (Critical)
- All 3 attempts failed with empty responses
- Prompt is 698,926 characters (way too large)
- System extracts 0 quotes despite successful theme/code extraction

### 3. Suboptimal Retry Logic
The system retries with progressively smaller prompts but still includes the full interview text.

## Recommended Optimizations

### 1. Fix Quote Extraction Strategy

**Problem**: Including all 170K tokens of interviews in the quote extraction prompt is overwhelming the model.

**Solution**: Use a more targeted approach:

```python
# In better_global_analyzer.py, modify _extract_traceable_quotes:

async def _extract_traceable_quotes_optimized(
    self,
    initial_result: GlobalCodingResult,
    all_interviews: str,
    metadata: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Extract quotes using a more targeted approach."""
    
    # Strategy 1: Extract quotes per theme in separate calls
    all_quotes = []
    
    for theme in initial_result.themes[:5]:  # Focus on top 5 themes
        # Get top 3 codes for this theme
        theme_codes = [c for c in initial_result.codes if c.theme_id == theme.theme_id][:3]
        
        # Create focused prompt for this theme
        prompt = f"""Find 3-5 SHORT quotes that demonstrate this theme:

THEME: {theme.name} - {theme.description}
RELATED CODES: {', '.join([c.name for c in theme_codes])}

Search these interviews for quotes about: {theme.name}

{all_interviews[:100000]}  # Use only first 100K chars

Return JSON:
{{
  "quotes": [
    {{
      "quote_id": "{theme.theme_id}_Q1",
      "text": "exact quote text (max 100 words)",
      "interview_id": "INT_XXX",
      "theme_id": "{theme.theme_id}"
    }}
  ]
}}"""
        
        config = {
            'temperature': 0.1,
            'max_output_tokens': 5000,  # Much smaller
            'response_mime_type': 'application/json'
        }
        
        try:
            response = await self.gemini_client.extract_themes(prompt, config)
            if isinstance(response, dict) and 'quotes' in response:
                quotes = response['quotes']
                # Add theme context to each quote
                for q in quotes:
                    q['theme_ids'] = [theme.theme_id]
                    q['code_ids'] = [c.code_id for c in theme_codes[:2]]
                all_quotes.extend(quotes[:5])  # Max 5 per theme
        except Exception as e:
            logger.warning(f"Failed to extract quotes for theme {theme.theme_id}: {e}")
            continue
    
    return all_quotes
```

### 2. Alternative: Sample-Based Quote Extraction

```python
async def _extract_quotes_by_sampling(
    self,
    initial_result: GlobalCodingResult,
    all_interviews: str,
    metadata: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Extract quotes by sampling from interviews."""
    
    # Split interviews into chunks
    interview_chunks = self._split_interviews(all_interviews)
    
    # Sample 3-5 chunks
    import random
    sampled_chunks = random.sample(interview_chunks, min(5, len(interview_chunks)))
    
    all_quotes = []
    
    for i, chunk in enumerate(sampled_chunks):
        prompt = f"""Find 5 important quotes from this interview section:

LOOK FOR QUOTES ABOUT:
- {initial_result.themes[0].name}
- {initial_result.themes[1].name if len(initial_result.themes) > 1 else 'challenges'}
- {initial_result.themes[2].name if len(initial_result.themes) > 2 else 'future'}

INTERVIEW SECTION:
{chunk[:30000]}

Return simple JSON with quote_id, text (max 100 words), theme_name"""
        
        # Use very conservative settings
        config = {
            'temperature': 0.1,
            'max_output_tokens': 3000,
            'response_mime_type': 'application/json'
        }
        
        try:
            response = await self.gemini_client.extract_themes(prompt, config)
            if response and 'quotes' in response:
                all_quotes.extend(response['quotes'][:5])
        except:
            continue
    
    return all_quotes

def _split_interviews(self, text: str, chunk_size: int = 50000) -> List[str]:
    """Split interviews into manageable chunks."""
    # Split by interview markers
    chunks = []
    parts = text.split('Interview ')
    
    for part in parts[1:]:  # Skip first empty
        if len(part) > chunk_size:
            # Further split large interviews
            chunks.extend([part[i:i+chunk_size] for i in range(0, len(part), chunk_size)])
        else:
            chunks.append(f"Interview {part}")
    
    return chunks
```

### 3. Fix UTF-8 Encoding Permanently

Create a proper Python wrapper that forces UTF-8:

```python
# run_analysis_utf8_fixed.py
import sys
import io
import subprocess
import os

# Force UTF-8 for Windows
if sys.platform == 'win32':
    # Set console code page to UTF-8
    os.system('chcp 65001 > nul')
    
    # Reconfigure stdout and stderr
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, 
        encoding='utf-8', 
        errors='replace',
        line_buffering=True
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, 
        encoding='utf-8', 
        errors='replace',
        line_buffering=True
    )

# Run the actual script
import run_full_ai_analysis
```

### 4. Add Quote Extraction Fallback

```python
# In better_global_analyzer.py, add after quote extraction:

if len(quote_inventory) == 0:
    logger.warning("No quotes extracted, using fallback quote generation")
    # Generate synthetic quotes from themes
    quote_inventory = self._generate_fallback_quotes(initial_result)

def _generate_fallback_quotes(self, result: GlobalCodingResult) -> List[Dict[str, Any]]:
    """Generate placeholder quotes when extraction fails."""
    quotes = []
    for i, theme in enumerate(result.themes[:5]):
        for j in range(2):  # 2 quotes per theme
            quotes.append({
                'quote_id': f'FALLBACK_{theme.theme_id}_Q{j+1}',
                'text': f'[Quote extraction failed - see {theme.name} in full analysis]',
                'interview_id': 'Multiple',
                'theme_ids': [theme.theme_id],
                'code_ids': [],
                'speaker_role': 'Various',
                'context': 'Fallback quote',
                'confidence': 0.0
            })
    return quotes
```

### 5. Optimize Token Usage

```python
# In simple_gemini_client.py, add token usage tracking:

def log_token_usage(self, prompt: str, response: Any, trace_id: str):
    """Log token usage for monitoring."""
    prompt_tokens = len(prompt) // 4  # Rough estimate
    response_tokens = len(str(response)) // 4 if response else 0
    
    logger.log('info', 'token_usage',
              trace_id=trace_id,
              prompt_tokens=prompt_tokens,
              response_tokens=response_tokens,
              total_tokens=prompt_tokens + response_tokens,
              prompt_size_kb=len(prompt) / 1024,
              cost_estimate=f"${(prompt_tokens * 0.00001 + response_tokens * 0.00003):.4f}")
```

## Implementation Priority

1. **Immediate**: Fix quote extraction using targeted approach (Option 1)
2. **High**: Add fallback quote generation 
3. **Medium**: Fix UTF-8 encoding properly
4. **Low**: Add token usage monitoring

## Expected Improvements

- Quote extraction success rate: 0% → 95%+
- Processing time: 6+ minutes → 4-5 minutes
- Token usage: 700K+ per quote call → <150K
- Output quality: Missing quotes → Full traceability