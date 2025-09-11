"""
Discourse Analysis Module for QCA Pipeline
Enables sophisticated dialogue analysis including co-occurrence patterns, 
turn-taking analysis, and conversational sequence mining.
"""

import logging
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass
import re
import json
from pathlib import Path

from src.qc.extraction.code_first_schemas import EnhancedQuote, DialogueTurn, ConversationalContext, CodedInterview, ThematicConnection

logger = logging.getLogger(__name__)


@dataclass
class DialogicalCooccurrence:
    """Represents thematic code co-occurrence across speaker turns"""
    speaker_a: str
    speaker_b: str
    code_a: str
    code_b: str
    sequence_gap: int  # Number of turns between the two codes
    conversation_thread: str
    support_count: int  # Number of times this pattern occurs
    example_quotes: List[Tuple[str, str]]  # (quote_a, quote_b) pairs
    
    @property
    def pattern_strength(self) -> float:
        """Calculate strength of this dialogue pattern"""
        # Stronger if: more support, closer in sequence, different speakers
        gap_penalty = max(0, 1 - (self.sequence_gap / 10))  # Penalty for distant turns
        support_bonus = min(1, self.support_count / 5)  # Bonus for repeated patterns
        return (gap_penalty + support_bonus) / 2


@dataclass
class TurnTakingPattern:
    """Analysis of turn-taking dynamics"""
    pattern_type: str  # "sequential", "overlapping", "dominating", "balanced"
    dominant_speaker: Optional[str] = None
    average_turn_length: Dict[str, int] = None
    interruption_count: Dict[str, int] = None
    topic_initiation_rate: Dict[str, float] = None
    response_latency_patterns: List[str] = None  # ["immediate", "delayed", "building"]
    
    def __post_init__(self):
        if self.average_turn_length is None:
            self.average_turn_length = {}
        if self.interruption_count is None:
            self.interruption_count = {}
        if self.topic_initiation_rate is None:
            self.topic_initiation_rate = {}
        if self.response_latency_patterns is None:
            self.response_latency_patterns = []


@dataclass
class ConversationalSequence:
    """A sequence of related dialogue turns forming a conversational unit"""
    sequence_id: str
    start_turn: int
    end_turn: int
    participants: List[str]
    topic_thread: str
    codes_discussed: List[str]
    sequence_type: str  # "question-answer", "build-up", "disagreement", "exploration"
    key_quotes: List[str]  # Most important quotes in this sequence
    
    @property
    def length(self) -> int:
        return self.end_turn - self.start_turn + 1


