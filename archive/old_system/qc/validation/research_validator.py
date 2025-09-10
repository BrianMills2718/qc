"""
Research Validation Framework

Provides rigorous validation metrics for qualitative research analysis using
quote-centric architecture for inter-coder reliability, saturation analysis,
bias detection, and reproducibility tracking.
"""

import asyncio
import logging
import statistics
import math
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict, Counter
import scipy.stats as stats
from itertools import combinations

logger = logging.getLogger(__name__)


@dataclass
class InterCoderReliabilityResult:
    """Results of inter-coder reliability analysis"""
    cohens_kappa: float
    percent_agreement: float
    krippendorffs_alpha: float
    systematic_differences: Dict[str, Any]
    coder_comparison_matrix: Dict[str, Dict[str, float]]
    reliability_confidence: float


@dataclass
class SaturationAnalysisResult:
    """Results of theoretical saturation analysis"""
    saturation_achieved: bool
    saturation_point: Optional[int]  # Interview number where saturation occurred
    saturation_confidence: float
    code_emergence_curve: List[Dict[str, Any]]
    new_codes_per_interview: List[int]
    saturation_metrics: Dict[str, float]


@dataclass
class BiasDetectionResult:
    """Results of bias detection analysis"""
    selection_bias_detected: bool
    selection_bias_strength: float
    interpretation_consistency: float
    systematic_biases: List[Dict[str, Any]]
    bias_confidence: float
    recommendations: List[str]


