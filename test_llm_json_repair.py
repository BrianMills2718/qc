#!/usr/bin/env python3
"""
Test using LLM to repair broken JSON output
"""
import asyncio
import json
import sys
from pathlib import Path

# Add project root to Python path  
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from qc.core.simple_gemini_client import SimpleGeminiClient

# Example of broken JSON from actual output
BROKEN_JSON = """
{
  "csv_export_data": {
    "themes_csv": "theme_id,name,prevalence,confidence,interview_count\\nT1,AI for Qualitative Data Processing,1.0,0.9,18",
    "codes_csv": "code_id,name,definition,frequency,first_appearance,theme_id\\nC001,AI for Transcription,Use of AI to convert audio to text,8,INT_001,T1",
    "$defs": {
      "SimpleCSVExport": {
        "properties": {
          "themes_csv": {"type": "string"},
          "codes_csv": {"type": "string"}
        }
      }
    },
    "$ref": "#/$defs/SimpleCSVExport"
  },
  "markdown_report": "# Analysis Report",
  "executive_summary": "Summary here"
}
"""

async def test_json_repair():
    """Test if LLM can repair broken JSON."""
    client = SimpleGeminiClient()
    
    repair_prompt = f"""Fix this broken JSON by removing any schema references ($defs, $ref) and returning only valid data JSON:

{BROKEN_JSON}

Return ONLY the fixed JSON with no explanation. The JSON should have this structure:
{{
  "csv_export_data": {{
    "themes_csv": "...",
    "codes_csv": "...",
    "quotes_csv": "...",
    "quote_chains_csv": "...",
    "contradictions_csv": "...",
    "stakeholder_positions_csv": "...",
    "saturation_curve_csv": "...",
    "traceability_matrix_csv": "..."
  }},
  "markdown_report": "...",
  "executive_summary": "...",
  "complete_quote_inventory_json": "...",
  "interview_summaries_json": "...",
  "traceability_completeness": 0.95,
  "quote_chain_coverage": 0.85,
  "stakeholder_coverage": 0.80,
  "evidence_strength": 0.90
}}"""

    generation_config = {
        'temperature': 0.1,
        'max_output_tokens': 5000,
        'response_mime_type': 'application/json'
    }
    
    try:
        # Try to get LLM to fix it
        fixed_json = await client.extract_themes(
            repair_prompt,
            generation_config=generation_config
        )
        
        print("LLM successfully repaired JSON!")
        print(json.dumps(fixed_json, indent=2)[:500] + "...")
        
        # Validate it's actually fixed
        if isinstance(fixed_json, dict) and '$defs' not in fixed_json and '$ref' not in str(fixed_json):
            print("\n[SUCCESS] JSON is clean - no schema references!")
            return True
        else:
            print("\n[FAIL] JSON still contains schema references")
            return False
            
    except Exception as e:
        print(f"Failed to repair JSON: {e}")
        return False


async def test_alternative_strategies():
    """Test alternative parsing strategies."""
    
    print("\n=== Alternative Strategies ===\n")
    
    # Strategy 1: Multiple output formats
    print("1. Multiple Format Strategy:")
    print("   - Try structured JSON first")
    print("   - Fall back to plain text on failure")
    print("   - Use LLM repair as last resort")
    
    # Strategy 2: Chunked responses
    print("\n2. Chunked Response Strategy:")
    print("   - Request each section separately")
    print("   - Smaller, focused prompts")
    print("   - Combine results programmatically")
    
    # Strategy 3: Validation loop
    print("\n3. Validation Loop Strategy:")
    print("   - Generate output")
    print("   - Validate structure")
    print("   - Ask LLM to fix specific issues")
    print("   - Repeat until valid")
    
    # Strategy 4: Template-based generation
    print("\n4. Template-Based Strategy:")
    print("   - Provide exact output template")
    print("   - Use fill-in-the-blank approach")
    print("   - More constrained generation")


async def main():
    print("Testing LLM JSON Repair Strategy...\n")
    
    success = await test_json_repair()
    
    if success:
        print("\n[SUCCESS] LLM repair strategy could work!")
    else:
        print("\n[FAIL] LLM repair strategy has issues")
    
    await test_alternative_strategies()
    
    print("\n=== Recommendation ===")
    print("Best approach: Hybrid strategy")
    print("1. Use plain text with flexible parsing (current approach)")
    print("2. Add validation for each section")
    print("3. Use LLM repair for specific broken sections only")
    print("4. Implement progressive fallbacks")


if __name__ == "__main__":
    asyncio.run(main())