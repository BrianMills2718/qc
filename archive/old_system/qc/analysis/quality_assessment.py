#!/usr/bin/env python3
"""
Quality Assessment Framework

Integrates connection quality monitoring into the main processing pipeline
and provides comprehensive quality assessment capabilities.
"""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

try:
    from .connection_quality_monitor import ConnectionQualityMonitor, ConnectionQualityMetrics
except ImportError:
    from connection_quality_monitor import ConnectionQualityMonitor, ConnectionQualityMetrics


class QualityAssessmentFramework:
    """
    Comprehensive quality assessment for focus group processing.
    Integrates with main pipeline to provide real-time quality monitoring.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize quality assessment framework.
        
        Args:
            config: Configuration for quality thresholds and monitoring
        """
        self.config = config or {}
        self.monitor = ConnectionQualityMonitor(
            quality_thresholds=self.config.get('quality_thresholds')
        )
        self.assessment_history = []
        
    def assess_processing_quality(self, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive quality assessment for processed interview data.
        
        Args:
            interview_data: Processed interview with quotes and connections
            
        Returns:
            Dict containing comprehensive quality assessment
        """
        # Connection quality metrics
        metrics = self.monitor.analyze_connection_quality(interview_data)
        alerts = self.monitor.generate_quality_alerts(metrics)
        coherence_analysis = self.monitor.validate_thematic_coherence(interview_data)
        
        # Additional quality checks
        code_application_quality = self._assess_code_application_quality(interview_data)
        speaker_identification_quality = self._assess_speaker_identification_quality(interview_data)
        quote_extraction_quality = self._assess_quote_extraction_quality(interview_data)
        
        # Overall quality score
        quality_score = self._calculate_overall_quality_score(
            metrics, code_application_quality, speaker_identification_quality, 
            quote_extraction_quality, coherence_analysis
        )
        
        assessment = {
            'assessment_timestamp': datetime.now().isoformat(),
            'interview_id': interview_data.get('interview_id', 'unknown'),
            'overall_quality_score': quality_score,
            'connection_quality': {
                'metrics': metrics.to_dict(),
                'alerts': [
                    {
                        'type': alert.alert_type,
                        'severity': alert.severity,
                        'message': alert.message,
                        'value': alert.metric_value
                    }
                    for alert in alerts
                ]
            },
            'thematic_coherence': coherence_analysis,
            'code_application_quality': code_application_quality,
            'speaker_identification_quality': speaker_identification_quality,
            'quote_extraction_quality': quote_extraction_quality,
            'recommendations': self._generate_quality_recommendations(
                metrics, alerts, coherence_analysis
            )
        }
        
        # Store in history
        self.assessment_history.append(assessment)
        
        return assessment
    
    def _assess_code_application_quality(self, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess quality of code application to quotes."""
        quotes = interview_data.get('quotes', [])
        
        if not quotes:
            return {'score': 0.0, 'issues': ['no_quotes_extracted']}
        
        # Check code application rate
        quotes_with_codes = [q for q in quotes if q.get('code_ids')]
        code_application_rate = len(quotes_with_codes) / len(quotes) if quotes else 0.0
        
        # Check for code diversity
        all_codes = []
        for quote in quotes:
            all_codes.extend(quote.get('code_ids', []))
        
        unique_codes = len(set(all_codes))
        total_codes_applied = len(all_codes)
        
        # Check for multi-code quotes (indicates depth)
        multi_code_quotes = [q for q in quotes if len(q.get('code_ids', [])) > 1]
        multi_code_rate = len(multi_code_quotes) / len(quotes) if quotes else 0.0
        
        issues = []
        if code_application_rate < 0.8:
            issues.append(f'low_code_application_rate_{code_application_rate:.2f}')
        if unique_codes < 5:
            issues.append(f'low_code_diversity_{unique_codes}')
        if multi_code_rate < 0.2:
            issues.append(f'low_multi_code_rate_{multi_code_rate:.2f}')
        
        # Calculate score based on multiple factors
        score = (code_application_rate * 0.5 + 
                min(unique_codes / 10, 1.0) * 0.3 + 
                multi_code_rate * 0.2)
        
        return {
            'score': min(score, 1.0),
            'code_application_rate': code_application_rate,
            'unique_codes': unique_codes,
            'total_codes_applied': total_codes_applied,
            'multi_code_rate': multi_code_rate,
            'issues': issues
        }
    
    def _assess_speaker_identification_quality(self, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess quality of speaker identification."""
        speakers = interview_data.get('speakers', [])
        quotes = interview_data.get('quotes', [])
        
        if not speakers:
            return {'score': 0.0, 'issues': ['no_speakers_identified']}
        
        # Check speaker consistency
        quote_speakers = set(q.get('speaker_name') for q in quotes if q.get('speaker_name'))
        identified_speakers = set(s.get('name') for s in speakers if s.get('name'))
        
        speaker_consistency = len(quote_speakers.intersection(identified_speakers)) / len(quote_speakers) if quote_speakers else 0.0
        
        # Check confidence scores
        speaker_confidences = [s.get('confidence', 0.0) for s in speakers]
        avg_speaker_confidence = sum(speaker_confidences) / len(speaker_confidences) if speaker_confidences else 0.0
        
        # Check quote distribution among speakers
        speaker_quote_counts = {}
        for quote in quotes:
            speaker = quote.get('speaker_name')
            if speaker:
                speaker_quote_counts[speaker] = speaker_quote_counts.get(speaker, 0) + 1
        
        quote_distribution_balance = self._calculate_distribution_balance(speaker_quote_counts.values())
        
        issues = []
        if speaker_consistency < 0.9:
            issues.append(f'speaker_inconsistency_{speaker_consistency:.2f}')
        if avg_speaker_confidence < 0.7:
            issues.append(f'low_speaker_confidence_{avg_speaker_confidence:.2f}')
        if quote_distribution_balance < 0.3:
            issues.append(f'unbalanced_quote_distribution_{quote_distribution_balance:.2f}')
        
        score = (speaker_consistency * 0.5 + 
                avg_speaker_confidence * 0.3 + 
                quote_distribution_balance * 0.2)
        
        return {
            'score': min(score, 1.0),
            'speaker_consistency': speaker_consistency,
            'avg_speaker_confidence': avg_speaker_confidence,
            'quote_distribution_balance': quote_distribution_balance,
            'speaker_count': len(speakers),
            'issues': issues
        }
    
    def _assess_quote_extraction_quality(self, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess quality of quote extraction."""
        quotes = interview_data.get('quotes', [])
        
        if not quotes:
            return {'score': 0.0, 'issues': ['no_quotes_extracted']}
        
        # Check quote length distribution
        quote_lengths = [len(q.get('text', '')) for q in quotes]
        avg_quote_length = sum(quote_lengths) / len(quote_lengths) if quote_lengths else 0.0
        
        # Check for extremely short or long quotes
        short_quotes = len([length for length in quote_lengths if length < 50])
        long_quotes = len([length for length in quote_lengths if length > 500])
        
        # Check location information
        quotes_with_locations = [q for q in quotes if q.get('location_start') is not None]
        location_coverage = len(quotes_with_locations) / len(quotes) if quotes else 0.0
        
        # Check text quality (avoid empty or whitespace-only)
        quality_quotes = [q for q in quotes if q.get('text', '').strip()]
        text_quality_rate = len(quality_quotes) / len(quotes) if quotes else 0.0
        
        issues = []
        if avg_quote_length < 100:
            issues.append(f'short_quotes_{avg_quote_length:.0f}_avg_length')
        if short_quotes > len(quotes) * 0.3:
            issues.append(f'too_many_short_quotes_{short_quotes}')
        if long_quotes > len(quotes) * 0.1:
            issues.append(f'too_many_long_quotes_{long_quotes}')
        if location_coverage < 0.8:
            issues.append(f'poor_location_coverage_{location_coverage:.2f}')
        if text_quality_rate < 0.95:
            issues.append(f'text_quality_issues_{text_quality_rate:.2f}')
        
        # Calculate score
        length_score = min(avg_quote_length / 150, 1.0)  # Target ~150 chars
        balance_score = 1.0 - (short_quotes + long_quotes) / len(quotes)
        
        score = (length_score * 0.3 + 
                balance_score * 0.3 + 
                location_coverage * 0.2 + 
                text_quality_rate * 0.2)
        
        return {
            'score': min(score, 1.0),
            'avg_quote_length': avg_quote_length,
            'short_quotes': short_quotes,
            'long_quotes': long_quotes,
            'location_coverage': location_coverage,
            'text_quality_rate': text_quality_rate,
            'total_quotes': len(quotes),
            'issues': issues
        }
    
    def _calculate_distribution_balance(self, values: List[int]) -> float:
        """Calculate how balanced a distribution is (0.0 = very unbalanced, 1.0 = perfectly balanced)."""
        if not values or len(values) < 2:
            return 1.0
        
        values = list(values)
        total = sum(values)
        if total == 0:
            return 1.0
        
        # Calculate variance from equal distribution
        expected_value = total / len(values)
        variance = sum((v - expected_value) ** 2 for v in values) / len(values)
        
        # Normalize to 0-1 scale (lower variance = higher balance)
        max_possible_variance = ((len(values) - 1) * expected_value ** 2) / len(values)
        if max_possible_variance == 0:
            return 1.0
        
        balance = 1.0 - (variance / max_possible_variance)
        return max(0.0, min(1.0, balance))
    
    def _calculate_overall_quality_score(self, metrics: ConnectionQualityMetrics,
                                       code_quality: Dict[str, Any],
                                       speaker_quality: Dict[str, Any],
                                       quote_quality: Dict[str, Any],
                                       coherence_analysis: Dict[str, Any]) -> float:
        """Calculate overall quality score based on all assessments."""
        
        # Connection quality score (based on whether rate is in expected range)
        connection_score = 1.0
        if metrics.connection_rate > 0.8:  # Over-connecting penalty
            connection_score = max(0.5, 1.0 - (metrics.connection_rate - 0.8) * 2)
        elif metrics.connection_rate < 0.2:  # Under-connecting penalty
            connection_score = max(0.5, 0.2 / max(metrics.connection_rate, 0.01))
        
        # Coherence score (based on issues found)
        total_connections = coherence_analysis.get('total_connections_analyzed', 1)
        coherence_issues = coherence_analysis.get('coherence_issues_count', 0)
        coherence_score = max(0.0, 1.0 - (coherence_issues / total_connections)) if total_connections > 0 else 1.0
        
        # Weighted overall score
        overall_score = (
            connection_score * 0.25 +
            code_quality.get('score', 0.0) * 0.25 +
            speaker_quality.get('score', 0.0) * 0.20 +
            quote_quality.get('score', 0.0) * 0.20 +
            coherence_score * 0.10
        )
        
        return min(1.0, max(0.0, overall_score))
    
    def _generate_quality_recommendations(self, metrics: ConnectionQualityMetrics,
                                        alerts: List[Any],
                                        coherence_analysis: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations based on quality assessment."""
        recommendations = []
        
        # Connection rate recommendations
        if metrics.connection_rate > 0.8:
            recommendations.append(
                "Consider implementing more conservative connection detection - "
                f"current rate ({metrics.connection_rate:.1%}) suggests over-connecting"
            )
        elif metrics.connection_rate < 0.3:
            recommendations.append(
                "Consider reviewing connection detection sensitivity - "
                f"current rate ({metrics.connection_rate:.1%}) may be too conservative"
            )
        
        # Self-connection recommendations
        if metrics.self_connection_rate > 0.25:
            recommendations.append(
                f"High self-connection rate ({metrics.self_connection_rate:.1%}) - "
                "verify that connections represent meaningful thematic development"
            )
        
        # Coherence recommendations
        coherence_issues = coherence_analysis.get('coherence_issues_count', 0)
        if coherence_issues > 0:
            recommendations.append(
                f"Found {coherence_issues} thematic coherence issues - "
                "review connections between quotes with different codes"
            )
        
        # Alert-based recommendations
        for alert in alerts:
            if alert.alert_type == 'confidence_clustering':
                recommendations.append(
                    "Confidence scores show clustering - consider providing clearer "
                    "guidance for uncertainty assessment in prompts"
                )
        
        return recommendations
    
    def generate_periodic_report(self, days: int = 7) -> Dict[str, Any]:
        """
        Generate periodic quality report from assessment history.
        
        Args:
            days: Number of days to include in report
            
        Returns:
            Dict containing periodic quality report
        """
        # Filter recent assessments
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        recent_assessments = [
            assessment for assessment in self.assessment_history
            if datetime.fromisoformat(assessment['assessment_timestamp']).timestamp() > cutoff_date
        ]
        
        if not recent_assessments:
            return {'error': f'No assessments found in last {days} days'}
        
        # Aggregate quality scores
        quality_scores = [a['overall_quality_score'] for a in recent_assessments]
        avg_quality_score = sum(quality_scores) / len(quality_scores)
        
        # Count issues by type
        all_issues = []
        for assessment in recent_assessments:
            for component in ['code_application_quality', 'speaker_identification_quality', 'quote_extraction_quality']:
                all_issues.extend(assessment.get(component, {}).get('issues', []))
        
        issue_counts = {}
        for issue in all_issues:
            issue_type = issue.split('_')[0]  # Get issue type prefix
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        return {
            'report_period': f'Last {days} days',
            'assessments_count': len(recent_assessments),
            'average_quality_score': avg_quality_score,
            'quality_score_range': f"{min(quality_scores):.2f} - {max(quality_scores):.2f}",
            'common_issues': dict(sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
            'improvement_trends': self._analyze_quality_trends(recent_assessments),
            'recommendations': self._generate_periodic_recommendations(recent_assessments)
        }
    
    def _analyze_quality_trends(self, assessments: List[Dict[str, Any]]) -> Dict[str, str]:
        """Analyze quality trends over time."""
        if len(assessments) < 2:
            return {'trend': 'insufficient_data'}
        
        # Sort by timestamp
        sorted_assessments = sorted(assessments, key=lambda x: x['assessment_timestamp'])
        
        # Compare first half vs second half
        mid_point = len(sorted_assessments) // 2
        first_half_avg = sum(a['overall_quality_score'] for a in sorted_assessments[:mid_point]) / mid_point
        second_half_avg = sum(a['overall_quality_score'] for a in sorted_assessments[mid_point:]) / (len(sorted_assessments) - mid_point)
        
        change = second_half_avg - first_half_avg
        
        if abs(change) < 0.05:
            trend = 'stable'
        elif change > 0:
            trend = 'improving'
        else:
            trend = 'declining'
        
        return {
            'trend': trend,
            'change': f"{change:+.3f}",
            'first_half_avg': f"{first_half_avg:.3f}",
            'second_half_avg': f"{second_half_avg:.3f}"
        }
    
    def _generate_periodic_recommendations(self, assessments: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on periodic analysis."""
        recommendations = []
        
        # Analyze connection rate patterns
        connection_rates = []
        for assessment in assessments:
            metrics = assessment.get('connection_quality', {}).get('metrics', {})
            if 'connection_rate' in metrics:
                connection_rates.append(metrics['connection_rate'])
        
        if connection_rates:
            avg_connection_rate = sum(connection_rates) / len(connection_rates)
            
            if avg_connection_rate > 0.8:
                recommendations.append(
                    "Consistently high connection rates across interviews suggest "
                    "implementing more conservative detection guidance"
                )
            
            # Check for high variability
            if connection_rates and (max(connection_rates) - min(connection_rates)) > 0.5:
                recommendations.append(
                    "High variability in connection rates suggests inconsistent "
                    "processing - review prompt consistency"
                )
        
        return recommendations


if __name__ == "__main__":
    # Example usage
    framework = QualityAssessmentFramework()
    
    # Test with sample interview data
    output_dir = Path("output_production/interviews")
    if output_dir.exists():
        for json_file in output_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    interview_data = json.load(f)
                
                assessment = framework.assess_processing_quality(interview_data)
                
                print(f"\n=== QUALITY ASSESSMENT: {json_file.name} ===")
                print(f"Overall Quality Score: {assessment['overall_quality_score']:.2f}")
                
                if assessment.get('recommendations'):
                    print("Recommendations:")
                    for rec in assessment['recommendations']:
                        print(f"  - {rec}")
                        
                break  # Just test one file
                
            except Exception as e:
                print(f"Error assessing {json_file}: {e}")