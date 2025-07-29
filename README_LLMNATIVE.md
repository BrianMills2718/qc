# LLM-Native Global Analysis Implementation

## Overview

This implementation leverages Gemini 2.5 Flash's 1M token context window to analyze all 103 interviews simultaneously, using only 2 LLM calls instead of 330+ sequential calls.

## Key Innovation

Instead of constraining LLMs to human-style sequential processing, we leverage their ability to see patterns across the entire dataset simultaneously. This could produce better insights in a fraction of the time.

## Quick Start

### 1. Check Setup
```bash
python check_setup.py
```

This will verify:
- Python version (3.8+ required)
- Required packages installed
- GEMINI_API_KEY environment variable set
- Interview data files present (103 DOCX files)

### 2. Set API Key
```bash
# Windows
set GEMINI_API_KEY=your-key-here

# Linux/Mac
export GEMINI_API_KEY=your-key-here
```

### 3. Run Sample Test (10 interviews)
```bash
python test_global_analysis.py
```

This will:
- Load 10 sample interviews
- Verify token count fits in context
- Perform global analysis (2 LLM calls)
- Export results to `output/global_analysis_sample/`

### 4. Run Full Analysis (103 interviews)
After the sample test succeeds, the script will ask if you want to run the full analysis.

## Token Usage

Our 103 interviews use approximately:
- **Total tokens: 318,320**
- **Available in 1M context: 730,256 tokens**
- **Average per interview: 3,090 tokens**

This fits comfortably within Gemini's context window with room for prompts and outputs.

## Output Files

The analysis produces:

### CSV Files
- `themes.csv` - Major themes with prevalence and confidence
- `codes.csv` - All codes with frequencies and definitions  
- `quotes.csv` - All quotes with full traceability
- `quote_chains.csv` - Sequences showing idea progression
- `contradictions.csv` - Opposing viewpoints with evidence
- `stakeholder_positions.csv` - Who supports/opposes each theme
- `saturation_curve.csv` - When new insights stopped appearing
- `traceability_matrix.csv` - Complete theme→code→quote→interview mapping

### Reports
- `report.md` - Comprehensive markdown report
- `complete_analysis.json` - Full analysis backup

## Architecture

### Two-Call Approach

**Call 1: Comprehensive Global Analysis**
- Analyzes all 103 interviews simultaneously
- Identifies themes, codes, quote chains, contradictions
- Tracks concept development across dataset
- Assesses theoretical saturation

**Call 2: Traceability Enhancement**  
- Enhances findings with complete quote evidence
- Creates CSV export tables
- Generates markdown report
- Ensures every insight traces to specific interviews

### Key Components

1. **DOCX Parser** (`qc/parsing/docx_parser.py`)
   - Extracts text from interview files
   - Preserves metadata for traceability

2. **Token Counter** (`qc/utils/token_counter.py`)
   - Accurate token counting using tiktoken
   - Ensures content fits in context window

3. **Global Analyzer** (`qc/core/global_qualitative_analyzer.py`)
   - Loads all interviews with metadata markers
   - Performs 2-call global analysis
   - Exports comprehensive results

4. **Pydantic Models** (`qc/models/comprehensive_analysis_models.py`)
   - Structured data models for analysis
   - Ensures consistent output format

## Comparison with Traditional Approach

| Metric | LLM-Native | Traditional Sequential |
|--------|------------|----------------------|
| LLM Calls | 2 | 330+ |
| Dev Time | 2-3 days | 15 days |
| Pattern Recognition | Global | Local |
| Saturation Assessment | Natural | Artificial |
| Quote Chains | Automatic | Manual |

## Quality Metrics

The analysis provides quality scores for:
- Traceability completeness (% with full evidence)
- Quote chain coverage (% of themes with chains)
- Stakeholder coverage (% of participants mapped)
- Overall evidence strength

## Fallback Options

If the global analysis doesn't meet quality standards, the system can fall back to:
1. Batched three-phase (36-40 calls)
2. Progressive sampling (125-155 calls)
3. Full systematic (330+ calls)

## Next Steps

1. Review sample results in `output/global_analysis_sample/`
2. Check quality metrics meet requirements
3. Run full analysis if sample is satisfactory
4. Store results in Neo4j for graph queries (optional)
5. Compare with systematic approach if needed

## Troubleshooting

### "Token limit exceeded"
- Check interview files aren't corrupted
- Verify no unusually large files
- Consider batching if over 900K tokens

### "API key not found"
- Set GEMINI_API_KEY environment variable
- Check spelling and no extra spaces

### "JSON parsing error"
- Check debug files in `debug_responses/`
- May need to adjust temperature setting
- Structured output should prevent this

## Contact

For issues or questions about the LLM-native approach, check the documentation in:
- `llm_native_approach.md` - Detailed implementation guide
- `CLAUDE.md` - Updated project roadmap
- `framework_specifications.md` - Architecture decisions