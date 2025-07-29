#!/usr/bin/env python3
"""
TRUE Qualitative Coding Extractor using Gemini 2.5 Flash

This implements ACTUAL qualitative coding methodology:
- Hierarchical thematic analysis
- Code development from data (grounded theory)
- Analytical memos
- Theoretical development

NOT just entity extraction!
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import uuid

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from .simple_gemini_client import StructuredLogger, SimpleGeminiExtractor


logger = StructuredLogger(__name__)


# ============= Proper Qualitative Coding Models =============

class CodedSegment(BaseModel):
    """A single coded segment from the transcript"""
    quote: str = Field(description="The exact quote from the transcript")
    line_start: int = Field(description="Starting line number")
    line_end: int = Field(description="Ending line number")
    speaker: Optional[str] = Field(default=None, description="Who said this")
    memo: str = Field(description="Analytical memo - why this code was applied")
    

class Code(BaseModel):
    """A single code with its properties"""
    name: str = Field(description="Code name (use underscores, no spaces)")
    definition: str = Field(description="Clear definition of what this code represents")
    segments: List[CodedSegment] = Field(description="All segments coded with this")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Code properties (conditions, consequences, etc)")
    

class CodeCategory(BaseModel):
    """A category grouping related codes"""
    name: str = Field(description="Category name")
    definition: str = Field(description="What this category represents")
    codes: List[Code] = Field(description="Codes within this category")
    memo: str = Field(description="Analytical memo about this category")
    relationships: List[str] = Field(default_factory=list, description="Related categories")
    

class Theme(BaseModel):
    """A major theme containing categories"""
    name: str = Field(description="Theme name")
    definition: str = Field(description="Theoretical definition of this theme")
    categories: List[CodeCategory] = Field(description="Categories within this theme")
    theoretical_memo: str = Field(description="Theoretical insights about this theme")
    

class QualitativeCodingResult(BaseModel):
    """Complete qualitative coding analysis result"""
    themes: List[Theme] = Field(description="Major themes with hierarchical structure")
    core_category: Optional[str] = Field(default=None, description="The central phenomenon (selective coding)")
    theoretical_insights: List[str] = Field(description="Key theoretical insights from the analysis")
    saturation_notes: str = Field(description="Notes on theoretical saturation")
    total_segments_coded: int = Field(description="Total number of segments coded")
    total_unique_codes: int = Field(description="Total number of unique codes")


# ============= Qualitative Coding Prompts =============

OPEN_CODING_PROMPT = """
Perform QUALITATIVE CODING analysis on this interview transcript.

You are an expert qualitative researcher using grounded theory methodology.

IMPORTANT: This is NOT entity extraction! Focus on MEANING, PATTERNS, and THEMES.

STEP 1 - OPEN CODING:
1. Read the entire transcript carefully
2. Identify meaningful segments that relate to experiences, feelings, challenges, strategies
3. Assign descriptive codes to these segments
4. Write analytical memos explaining WHY each code was applied

For each coded segment:
- Extract the EXACT quote
- Note line numbers (count lines starting from 1)
- Create a descriptive code name
- Write a clear definition
- Add an analytical memo (your interpretation)

STEP 2 - CATEGORIZATION:
Group related codes into categories based on:
- Similar concepts
- Related phenomena  
- Shared properties
- Common themes

STEP 3 - THEME DEVELOPMENT:
Identify major themes that encompass multiple categories.
Themes should represent larger theoretical concepts.

FOCUS ON:
- Experiences and emotions
- Challenges and barriers
- Strategies and solutions
- Changes over time
- Relationships and interactions
- Contradictions and tensions

Research Question: {research_question}

Transcript:
{transcript}

Output JSON matching the QualitativeCodingResult schema.
Remember: Build theory from the data, don't just extract mentioned things!
"""

AXIAL_CODING_PROMPT = """
Perform AXIAL CODING on these open codes to find relationships and build categories.

You have these initial codes from open coding:
{open_codes}

Now:
1. Group related codes into substantive categories
2. Identify properties and dimensions of each category
3. Find relationships between categories (causal, contextual, intervening)
4. Develop each category with:
   - Conditions (what leads to it)
   - Consequences (what results from it)
   - Strategies (how people deal with it)

