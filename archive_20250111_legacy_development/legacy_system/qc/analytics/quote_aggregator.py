"""
Advanced Quote Aggregation Module

Provides sophisticated aggregation and summarization capabilities for quote-centric
qualitative research analysis with statistical validation.
"""

import asyncio
import logging
import statistics
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict, Counter
import math

logger = logging.getLogger(__name__)


@dataclass
class QuoteAggregation:
    """Results of quote aggregation analysis"""
    aggregation_type: str
    entity_name: str
    code_names: List[str]
    total_quotes: int
    unique_interviews: int
    confidence_distribution: Dict[str, float]
    temporal_distribution: Dict[str, int]
    supporting_evidence: List[Dict[str, Any]]
    statistical_summary: Dict[str, float]


@dataclass
class CrossInterviewAggregation:
    """Results of cross-interview quote aggregation"""
    topic: str
    interview_coverage: Dict[str, int]  # interview_id -> quote_count
    consensus_strength: float
    divergence_points: List[Dict[str, Any]]
    aggregated_insights: List[str]
    evidence_quality_score: float


@dataclass
class QuoteDensityAnalysis:
    """Results of quote density analysis"""
    interview_id: str
    total_quotes: int
    quotes_per_line: float
    high_density_regions: List[Dict[str, Any]]
    entity_concentration: Dict[str, int]
    code_concentration: Dict[str, int]
    density_score: float


