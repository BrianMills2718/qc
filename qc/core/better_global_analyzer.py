"""
Better implementation of global analyzer with programmatic CSV generation
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
from qc.core.enhanced_logging import llm_logger
from qc.core.programmatic_csv_generator import CSVGenerator
from qc.core.error_recovery import DataFixer, RetryHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BetterGlobalAnalyzer:
    """
    Improved analyzer with better second call and programmatic CSV generation.
    """
    
    def __init__(self, research_question: str = None):
        """Initialize the analyzer."""
        self.docx_parser = DOCXParser()
        self.token_counter = TokenCounter()
        self.gemini_client = SimpleGeminiClient()
        self.csv_generator = CSVGenerator()
        self.data_fixer = DataFixer()
        self.retry_handler = RetryHandler(max_retries=3, base_delay=2.0)
        
        self.research_question = research_question or os.getenv(
            'RESEARCH_QUESTION',
            'How are AI methods being integrated into qualitative research practices?'
        )
        
        # Make interview directory configurable
        interviews_dir = os.getenv('INTERVIEWS_DIR')
        if not interviews_dir:
            # Default to AI interviews
            interviews_dir = str(project_root / "data" / "interviews" / "AI_Interviews_all_2025.0728" / "Interviews")
        
        self.interview_files = find_all_interview_files(Path(interviews_dir))
        logger.info(f"Found {len(self.interview_files)} interview files in {interviews_dir}")
        
    async def analyze_global(self, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Perform global analysis on all interviews with better approach.
        
        Args:
            sample_size: Optional number of interviews to analyze (for testing)
            
        Returns:
            Dict with analysis results and generated CSVs
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
        call_id = "comprehensive_analysis"
        call1_start = llm_logger.log_call_start(call_id, self.research_question, {
            "max_output_tokens": 60000,
            "temperature": 0.3
        })
        
        global_result = await self._comprehensive_global_analysis(
            all_interviews_text, 
            len(files_to_analyze),
            total_tokens
        )
        
        llm_logger.log_call_end(call_id, call1_start, global_result)
        logger.info(f"Call 1 complete: {len(global_result.themes)} themes, {len(global_result.codes)} codes")
        
        # Call 2: Extract real quotes from interviews
        logger.info("Extracting traceable quotes (Call 2)...")
        call_id = "quote_extraction"
        call2_start = llm_logger.log_call_start(call_id, "Quote extraction", {
            "max_output_tokens": 20000,
            "temperature": 0.1
        })
        
        # Try the new simple approach first
        try:
            quote_inventory = await self._extract_quotes_simple(
                global_result,
                all_interviews_text,
                metadata
            )
        except Exception as e:
            logger.warning(f"Simple extraction failed: {e}, falling back to original method")
            quote_inventory = await self._extract_traceable_quotes(
                global_result,
                all_interviews_text,
                metadata
            )
        
        llm_logger.log_call_end(call_id, call2_start, quote_inventory)
        logger.info(f"Call 2 complete: {len(quote_inventory)} quotes extracted")
        
        # Generate CSVs programmatically
        analysis_data = {
            'themes': [t.model_dump() for t in global_result.themes],
            'codes': [c.model_dump() for c in global_result.codes],
            'complete_quote_inventory': quote_inventory,
            'quote_chains': [qc.model_dump() for qc in global_result.quote_chains],
            'saturation_assessment': global_result.saturation_assessment.model_dump(),
            'contradictions': [cont.model_dump() for cont in global_result.contradictions],
            'stakeholder_positions': self._extract_stakeholder_positions(global_result)
        }
        
        csvs = self._generate_all_csvs(analysis_data, global_result)
        
        # Add processing metadata
        processing_time = time.time() - start_time
        
        result = {
            'global_analysis': global_result,
            'quote_inventory': quote_inventory,
            'csv_files': csvs,
            'metadata': {
                'processing_time_seconds': processing_time,
                'interviews_analyzed': len(files_to_analyze),
                'total_tokens': total_tokens,
                'llm_calls': 2,
                'model': self.gemini_client.model_name
            }
        }
        
        logger.info(f"Analysis complete in {processing_time:.1f} seconds")
        
        return result
    
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

2.5 **CREATE HIERARCHICAL CODE STRUCTURE** - organize codes into parent-child relationships
   - Identify broad parent codes (e.g., "AI Applications", "Challenges", "Opportunities")
   - Create sub-codes under each parent (e.g., under "AI Applications": "Transcription", "Coding", "Analysis")
   - Where relevant, create sub-sub-codes for even more specific concepts
   - Use hierarchy_level: 0 for top-level, 1 for sub-codes, 2 for sub-sub-codes
   - Set parent_code_id to link child codes to their parents

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
   - Find disagreements on key issues (e.g., "AI will replace researchers" vs "AI augments researchers")
   - Identify WHO holds each position (names and roles)
   - Provide exact quotes supporting BOTH sides
   - Note any suggested resolutions or middle ground
   - Link contradictions to relevant themes and codes

6. **MAP STAKEHOLDER POSITIONS** - who says what about which topics
   - Identify stakeholder types: researchers, management, clients, IT staff, etc.
   - Summarize each stakeholder's overall position on AI in research
   - Extract their main concerns and recommendations
   - Provide supporting quotes for their positions
   - Note their perceived influence level

RESEARCH QUESTION: {self.research_question}

INTERVIEW FORMAT NOTE:
The interviews come in two formats:
1. **Transcript format**: Has clear speaker labels (e.g., "Interviewer:", "Participant:", "John Smith:")
2. **Notes format**: Interview notes without speaker labels, just narrative descriptions

For quotes:
- From transcripts: Include speaker name when available (e.g., "Sara McCleskey: 'quote'")
- From notes: Use descriptive attribution (e.g., "Nigerian Army representative: 'quote'" or "Archivist (Cot d'Ivoire): 'quote'")
- Always include interview number (e.g., "Interview 001", "Interview 018")

METHODOLOGICAL INSTRUCTIONS:
- Apply grounded theory principles but leverage your global perspective
- Create codes that capture meaning across ALL interviews regardless of format
- Build themes hierarchically (themes → categories → codes)
- For EVERY code and theme, provide specific quote evidence with interview numbers
- Track which interviews support each finding
- Adapt quote extraction to the format (transcript vs notes)
- Assess when theoretical saturation naturally occurred in the sequence
- Note code frequency and distribution across interviews
- Identify quote chains that show conceptual development
- Map contradictions with evidence from both perspectives

CRITICAL: Ensure every finding is traceable to specific interviews and quotes.

ALL {interview_count} INTERVIEWS:
{all_interviews}

Return a SimpleGlobalResult with the following structure:
- themes: List of themes with theme_id, name, description, prevalence (MUST be a decimal number between 0.0 and 1.0, e.g., 0.8 for 80%), interviews_count, key_quotes (as strings), confidence_score (0.0-1.0)
- codes: List of codes with code_id, name, definition, frequency, interviews_present, first_appearance, theme_id (the ID of the theme this code belongs to), parent_code_id (if this is a sub-code), hierarchy_level (0=top-level, 1=sub-code, 2=sub-sub-code)
- quote_chains: List of chains with chain_id, theme_id, chain_type (MUST be one of: "evolution", "contradiction", "consensus_building", "problem_solution" - use underscores NOT hyphens), description, quotes (as ordered list of quote strings)
- contradictions: List of contradictions with:
  - contradiction_id (e.g., "CONT_001")
  - topic (what the disagreement is about)
  - position_1 (first viewpoint)
  - position_1_holders (list of names/roles who hold this view)
  - position_1_quotes (2-3 quotes supporting this position)
  - position_2 (opposing viewpoint)
  - position_2_holders (list of names/roles who hold this view)
  - position_2_quotes (2-3 quotes supporting this position)
  - resolution_notes (any middle ground or resolution suggested)
  - theme_ids (which themes this relates to)
  - code_ids (which codes this relates to)
- stakeholder_positions: List of key stakeholders with:
  - stakeholder_id (e.g., "STAKE_001")
  - stakeholder_name (person or group name)
  - stakeholder_type (researcher, management, client, etc.)
  - position_summary (their overall stance on AI in research)
  - main_quotes (2-3 key quotes expressing their position)
  - concerns (list of their main concerns)
  - recommendations (list of what they recommend)

IMPORTANT: 
1. Every code MUST be assigned to exactly one theme. Set the theme_id field in each code to match the theme_id of the theme it belongs to.
2. Create a hierarchical code structure. Top-level codes should have parent_code_id=null and hierarchy_level=0. Sub-codes should reference their parent's code_id and have hierarchy_level=1. Sub-sub-codes should have hierarchy_level=2.
3. Example hierarchy:
   - "AI_Applications" (parent_code_id=null, hierarchy_level=0)
     - "AI_Qual_Analysis" (parent_code_id="AI_Applications", hierarchy_level=1)
       - "AI_Transcription" (parent_code_id="AI_Qual_Analysis", hierarchy_level=2)
       - "AI_Coding" (parent_code_id="AI_Qual_Analysis", hierarchy_level=2)
4. Look for contradictions across the entire dataset - when different people express opposing views on the same topic.
5. Identify key stakeholders and summarize their positions based on their quotes throughout the interviews.
- theoretical_insights: List of key theoretical discoveries
- emergent_theory: Main theoretical contribution (single paragraph)
- methodological_notes: Notes on the analysis process
- saturation_point: Interview ID where saturation was reached
- saturation_evidence: Explanation of why saturation occurred at that point
- overall_confidence: Float between 0.0 and 1.0

Keep it simple and focused on the core findings."""

        # Configure for structured output with simplified schema
        generation_config = {
            'temperature': 0.0,
            'max_output_tokens': 60000,
            'response_mime_type': 'application/json',
            'response_schema': SimpleGlobalResult  # Use simplified schema
        }
        
        try:
            response = await self.retry_handler.retry_with_backoff(
                self.gemini_client.extract_themes,
                prompt,
                generation_config=generation_config
            )
            
            # Parse the JSON response
            if isinstance(response, dict):
                # Fix any missing fields
                fixed_response = self.data_fixer.fix_response_data(response)
                
                # Create SimpleGlobalResult from fixed response
                simple_result = SimpleGlobalResult(**fixed_response)
                
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
                
        except Exception as e:
            logger.error(f"Error in global analysis: {str(e)}")
            raise
    
    async def _extract_traceable_quotes(
        self,
        initial_result: GlobalCodingResult,
        all_interviews: str,
        metadata: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract quotes using parallel theme-specific calls."""
        
        logger.info("Starting parallel quote extraction for themes")
        
        # Split interviews into chunks for easier processing
        interview_chunks = self._split_interviews_by_markers(all_interviews)
        logger.info(f"Split interviews into {len(interview_chunks)} chunks")
        
        # Extract quotes for each theme in parallel
        import asyncio
        
        async def extract_quotes_for_theme(theme, theme_index):
            """Extract quotes for a single theme."""
            # Get related codes for this theme
            theme_codes = [c for c in initial_result.codes if c.theme_id == theme.theme_id][:5]
            
            # Sample 3-5 interview chunks for this theme
            import random
            sampled_chunks = random.sample(interview_chunks, min(5, len(interview_chunks)))
            combined_sample = '\n\n'.join(sampled_chunks[:3])[:80000]  # Max 80K chars per call
            
            prompt = f"""Find 5 EXACT quotes that demonstrate this specific theme.

THEME TO FIND: {theme.name}
DESCRIPTION: {theme.description}
RELATED CONCEPTS: {', '.join([c.name for c in theme_codes[:3]])}

INSTRUCTIONS:
1. Find EXACT quotes (word-for-word) from the interviews
2. Each quote should be 30-120 words
3. Include speaker name if mentioned
4. Include interview number (e.g., "Interview 001", "INT_001")

INTERVIEW EXCERPTS:
{combined_sample}

Return JSON with exactly this structure:
{{
  "quotes": [
    {{
      "quote_id": "T{theme_index:03d}_Q1",
      "text": "exact quote text here",
      "speaker": "Speaker Name or 'Participant'",
      "interview_id": "INT_001",
      "theme_ids": ["{theme.theme_id}"],
      "code_ids": ["{theme_codes[0].code_id if theme_codes else ''}"]
    }}
  ]
}}"""
            
            config = {
                'temperature': 0.1,
                'max_output_tokens': 5000,
                'response_mime_type': 'application/json'
            }
            
            try:
                response = await self.gemini_client.extract_themes(prompt, config)
                if isinstance(response, dict) and 'quotes' in response:
                    quotes = response.get('quotes', [])
                    # Clean and validate quotes
                    cleaned = []
                    for q in quotes[:5]:  # Max 5 per theme
                        if 'text' in q and 'quote_id' in q:
                            # Clean text
                            text = q['text'].replace('\n', ' ').replace('\r', ' ')
                            text = text.replace('"', "'").replace('"', "'").replace('"', "'")
                            text = text.replace('…', '...').replace('–', '-').replace('—', '-')
                            text = ''.join(c for c in text if ord(c) >= 32 or c == '\t')
                            if len(text) > 300:
                                text = text[:297] + '...'
                            
                            q['text'] = text.strip()
                            q['theme_ids'] = [theme.theme_id]
                            q['code_ids'] = [c.code_id for c in theme_codes[:2]]
                            q['speaker_role'] = q.get('speaker', 'Participant')
                            q['interview_id'] = q.get('interview_id', 'INT_001')
                            cleaned.append(q)
                    
                    logger.info(f"Extracted {len(cleaned)} quotes for theme {theme.theme_id}")
                    return cleaned
                else:
                    logger.warning(f"No quotes found for theme {theme.theme_id}")
                    return []
            except Exception as e:
                logger.error(f"Error extracting quotes for theme {theme.theme_id}: {e}")
                return []
        
        # Run parallel extraction for all themes
        tasks = []
        for i, theme in enumerate(initial_result.themes[:5]):  # Max 5 themes
            tasks.append(extract_quotes_for_theme(theme, i + 1))
        
        # Wait for all extractions to complete
        quote_lists = await asyncio.gather(*tasks)
        
        # Flatten results
        all_quotes = []
        for quotes in quote_lists:
            all_quotes.extend(quotes)
        
        logger.info(f"Total quotes extracted: {len(all_quotes)}")
        
        # If still no quotes, use fallback
        if len(all_quotes) == 0:
            logger.warning("No quotes extracted, using interview sampling fallback")
            all_quotes = await self._fallback_quote_extraction(initial_result, interview_chunks)
        
        return all_quotes
    
    def _split_interviews_by_markers(self, text: str) -> List[str]:
        """Split interviews into chunks based on interview markers."""
        chunks = []
        
        # Common interview markers
        markers = ['Interview ', 'INT_', 'Participant:', 'Interviewer:', '---', '***']
        
        # Try to split by "Interview " marker first
        parts = text.split('Interview ')
        
        if len(parts) > 1:
            for i, part in enumerate(parts[1:], 1):
                # Keep interview number
                chunk = f"Interview {part[:1000]}"  # First 1000 chars of each interview
                if len(chunk) > 100:  # Minimum viable chunk
                    chunks.append(chunk)
        else:
            # Fallback: split by size
            chunk_size = 50000
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i + chunk_size]
                if len(chunk) > 100:
                    chunks.append(chunk)
        
        return chunks[:20]  # Max 20 chunks
    
    async def _fallback_quote_extraction(self, initial_result: GlobalCodingResult, 
                                       interview_chunks: List[str]) -> List[Dict[str, Any]]:
        """Fallback method to extract at least some quotes."""
        logger.info("Using fallback quote extraction")
        
        # Take first 3 chunks
        sample = '\n\n'.join(interview_chunks[:3])[:40000]
        
        prompt = f"""Find 10 meaningful quotes about AI and research methods from these interviews.

INSTRUCTIONS:
1. Find EXACT quotes about AI, methods, challenges, or future
2. Each quote should be 30-100 words
3. Include any speaker names mentioned

INTERVIEWS:
{sample}

Return simple JSON:
{{
  "quotes": [
    {{
      "quote_id": "Q1",
      "text": "exact quote",
      "speaker": "name or Participant", 
      "topic": "what it's about"
    }}
  ]
}}"""
        
        config = {
            'temperature': 0.2,
            'max_output_tokens': 3000,
            'response_mime_type': 'application/json'
        }
        
        try:
            response = await self.gemini_client.extract_themes(prompt, config)
            if isinstance(response, dict) and 'quotes' in response:
                quotes = []
                for i, q in enumerate(response.get('quotes', [])[:10]):
                    if 'text' in q:
                        # Map topic to themes
                        topic = q.get('topic', '').lower()
                        theme_id = initial_result.themes[0].theme_id  # Default
                        
                        if 'challenge' in topic or 'problem' in topic:
                            theme_id = next((t.theme_id for t in initial_result.themes if 'challenge' in t.name.lower()), theme_id)
                        elif 'future' in topic:
                            theme_id = next((t.theme_id for t in initial_result.themes if 'future' in t.name.lower()), theme_id)
                        
                        quotes.append({
                            'quote_id': f'FB_Q{i+1:03d}',
                            'text': q['text'][:300],
                            'speaker_role': q.get('speaker', 'Participant'),
                            'interview_id': 'Multiple',
                            'theme_ids': [theme_id],
                            'code_ids': [],
                            'context': 'Fallback extraction',
                            'confidence': 0.7
                        })
                
                return quotes
            else:
                return []
        except Exception as e:
            logger.error(f"Fallback extraction failed: {e}")
            return []
    
    async def _extract_quotes_simple(
        self,
        initial_result: GlobalCodingResult,
        all_interviews: str,
        metadata: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract quotes using simplified text generation approach."""
        
        # Use module-level logger explicitly to avoid scope issues
        import logging
        method_logger = logging.getLogger(__name__)
        method_logger.info("Starting simplified quote extraction")
        all_quotes = []
        
        # Create interview sections
        interview_sections = self._create_interview_sections(all_interviews)
        method_logger.info(f"Created {len(interview_sections)} interview sections")
        
        # For each theme, extract quotes from relevant sections
        for theme_idx, theme in enumerate(initial_result.themes[:5]):
            method_logger.info(f"Extracting quotes for theme: {theme.name}")
            
            # Select relevant sections
            selected_sections = self._select_relevant_sections(
                interview_sections, 
                theme.name, 
                theme.description
            )
            
            theme_quotes = []
            for section_idx, section in enumerate(selected_sections[:2]):  # Max 2 sections per theme
                # Simple focused prompt
                prompt = f"""Find 2 quotes about: {theme.name}

Look for mentions of: {theme.description.split('.')[0]}

In this interview section:
---
{section[:25000]}
---

List exactly 2 quotes:

1. "[exact quote text]" - Speaker: [name or Participant]
2. "[exact quote text]" - Speaker: [name or Participant]"""

                try:
                    response = await self.gemini_client.generate_text(
                        prompt,
                        temperature=0.1,
                        max_tokens=1000
                    )
                    
                    # Parse the response
                    section_quotes = self._parse_simple_quote_response(
                        response, 
                        theme, 
                        f"S{section_idx}",
                        theme_idx + 1
                    )
                    theme_quotes.extend(section_quotes)
                    
                except Exception as e:
                    method_logger.warning(f"Failed to extract quotes for theme {theme.theme_id}: {e}")
                    continue
            
            # Ensure at least 1 quote per theme
            if len(theme_quotes) == 0:
                fallback_quote = {
                    'quote_id': f'T{theme_idx+1:03d}_FB',
                    'text': f'[Quote extraction failed for {theme.name} - see full analysis for themes]',
                    'speaker_role': 'System',
                    'interview_id': 'Multiple',
                    'theme_ids': [theme.theme_id],
                    'code_ids': [],
                    'context': 'Fallback placeholder',
                    'confidence': 0.0
                }
                theme_quotes.append(fallback_quote)
            
            all_quotes.extend(theme_quotes[:3])  # Max 3 per theme
        
        method_logger.info(f"Total quotes extracted: {len(all_quotes)}")
        return all_quotes
    
    def _create_interview_sections(self, text: str) -> List[str]:
        """Split interviews into meaningful sections."""
        sections = []
        
        # Split by Interview markers
        if "Interview " in text:
            parts = text.split("Interview ")
            for i, part in enumerate(parts[1:], 1):
                if len(part) > 500:
                    # Take meaningful chunks from each interview
                    section = f"Interview {i:03d}: {part[:8000]}"
                    sections.append(section)
        
        # Also try splitting by common markers if needed
        if len(sections) < 10:
            markers = ["Interviewer:", "Participant:", "Q:", "A:"]
            for marker in markers:
                if marker in text:
                    parts = text.split(marker)
                    for j, part in enumerate(parts[1:4]):  # Take first few
                        if len(part) > 300:
                            section = f"{marker} {part[:5000]}"
                            sections.append(section)
                    break
        
        return sections[:15]  # Max 15 sections
    
    def _select_relevant_sections(self, sections: List[str], theme_name: str, theme_desc: str) -> List[str]:
        """Select sections most likely to contain relevant quotes."""
        if not sections:
            return []
            
        # Simple scoring based on keyword presence
        keywords = theme_name.lower().replace("_", " ").split()
        keywords.extend(theme_desc.lower().split()[:5])
        
        scored_sections = []
        for section in sections:
            section_lower = section.lower()
            score = sum(1 for kw in keywords if kw in section_lower)
            scored_sections.append((score, section))
        
        # Sort by relevance and return top sections
        scored_sections.sort(key=lambda x: x[0], reverse=True)
        return [section for score, section in scored_sections[:5] if score > 0]
    
    def _parse_simple_quote_response(self, response_text: str, theme, section_id: str, theme_num: int) -> List[Dict[str, Any]]:
        """Parse quotes from simple text response."""
        quotes = []
        if not response_text:
            return quotes
            
        lines = response_text.split('\n')
        quote_count = 0
        
        for line in lines:
            # Look for quotes in format: "text" - Speaker: name
            if '"' in line and len(line.strip()) > 30:
                import re
                
                # Try to extract quote and speaker
                quote_match = re.search(r'"([^"]+)"', line)
                speaker_match = re.search(r'Speaker:\s*([^,\n]+)', line)
                
                if quote_match:
                    quote_text = quote_match.group(1).strip()
                    speaker = speaker_match.group(1).strip() if speaker_match else 'Participant'
                    
                    if len(quote_text) > 20:  # Meaningful quote
                        quote_count += 1
                        quotes.append({
                            'quote_id': f'T{theme_num:03d}_{section_id}_Q{quote_count}',
                            'text': quote_text[:300],  # Limit length
                            'speaker_role': speaker,
                            'interview_id': f'INT_{section_id}',
                            'theme_ids': [theme.theme_id],
                            'code_ids': [],
                            'context': f'About {theme.name}',
                            'confidence': 0.8
                        })
                        
                        if quote_count >= 2:  # Max 2 per section
                            break
        
        return quotes
    
    def _generate_all_csvs(self, analysis_data: Dict[str, Any], 
                          global_result: GlobalCodingResult) -> Dict[str, str]:
        """Generate all CSV files programmatically."""
        csvs = self.csv_generator.generate_all_csvs(analysis_data)
        
        # Add additional CSVs
        csvs['quote_chains.csv'] = self._generate_quote_chains_csv(
            analysis_data.get('quote_chains', [])
        )
        
        csvs['saturation_analysis.csv'] = self._generate_saturation_csv(
            analysis_data.get('saturation_assessment', {})
        )
        
        return csvs
    
    def _generate_quote_chains_csv(self, quote_chains: List[Dict[str, Any]]) -> str:
        """Generate quote chains CSV."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'chain_id', 'theme_id', 'chain_type', 'description', 'quote_count'
        ])
        writer.writeheader()
        
        for chain in quote_chains:
            writer.writerow({
                'chain_id': chain.get('chain_id'),
                'theme_id': chain.get('theme_id'),
                'chain_type': chain.get('chain_type'),
                'description': chain.get('description'),
                'quote_count': len(chain.get('quotes', []))
            })
        
        return output.getvalue()
    
    def _extract_stakeholder_positions(self, global_result: GlobalCodingResult) -> List[Dict[str, Any]]:
        """Extract stakeholder positions from the analysis."""
        # For now, return empty list as stakeholder extraction would need 
        # a more complex implementation or separate analysis
        # This could be enhanced to extract from contradictions and quotes
        return []
    
    def _generate_saturation_csv(self, saturation: Dict[str, Any]) -> str:
        """Generate saturation analysis CSV."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Saturation Analysis'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Saturation Point', saturation.get('saturation_point', '')])
        writer.writerow(['Interview Number', saturation.get('interview_number', '')])
        writer.writerow(['Evidence', saturation.get('evidence', '')])
        
        return output.getvalue()
    
    def export_results(self, result: Dict[str, Any], output_dir: Path):
        """Export all results to disk."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save CSVs
        self.csv_generator.save_csvs_to_disk(result['csv_files'], output_dir)
        
        # Save quote inventory
        with open(output_dir / 'quote_inventory.json', 'w', encoding='utf-8') as f:
            json.dump(result['quote_inventory'], f, indent=2)
        
        # Save full analysis
        analysis_dict = result['global_analysis'].model_dump()
        with open(output_dir / 'full_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(analysis_dict, f, indent=2, default=str)
        
        # Save metadata
        with open(output_dir / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump(result['metadata'], f, indent=2)
        
        logger.info(f"Exported all results to {output_dir}")


async def test_better_analyzer():
    """Test the better analyzer implementation."""
    analyzer = BetterGlobalAnalyzer()
    
    # Test with 3 interviews first
    logger.info("Testing with 3 interviews...")
    result = await analyzer.analyze_global(sample_size=3)
    
    # Export results
    output_dir = project_root / "output" / "better_analyzer_test"
    analyzer.export_results(result, output_dir)
    
    # Print summary
    print(f"\n=== ANALYSIS COMPLETE ===")
    print(f"Interviews analyzed: {result['metadata']['interviews_analyzed']}")
    print(f"Themes found: {len(result['global_analysis'].themes)}")
    print(f"Codes identified: {len(result['global_analysis'].codes)}")
    print(f"Quotes extracted: {len(result['quote_inventory'])}")
    print(f"Processing time: {result['metadata']['processing_time_seconds']:.1f}s")
    print(f"\nResults exported to: {output_dir}")
    
    return result


if __name__ == "__main__":
    asyncio.run(test_better_analyzer())