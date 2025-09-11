#!/usr/bin/env python3
"""
Analytical Memos Module

LLM-generated analytical insights and theoretical memo generation from qualitative coding data.
Creates structured analytical memos that synthesize patterns, generate theoretical insights,
and connect empirical findings to theoretical frameworks.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MemoType(Enum):
    """Types of analytical memos"""
    PATTERN_ANALYSIS = "pattern_analysis"
    THEORETICAL_MEMO = "theoretical_memo" 
    CROSS_CASE_ANALYSIS = "cross_case_analysis"
    THEME_SYNTHESIS = "theme_synthesis"
    METHODOLOGICAL_REFLECTION = "methodological_reflection"
    RESEARCH_INSIGHTS = "research_insights"
    CONCEPTUAL_FRAMEWORK = "conceptual_framework"


class InsightLevel(Enum):
    """Level of analytical insight"""
    DESCRIPTIVE = "descriptive"      # What happened
    ANALYTICAL = "analytical"        # Why it happened
    THEORETICAL = "theoretical"      # What it means
    PRESCRIPTIVE = "prescriptive"   # What should happen


# Pydantic schemas for structured LLM output
class ThematicPattern(BaseModel):
    """A discovered thematic pattern"""
    pattern_name: str = Field(description="Name of the pattern")
    description: str = Field(description="Detailed description of the pattern")
    supporting_codes: List[str] = Field(description="Codes that support this pattern")
    frequency: int = Field(description="Number of occurrences")
    confidence: float = Field(description="Confidence score 0-1")
    examples: List[str] = Field(description="Representative quote examples")


class TheoreticalConnection(BaseModel):
    """Connection to theoretical framework"""
    theory_name: str = Field(description="Name of relevant theory")
    connection_type: str = Field(description="Type of connection (supports, challenges, extends)")
    description: str = Field(description="How the findings connect to this theory")
    implications: str = Field(description="Theoretical implications")
    supporting_evidence: List[str] = Field(description="Evidence supporting this connection")


class ResearchInsight(BaseModel):
    """A research insight or finding"""
    insight_title: str = Field(description="Title of the insight")
    insight_level: str = Field(description="Level of insight: descriptive, analytical, theoretical, prescriptive")
    description: str = Field(description="Detailed description of the insight")
    significance: str = Field(description="Why this insight is important")
    supporting_data: List[str] = Field(description="Data supporting this insight")
    implications: str = Field(description="Implications for research or practice")


class AnalyticalMemo(BaseModel):
    """Complete analytical memo structure"""
    memo_id: str = Field(description="Unique identifier for the memo")
    title: str = Field(description="Memo title")
    memo_type: str = Field(description="Type of memo")
    executive_summary: str = Field(description="Brief executive summary")
    patterns: List[ThematicPattern] = Field(description="Discovered patterns")
    insights: List[ResearchInsight] = Field(description="Research insights")
    theoretical_connections: List[TheoreticalConnection] = Field(description="Theoretical connections")
    methodological_notes: str = Field(description="Notes on methodology and process")
    limitations: str = Field(description="Limitations of the analysis")
    future_research: str = Field(description="Suggestions for future research")
    confidence_assessment: str = Field(description="Overall confidence in findings")


class AnalyticalMemoGenerator:
    """Generates analytical memos using LLM analysis"""
    
    def __init__(self, llm_handler, data_loader=None):
        self.llm = llm_handler
        self.data_loader = data_loader
        self.memo_history = []
    
    async def generate_pattern_analysis_memo(
        self, 
        interview_data: List[Dict[str, Any]], 
        focus_codes: Optional[List[str]] = None,
        memo_title: str = None
    ) -> AnalyticalMemo:
        """
        Generate a pattern analysis memo from interview data
        
        Args:
            interview_data: List of interview data with quotes and codes
            focus_codes: Optional list of codes to focus on
            memo_title: Optional custom title for the memo
            
        Returns:
            Structured analytical memo
        """
        memo_id = f"pattern_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Prepare data summary for LLM
        data_summary = self._prepare_data_summary(interview_data, focus_codes)
        
        # Create analysis prompt
        analysis_prompt = self._create_pattern_analysis_prompt(data_summary, focus_codes)
        
        # Generate memo using LLM
        memo = await self.llm.extract_structured(
            prompt=analysis_prompt,
            schema=AnalyticalMemo,
            instructions="Generate a comprehensive analytical memo focusing on patterns in the qualitative data."
        )
        
        # Set memo metadata
        memo.memo_id = memo_id
        memo.memo_type = MemoType.PATTERN_ANALYSIS.value
        if memo_title:
            memo.title = memo_title
        
        # Store in history
        self.memo_history.append(memo)
        
        logger.info(f"Generated pattern analysis memo: {memo_id}")
        return memo
    
    async def generate_theoretical_memo(
        self,
        interview_data: List[Dict[str, Any]],
        theoretical_frameworks: Optional[List[str]] = None,
        memo_title: str = None
    ) -> AnalyticalMemo:
        """
        Generate a theoretical memo connecting findings to theory
        
        Args:
            interview_data: List of interview data with quotes and codes
            theoretical_frameworks: Optional list of relevant theories to consider
            memo_title: Optional custom title for the memo
            
        Returns:
            Structured theoretical memo
        """
        memo_id = f"theoretical_memo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Prepare data summary
        data_summary = self._prepare_data_summary(interview_data)
        
        # Create theoretical analysis prompt
        theoretical_prompt = self._create_theoretical_memo_prompt(
            data_summary, theoretical_frameworks
        )
        
        # Generate memo using LLM
        memo = await self.llm.extract_structured(
            prompt=theoretical_prompt,
            schema=AnalyticalMemo,
            instructions="Generate a theoretical memo connecting empirical findings to relevant theoretical frameworks."
        )
        
        # Set memo metadata
        memo.memo_id = memo_id
        memo.memo_type = MemoType.THEORETICAL_MEMO.value
        if memo_title:
            memo.title = memo_title
            
        # Store in history
        self.memo_history.append(memo)
        
        logger.info(f"Generated theoretical memo: {memo_id}")
        return memo
    
    async def generate_cross_case_analysis(
        self,
        interview_data: List[Dict[str, Any]],
        comparison_criteria: Optional[List[str]] = None,
        memo_title: str = None
    ) -> AnalyticalMemo:
        """
        Generate cross-case analysis memo comparing across interviews
        
        Args:
            interview_data: List of interview data with quotes and codes
            comparison_criteria: Optional criteria for comparison
            memo_title: Optional custom title for the memo
            
        Returns:
            Structured cross-case analysis memo
        """
        memo_id = f"cross_case_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Group data by interviews for comparison
        interviews_by_id = {}
        for interview in interview_data:
            interview_id = interview.get('interview_id', 'unknown')
            interviews_by_id[interview_id] = interview
        
        # Create comparison summary
        comparison_summary = self._create_comparison_summary(
            interviews_by_id, comparison_criteria
        )
        
        # Create cross-case analysis prompt
        cross_case_prompt = self._create_cross_case_prompt(comparison_summary)
        
        # Generate memo using LLM
        memo = await self.llm.extract_structured(
            prompt=cross_case_prompt,
            schema=AnalyticalMemo,
            instructions="Generate a cross-case analysis comparing patterns and themes across different interviews."
        )
        
        # Set memo metadata
        memo.memo_id = memo_id
        memo.memo_type = MemoType.CROSS_CASE_ANALYSIS.value
        if memo_title:
            memo.title = memo_title
            
        # Store in history
        self.memo_history.append(memo)
        
        logger.info(f"Generated cross-case analysis memo: {memo_id}")
        return memo
    
    def _prepare_data_summary(
        self, 
        interview_data: List[Dict[str, Any]], 
        focus_codes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Prepare a summary of the data for LLM analysis"""
        
        # Collect all codes and quotes
        all_codes = set()
        all_quotes = []
        interview_summaries = []
        
        for interview in interview_data:
            interview_id = interview.get('interview_id', 'Unknown')
            quotes = interview.get('quotes', [])
            
            interview_codes = set()
            interview_quotes = []
            
            for quote in quotes:
                quote_codes = quote.get('code_names', [])
                all_codes.update(quote_codes)
                interview_codes.update(quote_codes)
                
                # Filter by focus codes if specified
                if not focus_codes or any(code in focus_codes for code in quote_codes):
                    all_quotes.append({
                        'text': quote.get('text', ''),
                        'codes': quote_codes,
                        'speaker': quote.get('speaker', {}).get('name', 'Unknown'),
                        'interview': interview_id
                    })
                    interview_quotes.append(quote)
            
            interview_summaries.append({
                'interview_id': interview_id,
                'quote_count': len(interview_quotes),
                'unique_codes': list(interview_codes),
                'code_count': len(interview_codes)
            })
        
        # Calculate code frequencies
        code_frequencies = {}
        for quote in all_quotes:
            for code in quote['codes']:
                code_frequencies[code] = code_frequencies.get(code, 0) + 1
        
        return {
            'total_interviews': len(interview_data),
            'total_quotes': len(all_quotes),
            'total_codes': len(all_codes),
            'code_frequencies': dict(sorted(code_frequencies.items(), key=lambda x: x[1], reverse=True)),
            'interview_summaries': interview_summaries,
            'sample_quotes': all_quotes[:50],  # First 50 quotes for analysis
            'focus_codes': focus_codes or []
        }
    
    def _create_pattern_analysis_prompt(
        self, 
        data_summary: Dict[str, Any], 
        focus_codes: Optional[List[str]] = None
    ) -> str:
        """Create prompt for pattern analysis"""
        
        focus_text = ""
        if focus_codes:
            focus_text = f"Focus particularly on these codes: {', '.join(focus_codes)}"
        
        prompt = f"""
        You are an expert qualitative researcher analyzing interview data for patterns and themes.
        
        DATA SUMMARY:
        - Total interviews: {data_summary['total_interviews']}
        - Total quotes: {data_summary['total_quotes']}
        - Total codes: {data_summary['total_codes']}
        {focus_text}
        
        TOP CODES BY FREQUENCY:
        {json.dumps(dict(list(data_summary['code_frequencies'].items())[:10]), indent=2)}
        
        SAMPLE QUOTES FOR ANALYSIS:
        {json.dumps(data_summary['sample_quotes'][:20], indent=2)}
        
        TASK:
        Analyze this qualitative data to identify significant patterns and themes. Look for:
        1. Recurring patterns across interviews
        2. Relationships between codes and themes
        3. Underlying meanings and interpretations
        4. Significant variations or contradictions
        5. Emerging theoretical insights
        
        Generate a comprehensive analytical memo that identifies key patterns, provides insights
        at multiple levels (descriptive, analytical, theoretical), and suggests theoretical connections.
        Focus on patterns that are well-supported by the data and have clear implications for
        understanding the research phenomenon.
        """
        
        return prompt.strip()
    
    def _create_theoretical_memo_prompt(
        self,
        data_summary: Dict[str, Any],
        theoretical_frameworks: Optional[List[str]] = None
    ) -> str:
        """Create prompt for theoretical memo generation"""
        
        frameworks_text = ""
        if theoretical_frameworks:
            frameworks_text = f"""
        THEORETICAL FRAMEWORKS TO CONSIDER:
        {', '.join(theoretical_frameworks)}
        """
        
        prompt = f"""
        You are an expert qualitative researcher with deep knowledge of social science theories.
        Your task is to connect empirical findings to relevant theoretical frameworks.
        
        DATA SUMMARY:
        - Total interviews: {data_summary['total_interviews']}
        - Total quotes: {data_summary['total_quotes']}
        - Total codes: {data_summary['total_codes']}
        
        KEY PATTERNS IN DATA:
        {json.dumps(dict(list(data_summary['code_frequencies'].items())[:15]), indent=2)}
        
        SAMPLE EVIDENCE:
        {json.dumps(data_summary['sample_quotes'][:15], indent=2)}
        
        {frameworks_text}
        
        TASK:
        Generate a theoretical memo that:
        1. Identifies how findings relate to established theories
        2. Explores whether findings support, challenge, or extend existing theory
        3. Proposes new theoretical insights or conceptual frameworks
        4. Discusses implications for theory development
        5. Considers methodological implications
        
        Focus on making strong theoretical connections that are well-supported by the empirical data.
        Consider both confirmatory and contradictory evidence. Suggest areas for future theoretical development.
        """
        
        return prompt.strip()
    
    def _create_comparison_summary(
        self,
        interviews_by_id: Dict[str, Dict[str, Any]],
        comparison_criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create summary for cross-case comparison"""
        
        comparison_data = {}
        
        for interview_id, interview_data in interviews_by_id.items():
            quotes = interview_data.get('quotes', [])
            
            # Extract comparison data
            codes_used = set()
            speakers = set()
            quote_texts = []
            
            for quote in quotes:
                codes_used.update(quote.get('code_names', []))
                speaker_name = quote.get('speaker', {}).get('name', 'Unknown')
                speakers.add(speaker_name)
                quote_texts.append(quote.get('text', ''))
            
            comparison_data[interview_id] = {
                'codes_used': list(codes_used),
                'code_count': len(codes_used),
                'speakers': list(speakers),
                'quote_count': len(quotes),
                'sample_quotes': quote_texts[:10]
            }
        
        return comparison_data
    
    def _create_cross_case_prompt(self, comparison_summary: Dict[str, Any]) -> str:
        """Create prompt for cross-case analysis"""
        
        prompt = f"""
        You are an expert in comparative qualitative analysis. Analyze the following data across
        multiple interviews to identify patterns, similarities, and differences.
        
        INTERVIEW COMPARISON DATA:
        {json.dumps(comparison_summary, indent=2)}
        
        TASK:
        Generate a comprehensive cross-case analysis memo that:
        1. Identifies patterns that appear consistently across cases
        2. Highlights significant variations between cases
        3. Explains potential reasons for similarities and differences
        4. Develops typologies or categories based on patterns
        5. Generates insights about conditions that influence outcomes
        6. Suggests theoretical explanations for variations
        
        Focus on developing analytical insights that go beyond simple description.
        Look for underlying factors that might explain the patterns you observe.
        Consider both convergent and divergent evidence in your analysis.
        """
        
        return prompt.strip()
    
    def export_memo_to_markdown(self, memo: AnalyticalMemo, output_path: Path) -> str:
        """Export analytical memo to markdown format"""
        
        markdown_content = f"""# {memo.title}

**Memo ID:** {memo.memo_id}
**Type:** {memo.memo_type}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

{memo.executive_summary}

## Key Patterns

"""
        
        for i, pattern in enumerate(memo.patterns, 1):
            markdown_content += f"""### Pattern {i}: {pattern.pattern_name}

**Description:** {pattern.description}

**Supporting Codes:** {', '.join(pattern.supporting_codes)}

**Frequency:** {pattern.frequency} occurrences

**Confidence:** {pattern.confidence:.2f}

**Examples:**
"""
            for example in pattern.examples:
                markdown_content += f"- \"{example}\"\n"
            
            markdown_content += "\n"
        
        markdown_content += f"""## Research Insights

"""
        
        for i, insight in enumerate(memo.insights, 1):
            markdown_content += f"""### {insight.insight_title}

**Level:** {insight.insight_level}

**Description:** {insight.description}

**Significance:** {insight.significance}

**Implications:** {insight.implications}

**Supporting Evidence:**
"""
            for evidence in insight.supporting_data:
                markdown_content += f"- {evidence}\n"
            
            markdown_content += "\n"
        
        if memo.theoretical_connections:
            markdown_content += f"""## Theoretical Connections

"""
            for i, connection in enumerate(memo.theoretical_connections, 1):
                markdown_content += f"""### {connection.theory_name}

**Connection Type:** {connection.connection_type}

**Description:** {connection.description}

**Implications:** {connection.implications}

**Supporting Evidence:**
"""
                for evidence in connection.supporting_evidence:
                    markdown_content += f"- {evidence}\n"
                
                markdown_content += "\n"
        
        markdown_content += f"""## Methodological Notes

{memo.methodological_notes}

## Limitations

{memo.limitations}

## Future Research

{memo.future_research}

## Confidence Assessment

{memo.confidence_assessment}

---

*Generated by Qualitative Coding Analysis Tool - Analytical Memos Module*
"""
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"Exported memo to markdown: {output_path}")
        return str(output_path)
    
    def save_memo_json(self, memo: AnalyticalMemo, output_path: Path) -> str:
        """Save analytical memo as JSON"""
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(memo.model_dump(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved memo as JSON: {output_path}")
        return str(output_path)
    
    def get_memo_history(self) -> List[Dict[str, Any]]:
        """Get history of generated memos"""
        return [
            {
                'memo_id': memo.memo_id,
                'title': memo.title,
                'type': memo.memo_type,
                'pattern_count': len(memo.patterns),
                'insight_count': len(memo.insights),
                'theoretical_connections': len(memo.theoretical_connections)
            }
            for memo in self.memo_history
        ]


class MemoCollectionAnalyzer:
    """Analyze collections of analytical memos for meta-insights"""
    
    def __init__(self, llm_handler):
        self.llm = llm_handler
        
    async def synthesize_memos(
        self, 
        memos: List[AnalyticalMemo],
        synthesis_focus: Optional[str] = None
    ) -> AnalyticalMemo:
        """
        Synthesize insights across multiple analytical memos
        
        Args:
            memos: List of analytical memos to synthesize
            synthesis_focus: Optional focus for synthesis
            
        Returns:
            Synthesis memo combining insights from all input memos
        """
        
        # Prepare synthesis data
        synthesis_data = self._prepare_synthesis_data(memos, synthesis_focus)
        
        # Create synthesis prompt
        synthesis_prompt = self._create_synthesis_prompt(synthesis_data, synthesis_focus)
        
        # Generate synthesis memo
        synthesis_memo = await self.llm.extract_structured(
            prompt=synthesis_prompt,
            schema=AnalyticalMemo,
            instructions="Generate a comprehensive synthesis memo that integrates insights from multiple analytical memos."
        )
        
        # Set synthesis metadata
        synthesis_memo.memo_id = f"synthesis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        synthesis_memo.memo_type = "memo_synthesis"
        synthesis_memo.title = f"Synthesis of {len(memos)} Analytical Memos"
        
        logger.info(f"Generated synthesis memo from {len(memos)} source memos")
        return synthesis_memo
    
    def _prepare_synthesis_data(
        self, 
        memos: List[AnalyticalMemo], 
        synthesis_focus: Optional[str] = None
    ) -> Dict[str, Any]:
        """Prepare data for memo synthesis"""
        
        all_patterns = []
        all_insights = []
        all_theoretical_connections = []
        memo_summaries = []
        
        for memo in memos:
            memo_summaries.append({
                'memo_id': memo.memo_id,
                'title': memo.title,
                'type': memo.memo_type,
                'summary': memo.executive_summary
            })
            
            all_patterns.extend(memo.patterns)
            all_insights.extend(memo.insights)
            all_theoretical_connections.extend(memo.theoretical_connections)
        
        return {
            'source_memo_count': len(memos),
            'memo_summaries': memo_summaries,
            'total_patterns': len(all_patterns),
            'total_insights': len(all_insights),
            'total_theoretical_connections': len(all_theoretical_connections),
            'synthesis_focus': synthesis_focus,
            'patterns_sample': [p.model_dump() for p in all_patterns[:20]],
            'insights_sample': [i.model_dump() for i in all_insights[:20]],
            'theoretical_connections_sample': [t.model_dump() for t in all_theoretical_connections[:10]]
        }
    
    def _create_synthesis_prompt(
        self,
        synthesis_data: Dict[str, Any],
        synthesis_focus: Optional[str] = None
    ) -> str:
        """Create prompt for memo synthesis"""
        
        focus_text = ""
        if synthesis_focus:
            focus_text = f"Focus the synthesis on: {synthesis_focus}"
        
        prompt = f"""
        You are an expert qualitative researcher tasked with synthesizing insights from multiple
        analytical memos to generate higher-order theoretical insights.
        
        SOURCE DATA:
        - Number of source memos: {synthesis_data['source_memo_count']}
        - Total patterns identified: {synthesis_data['total_patterns']}
        - Total insights generated: {synthesis_data['total_insights']}
        - Total theoretical connections: {synthesis_data['total_theoretical_connections']}
        
        {focus_text}
        
        SOURCE MEMO SUMMARIES:
        {json.dumps(synthesis_data['memo_summaries'], indent=2)}
        
        SAMPLE PATTERNS:
        {json.dumps(synthesis_data['patterns_sample'][:10], indent=2)}
        
        SAMPLE INSIGHTS:
        {json.dumps(synthesis_data['insights_sample'][:10], indent=2)}
        
        TASK:
        Generate a comprehensive synthesis that:
        1. Identifies meta-patterns across all source memos
        2. Develops higher-order theoretical insights
        3. Reconciles contradictions or tensions between findings
        4. Creates an integrated conceptual framework
        5. Suggests implications for theory and practice
        6. Identifies areas requiring further investigation
        
        Focus on generating insights that emerge from the combination of findings rather than
        simply summarizing individual memos. Look for convergent and divergent evidence.
        Develop theoretical contributions that wouldn't be apparent from individual memos alone.
        """
        
        return prompt.strip()


# Example usage and testing functions
async def demo_analytical_memos():
    """Demonstrate analytical memo generation"""
    print("📝 Analytical Memos Demo")
    print("=" * 40)
    
    # This would normally use real LLM handler and data
    print("Note: This demo shows the structure. Real usage requires:")
    print("- LLM handler for structured generation")
    print("- Interview data with quotes and codes")
    print("- Neo4j connection for data loading")
    
    # Show available memo types
    print(f"\n📋 Available Memo Types:")
    for memo_type in MemoType:
        print(f"  • {memo_type.value}")
    
    # Show insight levels
    print(f"\n🎯 Insight Levels:")
    for level in InsightLevel:
        print(f"  • {level.value}")
    
    # Show example structure
    example_pattern = ThematicPattern(
        pattern_name="AI Adoption Resistance",
        description="Patterns of resistance to AI technology adoption",
        supporting_codes=["AI_Barriers", "Change_Resistance", "Trust_Issues"],
        frequency=15,
        confidence=0.85,
        examples=["We don't trust AI with sensitive data", "Change is always difficult"]
    )
    
    print(f"\n🔍 Example Pattern Structure:")
    print(json.dumps(example_pattern.model_dump(), indent=2))
    
    print(f"\n✅ Analytical Memos Module Ready!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_analytical_memos())