class AdvancedQuoteAggregator:
    """
    Advanced quote aggregation with statistical validation and insight generation
    """
    
    def __init__(self, neo4j_manager):
        self.neo4j = neo4j_manager
        self.min_confidence_threshold = 0.5
        self.high_density_threshold = 0.3  # quotes per line
        
    async def aggregate_entity_quotes(self, entity_name: str, interview_ids: Optional[List[str]] = None) -> QuoteAggregation:
        """
        Aggregate all quotes mentioning a specific entity with comprehensive analysis
        
        Args:
            entity_name: Name of entity to aggregate quotes for
            interview_ids: Optional list to limit analysis to specific interviews
            
        Returns:
            Comprehensive quote aggregation analysis
        """
        logger.info(f"Aggregating quotes for entity: {entity_name}")
        
        # Build query with optional interview filtering
        where_clause = "WHERE e.name = $entity_name"
        params = {"entity_name": entity_name}
        
        if interview_ids:
            where_clause += " AND q.interview_id IN $interview_ids"
            params["interview_ids"] = interview_ids
        
        aggregation_query = f"""
        MATCH (e:Entity)<-[r:MENTIONS]-(q:Quote)
        {where_clause}
        OPTIONAL MATCH (q)-[s:SUPPORTS]->(c:Code)
        RETURN q.interview_id as interview_id,
               q.text as quote_text,
               q.line_start as line_start,
               q.confidence as quote_confidence,
               r.confidence as mention_confidence,
               c.name as code_name,
               s.confidence as support_confidence
        ORDER BY q.interview_id, q.line_start
        """
        
        results = await self.neo4j.execute_cypher(aggregation_query, params)
        
        if not results:
            return QuoteAggregation(
                aggregation_type="entity_quotes",
                entity_name=entity_name,
                code_names=[],
                total_quotes=0,
                unique_interviews=0,
                confidence_distribution={},
                temporal_distribution={},
                supporting_evidence=[],
                statistical_summary={}
            )
        
        # Process results
        unique_quotes = {}  # quote_text -> full_data (deduplicate)
        interview_set = set()
        code_names = set()
        confidence_scores = []
        
        for result in results:
            quote_key = (result['interview_id'], result['line_start'])
            if quote_key not in unique_quotes:
                unique_quotes[quote_key] = result
                interview_set.add(result['interview_id'])
                
                # Collect confidence scores
                quote_conf = result.get('quote_confidence', 0) or 0
                mention_conf = result.get('mention_confidence', 0) or 0
                confidence_scores.append((quote_conf + mention_conf) / 2)
            
            # Collect code names
            if result['code_name']:
                code_names.add(result['code_name'])
        
        # Calculate confidence distribution
        confidence_distribution = self._calculate_confidence_distribution(confidence_scores)
        
        # Temporal distribution (by interview)
        temporal_distribution = {}
        for interview_id in interview_set:
            count = sum(1 for q in unique_quotes.values() if q['interview_id'] == interview_id)
            temporal_distribution[interview_id] = count
        
        # Supporting evidence (top quotes by confidence)
        sorted_quotes = sorted(unique_quotes.values(), 
                             key=lambda q: (q.get('quote_confidence', 0) or 0) + (q.get('mention_confidence', 0) or 0), 
                             reverse=True)
        
        supporting_evidence = []
        for quote in sorted_quotes[:5]:  # Top 5 quotes
            supporting_evidence.append({
                'text': quote['quote_text'],
                'interview_id': quote['interview_id'],
                'line_start': quote['line_start'],
                'confidence': (quote.get('quote_confidence', 0) or 0),
                'mention_confidence': (quote.get('mention_confidence', 0) or 0)
            })
        
        # Statistical summary
        statistical_summary = {
            'mean_confidence': statistics.mean(confidence_scores) if confidence_scores else 0,
            'median_confidence': statistics.median(confidence_scores) if confidence_scores else 0,
            'std_dev_confidence': statistics.stdev(confidence_scores) if len(confidence_scores) > 1 else 0,
            'min_confidence': min(confidence_scores) if confidence_scores else 0,
            'max_confidence': max(confidence_scores) if confidence_scores else 0
        }
        
        return QuoteAggregation(
            aggregation_type="entity_quotes",
            entity_name=entity_name,
            code_names=list(code_names),
            total_quotes=len(unique_quotes),
            unique_interviews=len(interview_set),
            confidence_distribution=confidence_distribution,
            temporal_distribution=temporal_distribution,
            supporting_evidence=supporting_evidence,
            statistical_summary=statistical_summary
        )
    
    def _calculate_confidence_distribution(self, confidence_scores: List[float]) -> Dict[str, float]:
        """Calculate confidence score distribution"""
        if not confidence_scores:
            return {}
        
        # Create confidence bins
        bins = {
            'very_low': 0,    # 0.0 - 0.2
            'low': 0,         # 0.2 - 0.4
            'medium': 0,      # 0.4 - 0.6
            'high': 0,        # 0.6 - 0.8
            'very_high': 0    # 0.8 - 1.0
        }
        
        for score in confidence_scores:
            if score < 0.2:
                bins['very_low'] += 1
            elif score < 0.4:
                bins['low'] += 1
            elif score < 0.6:
                bins['medium'] += 1
            elif score < 0.8:
                bins['high'] += 1
            else:
                bins['very_high'] += 1
        
        # Convert to percentages
        total = len(confidence_scores)
        return {k: (v / total) * 100 for k, v in bins.items()}
    
    async def aggregate_code_quotes(self, code_name: str, interview_ids: Optional[List[str]] = None) -> QuoteAggregation:
        """
        Aggregate all quotes supporting a specific code
        
        Args:
            code_name: Name of code to aggregate quotes for
            interview_ids: Optional list to limit analysis to specific interviews
            
        Returns:
            Comprehensive quote aggregation for the code
        """
        logger.info(f"Aggregating quotes for code: {code_name}")
        
        # Build query
        where_clause = "WHERE c.name = $code_name"
        params = {"code_name": code_name}
        
        if interview_ids:
            where_clause += " AND q.interview_id IN $interview_ids"
            params["interview_ids"] = interview_ids
        
        code_aggregation_query = f"""
        MATCH (c:Code)<-[s:SUPPORTS]-(q:Quote)
        {where_clause}
        OPTIONAL MATCH (q)-[m:MENTIONS]->(e:Entity)
        RETURN q.interview_id as interview_id,
               q.text as quote_text,
               q.line_start as line_start,
               q.confidence as quote_confidence,
               s.confidence as support_confidence,
               e.name as entity_name,
               m.confidence as mention_confidence
        ORDER BY q.interview_id, q.line_start
        """
        
        results = await self.neo4j.execute_cypher(code_aggregation_query, params)
        
        if not results:
            return QuoteAggregation(
                aggregation_type="code_quotes",
                entity_name=code_name,  # Using entity_name field for code_name
                code_names=[code_name],
                total_quotes=0,
                unique_interviews=0,
                confidence_distribution={},
                temporal_distribution={},
                supporting_evidence=[],
                statistical_summary={}
            )
        
        # Process similar to entity aggregation
        unique_quotes = {}
        interview_set = set()
        entity_names = set()
        confidence_scores = []
        
        for result in results:
            quote_key = (result['interview_id'], result['line_start'])
            if quote_key not in unique_quotes:
                unique_quotes[quote_key] = result
                interview_set.add(result['interview_id'])
                
                # Collect confidence scores
                quote_conf = result.get('quote_confidence', 0) or 0
                support_conf = result.get('support_confidence', 0) or 0
                confidence_scores.append((quote_conf + support_conf) / 2)
            
            if result['entity_name']:
                entity_names.add(result['entity_name'])
        
        # Build aggregation result
        confidence_distribution = self._calculate_confidence_distribution(confidence_scores)
        
        temporal_distribution = {}
        for interview_id in interview_set:
            count = sum(1 for q in unique_quotes.values() if q['interview_id'] == interview_id)
            temporal_distribution[interview_id] = count
        
        # Supporting evidence
        sorted_quotes = sorted(unique_quotes.values(), 
                             key=lambda q: (q.get('support_confidence', 0) or 0), 
                             reverse=True)
        
        supporting_evidence = []
        for quote in sorted_quotes[:5]:
            supporting_evidence.append({
                'text': quote['quote_text'],
                'interview_id': quote['interview_id'],
                'line_start': quote['line_start'],
                'confidence': quote.get('quote_confidence', 0) or 0,
                'support_confidence': quote.get('support_confidence', 0) or 0,
                'entity_mentioned': quote.get('entity_name', '')
            })
        
        # Statistical summary
        statistical_summary = {
            'mean_confidence': statistics.mean(confidence_scores) if confidence_scores else 0,
            'median_confidence': statistics.median(confidence_scores) if confidence_scores else 0,
            'std_dev_confidence': statistics.stdev(confidence_scores) if len(confidence_scores) > 1 else 0,
            'entities_mentioned': len(entity_names)
        }
        
        return QuoteAggregation(
            aggregation_type="code_quotes",
            entity_name=code_name,
            code_names=[code_name],
            total_quotes=len(unique_quotes),
            unique_interviews=len(interview_set),
            confidence_distribution=confidence_distribution,
            temporal_distribution=temporal_distribution,
            supporting_evidence=supporting_evidence,
            statistical_summary=statistical_summary
        )
    
    async def cross_interview_aggregation(self, topic: str, interview_ids: List[str]) -> CrossInterviewAggregation:
        """
        Aggregate quotes across multiple interviews for a specific topic
        
        Args:
            topic: Topic/entity name to analyze across interviews
            interview_ids: List of interview identifiers
            
        Returns:
            Cross-interview aggregation analysis
        """
        logger.info(f"Performing cross-interview aggregation for topic: {topic}")
        
        cross_query = """
        MATCH (e:Entity)<-[r:MENTIONS]-(q:Quote)
        WHERE (e.name CONTAINS $topic OR e.name = $topic) 
        AND q.interview_id IN $interview_ids
        OPTIONAL MATCH (q)-[s:SUPPORTS]->(c:Code)
        RETURN q.interview_id as interview_id,
               q.text as quote_text,
               q.line_start as line_start,
               q.confidence as quote_confidence,
               r.confidence as mention_confidence,
               c.name as code_name,
               s.confidence as support_confidence
        ORDER BY q.interview_id, q.line_start
        """
        
        results = await self.neo4j.execute_cypher(cross_query, {"topic": topic, "interview_ids": interview_ids})
        
        if not results:
            return CrossInterviewAggregation(
                topic=topic,
                interview_coverage={},
                consensus_strength=0.0,
                divergence_points=[],
                aggregated_insights=[],
                evidence_quality_score=0.0
            )
        
        # Analyze coverage per interview
        interview_coverage = defaultdict(int)
        interview_quotes = defaultdict(list)
        all_codes = set()
        
        for result in results:
            interview_id = result['interview_id']
            interview_coverage[interview_id] += 1
            interview_quotes[interview_id].append(result)
            
            if result['code_name']:
                all_codes.add(result['code_name'])
        
        # Calculate consensus strength
        consensus_strength = self._calculate_cross_interview_consensus(interview_quotes, all_codes)
        
        # Identify divergence points
        divergence_points = self._identify_divergence_points(interview_quotes, all_codes)
        
        # Generate aggregated insights
        aggregated_insights = self._generate_cross_interview_insights(interview_quotes, all_codes)
        
        # Calculate evidence quality score
        evidence_quality_score = self._calculate_evidence_quality(results)
        
        return CrossInterviewAggregation(
            topic=topic,
            interview_coverage=dict(interview_coverage),
            consensus_strength=consensus_strength,
            divergence_points=divergence_points,
            aggregated_insights=aggregated_insights,
            evidence_quality_score=evidence_quality_score
        )
    
    def _calculate_cross_interview_consensus(self, interview_quotes: Dict[str, List], all_codes: Set[str]) -> float:
        """Calculate consensus strength across interviews"""
        if len(interview_quotes) < 2 or not all_codes:
            return 0.0
        
        # For each code, check how many interviews mention it
        code_coverage = {}
        for code in all_codes:
            interviews_with_code = 0
            for interview_id, quotes in interview_quotes.items():
                if any(q.get('code_name') == code for q in quotes):
                    interviews_with_code += 1
            code_coverage[code] = interviews_with_code / len(interview_quotes)
        
        # Consensus strength is average coverage across all codes
        return statistics.mean(code_coverage.values()) if code_coverage else 0.0
    
    def _identify_divergence_points(self, interview_quotes: Dict[str, List], all_codes: Set[str]) -> List[Dict]:
        """Identify points where interviews diverge in their perspectives"""
        divergence_points = []
        
        for code in all_codes:
            # Find interviews that mention this code
            interviews_with_code = []
            interviews_without_code = []
            
            for interview_id, quotes in interview_quotes.items():
                has_code = any(q.get('code_name') == code for q in quotes)
                if has_code:
                    interviews_with_code.append(interview_id)
                else:
                    interviews_without_code.append(interview_id)
            
            # If code appears in some but not all interviews, it's a divergence point
            if len(interviews_with_code) > 0 and len(interviews_without_code) > 0:
                divergence_points.append({
                    'code': code,
                    'divergence_type': 'code_presence',
                    'interviews_with': interviews_with_code,
                    'interviews_without': interviews_without_code,
                    'divergence_strength': abs(len(interviews_with_code) - len(interviews_without_code)) / len(interview_quotes)
                })
        
        return divergence_points
    
    def _generate_cross_interview_insights(self, interview_quotes: Dict[str, List], all_codes: Set[str]) -> List[str]:
        """Generate insights from cross-interview analysis"""
        insights = []
        
        # Coverage insight
        total_interviews = len(interview_quotes)
        quotes_per_interview = [len(quotes) for quotes in interview_quotes.values()]
        avg_quotes = statistics.mean(quotes_per_interview) if quotes_per_interview else 0
        
        insights.append(f"Topic discussed across {total_interviews} interviews with average {avg_quotes:.1f} quotes per interview")
        
        # Code diversity insight
        if all_codes:
            insights.append(f"Topic associated with {len(all_codes)} different thematic codes: {', '.join(list(all_codes)[:3])}{'...' if len(all_codes) > 3 else ''}")
        
        # Interview variation insight
        if quotes_per_interview:
            std_dev = statistics.stdev(quotes_per_interview) if len(quotes_per_interview) > 1 else 0
            if std_dev > avg_quotes * 0.5:
                insights.append("High variation in quote frequency across interviews suggests differing perspectives or emphasis")
            else:
                insights.append("Consistent quote frequency across interviews suggests stable importance of topic")
        
        return insights
    
    def _calculate_evidence_quality(self, results: List[Dict]) -> float:
        """Calculate overall evidence quality score"""
        if not results:
            return 0.0
        
        # Factors: confidence scores, quote diversity, relationship strength
        confidence_scores = []
        unique_quotes = set()
        
        for result in results:
            # Confidence factor
            quote_conf = result.get('quote_confidence', 0) or 0
            mention_conf = result.get('mention_confidence', 0) or 0
            support_conf = result.get('support_confidence', 0) or 0
            
            avg_conf = statistics.mean([c for c in [quote_conf, mention_conf, support_conf] if c > 0])
            if avg_conf > 0:
                confidence_scores.append(avg_conf)
            
            # Diversity factor
            unique_quotes.add(result['quote_text'])
        
        # Calculate quality score
        avg_confidence = statistics.mean(confidence_scores) if confidence_scores else 0
        diversity_score = min(len(unique_quotes) / 10, 1.0)  # Normalize to max 10 quotes
        coverage_score = min(len(results) / 20, 1.0)  # Normalize to max 20 quotes
        
        quality_score = (avg_confidence * 0.5) + (diversity_score * 0.3) + (coverage_score * 0.2)
        return quality_score
    
    async def analyze_quote_density(self, interview_id: str) -> QuoteDensityAnalysis:
        """
        Analyze quote density patterns within a single interview
        
        Args:
            interview_id: Interview identifier to analyze
            
        Returns:
            Quote density analysis results
        """
        logger.info(f"Analyzing quote density for interview: {interview_id}")
        
        density_query = """
        MATCH (q:Quote)
        WHERE q.interview_id = $interview_id
        OPTIONAL MATCH (q)-[m:MENTIONS]->(e:Entity)
        OPTIONAL MATCH (q)-[s:SUPPORTS]->(c:Code)
        RETURN q.line_start as line_start,
               q.line_end as line_end,
               q.text as quote_text,
               q.confidence as quote_confidence,
               e.name as entity_name,
               c.name as code_name
        ORDER BY q.line_start
        """
        
        results = await self.neo4j.execute_cypher(density_query, {"interview_id": interview_id})
        
        if not results:
            return QuoteDensityAnalysis(
                interview_id=interview_id,
                total_quotes=0,
                quotes_per_line=0.0,
                high_density_regions=[],
                entity_concentration={},
                code_concentration={},
                density_score=0.0
            )
        
        # Calculate basic metrics
        total_quotes = len(results)
        max_line = max(result['line_end'] for result in results)
        min_line = min(result['line_start'] for result in results)
        total_lines = max_line - min_line + 1
        quotes_per_line = total_quotes / total_lines if total_lines > 0 else 0
        
        # Find high density regions (sliding window approach)
        high_density_regions = self._find_high_density_regions(results, total_lines)
        
        # Entity and code concentration
        entity_concentration = Counter()
        code_concentration = Counter()
        
        for result in results:
            if result['entity_name']:
                entity_concentration[result['entity_name']] += 1
            if result['code_name']:
                code_concentration[result['code_name']] += 1
        
        # Overall density score
        density_score = min(quotes_per_line / self.high_density_threshold, 1.0)
        
        return QuoteDensityAnalysis(
            interview_id=interview_id,
            total_quotes=total_quotes,
            quotes_per_line=quotes_per_line,
            high_density_regions=high_density_regions,
            entity_concentration=dict(entity_concentration.most_common(10)),
            code_concentration=dict(code_concentration.most_common(10)),
            density_score=density_score
        )
    
    def _find_high_density_regions(self, results: List[Dict], total_lines: int) -> List[Dict]:
        """Find regions with high quote density using sliding window"""
        if total_lines < 10:  # Too small for meaningful regions
            return []
        
        window_size = max(10, total_lines // 10)  # 10% of interview or minimum 10 lines
        regions = []
        
        # Group quotes by line ranges
        line_quotes = defaultdict(list)
        for result in results:
            start_line = result['line_start']
            line_quotes[start_line].append(result)
        
        # Sliding window to find high density regions
        lines = sorted(line_quotes.keys())
        
        for i in range(0, len(lines) - window_size + 1, window_size // 2):  # 50% overlap
            window_lines = lines[i:i + window_size]
            if not window_lines:
                continue
                
            start_line = window_lines[0]
            end_line = window_lines[-1]
            
            # Count quotes in this window
            quotes_in_window = []
            for line in window_lines:
                quotes_in_window.extend(line_quotes[line])
            
            density = len(quotes_in_window) / window_size
            
            if density > self.high_density_threshold:
                regions.append({
                    'start_line': start_line,
                    'end_line': end_line,
                    'quote_count': len(quotes_in_window),
                    'density': density,
                    'sample_quotes': [q['quote_text'][:50] + "..." for q in quotes_in_window[:2]]
                })
        
        # Sort by density and return top regions
        regions.sort(key=lambda r: r['density'], reverse=True)
        return regions[:5]  # Top 5 high density regions


# Convenience class for quick aggregations
class QuickAggregator:
    """Quick aggregation utilities for common use cases"""
    
    def __init__(self, neo4j_manager):
        self.aggregator = AdvancedQuoteAggregator(neo4j_manager)
    
    async def quick_entity_summary(self, entity_name: str) -> Dict[str, Any]:
        """Quick summary of quotes for an entity"""
        aggregation = await self.aggregator.aggregate_entity_quotes(entity_name)
        
        return {
            'entity': entity_name,
            'total_quotes': aggregation.total_quotes,
            'interviews_mentioned': aggregation.unique_interviews,
            'associated_codes': aggregation.code_names,
            'confidence_summary': {
                'mean': aggregation.statistical_summary.get('mean_confidence', 0),
                'high_confidence_percentage': aggregation.confidence_distribution.get('high', 0) + aggregation.confidence_distribution.get('very_high', 0)
            },
            'top_quote': aggregation.supporting_evidence[0]['text'] if aggregation.supporting_evidence else None
        }
    
    async def quick_code_summary(self, code_name: str) -> Dict[str, Any]:
        """Quick summary of quotes for a code"""
        aggregation = await self.aggregator.aggregate_code_quotes(code_name)
        
        return {
            'code': code_name,
            'total_quotes': aggregation.total_quotes,
            'interviews_mentioned': aggregation.unique_interviews,
            'entities_mentioned': aggregation.statistical_summary.get('entities_mentioned', 0),
            'confidence_summary': {
                'mean': aggregation.statistical_summary.get('mean_confidence', 0),
                'distribution': aggregation.confidence_distribution
            },
            'best_evidence': aggregation.supporting_evidence[0]['text'] if aggregation.supporting_evidence else None
        }