class InterCoderReliabilityValidator:
    """
    Validates inter-coder reliability using quote-level coding comparisons
    """
    
    def __init__(self, neo4j_manager):
        self.neo4j = neo4j_manager
        
    async def calculate_quote_coding_agreement(self, coder_sessions: List[str]) -> InterCoderReliabilityResult:
        """
        Calculate inter-coder reliability metrics for quote-code assignments
        
        Args:
            coder_sessions: List of session identifiers for different coders
            
        Returns:
            Comprehensive inter-coder reliability analysis
        """
        logger.info(f"Calculating inter-coder reliability across {len(coder_sessions)} coder sessions")
        
        # Get quote-code assignments for each coder
        coder_assignments = {}
        all_quotes = set()
        all_codes = set()
        
        for session_id in coder_sessions:
            assignments = await self._get_coder_assignments(session_id)
            coder_assignments[session_id] = assignments
            
            for quote_id, codes in assignments.items():
                all_quotes.add(quote_id)
                all_codes.update(codes)
        
        if len(all_quotes) == 0 or len(coder_sessions) < 2:
            return InterCoderReliabilityResult(
                cohens_kappa=0.0,
                percent_agreement=0.0,
                krippendorffs_alpha=0.0,
                systematic_differences={},
                coder_comparison_matrix={},
                reliability_confidence=0.0
            )
        
        # Calculate agreement matrices
        agreement_matrix = self._calculate_agreement_matrix(coder_assignments, all_quotes, all_codes)
        
        # Cohen's Kappa (for pairs of coders)
        cohens_kappa = self._calculate_cohens_kappa(agreement_matrix, coder_sessions)
        
        # Percent Agreement
        percent_agreement = self._calculate_percent_agreement(coder_assignments, all_quotes)
        
        # Krippendorff's Alpha (for multiple coders)
        krippendorffs_alpha = self._calculate_krippendorffs_alpha(coder_assignments, all_quotes, all_codes)
        
        # Systematic differences analysis
        systematic_differences = await self._analyze_systematic_differences(coder_assignments, all_codes)
        
        # Coder comparison matrix
        comparison_matrix = self._build_coder_comparison_matrix(coder_assignments, coder_sessions)
        
        # Reliability confidence based on sample size and agreement
        reliability_confidence = self._calculate_reliability_confidence(
            len(all_quotes), len(coder_sessions), percent_agreement
        )
        
        return InterCoderReliabilityResult(
            cohens_kappa=cohens_kappa,
            percent_agreement=percent_agreement,
            krippendorffs_alpha=krippendorffs_alpha,
            systematic_differences=systematic_differences,
            coder_comparison_matrix=comparison_matrix,
            reliability_confidence=reliability_confidence
        )
    
    async def _get_coder_assignments(self, session_id: str) -> Dict[str, Set[str]]:
        """Get quote-code assignments for a specific coder session"""
        
        query = """
        MATCH (q:Quote)-[s:SUPPORTS]->(c:Code)
        WHERE s.session_id = $session_id OR q.session_id = $session_id
        RETURN q.id as quote_id, collect(c.name) as codes
        """
        
        results = await self.neo4j.execute_cypher(query, {"session_id": session_id})
        
        assignments = {}
        for result in results:
            quote_id = result['quote_id']
            codes = set(result['codes'])
            assignments[quote_id] = codes
        
        return assignments
    
    def _calculate_agreement_matrix(self, coder_assignments: Dict, all_quotes: Set, all_codes: Set) -> Dict:
        """Calculate agreement matrix for all coder pairs"""
        
        agreement_data = {}
        
        for quote_id in all_quotes:
            quote_agreements = {}
            
            for code in all_codes:
                coder_decisions = []
                
                for session_id, assignments in coder_assignments.items():
                    # 1 if coder assigned this code to this quote, 0 otherwise
                    assigned = 1 if quote_id in assignments and code in assignments[quote_id] else 0
                    coder_decisions.append(assigned)
                
                quote_agreements[code] = coder_decisions
            
            agreement_data[quote_id] = quote_agreements
        
        return agreement_data
    
    def _calculate_cohens_kappa(self, agreement_matrix: Dict, coder_sessions: List[str]) -> float:
        """Calculate Cohen's Kappa for pairwise agreement"""
        
        if len(coder_sessions) < 2:
            return 0.0
        
        kappa_scores = []
        
        # Calculate kappa for all pairs of coders
        for i, j in combinations(range(len(coder_sessions)), 2):
            pair_agreements = []
            pair_disagreements = []
            
            for quote_id, code_decisions in agreement_matrix.items():
                for code, decisions in code_decisions.items():
                    coder1_decision = decisions[i]
                    coder2_decision = decisions[j]
                    
                    if coder1_decision == coder2_decision:
                        pair_agreements.append(1)
                    else:
                        pair_disagreements.append(1)
            
            if len(pair_agreements) + len(pair_disagreements) > 0:
                observed_agreement = len(pair_agreements) / (len(pair_agreements) + len(pair_disagreements))
                
                # Calculate expected agreement (assuming random assignment)
                expected_agreement = 0.5  # Binary decision, so 50% expected by chance
                
                if expected_agreement < 1.0:
                    kappa = (observed_agreement - expected_agreement) / (1.0 - expected_agreement)
                    kappa_scores.append(max(0.0, kappa))  # Ensure non-negative
        
        return statistics.mean(kappa_scores) if kappa_scores else 0.0
    
    def _calculate_percent_agreement(self, coder_assignments: Dict, all_quotes: Set) -> float:
        """Calculate overall percent agreement across all coders"""
        
        if len(coder_assignments) < 2:
            return 100.0
        
        total_decisions = 0
        agreement_count = 0
        
        for quote_id in all_quotes:
            # Get all code sets assigned by different coders for this quote
            code_sets = []
            for session_id, assignments in coder_assignments.items():
                if quote_id in assignments:
                    code_sets.append(assignments[quote_id])
                else:
                    code_sets.append(set())
            
            if len(code_sets) > 1:
                # Check if all coders agree on the same codes for this quote
                first_set = code_sets[0]
                agreement = all(code_set == first_set for code_set in code_sets[1:])
                
                total_decisions += 1
                if agreement:
                    agreement_count += 1
        
        return (agreement_count / total_decisions * 100) if total_decisions > 0 else 100.0
    
    def _calculate_krippendorffs_alpha(self, coder_assignments: Dict, all_quotes: Set, all_codes: Set) -> float:
        """Calculate Krippendorff's Alpha for multiple coders"""
        
        if len(coder_assignments) < 2 or len(all_quotes) == 0:
            return 0.0
        
        # Simplified Krippendorff's Alpha calculation
        # For each quote-code pair, calculate disagreement across coders
        total_pairs = 0
        disagreement_count = 0
        
        for quote_id in all_quotes:
            for code in all_codes:
                coder_decisions = []
                
                for session_id, assignments in coder_assignments.items():
                    assigned = quote_id in assignments and code in assignments[quote_id]
                    coder_decisions.append(assigned)
                
                # Count disagreements in this decision set
                if len(coder_decisions) > 1:
                    for i in range(len(coder_decisions)):
                        for j in range(i + 1, len(coder_decisions)):
                            total_pairs += 1
                            if coder_decisions[i] != coder_decisions[j]:
                                disagreement_count += 1
        
        if total_pairs > 0:
            observed_disagreement = disagreement_count / total_pairs
            expected_disagreement = 0.5  # Random assignment expected disagreement
            
            if expected_disagreement > 0:
                alpha = 1 - (observed_disagreement / expected_disagreement)
                return max(0.0, alpha)
        
        return 0.0
    
    async def _analyze_systematic_differences(self, coder_assignments: Dict, all_codes: Set) -> Dict[str, Any]:
        """Analyze systematic differences between coders"""
        
        coder_profiles = {}
        
        for session_id, assignments in coder_assignments.items():
            # Calculate coder's tendency to use each code
            code_usage = Counter()
            total_assignments = 0
            
            for quote_id, codes in assignments.items():
                total_assignments += len(codes)
                for code in codes:
                    code_usage[code] += 1
            
            # Calculate usage rates
            usage_rates = {}
            for code in all_codes:
                usage_rates[code] = code_usage[code] / max(1, total_assignments)
            
            coder_profiles[session_id] = {
                'total_assignments': total_assignments,
                'code_usage_rates': usage_rates,
                'most_used_codes': [item[0] for item in code_usage.most_common(5)],
                'average_codes_per_quote': total_assignments / max(1, len(assignments))
            }
        
        return {
            'coder_profiles': coder_profiles,
            'systematic_differences_detected': len(set(
                tuple(profile['most_used_codes']) for profile in coder_profiles.values()
            )) > 1
        }
    
    def _build_coder_comparison_matrix(self, coder_assignments: Dict, coder_sessions: List[str]) -> Dict[str, Dict[str, float]]:
        """Build matrix comparing each coder pair"""
        
        comparison_matrix = {}
        
        for i, session1 in enumerate(coder_sessions):
            comparison_matrix[session1] = {}
            
            for j, session2 in enumerate(coder_sessions):
                if i == j:
                    comparison_matrix[session1][session2] = 1.0
                else:
                    # Calculate similarity between two coders
                    similarity = self._calculate_coder_similarity(
                        coder_assignments.get(session1, {}),
                        coder_assignments.get(session2, {})
                    )
                    comparison_matrix[session1][session2] = similarity
        
        return comparison_matrix
    
    def _calculate_coder_similarity(self, assignments1: Dict, assignments2: Dict) -> float:
        """Calculate similarity between two coders' assignments"""
        
        all_quotes = set(assignments1.keys()) | set(assignments2.keys())
        
        if not all_quotes:
            return 1.0
        
        agreement_count = 0
        total_comparisons = 0
        
        for quote_id in all_quotes:
            codes1 = assignments1.get(quote_id, set())
            codes2 = assignments2.get(quote_id, set())
            
            # Jaccard similarity for this quote
            intersection = len(codes1 & codes2)
            union = len(codes1 | codes2)
            
            if union > 0:
                similarity = intersection / union
                agreement_count += similarity
            else:
                agreement_count += 1.0  # Both assigned no codes
                
            total_comparisons += 1
        
        return agreement_count / total_comparisons if total_comparisons > 0 else 1.0
    
    def _calculate_reliability_confidence(self, num_quotes: int, num_coders: int, percent_agreement: float) -> float:
        """Calculate confidence in reliability measures based on sample size and agreement"""
        
        # Confidence increases with more quotes, more coders, and higher agreement
        sample_factor = min(1.0, num_quotes / 100)  # Normalize to 100 quotes
        coder_factor = min(1.0, num_coders / 3)     # Normalize to 3 coders
        agreement_factor = percent_agreement / 100   # Convert to decimal
        
        confidence = (sample_factor * 0.4) + (coder_factor * 0.3) + (agreement_factor * 0.3)
        return confidence


