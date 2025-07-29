"""
LLM-Native Global Qualitative Analyzer

Analyzes all 103 interviews simultaneously using Gemini's 1M token context window
to leverage global pattern recognition instead of sequential processing.
"""
import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import time

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from qc.parsing.docx_parser import DOCXParser
from qc.utils.token_counter import TokenCounter
from qc.models.comprehensive_analysis_models import (
    GlobalCodingResult, EnhancedResult, QuoteEvidence,
    CSVExportData
)
from qc.models.simplified_schemas import (
    SimpleGlobalResult, SimpleEnhancedResult, transform_to_full_schema
)
from qc.core.simple_gemini_client import SimpleGeminiClient
from qc.core.load_and_verify_interviews import (
    find_all_interview_files, 
    load_all_interviews_with_metadata
)
from qc.core.robust_plain_text_parser import RobustPlainTextParser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GlobalQualitativeAnalyzer:
    """
    Analyzes all interviews simultaneously for global pattern recognition.
    """
    
    def __init__(self, research_question: str = None):
        """Initialize the global analyzer."""
        self.docx_parser = DOCXParser()
        self.token_counter = TokenCounter()
        self.gemini_client = SimpleGeminiClient()
        self.text_parser = RobustPlainTextParser()
        
        self.research_question = research_question or os.getenv(
            'RESEARCH_QUESTION',
            'How are AI methods being integrated into qualitative research practices?'
        )
        
        # Find interview files - ONLY AI interviews
        ai_interviews_dir = project_root / "data" / "interviews" / "AI_Interviews_all_2025.0728" / "Interviews"
        self.interview_files = find_all_interview_files(ai_interviews_dir)
        logger.info(f"Found {len(self.interview_files)} AI interview files")
        
    async def analyze_global(self, sample_size: Optional[int] = None) -> EnhancedResult:
        """
        Perform global analysis on all interviews (or a sample).
        
        Args:
            sample_size: Optional number of interviews to analyze (for testing)
            
        Returns:
            EnhancedResult with complete analysis and traceability
        """
        start_time = time.time()
        
        # Load interviews
        files_to_analyze = self.interview_files[:sample_size] if sample_size else self.interview_files
        logger.info(f"Loading {len(files_to_analyze)} interviews...")
        
        all_interviews_text, total_tokens, metadata = load_all_interviews_with_metadata(files_to_analyze)
        
        logger.info(f"Loaded {len(files_to_analyze)} interviews with {total_tokens:,} tokens")
        
        # Verify token limit
        if total_tokens > 900_000:
            raise ValueError(f"Content too large for single context: {total_tokens:,} tokens")
        
        # Call 1: Comprehensive global analysis
        logger.info("Performing comprehensive global analysis (Call 1)...")
        global_result = await self._comprehensive_global_analysis(
            all_interviews_text, 
            len(files_to_analyze),
            total_tokens
        )
        
        # Call 2: Enhance for traceability and export
        logger.info("Enhancing results for full traceability (Call 2)...")
        enhanced_result = await self._refine_for_traceability(
            global_result,
            all_interviews_text
        )
        
        # Add processing metadata
        processing_time = time.time() - start_time
        enhanced_result.global_analysis.processing_metadata = {
            'processing_time_seconds': processing_time,
            'interviews_analyzed': len(files_to_analyze),
            'total_tokens': total_tokens,
            'llm_calls': 2,
            'model': 'gemini-2.5-flash'
        }
        
        logger.info(f"Analysis complete in {processing_time:.1f} seconds")
        
        return enhanced_result
    
    async def _comprehensive_global_analysis(
        self, 
        all_interviews: str,
        interview_count: int,
        total_tokens: int
    ) -> GlobalCodingResult:
        """First LLM call: Comprehensive global analysis."""
        
        prompt = f"""Analyze these {interview_count} interviews using grounded theory methodology with GLOBAL CONTEXT.

Unlike human researchers who must process interviews sequentially, you can see ALL the data simultaneously. Use this advantage to:

1. **IDENTIFY THEMES** that emerge across the ENTIRE dataset
   - Look for patterns that span multiple interviews
   - Note which themes are universal vs. context-specific
   - Track theme prevalence across different stakeholder groups

2. **TRACK CONCEPT DEVELOPMENT** - how ideas evolve from Interview 001 to {interview_count:03d}
   - Identify when new concepts first appear
   - Track how definitions and understanding evolve
   - Note when concepts stabilize or transform

3. **FIND QUOTE CHAINS** - sequences of related quotes showing progression
   - Evolution chains: How ideas develop
   - Contradiction chains: Opposing viewpoints
   - Consensus chains: Agreement building
   - Problem-solution chains: Issues and resolutions

4. **ASSESS THEORETICAL SATURATION** - identify when new interviews stopped adding new insights
   - Track when each major theme reached saturation
   - Note which interviews added new dimensions
   - Identify the point where patterns stabilized

5. **DETECT CONTRADICTIONS** - opposing viewpoints with evidence from both sides
   - Find disagreements on key issues
   - Map which stakeholders hold which positions
   - Look for attempts at reconciliation

6. **MAP STAKEHOLDER POSITIONS** - who says what about which topics
   - Identify different stakeholder types
   - Track their positions on major themes
   - Note areas of consensus and conflict

RESEARCH QUESTION: {self.research_question}

METHODOLOGICAL INSTRUCTIONS:
- Apply grounded theory principles but leverage your global perspective
- Create codes that capture meaning across ALL interviews
- Build themes hierarchically (themes → categories → codes)
- For EVERY code and theme, provide specific quote evidence with interview numbers
- Track which interviews support each finding
- Provide exact quotes with speaker identification (e.g., "Sara McCleskey (RAND Researcher): 'exact quote here'")
- Assess when theoretical saturation naturally occurred in the sequence
- Note code frequency and distribution across interviews
- Identify quote chains that show conceptual development
- Map contradictions with evidence from both perspectives

CRITICAL: Ensure every finding is traceable to specific interviews and quotes.

ALL {interview_count} INTERVIEWS:
{all_interviews}

Return a SimpleGlobalResult with the following structure:
- themes: List of themes with theme_id, name, description, prevalence, interviews_count, key_quotes (as strings), confidence_score
- codes: List of codes with code_id, name, definition, frequency, interviews_present, first_appearance
- quote_chains: List of chains with chain_id, theme_id, chain_type, description, quotes (as ordered list of quote strings)
- theoretical_insights: List of key theoretical discoveries
- emergent_theory: Main theoretical contribution (single paragraph)
- methodological_notes: Notes on the analysis process
- saturation_point: Interview ID where saturation was reached
- saturation_evidence: Explanation of why saturation occurred at that point
- overall_confidence: Float between 0.0 and 1.0

Keep it simple and focused on the core findings."""

        # Configure for structured output with simplified schema
        generation_config = {
            'temperature': 0.3,
            'max_output_tokens': 60000,
            'response_mime_type': 'application/json',
            'response_schema': SimpleGlobalResult  # Use simplified schema
        }
        
        try:
            response = await self.gemini_client.extract_themes(
                prompt,
                generation_config=generation_config
            )
            
            # Parse the JSON response
            if isinstance(response, dict):
                # Debug: Log what we received
                logger.info(f"Received response keys: {list(response.keys())}")
                
                # Create SimpleGlobalResult from response
                simple_result = SimpleGlobalResult(**response)
                
                # Prepare metadata
                metadata = {
                    'study_id': f"study_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'analysis_timestamp': datetime.now(),
                    'research_question': self.research_question,
                    'interviews_analyzed': interview_count,
                    'total_tokens_analyzed': total_tokens
                }
                
                # Transform to full schema
                full_result_dict = transform_to_full_schema(simple_result, metadata)
                
                return GlobalCodingResult(**full_result_dict)
            else:
                # If response is already a string, parse it
                result_dict = json.loads(response)
                result_dict['study_id'] = f"study_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                result_dict['analysis_timestamp'] = datetime.now().isoformat()
                result_dict['research_question'] = self.research_question
                result_dict['interviews_analyzed'] = interview_count
                result_dict['total_tokens_analyzed'] = total_tokens
                
                return GlobalCodingResult(**result_dict)
                
        except Exception as e:
            logger.error(f"Error in global analysis: {str(e)}")
            raise
    
    async def _refine_for_traceability(
        self,
        initial_result: GlobalCodingResult,
        all_interviews: str
    ) -> EnhancedResult:
        """Second LLM call: Enhance for full traceability and exports."""
        
        # Convert initial result to JSON for the prompt
        initial_json = initial_result.model_dump_json(indent=2)
        
        # Don't truncate - we have 1M context window!
        # Just include the first result summary instead of raw interviews
        interviews_summary = f"Analysis based on {initial_result.interviews_analyzed} interviews with {initial_result.total_tokens_analyzed} tokens"
        
        prompt = f"""Enhance this qualitative analysis with FULL TRACEABILITY and export-ready data.

INITIAL ANALYSIS:
{initial_json}

ORIGINAL INTERVIEWS (first 10K chars for reference):
{interviews_summary}

ENHANCEMENT TASKS:

1. **COMPLETE QUOTE INVENTORY**: For every code and theme, ensure we have:
   - Exact quote text
   - Interview ID and number (e.g., INT_023)
   - Original file name
   - Approximate line number
   - Speaker role/position if identifiable
   - Brief context

2. **QUOTE CHAINS ENHANCEMENT**: For each major theme, create detailed chains showing:
   - Initial mention → Development → Contradictions → Resolution
   - Exact quotes with full metadata for each step
   - Which interviews contain each part of the chain
   - Interpretation of what the chain reveals

3. **CODE PROGRESSION DETAILS**: For key codes, provide:
   - First appearance with exact quote
   - How definition evolved with supporting quotes
   - Peak frequency period with examples
   - Final stabilization with evidence

4. **STAKEHOLDER MAPPING MATRIX**: Create clear position mapping:
   - Stakeholder type/role
   - Position on each major theme (support/oppose/neutral)
   - Evidence quotes for each position
   - Areas of consensus vs. conflict

5. **CSV EXPORT TABLES**: Create CSV strings for these tables (with headers):
   - themes_csv: "theme_id,name,prevalence,confidence,interview_count\nT001,Theme Name,0.8,0.9,10\n..."
   - codes_csv: "code_id,name,definition,frequency,first_appearance,theme_id\nC001,Code Name,Definition,12,INT_001,T001\n..."
   - quotes_csv: "quote_id,text,interview_id,interview_name,line_number,code_ids,theme_ids\nQ001,Quote text,INT_001,Interview 1,45,C001,T001\n..."
   - quote_chains_csv: "chain_id,type,description,quote_sequence,interpretation\nQC001,evolution,Description,Q001;Q002;Q003,Interpretation\n..."
   - contradictions_csv: "id,issue,position_a,position_b,evidence_a,evidence_b\nCON001,Issue,Position A,Position B,Evidence A,Evidence B\n..."
   - stakeholder_positions_csv: "stakeholder_type,theme_id,position,evidence\nType1,T001,Position,Evidence\n..."
   - saturation_curve_csv: "interview_batch,new_codes,new_themes,cumulative_codes\n1,5,2,5\n2,3,1,8\n..."
   - traceability_matrix_csv: "theme_id,code_id,quote_id,interview_id,line_number\nT001,C001,Q001,INT_001,45\n..."

6. **MARKDOWN REPORT**: Create a comprehensive report with:
   - Executive summary (1 page)
   - Major themes with quote chains
   - Code hierarchy with examples
   - Contradiction analysis
   - Stakeholder position summary
   - Theoretical insights
   - Methodological notes

7. **INTERVIEW SUMMARIES**: Brief summary of each interview's main contributions

Ensure EVERY insight can be traced back to specific interviews and quotes.

Return your response in the following EXACT plain text format with clear section markers:

=== THEMES_CSV ===
theme_id,name,prevalence,confidence,interview_count
T001,Theme Name,0.8,0.9,10
[more rows...]

=== CODES_CSV ===
code_id,name,definition,frequency,first_appearance,theme_id
C001,Code Name,Definition,12,INT_001,T001
[more rows...]

=== QUOTES_CSV ===
quote_id,text,interview_id,interview_name,line_number,code_ids,theme_ids
Q001,"Quote text here",INT_001,Interview 1,45,C001,T001
[more rows...]

=== QUOTE_CHAINS_CSV ===
chain_id,type,description,quote_sequence,interpretation
QC001,evolution,Description,Q001;Q002;Q003,Interpretation
[more rows...]

=== CONTRADICTIONS_CSV ===
id,issue,position_a,position_b,evidence_a,evidence_b
CON001,Issue,Position A,Position B,Evidence A,Evidence B
[more rows...]

=== STAKEHOLDER_POSITIONS_CSV ===
stakeholder_type,theme_id,position,evidence
Type1,T001,Position,Evidence
[more rows...]

=== SATURATION_CURVE_CSV ===
interview_batch,new_codes,new_themes,cumulative_codes
1,5,2,5
[more rows...]

=== TRACEABILITY_MATRIX_CSV ===
theme_id,code_id,quote_id,interview_id,line_number
T001,C001,Q001,INT_001,45
[more rows...]

=== MARKDOWN_REPORT ===
[Your comprehensive markdown report here]

=== EXECUTIVE_SUMMARY ===
[Your 1-page executive summary here]

=== COMPLETE_QUOTE_INVENTORY_JSON ===
{{"quotes": [{{"quote_id": "Q001", "text": "...", "interview_id": "INT_001", ...}}]}}

=== INTERVIEW_SUMMARIES_JSON ===
{{"INT_001": "Summary of interview 1", "INT_002": "Summary of interview 2", ...}}

=== METRICS ===
traceability_completeness: 0.95
quote_chain_coverage: 0.85
stakeholder_coverage: 0.80
evidence_strength: 0.90

Use these exact section markers (=== SECTION_NAME ===) to separate sections."""

        generation_config = {
            'temperature': 0.2,  # Lower for precise traceability
            'max_output_tokens': 60000,  # Increased from 30K
            'response_mime_type': 'text/plain'  # Use plain text to avoid JSON issues
        }
        
        try:
            response = await self.gemini_client.extract_themes(
                prompt,
                generation_config=generation_config
            )
            
            # Parse plain text response
            if isinstance(response, str):
                # Use robust parser
                sections = self.text_parser.parse(response)
                
                # Create SimpleEnhancedResult from parsed sections
                from qc.models.simplified_schemas import SimpleCSVExport
                
                csv_data = SimpleCSVExport(
                    themes_csv=sections.get('THEMES_CSV', ''),
                    codes_csv=sections.get('CODES_CSV', ''),
                    quotes_csv=sections.get('QUOTES_CSV', ''),
                    quote_chains_csv=sections.get('QUOTE_CHAINS_CSV', ''),
                    contradictions_csv=sections.get('CONTRADICTIONS_CSV', ''),
                    stakeholder_positions_csv=sections.get('STAKEHOLDER_POSITIONS_CSV', ''),
                    saturation_curve_csv=sections.get('SATURATION_CURVE_CSV', ''),
                    traceability_matrix_csv=sections.get('TRACEABILITY_MATRIX_CSV', '')
                )
                
                # Parse metrics with robust parser
                metrics_text = sections.get('METRICS', '')
                metrics = self.text_parser.extract_metrics(metrics_text)
                
                simple_enhanced = SimpleEnhancedResult(
                    csv_export_data=csv_data,
                    markdown_report=sections.get('MARKDOWN_REPORT', ''),
                    executive_summary=sections.get('EXECUTIVE_SUMMARY', ''),
                    complete_quote_inventory_json=sections.get('COMPLETE_QUOTE_INVENTORY_JSON', '{}'),
                    interview_summaries_json=sections.get('INTERVIEW_SUMMARIES_JSON', '{}'),
                    traceability_completeness=metrics.get('traceability_completeness', 0.0),
                    quote_chain_coverage=metrics.get('quote_chain_coverage', 0.0),
                    stakeholder_coverage=metrics.get('stakeholder_coverage', 0.0),
                    evidence_strength=metrics.get('evidence_strength', 0.0)
                )
                
                # Parse CSV strings back to tables
                import csv
                import io
                
                def csv_to_dicts(csv_string):
                    """Convert CSV string to list of dictionaries."""
                    if not csv_string.strip():
                        return []
                    reader = csv.DictReader(io.StringIO(csv_string))
                    return list(reader)
                
                # Transform to full EnhancedResult
                enhanced_dict = {
                    'global_analysis': initial_result.model_dump(),
                    'csv_export_data': {
                        'themes_table': csv_to_dicts(simple_enhanced.csv_export_data.themes_csv),
                        'codes_table': csv_to_dicts(simple_enhanced.csv_export_data.codes_csv),
                        'quotes_table': csv_to_dicts(simple_enhanced.csv_export_data.quotes_csv),
                        'quote_chains_table': csv_to_dicts(simple_enhanced.csv_export_data.quote_chains_csv),
                        'contradictions_table': csv_to_dicts(simple_enhanced.csv_export_data.contradictions_csv),
                        'stakeholder_positions_table': csv_to_dicts(simple_enhanced.csv_export_data.stakeholder_positions_csv),
                        'saturation_curve_table': csv_to_dicts(simple_enhanced.csv_export_data.saturation_curve_csv),
                        'traceability_matrix': csv_to_dicts(simple_enhanced.csv_export_data.traceability_matrix_csv)
                    },
                    'markdown_report': simple_enhanced.markdown_report,
                    'executive_summary': simple_enhanced.executive_summary,
                    'complete_quote_inventory': self._parse_quote_inventory(simple_enhanced.complete_quote_inventory_json),
                    'interview_summaries': self._safe_json_parse(simple_enhanced.interview_summaries_json, {}),
                    'traceability_completeness': simple_enhanced.traceability_completeness,
                    'quote_chain_coverage': simple_enhanced.quote_chain_coverage,
                    'stakeholder_coverage': simple_enhanced.stakeholder_coverage,
                    'evidence_strength': simple_enhanced.evidence_strength
                }
                return EnhancedResult(**enhanced_dict)
            else:
                # Parse JSON string
                result_dict = json.loads(response)
                simple_enhanced = SimpleEnhancedResult(**result_dict)
                
                # Parse CSV strings back to tables
                import csv
                import io
                
                def csv_to_dicts(csv_string):
                    """Convert CSV string to list of dictionaries."""
                    if not csv_string.strip():
                        return []
                    reader = csv.DictReader(io.StringIO(csv_string))
                    return list(reader)
                
                # Transform to full EnhancedResult
                enhanced_dict = {
                    'global_analysis': initial_result.model_dump(),
                    'csv_export_data': {
                        'themes_table': csv_to_dicts(simple_enhanced.csv_export_data.themes_csv),
                        'codes_table': csv_to_dicts(simple_enhanced.csv_export_data.codes_csv),
                        'quotes_table': csv_to_dicts(simple_enhanced.csv_export_data.quotes_csv),
                        'quote_chains_table': csv_to_dicts(simple_enhanced.csv_export_data.quote_chains_csv),
                        'contradictions_table': csv_to_dicts(simple_enhanced.csv_export_data.contradictions_csv),
                        'stakeholder_positions_table': csv_to_dicts(simple_enhanced.csv_export_data.stakeholder_positions_csv),
                        'saturation_curve_table': csv_to_dicts(simple_enhanced.csv_export_data.saturation_curve_csv),
                        'traceability_matrix': csv_to_dicts(simple_enhanced.csv_export_data.traceability_matrix_csv)
                    },
                    'markdown_report': simple_enhanced.markdown_report,
                    'executive_summary': simple_enhanced.executive_summary,
                    'complete_quote_inventory': self._parse_quote_inventory(simple_enhanced.complete_quote_inventory_json),
                    'interview_summaries': self._safe_json_parse(simple_enhanced.interview_summaries_json, {}),
                    'traceability_completeness': simple_enhanced.traceability_completeness,
                    'quote_chain_coverage': simple_enhanced.quote_chain_coverage,
                    'stakeholder_coverage': simple_enhanced.stakeholder_coverage,
                    'evidence_strength': simple_enhanced.evidence_strength
                }
                return EnhancedResult(**enhanced_dict)
                
        except Exception as e:
            logger.error(f"Error in traceability enhancement: {str(e)}")
            raise
    
    def _parse_plain_text_response(self, text: str) -> Dict[str, str]:
        """Parse plain text response into sections."""
        sections = {}
        current_section = None
        current_content = []
        
        for line in text.split('\n'):
            # Check for section marker
            if line.startswith('=== ') and line.endswith(' ==='):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = line[4:-4].strip()
                current_content = []
            else:
                # Add line to current section
                if current_section:
                    current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _parse_metrics(self, metrics_text: str) -> Dict[str, float]:
        """Parse metrics from text format."""
        metrics = {}
        
        for line in metrics_text.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                try:
                    metrics[key.strip()] = float(value.strip())
                except ValueError:
                    logger.warning(f"Could not parse metric: {line}")
        
        return metrics
    
    def _safe_json_parse(self, json_string: str, default: Any) -> Any:
        """Safely parse JSON with fallback to default."""
        try:
            if not json_string or not json_string.strip():
                return default
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}")
            return default
    
    def _parse_quote_inventory(self, json_string: str) -> List[QuoteEvidence]:
        """Parse quote inventory JSON into list of QuoteEvidence."""
        try:
            if not json_string or not json_string.strip():
                return []
            
            data = json.loads(json_string)
            if isinstance(data, dict) and 'quotes' in data:
                # Handle format: {"quotes": [...]}
                quotes_data = data['quotes']
            elif isinstance(data, list):
                # Handle format: [...]
                quotes_data = data
            else:
                logger.warning("Unexpected quote inventory format")
                return []
            
            # Convert to QuoteEvidence objects
            quotes = []
            for q in quotes_data:
                try:
                    quotes.append(QuoteEvidence(**q))
                except Exception as e:
                    logger.warning(f"Failed to parse quote: {e}")
            
            return quotes
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse quote inventory JSON: {e}")
            return []
    
    def export_csv_files(self, result: EnhancedResult, output_dir: Path):
        """Export all CSV files with full traceability."""
        import csv
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export each table
        tables = {
            'themes.csv': result.csv_export_data.themes_table,
            'codes.csv': result.csv_export_data.codes_table,
            'quotes.csv': result.csv_export_data.quotes_table,
            'quote_chains.csv': result.csv_export_data.quote_chains_table,
            'contradictions.csv': result.csv_export_data.contradictions_table,
            'stakeholder_positions.csv': result.csv_export_data.stakeholder_positions_table,
            'saturation_curve.csv': result.csv_export_data.saturation_curve_table,
            'traceability_matrix.csv': result.csv_export_data.traceability_matrix
        }
        
        for filename, data in tables.items():
            if data:
                file_path = output_dir / filename
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    if data:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
                logger.info(f"Exported {filename} with {len(data)} rows")
    
    def export_markdown_report(self, result: EnhancedResult, output_path: Path):
        """Export the markdown report."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result.markdown_report)
        
        logger.info(f"Exported markdown report to {output_path}")
    
    def export_json_backup(self, result: EnhancedResult, output_path: Path):
        """Export complete analysis as JSON for backup/portability."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result.model_dump(), f, indent=2, default=str)
        
        logger.info(f"Exported JSON backup to {output_path}")


