"""
Advanced Quote Analytics Module

Provides statistical pattern detection, temporal analysis, and contradiction
mapping for quote-centric qualitative research analysis.
"""

import asyncio
import logging
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict, Counter
import math

logger = logging.getLogger(__name__)


@dataclass
class QuoteFrequencyPattern:
    """Results of quote frequency analysis"""
    entity_name: str
    code_name: str
    quote_count: int
    interview_count: int
    frequency_per_interview: float
    confidence_score: float
    statistical_significance: float
    supporting_quotes: List[Dict[str, Any]]


@dataclass
class QuoteEvolutionPattern:
    """Results of quote evolution analysis over time"""
    entity_name: str
    timeline_patterns: List[Dict[str, Any]]
    evolution_trend: str  # "increasing", "decreasing", "stable", "cyclical"
    trend_confidence: float
    key_transition_points: List[Dict[str, Any]]
    supporting_evidence: List[Dict[str, Any]]


@dataclass
class ContradictionPattern:
    """Results of contradiction analysis"""
    topic: str
    contradiction_type: str  # "direct", "nuanced", "temporal"
    conflicting_perspectives: List[Dict[str, Any]]
    contradiction_strength: float
    resolution_potential: float
    supporting_quotes: List[Dict[str, Any]]


class QuotePatternAnalyzer:
    """
    Advanced quote pattern analysis with statistical significance testing
    """
    
    def __init__(self, neo4j_manager):
        self.neo4j = neo4j_manager
        self.significance_threshold = 0.05  # p < 0.05 for statistical significance
        
    async def analyze_quote_frequency_patterns(self, interview_ids: List[str]) -> List[QuoteFrequencyPattern]:
        """
        Analyze quote frequency patterns with statistical significance
        
        Args:
            interview_ids: List of interview identifiers to analyze
            
        Returns:
            List of statistically significant quote frequency patterns
        """
        logger.info(f"Analyzing quote frequency patterns across {len(interview_ids)} interviews")
        
        # Get all entity-code relationships with quote evidence
        frequency_query = """
        MATCH (e:Entity)<-[r1:MENTIONS]-(q:Quote)-[r2:SUPPORTS]->(c:Code)
        WHERE q.interview_id IN $interview_ids
        RETURN e.name as entity_name,
               c.name as code_name,
               q.interview_id as interview_id,
               q.text as quote_text,
               q.line_start as quote_line,
               r1.confidence as mention_confidence,
               r2.confidence as support_confidence
        """
        
        results = await self.neo4j.execute_cypher(frequency_query, {"interview_ids": interview_ids})
        
        if not results:
            logger.warning("No entity-code relationships with quote evidence found")
            return []
        
        # Group by entity-code pairs
        entity_code_quotes = defaultdict(list)
        for result in results:
            key = (result['entity_name'], result['code_name'])
            entity_code_quotes[key].append(result)
        
        patterns = []
        
        for (entity_name, code_name), quotes in entity_code_quotes.items():
            # Calculate frequency statistics
            quote_count = len(quotes)
            interview_set = set(quote['interview_id'] for quote in quotes)
            interview_count = len(interview_set)
            frequency_per_interview = quote_count / interview_count if interview_count > 0 else 0
            
            # Calculate confidence score (average of mention and support confidences)
            confidence_scores = []
            for quote in quotes:
                mention_conf = quote.get('mention_confidence', 0) or 0
                support_conf = quote.get('support_confidence', 0) or 0
                confidence_scores.append((mention_conf + support_conf) / 2)
            
            avg_confidence = statistics.mean(confidence_scores) if confidence_scores else 0
            
            # Statistical significance (simplified chi-square test)
            expected_frequency = len(interview_ids) * 0.1  # Assume 10% baseline frequency
            statistical_significance = self._calculate_significance(quote_count, expected_frequency)
            
            # Only include statistically significant patterns
            if statistical_significance < self.significance_threshold and quote_count >= 2:
                supporting_quotes = []
                for quote in quotes[:3]:  # Top 3 supporting quotes
                    supporting_quotes.append({
                        'text': quote['quote_text'],
                        'line_start': quote['quote_line'],
                        'interview_id': quote['interview_id'],
                        'mention_confidence': quote.get('mention_confidence', 0),
                        'support_confidence': quote.get('support_confidence', 0)
                    })
                
                pattern = QuoteFrequencyPattern(
                    entity_name=entity_name,
                    code_name=code_name,
                    quote_count=quote_count,
                    interview_count=interview_count,
                    frequency_per_interview=frequency_per_interview,
                    confidence_score=avg_confidence,
                    statistical_significance=statistical_significance,
                    supporting_quotes=supporting_quotes
                )
                patterns.append(pattern)
        
        # Sort by statistical significance and confidence
        patterns.sort(key=lambda p: (p.statistical_significance, -p.confidence_score))
        
        logger.info(f"Found {len(patterns)} statistically significant quote frequency patterns")
        return patterns
    
    def _calculate_significance(self, observed: int, expected: float) -> float:
        """Calculate statistical significance using simplified chi-square test"""
        if expected == 0:
            return 1.0
        
        chi_square = ((observed - expected) ** 2) / expected
        # Simplified p-value approximation (more sophisticated would use chi-square distribution)
        p_value = math.exp(-chi_square / 2)
        return min(p_value, 1.0)
    
    async def detect_quote_evolution_patterns(self, entity_name: str, interview_ids: List[str]) -> QuoteEvolutionPattern:
        """
        Detect how quotes about an entity evolve across interviews
        
        Args:
            entity_name: Name of entity to analyze
            interview_ids: Ordered list of interview IDs (chronological)
            
        Returns:
            Quote evolution pattern analysis
        """
        logger.info(f"Analyzing quote evolution patterns for entity: {entity_name}")
        
        evolution_query = """
        MATCH (e:Entity {name: $entity_name})<-[r:MENTIONS]-(q:Quote)
        WHERE q.interview_id IN $interview_ids
        RETURN q.interview_id as interview_id,
               q.text as quote_text,
               q.line_start as quote_line,
               q.confidence as quote_confidence,
               r.confidence as mention_confidence
        ORDER BY q.interview_id
        """
        
        results = await self.neo4j.execute_cypher(
            evolution_query, 
            {"entity_name": entity_name, "interview_ids": interview_ids}
        )
        
        if not results:
            logger.warning(f"No quotes found for entity: {entity_name}")
            return QuoteEvolutionPattern(
                entity_name=entity_name,
                timeline_patterns=[],
                evolution_trend="no_data",
                trend_confidence=0.0,
                key_transition_points=[],
                supporting_evidence=[]
            )
        
        # Group quotes by interview
        interview_quotes = defaultdict(list)
        for result in results:
            interview_quotes[result['interview_id']].append(result)
        
        # Build timeline patterns
        timeline_patterns = []
        quote_counts = []
        confidence_scores = []
        
        for interview_id in interview_ids:
            quotes = interview_quotes.get(interview_id, [])
            quote_count = len(quotes)
            avg_confidence = statistics.mean([q.get('quote_confidence', 0) or 0 for q in quotes]) if quotes else 0
            
            timeline_patterns.append({
                'interview_id': interview_id,
                'quote_count': quote_count,
                'average_confidence': avg_confidence,
                'sample_quotes': [q['quote_text'][:50] + "..." for q in quotes[:2]]
            })
            
            quote_counts.append(quote_count)
            confidence_scores.append(avg_confidence)
        
        # Detect trend
        evolution_trend, trend_confidence = self._detect_trend(quote_counts)
        
        # Identify key transition points
        key_transition_points = self._identify_transition_points(timeline_patterns)
        
        # Supporting evidence
        supporting_evidence = []
        for result in results[:5]:  # Top 5 quotes as evidence
            supporting_evidence.append({
                'quote_text': result['quote_text'],
                'interview_id': result['interview_id'],
                'line_start': result['quote_line'],
                'confidence': result.get('quote_confidence', 0)
            })
        
        return QuoteEvolutionPattern(
            entity_name=entity_name,
            timeline_patterns=timeline_patterns,
            evolution_trend=evolution_trend,
            trend_confidence=trend_confidence,
            key_transition_points=key_transition_points,
            supporting_evidence=supporting_evidence
        )
    
    def _detect_trend(self, values: List[float]) -> Tuple[str, float]:
        """Detect trend in time series data"""
        if len(values) < 3:
            return "insufficient_data", 0.0
        
        # Simple linear regression to detect trend
        n = len(values)
        x = list(range(n))
        
        # Calculate correlation coefficient
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(values)
        
        numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
        denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n))
        denominator_y = sum((values[i] - mean_y) ** 2 for i in range(n))
        
        if denominator_x == 0 or denominator_y == 0:
            return "stable", 0.5
        
        correlation = numerator / math.sqrt(denominator_x * denominator_y)
        
        # Determine trend based on correlation
        if abs(correlation) < 0.3:
            trend = "stable"
        elif correlation > 0.3:
            trend = "increasing"
        else:
            trend = "decreasing"
        
        confidence = abs(correlation)
        return trend, confidence
    
    def _identify_transition_points(self, timeline_patterns: List[Dict]) -> List[Dict]:
        """Identify key transition points in quote patterns"""
        if len(timeline_patterns) < 3:
            return []
        
        transition_points = []
        
        for i in range(1, len(timeline_patterns) - 1):
            prev_count = timeline_patterns[i-1]['quote_count']
            curr_count = timeline_patterns[i]['quote_count']
            next_count = timeline_patterns[i+1]['quote_count']
            
            # Check for significant changes
            if curr_count > prev_count * 1.5 and curr_count > next_count * 1.5:
                transition_points.append({
                    'interview_id': timeline_patterns[i]['interview_id'],
                    'transition_type': 'spike',
                    'magnitude': curr_count - prev_count,
                    'description': f'Quote frequency spike: {curr_count} quotes (vs {prev_count} previous)'
                })
            elif curr_count < prev_count * 0.5 and curr_count < next_count * 0.5:
                transition_points.append({
                    'interview_id': timeline_patterns[i]['interview_id'],
                    'transition_type': 'drop',
                    'magnitude': prev_count - curr_count,
                    'description': f'Quote frequency drop: {curr_count} quotes (vs {prev_count} previous)'
                })
        
        return transition_points
    
    async def analyze_speaker_perspective_patterns(self, interview_ids: List[str]) -> Dict[str, Any]:
        """
        Analyze patterns in speaker perspectives across interviews
        
        Args:
            interview_ids: List of interview identifiers
            
        Returns:
            Speaker perspective pattern analysis
        """
        logger.info(f"Analyzing speaker perspective patterns across {len(interview_ids)} interviews")
        
        # This would require speaker information in quotes
        # For now, return a placeholder structure
        return {
            'analysis_type': 'speaker_perspective_patterns',
            'interview_count': len(interview_ids),
            'patterns_detected': [],
            'confidence_score': 0.0,
            'notes': 'Speaker perspective analysis requires speaker metadata in quotes'
        }