class SaturationAnalyzer:
    """
    Analyzes theoretical saturation using quote-centric data
    """
    
    def __init__(self, neo4j_manager):
        self.neo4j = neo4j_manager
        self.saturation_threshold = 2  # Number of interviews with no new codes to declare saturation
        
    async def detect_theoretical_saturation(self, interview_sequence: List[str]) -> SaturationAnalysisResult:
        """
        Detect theoretical saturation point in interview sequence
        
        Args:
            interview_sequence: Ordered list of interview identifiers
            
        Returns:
            Comprehensive saturation analysis
        """
        logger.info(f"Analyzing theoretical saturation across {len(interview_sequence)} interviews")
        
        # Get code emergence data for each interview
        code_emergence = await self._analyze_code_emergence_by_interview(interview_sequence)
        
        # Detect saturation point
        saturation_point, saturation_achieved = self._detect_saturation_point(code_emergence)
        
        # Calculate saturation confidence
        saturation_confidence = self._calculate_saturation_confidence(code_emergence, saturation_point)
        
        # Generate saturation metrics
        saturation_metrics = self._calculate_saturation_metrics(code_emergence)
        
        return SaturationAnalysisResult(
            saturation_achieved=saturation_achieved,
            saturation_point=saturation_point,
            saturation_confidence=saturation_confidence,
            code_emergence_curve=code_emergence,
            new_codes_per_interview=[item['new_codes_count'] for item in code_emergence],
            saturation_metrics=saturation_metrics
        )
    
    async def _analyze_code_emergence_by_interview(self, interview_sequence: List[str]) -> List[Dict[str, Any]]:
        """Analyze code emergence patterns across interview sequence"""
        
        seen_codes = set()
        emergence_data = []
        
        for i, interview_id in enumerate(interview_sequence):
            # Get all codes that appear in this interview
            query = """
            MATCH (q:Quote)-[s:SUPPORTS]->(c:Code)
            WHERE q.interview_id = $interview_id
            RETURN DISTINCT c.name as code_name, c.definition as code_definition
            """
            
            results = await self.neo4j.execute_cypher(query, {"interview_id": interview_id})
            
            interview_codes = set(result['code_name'] for result in results)
            new_codes = interview_codes - seen_codes
            
            # Get quotes that support new codes
            new_code_quotes = 0
            if new_codes:
                quote_query = """
                MATCH (q:Quote)-[s:SUPPORTS]->(c:Code)
                WHERE q.interview_id = $interview_id AND c.name IN $new_codes
                RETURN count(DISTINCT q.id) as quote_count
                """
                
                quote_results = await self.neo4j.execute_cypher(
                    quote_query, 
                    {"interview_id": interview_id, "new_codes": list(new_codes)}
                )
                new_code_quotes = quote_results[0]['quote_count'] if quote_results else 0
            
            emergence_data.append({
                'interview_index': i,
                'interview_id': interview_id,
                'new_codes_count': len(new_codes),
                'new_codes': list(new_codes),
                'cumulative_codes': len(seen_codes | interview_codes),
                'total_codes_this_interview': len(interview_codes),
                'new_code_quotes': new_code_quotes,
                'saturation_indicator': len(new_codes) == 0
            })
            
            seen_codes.update(interview_codes)
        
        return emergence_data
    
    def _detect_saturation_point(self, code_emergence: List[Dict]) -> Tuple[Optional[int], bool]:
        """Detect the point where theoretical saturation is achieved"""
        
        consecutive_no_new_codes = 0
        saturation_point = None
        
        for i, data in enumerate(code_emergence):
            if data['new_codes_count'] == 0:
                consecutive_no_new_codes += 1
                
                if consecutive_no_new_codes >= self.saturation_threshold and saturation_point is None:
                    # Saturation achieved at the start of this sequence
                    saturation_point = max(0, i - self.saturation_threshold + 1)
            else:
                consecutive_no_new_codes = 0
        
        saturation_achieved = saturation_point is not None
        
        return saturation_point, saturation_achieved
    
    def _calculate_saturation_confidence(self, code_emergence: List[Dict], saturation_point: Optional[int]) -> float:
        """Calculate confidence in saturation assessment"""
        
        if not saturation_point or len(code_emergence) < 3:
            return 0.0
        
        # Confidence factors:
        # 1. Length of sequence after saturation point
        post_saturation_length = len(code_emergence) - saturation_point
        length_factor = min(1.0, post_saturation_length / 5)  # Normalize to 5 interviews
        
        # 2. Consistency of no new codes after saturation
        post_saturation_data = code_emergence[saturation_point:]
        consistency_factor = 1.0 - (sum(1 for d in post_saturation_data if d['new_codes_count'] > 0) / len(post_saturation_data))
        
        # 3. Overall trend strength
        new_codes_trend = [d['new_codes_count'] for d in code_emergence]
        if len(new_codes_trend) > 1:
            # Calculate trend strength (decreasing trend)
            x = list(range(len(new_codes_trend)))
            if len(x) > 1:
                correlation = abs(stats.pearsonr(x, new_codes_trend)[0]) if statistics.stdev(new_codes_trend) > 0 else 0
                trend_factor = correlation
            else:
                trend_factor = 0.5
        else:
            trend_factor = 0.5
        
        confidence = (length_factor * 0.4) + (consistency_factor * 0.4) + (trend_factor * 0.2)
        return confidence
    
    def _calculate_saturation_metrics(self, code_emergence: List[Dict]) -> Dict[str, float]:
        """Calculate various saturation-related metrics"""
        
        new_codes_per_interview = [d['new_codes_count'] for d in code_emergence]
        cumulative_codes = [d['cumulative_codes'] for d in code_emergence]
        
        metrics = {
            'total_interviews': len(code_emergence),
            'total_unique_codes': max(cumulative_codes) if cumulative_codes else 0,
            'average_new_codes_per_interview': statistics.mean(new_codes_per_interview) if new_codes_per_interview else 0,
            'max_new_codes_single_interview': max(new_codes_per_interview) if new_codes_per_interview else 0,
            'interviews_with_no_new_codes': sum(1 for count in new_codes_per_interview if count == 0),
            'code_emergence_variance': statistics.variance(new_codes_per_interview) if len(new_codes_per_interview) > 1 else 0
        }
        
        # Calculate diminishing returns metric
        if len(cumulative_codes) > 1:
            growth_rates = []
            for i in range(1, len(cumulative_codes)):
                if cumulative_codes[i-1] > 0:
                    growth_rate = (cumulative_codes[i] - cumulative_codes[i-1]) / cumulative_codes[i-1]
                    growth_rates.append(growth_rate)
            
            if growth_rates:
                metrics['average_growth_rate'] = statistics.mean(growth_rates)
                metrics['diminishing_returns_detected'] = len(growth_rates) > 2 and growth_rates[-1] < growth_rates[0] * 0.5
            else:
                metrics['average_growth_rate'] = 0.0
                metrics['diminishing_returns_detected'] = False
        else:
            metrics['average_growth_rate'] = 0.0
            metrics['diminishing_returns_detected'] = False
        
        return metrics