async def test_with_sample():
    """Test with a small sample of interviews."""
    analyzer = GlobalQualitativeAnalyzer()
    
    # Test with 10 interviews first
    logger.info("Testing with 10 interviews...")
    result = await analyzer.analyze_global(sample_size=10)
    
    # Basic quality checks
    assert len(result.global_analysis.themes) > 0, "No themes found"
    assert len(result.global_analysis.codes) > 0, "No codes found"
    assert result.global_analysis.confidence_scores is not None, "No confidence scores"
    
    # Check traceability
    assert result.traceability_completeness > 0.7, "Low traceability"
    assert len(result.csv_export_data.quotes_table) > 0, "No quotes exported"
    
    logger.info(f"Found {len(result.global_analysis.themes)} themes")
    logger.info(f"Found {len(result.global_analysis.codes)} codes")
    logger.info(f"Traceability: {result.traceability_completeness:.1%}")
    
    # Export sample results
    output_dir = project_root / "output" / "global_analysis_sample"
    analyzer.export_csv_files(result, output_dir / "csv")
    analyzer.export_markdown_report(result, output_dir / "report.md")
    analyzer.export_json_backup(result, output_dir / "complete_analysis.json")
    
    return result


async def analyze_full_dataset():
    """Analyze all 103 interviews."""
    analyzer = GlobalQualitativeAnalyzer()
    
    logger.info("Analyzing all 103 interviews...")
    result = await analyzer.analyze_global()
    
    # Export full results
    output_dir = project_root / "output" / "global_analysis_full"
    analyzer.export_csv_files(result, output_dir / "csv")
    analyzer.export_markdown_report(result, output_dir / "report.md")
    analyzer.export_json_backup(result, output_dir / "complete_analysis.json")
    
    # Print summary
    print(f"\n=== GLOBAL ANALYSIS COMPLETE ===")
    print(f"Interviews analyzed: {result.global_analysis.interviews_analyzed}")
    print(f"Themes found: {len(result.global_analysis.themes)}")
    print(f"Codes identified: {len(result.global_analysis.codes)}")
    print(f"Quote chains: {len(result.global_analysis.quote_chains)}")
    print(f"Contradictions: {len(result.global_analysis.contradictions)}")
    print(f"Saturation point: Interview {result.global_analysis.saturation_assessment.interview_number}")
    print(f"Processing time: {result.global_analysis.processing_metadata['processing_time_seconds']:.1f}s")
    print(f"LLM calls used: {result.global_analysis.processing_metadata['llm_calls']}")
    
    return result


if __name__ == "__main__":
    # Run sample test
    asyncio.run(test_with_sample())