class ContradictionMapper:
    """
    Map and analyze contradictions in quote relationships
    """
    
    def __init__(self, neo4j_manager):
        self.neo4j = neo4j_manager
        self.contradiction_threshold = 0.6  # Minimum strength to consider significant
    
    async def build_contradiction_network(self, topic: str) -> Dict[str, Any]:
        """
        Build a network of contradictory quotes around a topic
        
        Args:
            topic: Topic/entity name to analyze for contradictions
            
        Returns:
            Contradiction network structure
        """
        logger.info(f"Building contradiction network for topic: {topic}")
        
        # Find quotes that mention the topic
        topic_query = """
        MATCH (e:Entity)<-[r:MENTIONS]-(q:Quote)
        WHERE e.name CONTAINS $topic OR e.name = $topic
        OPTIONAL MATCH (q)-[s:SUPPORTS]->(c:Code)
        RETURN q.id as quote_id,
               q.text as quote_text,
               q.interview_id as interview_id,
               q.line_start as line_start,
               q.confidence as quote_confidence,
               e.name as entity_name,
               c.name as code_name
        """
        
        results = await self.neo4j.execute_cypher(topic_query, {"topic": topic})
        
        if len(results) < 2:
            logger.warning(f"Insufficient quotes found for contradiction analysis of topic: {topic}")
            return {
                'topic': topic,
                'contradiction_network': {},
                'contradictions_found': 0,
                'analysis_confidence': 0.0
            }
        
        # Group quotes by the codes they support
        code_quotes = defaultdict(list)
        all_quotes = {}
        
        for result in results:
            quote_id = result['quote_id']
            all_quotes[quote_id] = result
            
            if result['code_name']:
                code_quotes[result['code_name']].append(result)
        
        # Find potential contradictions (same entity, different codes)
        contradictions = []
        codes = list(code_quotes.keys())
        
        for i in range(len(codes)):
            for j in range(i + 1, len(codes)):
                code1, code2 = codes[i], codes[j]
                quotes1 = code_quotes[code1]
                quotes2 = code_quotes[code2]
                
                # Check if quotes from different interviews suggest different things
                interviews1 = set(q['interview_id'] for q in quotes1)
                interviews2 = set(q['interview_id'] for q in quotes2)
                
                if interviews1 != interviews2:  # Different interview sources
                    contradiction_strength = self._assess_contradiction_strength(quotes1, quotes2)
                    
                    if contradiction_strength > self.contradiction_threshold:
                        contradictions.append({
                            'code1': code1,
                            'code2': code2,
                            'quotes1': quotes1[:2],  # Sample quotes
                            'quotes2': quotes2[:2],  # Sample quotes
                            'strength': contradiction_strength,
                            'interview_sources1': list(interviews1),
                            'interview_sources2': list(interviews2)
                        })
        
        return {
            'topic': topic,
            'contradiction_network': {
                'nodes': [{'id': code, 'type': 'code'} for code in codes],
                'edges': [
                    {
                        'source': c['code1'],
                        'target': c['code2'],
                        'type': 'contradiction',
                        'strength': c['strength']
                    }
                    for c in contradictions
                ]
            },
            'contradictions_found': len(contradictions),
            'detailed_contradictions': contradictions,
            'analysis_confidence': self._calculate_network_confidence(contradictions, len(results))
        }
    
    def _assess_contradiction_strength(self, quotes1: List[Dict], quotes2: List[Dict]) -> float:
        """Assess the strength of contradiction between two sets of quotes"""
        # Simple heuristic: more quotes from different interviews = stronger contradiction
        interviews1 = set(q['interview_id'] for q in quotes1)
        interviews2 = set(q['interview_id'] for q in quotes2)
        
        # No overlap in interviews suggests potential contradiction
        overlap = len(interviews1.intersection(interviews2))
        total_interviews = len(interviews1.union(interviews2))
        
        if total_interviews == 0:
            return 0.0
        
        # Higher strength when there's less overlap
        contradiction_strength = 1.0 - (overlap / total_interviews)
        
        # Boost strength if we have multiple quotes from each perspective
        if len(quotes1) > 1 and len(quotes2) > 1:
            contradiction_strength *= 1.2
        
        return min(contradiction_strength, 1.0)
    
    def _calculate_network_confidence(self, contradictions: List[Dict], total_quotes: int) -> float:
        """Calculate confidence in the contradiction network analysis"""
        if total_quotes < 3:
            return 0.2
        
        if not contradictions:
            return 0.8  # High confidence in no contradictions if we have enough data
        
        # Confidence based on number of contradictions and quote coverage
        avg_strength = statistics.mean([c['strength'] for c in contradictions])
        coverage_factor = min(total_quotes / 10, 1.0)  # More quotes = higher confidence
        
        return avg_strength * coverage_factor
    
    async def analyze_perspective_clusters(self, interview_ids: List[str]) -> Dict[str, Any]:
        """
        Cluster perspectives based on quote patterns
        
        Args:
            interview_ids: List of interview identifiers
            
        Returns:
            Perspective clustering analysis
        """
        logger.info(f"Analyzing perspective clusters across {len(interview_ids)} interviews")
        
        # Find all entity-code relationships with quotes
        cluster_query = """
        MATCH (e:Entity)<-[r1:MENTIONS]-(q:Quote)-[r2:SUPPORTS]->(c:Code)
        WHERE q.interview_id IN $interview_ids
        RETURN q.interview_id as interview_id,
               e.name as entity_name,
               c.name as code_name,
               count(q) as quote_count
        """
        
        results = await self.neo4j.execute_cypher(cluster_query, {"interview_ids": interview_ids})
        
        if not results:
            return {
                'clusters': [],
                'cluster_count': 0,
                'analysis_confidence': 0.0
            }
        
        # Build interview profiles based on entity-code patterns
        interview_profiles = defaultdict(dict)
        all_entity_codes = set()
        
        for result in results:
            interview_id = result['interview_id']
            entity_code = f"{result['entity_name']}::{result['code_name']}"
            quote_count = result['quote_count']
            
            interview_profiles[interview_id][entity_code] = quote_count
            all_entity_codes.add(entity_code)
        
        # Simple clustering based on shared entity-code patterns
        clusters = []
        processed_interviews = set()
        
        for interview_id, profile in interview_profiles.items():
            if interview_id in processed_interviews:
                continue
                
            cluster = {
                'cluster_id': len(clusters) + 1,
                'interviews': [interview_id],
                'shared_patterns': list(profile.keys()),
                'pattern_strength': sum(profile.values())
            }
            
            processed_interviews.add(interview_id)
            
            # Find similar interviews
            for other_interview, other_profile in interview_profiles.items():
                if other_interview in processed_interviews:
                    continue
                
                # Calculate similarity (Jaccard similarity)
                common_patterns = set(profile.keys()).intersection(set(other_profile.keys()))
                total_patterns = set(profile.keys()).union(set(other_profile.keys()))
                
                if total_patterns:
                    similarity = len(common_patterns) / len(total_patterns)
                    if similarity > 0.3:  # 30% similarity threshold
                        cluster['interviews'].append(other_interview)
                        processed_interviews.add(other_interview)
            
            clusters.append(cluster)
        
        return {
            'clusters': clusters,
            'cluster_count': len(clusters),
            'total_interviews_analyzed': len(interview_ids),
            'analysis_confidence': len(processed_interviews) / len(interview_ids) if interview_ids else 0.0
        }
    
    async def detect_consensus_breakdown_points(self, code_name: str) -> Dict[str, Any]:
        """
        Detect points where consensus breaks down for a specific code
        
        Args:
            code_name: Name of the code to analyze
            
        Returns:
            Consensus breakdown analysis
        """
        logger.info(f"Detecting consensus breakdown points for code: {code_name}")
        
        breakdown_query = """
        MATCH (c:Code {name: $code_name})<-[r:SUPPORTS]-(q:Quote)
        OPTIONAL MATCH (q)-[m:MENTIONS]->(e:Entity)
        RETURN q.interview_id as interview_id,
               q.text as quote_text,
               q.line_start as line_start,
               e.name as entity_name,
               r.confidence as support_confidence
        ORDER BY q.interview_id
        """
        
        results = await self.neo4j.execute_cypher(breakdown_query, {"code_name": code_name})
        
        if len(results) < 3:
            return {
                'code_name': code_name,
                'breakdown_points': [],
                'consensus_strength': 0.0,
                'analysis_confidence': 0.0
            }
        
        # Group by interview and analyze confidence patterns
        interview_data = defaultdict(list)
        for result in results:
            interview_data[result['interview_id']].append(result)
        
        # Calculate consensus strength per interview
        interview_consensus = {}
        for interview_id, quotes in interview_data.items():
            confidences = [q.get('support_confidence', 0) or 0 for q in quotes]
            avg_confidence = statistics.mean(confidences) if confidences else 0
            consensus_variance = statistics.variance(confidences) if len(confidences) > 1 else 0
            
            interview_consensus[interview_id] = {
                'average_confidence': avg_confidence,
                'confidence_variance': consensus_variance,
                'quote_count': len(quotes),
                'sample_quotes': [q['quote_text'][:50] + "..." for q in quotes[:2]]
            }
        
        # Identify breakdown points (high variance, low confidence)
        breakdown_points = []
        interviews = list(interview_consensus.keys())
        
        for interview_id, data in interview_consensus.items():
            if data['confidence_variance'] > 0.2 and data['average_confidence'] < 0.5:
                breakdown_points.append({
                    'interview_id': interview_id,
                    'breakdown_type': 'high_variance_low_confidence',
                    'average_confidence': data['average_confidence'],
                    'confidence_variance': data['confidence_variance'],
                    'quote_count': data['quote_count'],
                    'evidence': data['sample_quotes']
                })
        
        overall_confidence = statistics.mean([d['average_confidence'] for d in interview_consensus.values()])
        
        return {
            'code_name': code_name,
            'breakdown_points': breakdown_points,
            'consensus_strength': overall_confidence,
            'interview_analysis': interview_consensus,
            'analysis_confidence': len(results) / 10 if len(results) < 10 else 1.0
        }


# Convenience classes for specific analytics
class QuoteFrequencyAnalyzer:
    """Specialized analyzer for quote frequency patterns"""
    
    def __init__(self, neo4j_manager):
        self.pattern_analyzer = QuotePatternAnalyzer(neo4j_manager)
    
    async def analyze_frequency_patterns(self, interview_ids: List[str]) -> List[QuoteFrequencyPattern]:
        """Analyze quote frequency patterns across interviews"""
        return await self.pattern_analyzer.analyze_quote_frequency_patterns(interview_ids)


class QuoteEvolutionTracker:
    """Specialized tracker for quote evolution over time"""
    
    def __init__(self, neo4j_manager):
        self.pattern_analyzer = QuotePatternAnalyzer(neo4j_manager)
    
    async def track_entity_evolution(self, entity_name: str, interview_ids: List[str]) -> QuoteEvolutionPattern:
        """Track how quotes about an entity evolve over time"""
        return await self.pattern_analyzer.detect_quote_evolution_patterns(entity_name, interview_ids)