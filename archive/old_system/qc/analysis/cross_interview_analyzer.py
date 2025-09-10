"""
Cross-interview pattern detection and analysis.

This module provides tools for identifying patterns, consensus, and divergence
across multiple interviews in the qualitative coding system.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict, Counter

from ..core.neo4j_manager import EnhancedNeo4jManager

logger = logging.getLogger(__name__)


@dataclass
class ConsensusPattern:
    """Represents a consensus pattern found across interviews"""
    pattern_type: str  # "entity_usage", "relationship_pattern", "theme_agreement"
    description: str
    supporting_interviews: List[str]
    supporting_count: int
    total_interviews: int
    consensus_strength: float  # 0.0 to 1.0
    evidence: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class DivergencePattern:
    """Represents a divergence or disagreement pattern"""
    pattern_type: str
    description: str
    conflicting_perspectives: List[Dict[str, Any]]
    interview_groups: Dict[str, List[str]]  # perspective -> interview_ids
    metadata: Dict[str, Any]


@dataclass
class EvolutionPattern:
    """Represents temporal evolution of patterns"""
    pattern_type: str
    description: str
    timeline: List[Dict[str, Any]]  # timestamp -> pattern_state
    trend_direction: str  # "increasing", "decreasing", "stable", "cyclical"
    metadata: Dict[str, Any]


class CrossInterviewAnalyzer:
    """Analyzes patterns across multiple interviews"""
    
    def __init__(self, neo4j_manager: EnhancedNeo4jManager):
        self.neo4j = neo4j_manager
        
    async def analyze_consensus_patterns(self, 
                                       interview_ids: Optional[List[str]] = None,
                                       min_consensus_threshold: float = 0.6) -> List[ConsensusPattern]:
        """
        Identify consensus patterns across interviews
        
        Args:
            interview_ids: Specific interviews to analyze (None for all)
            min_consensus_threshold: Minimum agreement level (0.0-1.0)
            
        Returns:
            List of consensus patterns found
        """
        patterns = []
        
        # Tool usage consensus
        tool_patterns = await self._analyze_tool_usage_consensus(interview_ids, min_consensus_threshold)
        patterns.extend(tool_patterns)
        
        # Sentiment consensus
        sentiment_patterns = await self._analyze_sentiment_consensus(interview_ids, min_consensus_threshold)
        patterns.extend(sentiment_patterns)
        
        # Organizational patterns
        org_patterns = await self._analyze_organizational_consensus(interview_ids, min_consensus_threshold)
        patterns.extend(org_patterns)
        
        return patterns
    
    async def analyze_divergence_patterns(self,
                                        interview_ids: Optional[List[str]] = None) -> List[DivergencePattern]:
        """
        Identify divergence patterns where interviews disagree
        
        Args:
            interview_ids: Specific interviews to analyze (None for all)
            
        Returns:
            List of divergence patterns found
        """
        patterns = []
        
        # Tool sentiment divergence
        tool_divergence = await self._analyze_tool_sentiment_divergence(interview_ids)
        patterns.extend(tool_divergence)
        
        # Organizational perspective divergence
        org_divergence = await self._analyze_organizational_perspective_divergence(interview_ids)
        patterns.extend(org_divergence)
        
        # Method preference divergence
        method_divergence = await self._analyze_method_preference_divergence(interview_ids)
        patterns.extend(method_divergence)
        
        return patterns
    
    async def analyze_evolution_patterns(self,
                                       interview_ids: Optional[List[str]] = None) -> List[EvolutionPattern]:
        """
        Identify temporal evolution patterns in interviews
        
        Args:
            interview_ids: Specific interviews to analyze (None for all)
            
        Returns:
            List of evolution patterns found
        """
        patterns = []
        
        # Tool adoption evolution
        adoption_patterns = await self._analyze_tool_adoption_evolution(interview_ids)
        patterns.extend(adoption_patterns)
        
        # Organizational change evolution  
        org_evolution = await self._analyze_organizational_evolution(interview_ids)
        patterns.extend(org_evolution)
        
        return patterns
    
    async def _analyze_tool_usage_consensus(self, 
                                          interview_ids: Optional[List[str]],
                                          threshold: float) -> List[ConsensusPattern]:
        """Analyze consensus on tool usage patterns"""
        patterns = []
        
        # Query for tool usage across interviews
        query = """
        MATCH (p:Person)-[r:USES]->(t:Tool)
        WHERE ($interview_ids IS NULL OR p.interview_id IN $interview_ids)
        RETURN t.name as tool_name,
               collect(DISTINCT p.interview_id) as interview_ids,
               collect({
                   person: p.name,
                   interview: p.interview_id,
                   confidence: r.confidence,
                   context: r.context
               }) as usage_evidence,
               count(DISTINCT p.interview_id) as interview_count
        ORDER BY interview_count DESC
        """
        
        result = await self.neo4j.execute_cypher(query, {"interview_ids": interview_ids})
        
        # Get total interview count for consensus calculation
        total_interviews = await self._get_total_interview_count(interview_ids)
        
        for record in result:
            tool_name = record['tool_name']
            interview_count = record['interview_count']
            consensus_strength = interview_count / total_interviews
            
            if consensus_strength >= threshold:
                patterns.append(ConsensusPattern(
                    pattern_type="tool_usage_consensus",
                    description=f"Strong consensus on usage of {tool_name}",
                    supporting_interviews=record['interview_ids'],
                    supporting_count=interview_count,
                    total_interviews=total_interviews,
                    consensus_strength=consensus_strength,
                    evidence=record['usage_evidence'],
                    metadata={
                        'tool_name': tool_name,
                        'usage_frequency': interview_count
                    }
                ))
        
        return patterns
    
    async def _analyze_sentiment_consensus(self,
                                         interview_ids: Optional[List[str]],
                                         threshold: float) -> List[ConsensusPattern]:
        """Analyze consensus on sentiment towards tools/methods"""
        patterns = []
        
        # Query for sentiment patterns
        query = """
        MATCH (p:Person)-[r]->(target)
        WHERE type(r) IN ['ADVOCATES_FOR', 'SKEPTICAL_OF', 'SUPPORTS', 'CRITICIZES']
          AND ($interview_ids IS NULL OR p.interview_id IN $interview_ids)
        RETURN target.name as target_name,
               type(r) as sentiment,
               collect(DISTINCT p.interview_id) as interview_ids,
               collect({
                   person: p.name,
                   interview: p.interview_id,
                   confidence: r.confidence,
                   context: r.context
               }) as sentiment_evidence,
               count(DISTINCT p.interview_id) as interview_count
        ORDER BY target_name, sentiment
        """
        
        result = await self.neo4j.execute_cypher(query, {"interview_ids": interview_ids})
        total_interviews = await self._get_total_interview_count(interview_ids)
        
        # Group by target to find consensus
        sentiment_by_target = defaultdict(list)
        for record in result:
            sentiment_by_target[record['target_name']].append(record)
        
        for target_name, sentiments in sentiment_by_target.items():
            # Find dominant sentiment
            sentiment_counts = Counter(s['sentiment'] for s in sentiments)
            if sentiment_counts:
                dominant_sentiment, dominant_count = sentiment_counts.most_common(1)[0]
                consensus_strength = dominant_count / total_interviews
                
                if consensus_strength >= threshold:
                    # Get evidence for dominant sentiment
                    dominant_evidence = [s for s in sentiments if s['sentiment'] == dominant_sentiment][0]
                    
                    patterns.append(ConsensusPattern(
                        pattern_type="sentiment_consensus",
                        description=f"Strong consensus: {dominant_sentiment} towards {target_name}",
                        supporting_interviews=dominant_evidence['interview_ids'],
                        supporting_count=dominant_count,
                        total_interviews=total_interviews,
                        consensus_strength=consensus_strength,
                        evidence=dominant_evidence['sentiment_evidence'],
                        metadata={
                            'target_name': target_name,
                            'sentiment': dominant_sentiment
                        }
                    ))
        
        return patterns
    
    async def _analyze_organizational_consensus(self,
                                              interview_ids: Optional[List[str]],
                                              threshold: float) -> List[ConsensusPattern]:
        """Analyze consensus on organizational aspects"""
        patterns = []
        
        # Query for organizational patterns
        query = """
        MATCH (p:Person)-[r:WORKS_AT]->(o:Organization)
        WHERE ($interview_ids IS NULL OR p.interview_id IN $interview_ids)
        WITH o.name as org_name, 
             collect(DISTINCT p.interview_id) as interview_ids,
             count(DISTINCT p.interview_id) as interview_count
        WHERE interview_count >= 2
        RETURN org_name, interview_ids, interview_count
        ORDER BY interview_count DESC
        """
        
        result = await self.neo4j.execute_cypher(query, {"interview_ids": interview_ids})
        total_interviews = await self._get_total_interview_count(interview_ids)
        
        for record in result:
            org_name = record['org_name']
            interview_count = record['interview_count']
            consensus_strength = interview_count / total_interviews
            
            if consensus_strength >= threshold:
                patterns.append(ConsensusPattern(
                    pattern_type="organizational_consensus",
                    description=f"Multiple interviews from {org_name}",
                    supporting_interviews=record['interview_ids'],
                    supporting_count=interview_count,
                    total_interviews=total_interviews,
                    consensus_strength=consensus_strength,
                    evidence=[],
                    metadata={
                        'organization': org_name,
                        'representation_level': interview_count
                    }
                ))
        
        return patterns
    
    async def _analyze_tool_sentiment_divergence(self,
                                               interview_ids: Optional[List[str]]) -> List[DivergencePattern]:
        """Analyze divergence in tool sentiment"""
        patterns = []
        
        # Query for conflicting sentiments towards same tools
        query = """
        MATCH (p:Person)-[r]->(t:Tool)
        WHERE type(r) IN ['ADVOCATES_FOR', 'SKEPTICAL_OF', 'SUPPORTS', 'CRITICIZES']
          AND ($interview_ids IS NULL OR p.interview_id IN $interview_ids)
        WITH t.name as tool_name,
             type(r) as sentiment,
             collect({
                 person: p.name,
                 interview: p.interview_id,
                 confidence: r.confidence,
                 context: r.context
             }) as evidence
        WITH tool_name,
             collect({sentiment: sentiment, evidence: evidence}) as sentiments
        WHERE size(sentiments) > 1
        RETURN tool_name, sentiments
        """
        
        result = await self.neo4j.execute_cypher(query, {"interview_ids": interview_ids})
        
        for record in result:
            tool_name = record['tool_name']
            sentiments = record['sentiments']
            
            # Check if there are actually conflicting sentiments
            sentiment_types = [s['sentiment'] for s in sentiments]
            positive_sentiments = {'ADVOCATES_FOR', 'SUPPORTS'}
            negative_sentiments = {'SKEPTICAL_OF', 'CRITICIZES'}
            
            has_positive = any(s in positive_sentiments for s in sentiment_types)
            has_negative = any(s in negative_sentiments for s in sentiment_types)
            
            if has_positive and has_negative:
                # Create perspective groups
                perspective_groups = {}
                conflicting_perspectives = []
                
                for sentiment_data in sentiments:
                    sentiment = sentiment_data['sentiment']
                    evidence = sentiment_data['evidence']
                    
                    perspective = "positive" if sentiment in positive_sentiments else "negative"
                    
                    if perspective not in perspective_groups:
                        perspective_groups[perspective] = []
                        conflicting_perspectives.append({
                            'perspective': perspective,
                            'sentiment': sentiment,
                            'evidence_count': len(evidence),
                            'evidence': evidence
                        })
                    
                    perspective_groups[perspective].extend([e['interview'] for e in evidence])
                
                patterns.append(DivergencePattern(
                    pattern_type="tool_sentiment_divergence",
                    description=f"Conflicting sentiments towards {tool_name}",
                    conflicting_perspectives=conflicting_perspectives,
                    interview_groups=perspective_groups,
                    metadata={
                        'tool_name': tool_name,
                        'conflict_type': 'positive_vs_negative'
                    }
                ))
        
        return patterns
    
    async def _analyze_organizational_perspective_divergence(self,
                                                           interview_ids: Optional[List[str]]) -> List[DivergencePattern]:
        """Analyze divergence by organizational affiliation"""
        patterns = []
        
        # This would analyze how different organizations have different perspectives
        # Implementation would be similar to tool sentiment but grouped by organization
        
        return patterns
    
    async def _analyze_method_preference_divergence(self,
                                                   interview_ids: Optional[List[str]]) -> List[DivergencePattern]:
        """Analyze divergence in methodology preferences"""
        patterns = []
        
        # This would analyze conflicting preferences for research methods
        # Implementation would identify where different people prefer different approaches
        
        return patterns
    
    async def _analyze_tool_adoption_evolution(self,
                                             interview_ids: Optional[List[str]]) -> List[EvolutionPattern]:
        """Analyze evolution of tool adoption over time"""
        patterns = []
        
        # Query for temporal patterns in tool usage
        query = """
        MATCH (p:Person)-[r:USES]->(t:Tool)
        WHERE ($interview_ids IS NULL OR p.interview_id IN $interview_ids)
          AND p.interview_date IS NOT NULL
        WITH t.name as tool_name,
             p.interview_date as interview_date,
             count(*) as usage_count
        ORDER BY tool_name, interview_date
        RETURN tool_name,
               collect({date: interview_date, usage_count: usage_count}) as timeline
        """
        
        result = await self.neo4j.execute_cypher(query, {"interview_ids": interview_ids})
        
        for record in result:
            tool_name = record['tool_name']
            timeline = record['timeline']
            
            if len(timeline) >= 3:  # Need at least 3 points for trend analysis
                # Analyze trend direction
                usage_counts = [point['usage_count'] for point in timeline]
                trend_direction = self._calculate_trend_direction(usage_counts)
                
                patterns.append(EvolutionPattern(
                    pattern_type="tool_adoption_evolution",
                    description=f"Evolution of {tool_name} adoption over time",
                    timeline=timeline,
                    trend_direction=trend_direction,
                    metadata={
                        'tool_name': tool_name,
                        'data_points': len(timeline),
                        'total_usage': sum(usage_counts)
                    }
                ))
        
        return patterns
    
    async def _analyze_organizational_evolution(self,
                                              interview_ids: Optional[List[str]]) -> List[EvolutionPattern]:
        """Analyze organizational changes over time"""
        patterns = []
        
        # This would analyze how organizational structures/attitudes change over time
        # Implementation would look for temporal patterns in organizational relationships
        
        return patterns
    
    async def _get_total_interview_count(self, interview_ids: Optional[List[str]]) -> int:
        """Get total number of interviews in scope"""
        query = """
        MATCH (p:Person)
        WHERE ($interview_ids IS NULL OR p.interview_id IN $interview_ids)
        RETURN count(DISTINCT p.interview_id) as total_interviews
        """
        
        result = await self.neo4j.execute_cypher(query, {"interview_ids": interview_ids})
        return result[0]['total_interviews'] if result else 0
    
    def _calculate_trend_direction(self, values: List[int]) -> str:
        """Calculate trend direction from a series of values"""
        if len(values) < 2:
            return "stable"
        
        # Simple trend analysis
        increases = sum(1 for i in range(1, len(values)) if values[i] > values[i-1])
        decreases = sum(1 for i in range(1, len(values)) if values[i] < values[i-1])
        
        total_changes = increases + decreases
        if total_changes == 0:
            return "stable"
        
        increase_ratio = increases / total_changes
        
        if increase_ratio > 0.7:
            return "increasing"
        elif increase_ratio < 0.3:
            return "decreasing"
        else:
            return "stable"


class CrossInterviewQueryBuilder:
    """Build cross-interview analysis queries"""
    
    def __init__(self, analyzer: CrossInterviewAnalyzer):
        self.analyzer = analyzer
    
    async def find_knowledge_gaps(self, 
                                interview_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Identify knowledge gaps - things mentioned by few people
        
        Returns:
            Dictionary with gap analysis results
        """
        # Tools mentioned by only 1-2 people
        tool_gaps_query = """
        MATCH (p:Person)-[r:USES]->(t:Tool)
        WHERE ($interview_ids IS NULL OR p.interview_id IN $interview_ids)
        WITH t.name as tool_name,
             count(DISTINCT p.interview_id) as mention_count,
             collect(DISTINCT p.name) as mentioning_people
        WHERE mention_count <= 2
        RETURN tool_name, mention_count, mentioning_people
        ORDER BY mention_count ASC
        """
        
        tool_gaps = await self.analyzer.neo4j.execute_cypher(tool_gaps_query, {"interview_ids": interview_ids})
        
        # Methods mentioned by few people
        method_gaps_query = """
        MATCH (p:Person)-[r:USES]->(m:Method)
        WHERE ($interview_ids IS NULL OR p.interview_id IN $interview_ids)
        WITH m.name as method_name,
             count(DISTINCT p.interview_id) as mention_count,
             collect(DISTINCT p.name) as mentioning_people
        WHERE mention_count <= 2
        RETURN method_name, mention_count, mentioning_people
        ORDER BY mention_count ASC
        """
        
        method_gaps = await self.analyzer.neo4j.execute_cypher(method_gaps_query, {"interview_ids": interview_ids})
        
        return {
            'tool_knowledge_gaps': [dict(record) for record in tool_gaps],
            'method_knowledge_gaps': [dict(record) for record in method_gaps],
            'gap_analysis_date': datetime.utcnow().isoformat()
        }
    
    async def analyze_innovation_diffusion(self,
                                         interview_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze how innovations/tools diffuse through the organization
        
        Returns:
            Innovation diffusion analysis
        """
        # Find early adopters vs late adopters
        diffusion_query = """
        MATCH (p:Person)-[r:USES]->(t:Tool)
        WHERE ($interview_ids IS NULL OR p.interview_id IN $interview_ids)
          AND p.interview_date IS NOT NULL
        WITH t.name as tool_name,
             p.name as person_name,
             p.interview_date as adoption_date,
             p.role as person_role
        ORDER BY tool_name, adoption_date
        RETURN tool_name,
               collect({
                   person: person_name,
                   date: adoption_date,
                   role: person_role
               }) as adoption_timeline
        """
        
        diffusion_data = await self.analyzer.neo4j.execute_cypher(diffusion_query, {"interview_ids": interview_ids})
        
        return {
            'innovation_diffusion': [dict(record) for record in diffusion_data],
            'analysis_date': datetime.utcnow().isoformat()
        }


@dataclass
class QuoteEvidencedPattern:
    """Consensus or divergence pattern with supporting quote evidence"""
    pattern_type: str
    description: str
    supporting_interviews: List[str]
    consensus_strength: float
    quote_evidence: List[Dict[str, Any]]  # quotes with line numbers and sources
    metadata: Dict[str, Any]


@dataclass
class ContradictoryQuotes:
    """Represents contradictory quotes on the same topic"""
    topic: str
    conflicting_quotes: List[Dict[str, Any]]
    interview_sources: List[str]
    confidence_scores: List[float]
    metadata: Dict[str, Any]


class QuoteCentricCrossAnalyzer:
    """
    Enhanced cross-interview analyzer with quote evidence support
    
    This addresses the critical enhancement specified in CLAUDE.md Phase 3B,
    providing all consensus and divergence patterns with supporting quote evidence
    including line numbers and interview sources.
    """
    
    def __init__(self, neo4j_manager: EnhancedNeo4jManager):
        self.neo4j = neo4j_manager
        self.traditional_analyzer = CrossInterviewAnalyzer(neo4j_manager)  # Backward compatibility
    
    async def analyze_consensus_with_evidence(self, 
                                            interview_ids: Optional[List[str]] = None,
                                            min_consensus_threshold: float = 0.6) -> List[QuoteEvidencedPattern]:
        """
        Identify consensus patterns with supporting quote evidence
        
        Args:
            interview_ids: Specific interviews to analyze (None for all)
            min_consensus_threshold: Minimum agreement level (0.0-1.0)
            
        Returns:
            List of consensus patterns with quote evidence
        """
        patterns = []
        
        # Entity-code consensus with quote evidence
        entity_code_patterns = await self._analyze_entity_code_consensus_with_quotes(interview_ids, min_consensus_threshold)
        patterns.extend(entity_code_patterns)
        
        # Tool usage consensus with quote evidence
        tool_patterns = await self._analyze_tool_consensus_with_quotes(interview_ids, min_consensus_threshold)
        patterns.extend(tool_patterns)
        
        # Method consensus with quote evidence
        method_patterns = await self._analyze_method_consensus_with_quotes(interview_ids, min_consensus_threshold)
        patterns.extend(method_patterns)
        
        return patterns
    
    async def find_contradictory_quotes(self,
                                      topic_entities: Optional[List[str]] = None,
                                      interview_ids: Optional[List[str]] = None) -> List[ContradictoryQuotes]:
        """
        Find contradictory quotes on the same topics
        
        Args:
            topic_entities: Specific entities/topics to analyze for contradictions
            interview_ids: Specific interviews to analyze (None for all)
            
        Returns:
            List of contradictory quote patterns
        """
        contradictions = []
        
        # Find entity-based contradictions
        entity_contradictions = await self._find_entity_contradictions(topic_entities, interview_ids)
        contradictions.extend(entity_contradictions)
        
        # Find code-based contradictions
        code_contradictions = await self._find_code_contradictions(interview_ids)
        contradictions.extend(code_contradictions)
        
        return contradictions
    
    async def _analyze_entity_code_consensus_with_quotes(self,
                                                       interview_ids: Optional[List[str]],
                                                       threshold: float) -> List[QuoteEvidencedPattern]:
        """Analyze entity-code relationships with supporting quotes"""
        patterns = []
        
        # Query for entity-code relationships with quote evidence
        query = """
        MATCH (e:Entity)<-[r1:MENTIONS]-(q:Quote)-[r2:SUPPORTS]->(c:Code)
        WHERE ($interview_ids IS NULL OR q.interview_id IN $interview_ids)
        WITH e.name as entity_name,
             e.entity_type as entity_type,
             c.name as code_name,
             collect({
                 quote_text: q.text,
                 quote_line_start: q.line_start,
                 quote_line_end: q.line_end,
                 interview_id: q.interview_id,
                 mention_confidence: r1.confidence,
                 support_confidence: r2.confidence,
                 semantic_type: q.semantic_type
             }) as quote_evidence,
             collect(DISTINCT q.interview_id) as supporting_interviews,
             count(DISTINCT q.interview_id) as interview_count
        WHERE interview_count >= 2
        RETURN entity_name, entity_type, code_name, quote_evidence, supporting_interviews, interview_count
        ORDER BY interview_count DESC
        """
        
        result = await self.neo4j.execute_cypher(query, {"interview_ids": interview_ids})
        total_interviews = await self._get_total_interview_count(interview_ids)
        
        for record in result:
            entity_name = record['entity_name']
            entity_type = record['entity_type']
            code_name = record['code_name']
            interview_count = record['interview_count']
            consensus_strength = interview_count / total_interviews
            
            if consensus_strength >= threshold:
                patterns.append(QuoteEvidencedPattern(
                    pattern_type="entity_code_consensus_with_quotes",
                    description=f"Strong consensus: {entity_name} ({entity_type}) relates to {code_name}",
                    supporting_interviews=record['supporting_interviews'],
                    consensus_strength=consensus_strength,
                    quote_evidence=record['quote_evidence'],
                    metadata={
                        'entity_name': entity_name,
                        'entity_type': entity_type,
                        'code_name': code_name,
                        'evidence_count': len(record['quote_evidence']),
                        'interview_count': interview_count
                    }
                ))
        
        return patterns
    
    async def _analyze_tool_consensus_with_quotes(self,
                                                interview_ids: Optional[List[str]],
                                                threshold: float) -> List[QuoteEvidencedPattern]:
        """Analyze tool usage consensus with supporting quotes"""
        patterns = []
        
        # Query for tool usage with quote evidence
        query = """
        MATCH (t:Tool)<-[r1:MENTIONS]-(q:Quote)-[r2:SUPPORTS]->(c:Code)
        WHERE c.name IN ['tool_usage', 'technology_adoption', 'software_tools', 'implementation']
          AND ($interview_ids IS NULL OR q.interview_id IN $interview_ids)
        WITH t.name as tool_name,
             collect({
                 quote_text: q.text,
                 quote_line_start: q.line_start,
                 quote_line_end: q.line_end,
                 interview_id: q.interview_id,
                 mention_confidence: r1.confidence,
                 support_confidence: r2.confidence,
                 code_name: c.name
             }) as quote_evidence,
             collect(DISTINCT q.interview_id) as supporting_interviews,
             count(DISTINCT q.interview_id) as interview_count
        WHERE interview_count >= 2
        RETURN tool_name, quote_evidence, supporting_interviews, interview_count
        ORDER BY interview_count DESC
        """
        
        result = await self.neo4j.execute_cypher(query, {"interview_ids": interview_ids})
        total_interviews = await self._get_total_interview_count(interview_ids)
        
        for record in result:
            tool_name = record['tool_name']
            interview_count = record['interview_count']
            consensus_strength = interview_count / total_interviews
            
            if consensus_strength >= threshold:
                patterns.append(QuoteEvidencedPattern(
                    pattern_type="tool_consensus_with_quotes",
                    description=f"Strong consensus on tool usage: {tool_name}",
                    supporting_interviews=record['supporting_interviews'],
                    consensus_strength=consensus_strength,
                    quote_evidence=record['quote_evidence'],
                    metadata={
                        'tool_name': tool_name,
                        'evidence_count': len(record['quote_evidence']),
                        'interview_count': interview_count
                    }
                ))
        
        return patterns
    
    async def _analyze_method_consensus_with_quotes(self,
                                                  interview_ids: Optional[List[str]],
                                                  threshold: float) -> List[QuoteEvidencedPattern]:
        """Analyze method usage consensus with supporting quotes"""
        patterns = []
        
        # Query for method usage with quote evidence
        query = """
        MATCH (m:Method)<-[r1:MENTIONS]-(q:Quote)-[r2:SUPPORTS]->(c:Code)
        WHERE ($interview_ids IS NULL OR q.interview_id IN $interview_ids)
        WITH m.name as method_name,
             collect({
                 quote_text: q.text,
                 quote_line_start: q.line_start,
                 quote_line_end: q.line_end,
                 interview_id: q.interview_id,
                 mention_confidence: r1.confidence,
                 support_confidence: r2.confidence,
                 code_name: c.name
             }) as quote_evidence,
             collect(DISTINCT q.interview_id) as supporting_interviews,
             count(DISTINCT q.interview_id) as interview_count
        WHERE interview_count >= 2
        RETURN method_name, quote_evidence, supporting_interviews, interview_count
        ORDER BY interview_count DESC
        """
        
        result = await self.neo4j.execute_cypher(query, {"interview_ids": interview_ids})
        total_interviews = await self._get_total_interview_count(interview_ids)
        
        for record in result:
            method_name = record['method_name']
            interview_count = record['interview_count']
            consensus_strength = interview_count / total_interviews
            
            if consensus_strength >= threshold:
                patterns.append(QuoteEvidencedPattern(
                    pattern_type="method_consensus_with_quotes",
                    description=f"Strong consensus on method: {method_name}",
                    supporting_interviews=record['supporting_interviews'],
                    consensus_strength=consensus_strength,
                    quote_evidence=record['quote_evidence'],
                    metadata={
                        'method_name': method_name,
                        'evidence_count': len(record['quote_evidence']),
                        'interview_count': interview_count
                    }
                ))
        
        return patterns
    
    async def _find_entity_contradictions(self,
                                        topic_entities: Optional[List[str]],
                                        interview_ids: Optional[List[str]]) -> List[ContradictoryQuotes]:
        """Find contradictory quotes about specific entities"""
        contradictions = []
        
        # Query for potentially contradictory quotes about entities
        # This looks for the same entity mentioned in different codes that might conflict
        query = """
        MATCH (e:Entity)<-[r1:MENTIONS]-(q1:Quote)-[r2:SUPPORTS]->(c1:Code),
              (e)<-[r3:MENTIONS]-(q2:Quote)-[r4:SUPPORTS]->(c2:Code)
        WHERE c1.name <> c2.name
          AND q1.interview_id <> q2.interview_id
          AND ($topic_entities IS NULL OR e.name IN $topic_entities)
          AND ($interview_ids IS NULL OR (q1.interview_id IN $interview_ids AND q2.interview_id IN $interview_ids))
        WITH e.name as entity_name,
             e.entity_type as entity_type,
             collect(DISTINCT {
                 quote_text: q1.text,
                 quote_line_start: q1.line_start,
                 quote_line_end: q1.line_end,
                 interview_id: q1.interview_id,
                 code_name: c1.name,
                 confidence: r2.confidence
             }) + collect(DISTINCT {
                 quote_text: q2.text,
                 quote_line_start: q2.line_start,
                 quote_line_end: q2.line_end,
                 interview_id: q2.interview_id,
                 code_name: c2.name,
                 confidence: r4.confidence
             }) as conflicting_quotes,
             collect(DISTINCT q1.interview_id) + collect(DISTINCT q2.interview_id) as interview_sources
        WHERE size(conflicting_quotes) >= 2
        RETURN entity_name, entity_type, conflicting_quotes, interview_sources
        ORDER BY size(conflicting_quotes) DESC
        """
        
        result = await self.neo4j.execute_cypher(query, {
            "topic_entities": topic_entities,
            "interview_ids": interview_ids
        })
        
        for record in result:
            entity_name = record['entity_name']
            entity_type = record['entity_type']
            conflicting_quotes = record['conflicting_quotes']
            interview_sources = list(set(record['interview_sources']))  # Remove duplicates
            
            # Check if there are actually contradictory codes
            codes_mentioned = list(set(quote['code_name'] for quote in conflicting_quotes))
            if len(codes_mentioned) >= 2:
                confidence_scores = [quote['confidence'] for quote in conflicting_quotes if quote['confidence']]
                
                contradictions.append(ContradictoryQuotes(
                    topic=f"{entity_name} ({entity_type})",
                    conflicting_quotes=conflicting_quotes,
                    interview_sources=interview_sources,
                    confidence_scores=confidence_scores,
                    metadata={
                        'entity_name': entity_name,
                        'entity_type': entity_type,
                        'codes_in_conflict': codes_mentioned,
                        'quote_count': len(conflicting_quotes),
                        'interview_count': len(interview_sources)
                    }
                ))
        
        return contradictions
    
    async def _find_code_contradictions(self,
                                      interview_ids: Optional[List[str]]) -> List[ContradictoryQuotes]:
        """Find contradictory quotes within the same code across interviews"""
        contradictions = []
        
        # This would look for quotes that support the same code but express conflicting viewpoints
        # Implementation would analyze semantic content of quotes for conflicting sentiment
        # For now, return empty as this requires more sophisticated NLP analysis
        
        return contradictions
    
    async def _get_total_interview_count(self, interview_ids: Optional[List[str]]) -> int:
        """Get total number of interviews in scope"""
        query = """
        MATCH (q:Quote)
        WHERE ($interview_ids IS NULL OR q.interview_id IN $interview_ids)
        RETURN count(DISTINCT q.interview_id) as total_interviews
        """
        
        result = await self.neo4j.execute_cypher(query, {"interview_ids": interview_ids})
        return result[0]['total_interviews'] if result else 0