Build a hierarchical structure showing how codes relate to form broader categories and themes.

Output refined categories with clear relationships and properties.
"""

SELECTIVE_CODING_PROMPT = """
Perform SELECTIVE CODING to identify the CORE CATEGORY.

Based on this coding analysis:
{coding_analysis}

Identify:
1. The CENTRAL phenomenon that ties everything together
2. How all other categories relate to this core category
3. The overall theoretical story the data tells
4. Key theoretical insights

The core category should:
- Appear frequently in the data
- Connect to most other categories
- Have explanatory power
- Be sufficiently abstract

Provide a theoretical model explaining the core phenomenon.
"""


class QualitativeCodingExtractor(SimpleGeminiExtractor):
    """
    Proper qualitative coding extractor that focuses on thematic analysis,
    not entity extraction.
    """
    
    def __init__(self, debug_dir: Optional[Path] = None):
        """Initialize with qualitative coding focus"""
        super().__init__(debug_dir)
        
        # QC-specific directories
        self.memos_dir = self.debug_dir / 'memos'
        self.memos_dir.mkdir(exist_ok=True)
        
        self.codebooks_dir = self.debug_dir / 'codebooks'
        self.codebooks_dir.mkdir(exist_ok=True)
        
        logger.log('info', 'Initialized QualitativeCodingExtractor',
                  model=self.model_name,
                  focus='thematic_analysis')
    
    async def perform_qualitative_coding(
        self,
        transcript: str,
        research_question: str = "What are the key themes and patterns in this interview?",
        interview_id: Optional[str] = None,
        existing_codebook: Optional[Dict] = None
    ) -> QualitativeCodingResult:
        """
        Perform proper qualitative coding analysis.
        
        This is TRUE qualitative coding:
        - Identifies patterns of meaning
        - Develops hierarchical code structure
        - Creates analytical memos
        - Builds theory from data
        
        Args:
            transcript: Interview transcript text
            research_question: The research question guiding analysis
            interview_id: Identifier for tracking
            existing_codebook: Optional existing codes to apply/extend
            
        Returns:
            Hierarchical thematic analysis with codes, categories, and themes
        """
        trace_id = str(uuid.uuid4())
        interview_id = interview_id or f"qc_{trace_id[:8]}"
        
        logger.log('info', 'qualitative_coding_started',
                  trace_id=trace_id,
                  interview_id=interview_id,
                  research_question=research_question,
                  has_existing_codebook=existing_codebook is not None)
        
        # Build the QC-focused prompt
        prompt = OPEN_CODING_PROMPT.format(
            research_question=research_question,
            transcript=transcript
        )
        
        # If we have an existing codebook, add it to context
        if existing_codebook:
            prompt += f"\n\nExisting Codebook for reference:\n{json.dumps(existing_codebook, indent=2)}"
            prompt += "\n\nYou may use existing codes where appropriate, but also create new codes as needed."
        
        try:
            # Perform the qualitative coding
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.4,  # Slightly higher for interpretive work
                    max_output_tokens=self.generation_config.max_output_tokens,
                    response_mime_type='application/json',
                    response_schema=QualitativeCodingResult
                )
            )
            
            # Save the coding results
            coding_file = self.debug_dir / f"{interview_id}_coding_{trace_id}.json"
            coding_data = {
                'trace_id': trace_id,
                'interview_id': interview_id,
                'research_question': research_question,
                'timestamp': datetime.utcnow().isoformat(),
                'coding_result': response.text,
                'had_existing_codebook': existing_codebook is not None
            }
            coding_file.write_text(json.dumps(coding_data, indent=2), encoding='utf-8')
            
            # Parse result
            if response.parsed:
                result = response.parsed
                
                # Save analytical memos
                self._save_memos(result, interview_id, trace_id)
                
                # Update codebook
                self._update_codebook(result, interview_id)
                
                logger.log('info', 'qualitative_coding_complete',
                          trace_id=trace_id,
                          themes_count=len(result.themes),
                          total_codes=result.total_unique_codes,
                          segments_coded=result.total_segments_coded,
                          core_category=result.core_category)
                
                return result
            else:
                # Manual parsing fallback
                result_dict = json.loads(response.text)
                return QualitativeCodingResult.model_validate(result_dict)
                
        except Exception as e:
            logger.log('error', 'qualitative_coding_failed',
                      trace_id=trace_id,
                      error=str(e),
                      error_type=type(e).__name__)
            raise
    
    def _save_memos(self, result: QualitativeCodingResult, interview_id: str, trace_id: str):
        """Save analytical memos from the coding"""
        memos = []
        
        # Extract all memos
        for theme in result.themes:
            memos.append({
                'type': 'theoretical',
                'level': 'theme',
                'name': theme.name,
                'memo': theme.theoretical_memo
            })
            
            for category in theme.categories:
                memos.append({
                    'type': 'analytical',
                    'level': 'category',
                    'name': category.name,
                    'memo': category.memo
                })
                
                for code in category.codes:
                    for segment in code.segments:
                        memos.append({
                            'type': 'coding',
                            'level': 'segment',
                            'code': code.name,
                            'quote': segment.quote[:100] + '...',
                            'memo': segment.memo
                        })
        
        # Save memos
        memo_file = self.memos_dir / f"{interview_id}_memos_{trace_id}.json"
        memo_file.write_text(json.dumps({
            'interview_id': interview_id,
            'timestamp': datetime.utcnow().isoformat(),
            'memos': memos,
            'theoretical_insights': result.theoretical_insights
        }, indent=2))
    
    def _update_codebook(self, result: QualitativeCodingResult, interview_id: str):
        """Update the evolving codebook"""
        codebook_file = self.codebooks_dir / 'evolving_codebook.json'
        
        # Load existing codebook
        if codebook_file.exists():
            codebook = json.loads(codebook_file.read_text())
        else:
            codebook = {
                'themes': {},
                'categories': {},
                'codes': {},
                'last_updated': None,
                'interviews_coded': []
            }
        
        # Update with new codes
        for theme in result.themes:
            if theme.name not in codebook['themes']:
                codebook['themes'][theme.name] = {
                    'definition': theme.definition,
                    'first_seen': interview_id,
                    'frequency': 0
                }
            codebook['themes'][theme.name]['frequency'] += 1
            
            for category in theme.categories:
                if category.name not in codebook['categories']:
                    codebook['categories'][category.name] = {
                        'definition': category.definition,
                        'parent_theme': theme.name,
                        'first_seen': interview_id,
                        'frequency': 0
                    }
                codebook['categories'][category.name]['frequency'] += 1
                
                for code in category.codes:
                    if code.name not in codebook['codes']:
                        codebook['codes'][code.name] = {
                            'definition': code.definition,
                            'parent_category': category.name,
                            'parent_theme': theme.name,
                            'first_seen': interview_id,
                            'frequency': 0,
                            'example_quotes': []
                        }
                    codebook['codes'][code.name]['frequency'] += len(code.segments)
                    
                    # Add example quotes (max 3 per code)
                    for segment in code.segments[:3]:
                        if segment.quote not in [q['quote'] for q in codebook['codes'][code.name]['example_quotes']]:
                            codebook['codes'][code.name]['example_quotes'].append({
                                'quote': segment.quote,
                                'interview': interview_id
                            })
        
        # Update metadata
        codebook['last_updated'] = datetime.utcnow().isoformat()
        if interview_id not in codebook['interviews_coded']:
            codebook['interviews_coded'].append(interview_id)
        
        # Save updated codebook
        codebook_file.write_text(json.dumps(codebook, indent=2))
        
        logger.log('info', 'codebook_updated',
                  total_themes=len(codebook['themes']),
                  total_categories=len(codebook['categories']),
                  total_codes=len(codebook['codes']),
                  interviews_coded=len(codebook['interviews_coded']))
    
    def get_codebook_summary(self) -> Dict[str, Any]:
        """Get summary of the current codebook"""
        codebook_file = self.codebooks_dir / 'evolving_codebook.json'
        
        if not codebook_file.exists():
            return {"message": "No codebook found yet"}
        
        codebook = json.loads(codebook_file.read_text())
        
        # Calculate saturation indicators
        total_interviews = len(codebook['interviews_coded'])
        
        # Codes that appeared in only one interview might indicate non-saturation
        single_interview_codes = [
            code for code, data in codebook['codes'].items()
            if data['frequency'] == 1
        ]
        
        return {
            'total_interviews_coded': total_interviews,
            'total_themes': len(codebook['themes']),
            'total_categories': len(codebook['categories']),
            'total_codes': len(codebook['codes']),
            'most_frequent_codes': sorted(
                [(code, data['frequency']) for code, data in codebook['codes'].items()],
                key=lambda x: x[1],
                reverse=True
            )[:10],
            'saturation_indicators': {
                'codes_appearing_once': len(single_interview_codes),
                'percentage_saturated': (1 - len(single_interview_codes) / len(codebook['codes'])) * 100 if codebook['codes'] else 0
            },
            'last_updated': codebook['last_updated']
        }


# Example usage
async def demonstrate_qualitative_coding():
    """Demonstrate proper qualitative coding"""
    
    # Sample transcript focused on remote work experiences
    transcript = """
    Interviewer: Can you tell me about your experience transitioning to remote work?
    
    Participant: Oh, it's been quite a journey. At first, I was excited - no commute, 
    work in my pajamas, you know? But after a few weeks, I started feeling really 
    isolated. I missed the energy of the office, those spontaneous conversations by 
    the coffee machine.
    
    Interviewer: How did that isolation affect you?
    
    Participant: I found myself working longer hours because there was no clear 
    boundary between work and home. My laptop was always there, calling to me. 
    I'd check emails at 10 PM, thinking "just one more thing." My partner started 
    getting frustrated because I was always "at work" even though I was home.
    
    The trust issue was huge too. My manager started scheduling more check-ins, 
    which felt like micromanagement. It's like they didn't trust us to work without 
    supervision. That really bothered me because I've always been self-motivated.
    
    Interviewer: How did you handle these challenges?
    
    Participant: I had to create strict boundaries. I set up a dedicated workspace 
    and when I leave that room, work is done. No exceptions. I also started being 
    more intentional about communication - over-communicating really, to show I was 
    engaged and productive.
    
    But you know what? I've also discovered benefits I didn't expect. I'm eating 
    healthier because I can cook lunch. I exercise during what would have been my 
    commute time. And I've gotten really close to my neighbors because we're all 
    home more. It's created this unexpected sense of community.
    
    The whole experience has made me rethink what work means. Is it a place you go 
    or something you do? I'm leaning toward the latter now.
    """
    
    # Research question
    research_question = "How do knowledge workers experience and adapt to remote work?"
    
    # Create extractor
    extractor = QualitativeCodingExtractor()
    
    try:
        # Perform qualitative coding
        result = await extractor.perform_qualitative_coding(
            transcript=transcript,
            research_question=research_question,
            interview_id="remote_work_001"
        )
        
        # Display results
        print("\n=== QUALITATIVE CODING RESULTS ===\n")
        
        print(f"Core Category: {result.core_category or 'To be determined after more interviews'}")
        print(f"Total Segments Coded: {result.total_segments_coded}")
        print(f"Unique Codes: {result.total_unique_codes}")
        
        print("\n=== HIERARCHICAL THEME STRUCTURE ===\n")
        
        for theme in result.themes:
            print(f"\n📌 THEME: {theme.name}")
            print(f"   Definition: {theme.definition}")
            print(f"   Theoretical Memo: {theme.theoretical_memo}")
            
            for category in theme.categories:
                print(f"\n   📁 Category: {category.name}")
                print(f"      Definition: {category.definition}")
                
                for code in category.codes:
                    print(f"\n      📄 Code: {code.name}")
                    print(f"         Definition: {code.definition}")
                    print(f"         Segments: {len(code.segments)}")
                    
                    # Show first segment as example
                    if code.segments:
                        segment = code.segments[0]
                        print(f"         Example: \"{segment.quote[:80]}...\"")
                        print(f"         Memo: {segment.memo}")
        
        print("\n=== THEORETICAL INSIGHTS ===\n")
        for insight in result.theoretical_insights:
            print(f"• {insight}")
        
        print("\n=== SATURATION NOTES ===")
        print(result.saturation_notes)
        
        # Show codebook summary
        print("\n=== CODEBOOK SUMMARY ===")
        summary = extractor.get_codebook_summary()
        print(json.dumps(summary, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demonstrate_qualitative_coding())