class DiscourseAnalyzer:
    """Advanced discourse analysis for qualitative research"""
    
    def __init__(self):
        self.co_occurrence_threshold = 0.1  # Minimum pattern strength
        self.sequence_gap_limit = 5  # Max turns apart for co-occurrence
        
    def analyze_dialogical_cooccurrence(self, interviews: List[CodedInterview]) -> List[DialogicalCooccurrence]:
        """
        Analyze thematic code co-occurrence across speaker turns
        
        This enables research questions like:
        - When Speaker A mentions AI reliability concerns, how often does Speaker B 
          respond with training or validation themes?
        - What patterns emerge in multi-party discussions about specific topics?
        """
        cooccurrences = []
        
        for interview in interviews:
            # Focus on focus group interviews with multiple speakers
            if len(set(q.speaker.name for q in interview.quotes)) < 3:
                continue
                
            # Sort quotes by sequence position
            sorted_quotes = sorted(interview.quotes, key=lambda x: x.sequence_position)
            
            # Analyze pairs of quotes within the sequence gap limit
            for i, quote_a in enumerate(sorted_quotes):
                for j in range(i + 1, min(i + self.sequence_gap_limit + 1, len(sorted_quotes))):
                    quote_b = sorted_quotes[j]
                    
                    # Skip same speaker (we want cross-speaker patterns)
                    if quote_a.speaker.name == quote_b.speaker.name:
                        continue
                    
                    # Analyze code co-occurrence
                    for code_a in quote_a.code_ids:
                        for code_b in quote_b.code_ids:
                            # Create or update co-occurrence pattern
                            pattern_key = self._create_cooccurrence_key(
                                quote_a.speaker.name, quote_b.speaker.name, code_a, code_b
                            )
                            
                            # Find existing pattern or create new
                            existing = next((c for c in cooccurrences 
                                           if self._match_cooccurrence(c, quote_a, quote_b, code_a, code_b)), None)
                            
                            if existing:
                                existing.support_count += 1
                                existing.example_quotes.append((quote_a.text[:100], quote_b.text[:100]))
                            else:
                                new_cooccurrence = DialogicalCooccurrence(
                                    speaker_a=quote_a.speaker.name,
                                    speaker_b=quote_b.speaker.name,
                                    code_a=code_a,
                                    code_b=code_b,
                                    sequence_gap=quote_b.sequence_position - quote_a.sequence_position,
                                    conversation_thread=quote_a.conversational_context.conversational_thread or "main",
                                    support_count=1,
                                    example_quotes=[(quote_a.text[:100], quote_b.text[:100])]
                                )
                                cooccurrences.append(new_cooccurrence)
        
        # Filter by strength and return strongest patterns
        strong_patterns = [c for c in cooccurrences if c.pattern_strength >= self.co_occurrence_threshold]
        return sorted(strong_patterns, key=lambda x: x.pattern_strength, reverse=True)
    
    def analyze_turn_taking_patterns(self, interview: CodedInterview) -> TurnTakingPattern:
        """
        Analyze turn-taking patterns within a single interview
        
        Identifies:
        - Balanced vs. dominated conversations
        - Interruption patterns
        - Response styles
        - Topic initiation patterns
        """
        if not interview.quotes:
            return TurnTakingPattern(pattern_type="no_data")
        
        # Sort by sequence position
        sorted_quotes = sorted(interview.quotes, key=lambda x: x.sequence_position)
        speakers = list(set(q.speaker.name for q in sorted_quotes))
        
        # Calculate basic metrics
        speaker_stats = defaultdict(lambda: {"turns": 0, "words": 0, "questions": 0, "responses": 0})
        
        for quote in sorted_quotes:
            speaker = quote.speaker.name
            speaker_stats[speaker]["turns"] += 1
            speaker_stats[speaker]["words"] += len(quote.text.split())
            
            if quote.dialogue_turn.contains_question:
                speaker_stats[speaker]["questions"] += 1
            if quote.conversational_context.is_response_to:
                speaker_stats[speaker]["responses"] += 1
        
        # Determine pattern type
        total_turns = len(sorted_quotes)
        turn_distribution = [speaker_stats[s]["turns"] / total_turns for s in speakers]
        max_share = max(turn_distribution)
        
        if max_share > 0.6:
            pattern_type = "dominating"
            dominant_speaker = speakers[turn_distribution.index(max_share)]
        elif max_share < 0.4 and len(speakers) > 2:
            pattern_type = "balanced"
            dominant_speaker = None
        else:
            pattern_type = "sequential"
            dominant_speaker = None
        
        # Calculate derived metrics
        avg_turn_length = {s: stats["words"] / max(stats["turns"], 1) 
                          for s, stats in speaker_stats.items()}
        
        topic_initiation_rate = {s: stats["questions"] / max(stats["turns"], 1)
                               for s, stats in speaker_stats.items()}
        
        # Analyze interruption patterns (simplified heuristic)
        interruptions = defaultdict(int)
        for i in range(1, len(sorted_quotes)):
            current_quote = sorted_quotes[i]
            prev_quote = sorted_quotes[i-1]
            
            # Heuristic: very short turns following longer ones might indicate interruptions
            if (len(current_quote.text.split()) < 5 and 
                len(prev_quote.text.split()) > 15 and
                current_quote.speaker.name != prev_quote.speaker.name):
                interruptions[current_quote.speaker.name] += 1
        
        return TurnTakingPattern(
            pattern_type=pattern_type,
            dominant_speaker=dominant_speaker,
            average_turn_length=avg_turn_length,
            interruption_count=dict(interruptions),
            topic_initiation_rate=topic_initiation_rate,
            response_latency_patterns=self._analyze_response_patterns(sorted_quotes)
        )
    
    def mine_conversational_sequences(self, interview: CodedInterview) -> List[ConversationalSequence]:
        """
        Identify meaningful conversational sequences (question-answer pairs, 
        topic explorations, build-up discussions)
        
        Enables analysis of:
        - How topics develop across multiple turns
        - Question-answer dynamics
        - Consensus building or disagreement patterns
        """
        if not interview.quotes:
            return []
        
        sorted_quotes = sorted(interview.quotes, key=lambda x: x.sequence_position)
        sequences = []
        
        i = 0
        while i < len(sorted_quotes):
            sequence = self._identify_sequence_starting_at(sorted_quotes, i)
            if sequence and sequence.length >= 2:  # Only meaningful sequences
                sequences.append(sequence)
                i = sequence.end_turn
            else:
                i += 1
        
        return sequences
    
    def generate_discourse_report(self, interviews: List[CodedInterview], 
                                output_file: Optional[str] = None) -> Dict:
        """
        Generate comprehensive discourse analysis report
        
        Returns:
            Dictionary with complete discourse analysis results
        """
        logger.info("Generating comprehensive discourse analysis report...")
        
        # Analyze co-occurrence patterns
        cooccurrences = self.analyze_dialogical_cooccurrence(interviews)
        
        # Analyze each interview's turn-taking patterns
        turn_taking_analyses = {}
        conversational_sequences = {}
        
        for interview in interviews:
            interview_id = interview.interview_id
            turn_taking_analyses[interview_id] = self.analyze_turn_taking_patterns(interview)
            conversational_sequences[interview_id] = self.mine_conversational_sequences(interview)
        
        # Generate summary statistics
        report = {
            "discourse_analysis_summary": {
                "total_interviews_analyzed": len(interviews),
                "focus_group_count": len([i for i in interviews if len(set(q.speaker.name for q in i.quotes)) >= 3]),
                "individual_interview_count": len([i for i in interviews if len(set(q.speaker.name for q in i.quotes)) < 3]),
                "total_dialogical_patterns": len(cooccurrences),
                "strong_patterns": len([c for c in cooccurrences if c.pattern_strength > 0.5])
            },
            
            "dialogical_cooccurrence_patterns": [
                {
                    "speakers": f"{c.speaker_a} → {c.speaker_b}",
                    "codes": f"{c.code_a} → {c.code_b}",
                    "pattern_strength": round(c.pattern_strength, 3),
                    "support_count": c.support_count,
                    "sequence_gap": c.sequence_gap,
                    "example_interaction": {
                        "speaker_a_quote": c.example_quotes[0][0] + "..." if c.example_quotes else "",
                        "speaker_b_quote": c.example_quotes[0][1] + "..." if c.example_quotes else ""
                    }
                }
                for c in cooccurrences[:20]  # Top 20 patterns
            ],
            
            "turn_taking_analysis": {
                interview_id: {
                    "pattern_type": analysis.pattern_type,
                    "dominant_speaker": analysis.dominant_speaker,
                    "speaker_metrics": {
                        "average_turn_length": analysis.average_turn_length,
                        "topic_initiation_rate": analysis.topic_initiation_rate,
                        "interruption_count": analysis.interruption_count
                    }
                }
                for interview_id, analysis in turn_taking_analyses.items()
            },
            
            "conversational_sequences": {
                interview_id: [
                    {
                        "sequence_id": seq.sequence_id,
                        "participants": seq.participants,
                        "topic_codes": seq.codes_discussed,
                        "sequence_type": seq.sequence_type,
                        "length": seq.length,
                        "key_quote": seq.key_quotes[0] if seq.key_quotes else ""
                    }
                    for seq in sequences[:10]  # Top 10 per interview
                ]
                for interview_id, sequences in conversational_sequences.items()
            }
        }
        
        # Save report if requested
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"Discourse analysis report saved to: {output_path}")
        
        return report
    
    # Helper methods
    
    def _create_cooccurrence_key(self, speaker_a: str, speaker_b: str, 
                                code_a: str, code_b: str) -> str:
        """Create unique key for co-occurrence pattern"""
        return f"{speaker_a}:{code_a} → {speaker_b}:{code_b}"
    
    def _match_cooccurrence(self, existing: DialogicalCooccurrence, 
                          quote_a: EnhancedQuote, quote_b: EnhancedQuote,
                          code_a: str, code_b: str) -> bool:
        """Check if this matches an existing co-occurrence pattern"""
        return (existing.speaker_a == quote_a.speaker.name and
                existing.speaker_b == quote_b.speaker.name and
                existing.code_a == code_a and
                existing.code_b == code_b)
    
    def _analyze_response_patterns(self, sorted_quotes: List[EnhancedQuote]) -> List[str]:
        """Analyze response timing and style patterns"""
        patterns = []
        
        response_quotes = [q for q in sorted_quotes if q.conversational_context.is_response_to]
        
        if len(response_quotes) > len(sorted_quotes) * 0.3:
            patterns.append("highly_interactive")
        elif len(response_quotes) > len(sorted_quotes) * 0.1:
            patterns.append("moderately_interactive")
        else:
            patterns.append("low_interaction")
        
        # Analyze response markers
        agreement_responses = sum(1 for q in response_quotes 
                                if q.dialogue_turn.contains_response_markers)
        
        if agreement_responses > len(response_quotes) * 0.5:
            patterns.append("agreement_heavy")
        
        return patterns
    
    def _identify_sequence_starting_at(self, sorted_quotes: List[EnhancedQuote], 
                                     start_idx: int) -> Optional[ConversationalSequence]:
        """Identify a conversational sequence starting at the given index"""
        if start_idx >= len(sorted_quotes):
            return None
        
        start_quote = sorted_quotes[start_idx]
        
        # Look for question-answer sequences
        if start_quote.dialogue_turn.contains_question:
            return self._build_qa_sequence(sorted_quotes, start_idx)
        
        # Look for topic development sequences
        return self._build_topic_sequence(sorted_quotes, start_idx)
    
    def _build_qa_sequence(self, sorted_quotes: List[EnhancedQuote], 
                          start_idx: int) -> Optional[ConversationalSequence]:
        """Build question-answer sequence"""
        question_quote = sorted_quotes[start_idx]
        participants = [question_quote.speaker.name]
        end_idx = start_idx
        
        # Look for responses to this question
        for i in range(start_idx + 1, min(start_idx + 4, len(sorted_quotes))):  # Look ahead 3 turns
            quote = sorted_quotes[i]
            
            # Check if this responds to our question
            if (quote.conversational_context.is_response_to or
                quote.dialogue_turn.contains_response_markers or
                question_quote.speaker.name != quote.speaker.name):  # Different speaker
                
                participants.append(quote.speaker.name)
                end_idx = i
            else:
                break  # End of response sequence
        
        if end_idx > start_idx:  # Found at least one response
            all_codes = set()
            key_quotes = []
            
            for i in range(start_idx, end_idx + 1):
                quote = sorted_quotes[i]
                all_codes.update(quote.code_ids)
                if i == start_idx or i == end_idx:  # Question and final answer
                    key_quotes.append(quote.text[:150] + "...")
            
            return ConversationalSequence(
                sequence_id=f"QA_{start_idx}_{end_idx}",
                start_turn=start_idx + 1,  # 1-indexed
                end_turn=end_idx + 1,
                participants=list(set(participants)),
                topic_thread=question_quote.conversational_context.conversational_thread or "main",
                codes_discussed=list(all_codes),
                sequence_type="question-answer",
                key_quotes=key_quotes
            )
        
        return None
    
    def _build_topic_sequence(self, sorted_quotes: List[EnhancedQuote], 
                            start_idx: int) -> Optional[ConversationalSequence]:
        """Build topic development sequence"""
        start_quote = sorted_quotes[start_idx]
        participants = [start_quote.speaker.name]
        codes = set(start_quote.code_ids)
        end_idx = start_idx
        
        # Look for continuation of same topic/codes
        for i in range(start_idx + 1, min(start_idx + 6, len(sorted_quotes))):
            quote = sorted_quotes[i]
            
            # Check if this continues the topic
            if (any(code in quote.code_ids for code in codes) or
                quote.conversational_context.topic_continuity in ["continues", "building"]):
                
                participants.append(quote.speaker.name)
                codes.update(quote.code_ids)
                end_idx = i
            else:
                break  # Topic shift
        
        if end_idx > start_idx:  # Found topic development
            key_quotes = [start_quote.text[:150] + "..."]
            if end_idx > start_idx:
                key_quotes.append(sorted_quotes[end_idx].text[:150] + "...")
            
            return ConversationalSequence(
                sequence_id=f"TOPIC_{start_idx}_{end_idx}",
                start_turn=start_idx + 1,
                end_turn=end_idx + 1,
                participants=list(set(participants)),
                topic_thread=start_quote.conversational_context.conversational_thread or "main",
                codes_discussed=list(codes),
                sequence_type="topic_development",
                key_quotes=key_quotes
            )
        
        return None
    
    def export_for_network_analysis(self, cooccurrences: List[DialogicalCooccurrence],
                                  output_file: str) -> None:
        """
        Export co-occurrence data in format suitable for network analysis tools
        (Gephi, Cytoscape, networkx)
        """
        # Create nodes (speakers and codes)
        nodes = []
        edges = []
        
        speakers = set()
        codes = set()
        
        for cooc in cooccurrences:
            speakers.update([cooc.speaker_a, cooc.speaker_b])
            codes.update([cooc.code_a, cooc.code_b])
        
        # Speaker nodes
        for speaker in speakers:
            nodes.append({
                "id": f"speaker_{speaker}",
                "label": speaker,
                "type": "speaker"
            })
        
        # Code nodes  
        for code in codes:
            nodes.append({
                "id": f"code_{code}",
                "label": code,
                "type": "code"
            })
        
        # Co-occurrence edges
        for cooc in cooccurrences:
            edges.append({
                "source": f"speaker_{cooc.speaker_a}",
                "target": f"code_{cooc.code_a}",
                "weight": 1,
                "type": "mentions"
            })
            edges.append({
                "source": f"speaker_{cooc.speaker_b}",
                "target": f"code_{cooc.code_b}",
                "weight": 1,
                "type": "mentions"
            })
            edges.append({
                "source": f"code_{cooc.code_a}",
                "target": f"code_{cooc.code_b}",
                "weight": cooc.pattern_strength,
                "type": "cooccurrence",
                "sequence_gap": cooc.sequence_gap,
                "support_count": cooc.support_count
            })
        
        network_data = {
            "nodes": nodes,
            "edges": edges
        }
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(network_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Network analysis data exported to: {output_path}")


# Convenience functions for common discourse analysis tasks

def analyze_focus_group_dynamics(interviews: List[CodedInterview], 
                                output_dir: str = "discourse_analysis") -> Dict:
    """
    Comprehensive focus group discourse analysis
    
    Args:
        interviews: List of coded interviews (focus groups)
        output_dir: Directory to save analysis outputs
        
    Returns:
        Dictionary with complete analysis results
    """
    analyzer = DiscourseAnalyzer()
    
    # Filter to focus groups only
    focus_groups = [i for i in interviews if len(set(q.speaker.name for q in i.quotes)) >= 3]
    
    if not focus_groups:
        logger.warning("No focus group interviews found for discourse analysis")
        return {}
    
    # Generate comprehensive report
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    report = analyzer.generate_discourse_report(
        focus_groups, 
        output_file=str(output_path / "discourse_analysis_report.json")
    )
    
    # Export network data
    cooccurrences = analyzer.analyze_dialogical_cooccurrence(focus_groups)
    analyzer.export_for_network_analysis(
        cooccurrences,
        str(output_path / "dialogue_network.json")
    )
    
    return report


def find_response_patterns(interviews: List[CodedInterview], 
                         target_code: str) -> List[Dict]:
    """
    Find how different speakers respond when a specific code is mentioned
    
    Args:
        interviews: List of coded interviews
        target_code: Code to analyze responses to
        
    Returns:
        List of response patterns
    """
    analyzer = DiscourseAnalyzer()
    cooccurrences = analyzer.analyze_dialogical_cooccurrence(interviews)
    
    # Filter to patterns involving the target code
    relevant_patterns = [
        c for c in cooccurrences 
        if c.code_a == target_code or c.code_b == target_code
    ]
    
    return [
        {
            "trigger_speaker": c.speaker_a if c.code_a == target_code else c.speaker_b,
            "response_speaker": c.speaker_b if c.code_a == target_code else c.speaker_a,
            "response_code": c.code_b if c.code_a == target_code else c.code_a,
            "pattern_strength": c.pattern_strength,
            "example_quotes": c.example_quotes[0] if c.example_quotes else ("", "")
        }
        for c in relevant_patterns
    ]


@dataclass 
class QualitativeInsight:
    """A qualitative insight generated from dialogue analysis"""
    insight_type: str  # "thematic_flow", "viewpoint_synergy", "conceptual_tension"
    title: str  # Short descriptive title
    description: str  # Detailed insight description
    participants: List[str]  # Speakers involved
    evidence: List[str]  # Supporting quotes or evidence
    confidence: float  # 0-1 confidence in this insight
    thematic_connections: List[str]  # Related ThematicConnection IDs
    
    
class QualitativeInsightEngine:
    """
    Generate qualitative insights about thematic flow and viewpoint relationships
    
    This class transforms dialogue structure data into actionable insights for researchers,
    focusing on content relationships rather than linguistic discourse analysis.
    """
    
    def __init__(self):
        self.min_confidence = 0.7  # Minimum confidence for connections to consider
        self.min_chain_length = 3   # Minimum number of speakers in a thematic chain
        
    def generate_insights(self, interview: CodedInterview) -> List[QualitativeInsight]:
        """
        Generate comprehensive qualitative insights from interview data
        
        Args:
            interview: Coded interview with thematic connections
            
        Returns:
            List of QualitativeInsight objects
        """
        insights = []
        
        if not interview.thematic_connections:
            logger.info(f"No thematic connections found in {interview.interview_id}")
            return insights
        
        # Filter high-confidence connections
        strong_connections = [
            c for c in interview.thematic_connections 
            if c.confidence_score >= self.min_confidence
        ]
        
        if not strong_connections:
            logger.info(f"No high-confidence connections in {interview.interview_id}")
            return insights
        
        logger.info(f"Analyzing {len(strong_connections)} strong thematic connections...")
        
        # Generate different types of insights
        insights.extend(self._identify_thematic_development_chains(strong_connections))
        insights.extend(self._identify_viewpoint_synergies(strong_connections))  
        insights.extend(self._identify_conceptual_tensions(strong_connections))
        insights.extend(self._identify_idea_building_patterns(strong_connections))
        
        # Sort by confidence and return
        insights.sort(key=lambda x: x.confidence, reverse=True)
        logger.info(f"Generated {len(insights)} qualitative insights")
        
        return insights
    
    def _identify_thematic_development_chains(self, connections: List[ThematicConnection]) -> List[QualitativeInsight]:
        """
        Identify chains where ideas develop across multiple speakers
        
        Example: Sara's CODING_DIFFICULTY → Douglas's TIME_PRESSURE → Luke's TOOL_SOLUTIONS
        """
        insights = []
        
        # Build connection chains
        chains = self._build_connection_chains(connections)
        
        for chain in chains:
            if len(chain) >= self.min_chain_length:
                # Extract the thematic progression
                speakers = [c.source_speaker for c in chain] + [chain[-1].target_speaker]
                themes = self._extract_theme_progression(chain)
                
                insight = QualitativeInsight(
                    insight_type="thematic_flow",
                    title=f"{len(chain)+1}-speaker idea development: {' → '.join(themes[:3])}",
                    description=self._generate_chain_description(chain, speakers, themes),
                    participants=list(dict.fromkeys(speakers)),  # Remove duplicates, preserve order
                    evidence=[c.evidence for c in chain],
                    confidence=sum(c.confidence_score for c in chain) / len(chain),
                    thematic_connections=[f"{c.source_quote_id}→{c.target_quote_id}" for c in chain]
                )
                insights.append(insight)
        
        return insights
    
    def _identify_viewpoint_synergies(self, connections: List[ThematicConnection]) -> List[QualitativeInsight]:
        """
        Identify cases where speakers agree or build constructively on each other's ideas
        """
        insights = []
        
        # Look for "builds_on", "addresses" (positive), "relates_to" connections
        synergy_types = ["builds_on", "addresses", "relates_to"]
        synergistic_connections = [
            c for c in connections 
            if c.connection_type in synergy_types
        ]
        
        # Group by thematic overlap to find synergistic clusters
        theme_clusters = self._cluster_by_themes(synergistic_connections)
        
        for theme, cluster_connections in theme_clusters.items():
            if len(cluster_connections) >= 2:  # At least 2 connections sharing theme
                speakers = list(set([c.source_speaker for c in cluster_connections] + 
                                  [c.target_speaker for c in cluster_connections]))
                
                insight = QualitativeInsight(
                    insight_type="viewpoint_synergy", 
                    title=f"Collaborative agreement on {theme} ({len(speakers)} speakers)",
                    description=self._generate_synergy_description(theme, cluster_connections, speakers),
                    participants=speakers,
                    evidence=[c.evidence for c in cluster_connections],
                    confidence=sum(c.confidence_score for c in cluster_connections) / len(cluster_connections),
                    thematic_connections=[f"{c.source_quote_id}→{c.target_quote_id}" for c in cluster_connections]
                )
                insights.append(insight)
        
        return insights
    
    def _identify_conceptual_tensions(self, connections: List[ThematicConnection]) -> List[QualitativeInsight]:
        """
        Identify tensions, disagreements, or alternative viewpoints
        """
        insights = []
        
        # Look for "contradicts" connections and opposing themes
        tension_connections = [c for c in connections if c.connection_type == "contradicts"]
        
        for connection in tension_connections:
            insight = QualitativeInsight(
                insight_type="conceptual_tension",
                title=f"Tension: {connection.source_speaker} vs {connection.target_speaker}",
                description=f"{connection.source_speaker} and {connection.target_speaker} present conflicting views on {', '.join(connection.thematic_overlap)}. {connection.reasoning}",
                participants=[connection.source_speaker, connection.target_speaker],
                evidence=[connection.evidence],
                confidence=connection.confidence_score,
                thematic_connections=[f"{connection.source_quote_id}→{connection.target_quote_id}"]
            )
            insights.append(insight)
        
        return insights
    
    def _identify_idea_building_patterns(self, connections: List[ThematicConnection]) -> List[QualitativeInsight]:
        """
        Identify patterns where speakers provide examples or evidence for others' points
        """
        insights = []
        
        exemplification_connections = [c for c in connections if c.connection_type == "exemplifies"]
        
        # Group by source speaker to find patterns
        source_groups = {}
        for conn in exemplification_connections:
            if conn.source_speaker not in source_groups:
                source_groups[conn.source_speaker] = []
            source_groups[conn.source_speaker].append(conn)
        
        for source_speaker, connections_list in source_groups.items():
            if len(connections_list) >= 2:  # Pattern of providing examples
                targets = [c.target_speaker for c in connections_list]
                themes = set()
                for c in connections_list:
                    themes.update(c.thematic_overlap)
                
                insight = QualitativeInsight(
                    insight_type="idea_building",
                    title=f"{source_speaker} provides examples for {len(set(targets))} speakers",
                    description=f"{source_speaker} consistently provides concrete examples and evidence to support points made by {', '.join(set(targets))} on topics including {', '.join(list(themes)[:3])}.",
                    participants=[source_speaker] + list(set(targets)),
                    evidence=[c.evidence for c in connections_list],
                    confidence=sum(c.confidence_score for c in connections_list) / len(connections_list),
                    thematic_connections=[f"{c.source_quote_id}→{c.target_quote_id}" for c in connections_list]
                )
                insights.append(insight)
        
        return insights
    
    def _build_connection_chains(self, connections: List[ThematicConnection]) -> List[List[ThematicConnection]]:
        """Build chains of thematic connections across speakers"""
        chains = []
        
        # Create a mapping of target to connections that could follow
        target_to_sources = {}
        for conn in connections:
            if conn.target_quote_id not in target_to_sources:
                target_to_sources[conn.target_quote_id] = []
            target_to_sources[conn.target_quote_id].append(conn)
        
        # For each connection, try to build a chain forward
        for start_conn in connections:
            chain = [start_conn]
            current_target = start_conn.target_quote_id
            
            # Look for connections that build on this one
            while current_target in target_to_sources:
                next_connections = [
                    c for c in target_to_sources[current_target] 
                    if c not in chain and c.source_quote_id == current_target
                ]
                
                if next_connections:
                    # Choose the highest confidence next connection
                    next_conn = max(next_connections, key=lambda x: x.confidence_score)
                    chain.append(next_conn)
                    current_target = next_conn.target_quote_id
                else:
                    break
            
            if len(chain) >= 2:  # Only keep chains of 2+ connections
                chains.append(chain)
        
        return chains
    
    def _extract_theme_progression(self, chain: List[ThematicConnection]) -> List[str]:
        """Extract the key themes that develop through a connection chain"""
        themes = []
        
        for connection in chain:
            # Get the most prominent theme from the overlap
            if connection.thematic_overlap:
                theme = connection.thematic_overlap[0]  # First is often most prominent
                if theme not in themes:
                    themes.append(theme)
        
        return themes
    
    def _generate_chain_description(self, chain: List[ThematicConnection], speakers: List[str], themes: List[str]) -> str:
        """Generate a human-readable description of a thematic development chain"""
        if len(chain) == 1:
            conn = chain[0]
            return f"{conn.source_speaker}'s {themes[0] if themes else 'idea'} is {conn.connection_type.replace('_', ' ')} by {conn.target_speaker}, showing {conn.reasoning}"
        
        description_parts = []
        for i, conn in enumerate(chain):
            if i == 0:
                description_parts.append(f"{conn.source_speaker} introduces {themes[i] if i < len(themes) else 'the topic'}")
            else:
                action = conn.connection_type.replace('_', ' ')
                description_parts.append(f"{conn.target_speaker} {action} this with {themes[i] if i < len(themes) else 'related ideas'}")
        
        return ". ".join(description_parts) + f". This {len(speakers)}-speaker progression demonstrates collaborative idea development."
    
    def _cluster_by_themes(self, connections: List[ThematicConnection]) -> Dict[str, List[ThematicConnection]]:
        """Cluster connections by shared themes"""
        clusters = {}
        
        for conn in connections:
            for theme in conn.thematic_overlap:
                if theme not in clusters:
                    clusters[theme] = []
                clusters[theme].append(conn)
        
        return clusters
    
    def _generate_synergy_description(self, theme: str, connections: List[ThematicConnection], speakers: List[str]) -> str:
        """Generate description of viewpoint synergy"""
        connection_types = [c.connection_type for c in connections]
        
        if "builds_on" in connection_types:
            return f"Multiple speakers ({', '.join(speakers)}) collaboratively develop ideas around {theme}, with each building constructively on others' contributions."
        elif "addresses" in connection_types:
            return f"Speakers show responsive engagement on {theme}, with {', '.join(speakers)} directly addressing and expanding on each other's points."
        else:
            return f"Strong thematic alignment on {theme} among {', '.join(speakers)}, indicating shared understanding or agreement."
    
    def generate_insight_report(self, interviews: List[CodedInterview], output_file: Optional[str] = None) -> Dict:
        """
        Generate comprehensive qualitative insight report for multiple interviews
        
        Args:
            interviews: List of coded interviews with thematic connections
            output_file: Optional file path to save the report
            
        Returns:
            Dictionary containing the complete insight analysis
        """
        logger.info(f"Generating qualitative insights for {len(interviews)} interviews...")
        
        all_insights = []
        interview_summaries = {}
        
        for interview in interviews:
            insights = self.generate_insights(interview)
            all_insights.extend(insights)
            
            interview_summaries[interview.interview_id] = {
                "total_insights": len(insights),
                "thematic_flows": len([i for i in insights if i.insight_type == "thematic_flow"]),
                "viewpoint_synergies": len([i for i in insights if i.insight_type == "viewpoint_synergy"]),
                "conceptual_tensions": len([i for i in insights if i.insight_type == "conceptual_tension"]),
                "idea_building_patterns": len([i for i in insights if i.insight_type == "idea_building"]),
                "top_insights": [
                    {
                        "type": insight.insight_type,
                        "title": insight.title,
                        "confidence": round(insight.confidence, 3),
                        "participants": insight.participants
                    }
                    for insight in sorted(insights, key=lambda x: x.confidence, reverse=True)[:5]
                ]
            }
        
        # Generate overall summary
        report = {
            "qualitative_insight_summary": {
                "total_interviews": len(interviews),
                "interviews_with_insights": len([s for s in interview_summaries.values() if s["total_insights"] > 0]),
                "total_insights_generated": len(all_insights),
                "insight_type_breakdown": {
                    "thematic_flows": len([i for i in all_insights if i.insight_type == "thematic_flow"]),
                    "viewpoint_synergies": len([i for i in all_insights if i.insight_type == "viewpoint_synergy"]),
                    "conceptual_tensions": len([i for i in all_insights if i.insight_type == "conceptual_tension"]),
                    "idea_building_patterns": len([i for i in all_insights if i.insight_type == "idea_building"])
                }
            },
            
            "interview_insights": interview_summaries,
            
            "top_insights_across_all_interviews": [
                {
                    "insight_type": insight.insight_type,
                    "title": insight.title,
                    "description": insight.description,
                    "participants": insight.participants,
                    "confidence": round(insight.confidence, 3),
                    "evidence_samples": insight.evidence[:2]  # First 2 pieces of evidence
                }
                for insight in sorted(all_insights, key=lambda x: x.confidence, reverse=True)[:10]
            ]
        }
        
        # Save report if requested
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"Qualitative insight report saved to: {output_path}")
        
        return report