class BiasDetector:
    """
    Detects systematic biases in quote selection and interpretation
    """
    
    def __init__(self, neo4j_manager):
        self.neo4j = neo4j_manager
        
    async def detect_quote_selection_bias(self, interview_ids: List[str]) -> BiasDetectionResult:
        """
        Detect bias in quote selection patterns
        
        Args:
            interview_ids: List of interviews to analyze for bias
            
        Returns:
            Comprehensive bias detection analysis
        """
        logger.info(f"Detecting quote selection bias across {len(interview_ids)} interviews")
        
        # Analyze quote selection patterns
        selection_patterns = await self._analyze_quote_selection_patterns(interview_ids)
        
        # Detect systematic biases
        systematic_biases = await self._detect_systematic_biases(selection_patterns)
        
        # Calculate bias strength
        bias_strength = self._calculate_bias_strength(systematic_biases)
        
        # Analyze interpretation consistency
        interpretation_consistency = await self._analyze_interpretation_consistency(interview_ids)
        
        # Generate recommendations
        recommendations = self._generate_bias_recommendations(systematic_biases, interpretation_consistency)
        
        # Calculate overall bias confidence
        bias_confidence = self._calculate_bias_confidence(
            len(interview_ids), bias_strength, interpretation_consistency
        )
        
        return BiasDetectionResult(
            selection_bias_detected=bias_strength > 0.3,
            selection_bias_strength=bias_strength,
            interpretation_consistency=interpretation_consistency,
            systematic_biases=systematic_biases,
            bias_confidence=bias_confidence,
            recommendations=recommendations
        )
    
    async def _analyze_quote_selection_patterns(self, interview_ids: List[str]) -> Dict[str, Any]:
        """Analyze patterns in quote selection across interviews"""
        
        # Get quote characteristics for analysis
        query = """
        MATCH (q:Quote)
        WHERE q.interview_id IN $interview_ids
        OPTIONAL MATCH (q)-[s:SUPPORTS]->(c:Code)
        OPTIONAL MATCH (q)-[m:MENTIONS]->(e:Entity)
        RETURN q.interview_id as interview_id,
               q.line_start as line_start,
               q.line_end as line_end,
               q.confidence as confidence,
               size(q.text) as quote_length,
               count(DISTINCT c.name) as codes_count,
               count(DISTINCT e.name) as entities_count,
               collect(DISTINCT c.name) as codes,
               collect(DISTINCT e.name) as entities
        """
        
        results = await self.neo4j.execute_cypher(query, {"interview_ids": interview_ids})
        
        # Analyze selection patterns by interview
        interview_patterns = defaultdict(list)
        overall_patterns = {
            'quote_lengths': [],
            'confidence_scores': [],
            'codes_per_quote': [],
            'entities_per_quote': []
        }
        
        for result in results:
            interview_id = result['interview_id']
            
            pattern_data = {
                'line_start': result['line_start'],
                'quote_length': result['quote_length'],
                'confidence': result['confidence'] or 0,
                'codes_count': result['codes_count'],
                'entities_count': result['entities_count'],
                'codes': result['codes'],
                'entities': result['entities']
            }
            
            interview_patterns[interview_id].append(pattern_data)
            
            # Add to overall patterns
            overall_patterns['quote_lengths'].append(result['quote_length'])
            overall_patterns['confidence_scores'].append(result['confidence'] or 0)
            overall_patterns['codes_per_quote'].append(result['codes_count'])
            overall_patterns['entities_per_quote'].append(result['entities_count'])
        
        return {
            'interview_patterns': dict(interview_patterns),
            'overall_patterns': overall_patterns
        }
    
    async def _detect_systematic_biases(self, selection_patterns: Dict) -> List[Dict[str, Any]]:
        """Detect systematic biases in selection patterns"""
        
        biases = []
        interview_patterns = selection_patterns['interview_patterns']
        overall_patterns = selection_patterns['overall_patterns']
        
        if len(interview_patterns) < 2:
            return biases
        
        # 1. Length bias - preference for longer or shorter quotes
        interview_avg_lengths = {}
        for interview_id, patterns in interview_patterns.items():
            lengths = [p['quote_length'] for p in patterns]
            interview_avg_lengths[interview_id] = statistics.mean(lengths) if lengths else 0
        
        if len(interview_avg_lengths) > 1:
            length_variance = statistics.variance(interview_avg_lengths.values())
            overall_avg_length = statistics.mean(overall_patterns['quote_lengths'])
            
            if length_variance > (overall_avg_length * 0.5) ** 2:  # High variance relative to mean
                biases.append({
                    'bias_type': 'length_bias',
                    'description': 'Systematic preference for quotes of certain lengths across interviews',
                    'strength': min(1.0, length_variance / (overall_avg_length ** 2)),
                    'evidence': interview_avg_lengths
                })
        
        # 2. Confidence bias - preference for high/low confidence quotes
        interview_avg_confidence = {}
        for interview_id, patterns in interview_patterns.items():
            confidences = [p['confidence'] for p in patterns]
            interview_avg_confidence[interview_id] = statistics.mean(confidences) if confidences else 0
        
        if len(interview_avg_confidence) > 1:
            confidence_variance = statistics.variance(interview_avg_confidence.values())
            
            if confidence_variance > 0.01:  # Threshold for confidence bias
                biases.append({
                    'bias_type': 'confidence_bias',
                    'description': 'Systematic preference for quotes with certain confidence levels',
                    'strength': min(1.0, confidence_variance * 10),
                    'evidence': interview_avg_confidence
                })
        
        # 3. Complexity bias - preference for quotes with many/few codes
        interview_avg_complexity = {}
        for interview_id, patterns in interview_patterns.items():
            complexities = [p['codes_count'] + p['entities_count'] for p in patterns]
            interview_avg_complexity[interview_id] = statistics.mean(complexities) if complexities else 0
        
        if len(interview_avg_complexity) > 1:
            complexity_variance = statistics.variance(interview_avg_complexity.values())
            overall_avg_complexity = statistics.mean([
                c + e for c, e in zip(overall_patterns['codes_per_quote'], overall_patterns['entities_per_quote'])
            ])
            
            if complexity_variance > 1 and overall_avg_complexity > 0:
                biases.append({
                    'bias_type': 'complexity_bias',
                    'description': 'Systematic preference for quotes with certain complexity levels',
                    'strength': min(1.0, complexity_variance / (overall_avg_complexity + 1)),
                    'evidence': interview_avg_complexity
                })
        
        return biases
    
    def _calculate_bias_strength(self, systematic_biases: List[Dict]) -> float:
        """Calculate overall bias strength"""
        
        if not systematic_biases:
            return 0.0
        
        # Average strength of all detected biases
        strengths = [bias['strength'] for bias in systematic_biases]
        return statistics.mean(strengths)
    
    async def _analyze_interpretation_consistency(self, interview_ids: List[str]) -> float:
        """Analyze consistency in interpretation across interviews"""
        
        # Get entity-code associations across interviews
        query = """
        MATCH (e:Entity)<-[m:MENTIONS]-(q:Quote)-[s:SUPPORTS]->(c:Code)
        WHERE q.interview_id IN $interview_ids
        RETURN e.name as entity_name, c.name as code_name, 
               q.interview_id as interview_id, count(*) as frequency
        """
        
        results = await self.neo4j.execute_cypher(query, {"interview_ids": interview_ids})
        
        # Build entity-code interpretation matrix
        entity_code_patterns = defaultdict(lambda: defaultdict(list))
        
        for result in results:
            entity_name = result['entity_name']
            code_name = result['code_name']
            interview_id = result['interview_id']
            frequency = result['frequency']
            
            entity_code_patterns[entity_name][code_name].append({
                'interview_id': interview_id,
                'frequency': frequency
            })
        
        # Calculate consistency for each entity-code pair
        consistency_scores = []
        
        for entity_name, code_patterns in entity_code_patterns.items():
            for code_name, interview_data in code_patterns.items():
                if len(interview_data) > 1:  # Only analyze patterns that appear in multiple interviews
                    frequencies = [d['frequency'] for d in interview_data]
                    
                    # Consistency is inverse of coefficient of variation
                    if statistics.mean(frequencies) > 0:
                        cv = statistics.stdev(frequencies) / statistics.mean(frequencies) if len(frequencies) > 1 else 0
                        consistency = max(0, 1 - cv)
                        consistency_scores.append(consistency)
        
        return statistics.mean(consistency_scores) if consistency_scores else 1.0
    
    def _generate_bias_recommendations(self, systematic_biases: List[Dict], interpretation_consistency: float) -> List[str]:
        """Generate recommendations for addressing detected biases"""
        
        recommendations = []
        
        if systematic_biases:
            recommendations.append("Systematic biases detected in quote selection patterns")
            
            for bias in systematic_biases:
                if bias['bias_type'] == 'length_bias':
                    recommendations.append("Consider establishing guidelines for quote length selection")
                elif bias['bias_type'] == 'confidence_bias':
                    recommendations.append("Review confidence scoring consistency across interviews")
                elif bias['bias_type'] == 'complexity_bias':
                    recommendations.append("Balance selection of simple and complex quotes")
        
        if interpretation_consistency < 0.7:
            recommendations.append("Low interpretation consistency detected - consider inter-coder reliability training")
        
        if not recommendations:
            recommendations.append("No significant biases detected - analysis appears systematic")
        
        return recommendations
    
    def _calculate_bias_confidence(self, num_interviews: int, bias_strength: float, interpretation_consistency: float) -> float:
        """Calculate confidence in bias detection analysis"""
        
        # Confidence increases with more data and clearer patterns
        sample_factor = min(1.0, num_interviews / 10)  # Normalize to 10 interviews
        
        # Strong bias or high consistency both increase confidence
        pattern_clarity = max(bias_strength, interpretation_consistency)
        
        confidence = (sample_factor * 0.6) + (pattern_clarity * 0.4)
        return confidence


# Convenience class for integrated research validation
class ResearchValidationSuite:
    """
    Integrated research validation suite combining all validation components
    """
    
    def __init__(self, neo4j_manager):
        self.neo4j = neo4j_manager
        self.reliability_validator = InterCoderReliabilityValidator(neo4j_manager)
        self.saturation_analyzer = SaturationAnalyzer(neo4j_manager)
        self.bias_detector = BiasDetector(neo4j_manager)
    
    async def comprehensive_validation(self, 
                                     coder_sessions: List[str],
                                     interview_sequence: List[str]) -> Dict[str, Any]:
        """
        Run comprehensive research validation analysis
        
        Args:
            coder_sessions: List of coder session identifiers
            interview_sequence: Ordered list of interview identifiers
            
        Returns:
            Complete validation report
        """
        logger.info("Running comprehensive research validation analysis")
        
        # Run all validation analyses
        tasks = [
            self.reliability_validator.calculate_quote_coding_agreement(coder_sessions),
            self.saturation_analyzer.detect_theoretical_saturation(interview_sequence),
            self.bias_detector.detect_quote_selection_bias(interview_sequence)
        ]
        
        reliability_result, saturation_result, bias_result = await asyncio.gather(*tasks)
        
        # Generate overall research quality score
        quality_score = self._calculate_research_quality_score(
            reliability_result, saturation_result, bias_result
        )
        
        return {
            'research_quality_score': quality_score,
            'inter_coder_reliability': reliability_result,
            'saturation_analysis': saturation_result,
            'bias_detection': bias_result,
            'validation_timestamp': datetime.utcnow().isoformat(),
            'recommendations': self._generate_integrated_recommendations(
                reliability_result, saturation_result, bias_result
            )
        }
    
    def _calculate_research_quality_score(self, reliability_result, saturation_result, bias_result) -> float:
        """Calculate overall research quality score (0-1 scale)"""
        
        # Weight different factors
        reliability_score = reliability_result.reliability_confidence * 0.4
        saturation_score = saturation_result.saturation_confidence * 0.3
        bias_score = (1 - bias_result.selection_bias_strength) * 0.3
        
        overall_score = reliability_score + saturation_score + bias_score
        return overall_score
    
    def _generate_integrated_recommendations(self, reliability_result, saturation_result, bias_result) -> List[str]:
        """Generate integrated recommendations across all validation areas"""
        
        recommendations = []
        
        # Reliability recommendations
        if reliability_result.reliability_confidence < 0.7:
            recommendations.append("Consider additional inter-coder reliability training")
        
        # Saturation recommendations
        if not saturation_result.saturation_achieved:
            recommendations.append("Theoretical saturation not yet achieved - consider additional interviews")
        
        # Bias recommendations
        recommendations.extend(bias_result.recommendations)
        
        # Overall recommendations
        quality_score = self._calculate_research_quality_score(reliability_result, saturation_result, bias_result)
        
        if quality_score > 0.8:
            recommendations.append("High research quality achieved - analysis ready for publication")
        elif quality_score > 0.6:
            recommendations.append("Good research quality - minor improvements recommended")
        else:
            recommendations.append("Research quality needs improvement before publication")
        
        return recommendations