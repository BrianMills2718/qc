#!/usr/bin/env python3
"""
Connection Quality Monitoring System

Implements quality monitoring for thematic connections in focus group processing,
tracking connection rates, patterns, and providing quality assessment feedback.
"""

import json
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ConnectionQualityMetrics:
    """Metrics for thematic connection quality assessment."""
    interview_id: str
    interview_type: str
    total_quotes: int
    quotes_with_connections: int
    connection_rate: float
    self_connection_count: int
    self_connection_rate: float
    connection_type_distribution: Dict[str, int]
    confidence_score_distribution: Dict[str, int]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QualityAlert:
    """Alert for unusual connection patterns."""
    alert_type: str
    severity: str  # "info", "warning", "critical"
    message: str
    interview_id: str
    metric_value: float
    expected_range: str
    timestamp: str


class ConnectionQualityMonitor:
    """Monitors thematic connection quality in focus group processing."""
    
    def __init__(self, quality_thresholds: Optional[Dict[str, Any]] = None):
        """
        Initialize quality monitor with configurable thresholds.
        
        Args:
            quality_thresholds: Custom thresholds for quality assessment
        """
        self.quality_thresholds = quality_thresholds or {
            'connection_rate_low': 0.20,
            'connection_rate_high': 0.80,
            'typical_range_low': 0.30,
            'typical_range_high': 0.60,
            'self_connection_high': 0.30,
            'confidence_clustering_threshold': 0.70
        }
        
    def analyze_connection_quality(self, interview_data: Dict[str, Any]) -> ConnectionQualityMetrics:
        """
        Analyze connection quality for a single interview.
        
        Args:
            interview_data: Processed interview data with quotes and connections
            
        Returns:
            ConnectionQualityMetrics: Quality metrics for the interview
        """
        quotes = interview_data.get('quotes', [])
        interview_id = interview_data.get('interview_id', 'unknown')
        interview_type = self._detect_interview_type(interview_data)
        
        # Basic connection metrics
        total_quotes = len(quotes)
        quotes_with_connections = len([q for q in quotes if q.get('thematic_connection') != 'none'])
        connection_rate = quotes_with_connections / total_quotes if total_quotes > 0 else 0.0
        
        # Self-connection analysis
        self_connections = [
            q for q in quotes 
            if (q.get('thematic_connection') != 'none' and 
                q.get('speaker_name') == q.get('connection_target'))
        ]
        self_connection_count = len(self_connections)
        self_connection_rate = self_connection_count / total_quotes if total_quotes > 0 else 0.0
        
        # Connection type distribution
        connection_types = [q.get('thematic_connection', 'none') for q in quotes]
        connection_type_distribution = {
            conn_type: connection_types.count(conn_type)
            for conn_type in set(connection_types)
        }
        
        # Confidence score distribution
        confidence_scores = [
            str(q.get('connection_confidence', 'null'))
            for q in quotes if q.get('connection_confidence') is not None
        ]
        confidence_score_distribution = {
            score: confidence_scores.count(score)
            for score in set(confidence_scores)
        }
        
        return ConnectionQualityMetrics(
            interview_id=interview_id,
            interview_type=interview_type,
            total_quotes=total_quotes,
            quotes_with_connections=quotes_with_connections,
            connection_rate=connection_rate,
            self_connection_count=self_connection_count,
            self_connection_rate=self_connection_rate,
            connection_type_distribution=connection_type_distribution,
            confidence_score_distribution=confidence_score_distribution,
            timestamp=datetime.now().isoformat()
        )
    
    def generate_quality_alerts(self, metrics: ConnectionQualityMetrics) -> List[QualityAlert]:
        """
        Generate quality alerts based on connection metrics.
        
        Args:
            metrics: Connection quality metrics
            
        Returns:
            List[QualityAlert]: Generated quality alerts
        """
        alerts = []
        timestamp = datetime.now().isoformat()
        
        # Check connection rate alerts
        if metrics.connection_rate > self.quality_thresholds['connection_rate_high']:
            alerts.append(QualityAlert(
                alert_type="high_connection_rate",
                severity="warning",
                message=f"Connection rate ({metrics.connection_rate:.1%}) exceeds typical range, possible over-connecting",
                interview_id=metrics.interview_id,
                metric_value=metrics.connection_rate,
                expected_range=f"{self.quality_thresholds['typical_range_low']:.0%}-{self.quality_thresholds['typical_range_high']:.0%}",
                timestamp=timestamp
            ))
        
        if metrics.connection_rate < self.quality_thresholds['connection_rate_low']:
            alerts.append(QualityAlert(
                alert_type="low_connection_rate",
                severity="info",
                message=f"Connection rate ({metrics.connection_rate:.1%}) below typical range, consider if conservative detection is appropriate",
                interview_id=metrics.interview_id,
                metric_value=metrics.connection_rate,
                expected_range=f"{self.quality_thresholds['typical_range_low']:.0%}-{self.quality_thresholds['typical_range_high']:.0%}",
                timestamp=timestamp
            ))
        
        # Check self-connection rate
        if metrics.self_connection_rate > self.quality_thresholds['self_connection_high']:
            alerts.append(QualityAlert(
                alert_type="high_self_connection_rate",
                severity="info",
                message=f"Self-connection rate ({metrics.self_connection_rate:.1%}) is high, verify thematic coherence",
                interview_id=metrics.interview_id,
                metric_value=metrics.self_connection_rate,
                expected_range=f"<{self.quality_thresholds['self_connection_high']:.0%}",
                timestamp=timestamp
            ))
        
        # Check confidence score clustering
        if len(metrics.confidence_score_distribution) <= 3:
            unique_scores = list(metrics.confidence_score_distribution.keys())
            if 'null' in unique_scores:
                unique_scores.remove('null')
            
            if len(unique_scores) <= 3:
                alerts.append(QualityAlert(
                    alert_type="confidence_clustering",
                    severity="info",
                    message=f"Confidence scores clustered in narrow range: {unique_scores}, consider broader distribution",
                    interview_id=metrics.interview_id,
                    metric_value=len(unique_scores),
                    expected_range="broader distribution expected",
                    timestamp=timestamp
                ))
        
        return alerts
    
    def validate_thematic_coherence(self, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate thematic coherence between connected quotes.
        
        Args:
            interview_data: Interview data with quotes and connections
            
        Returns:
            Dict containing coherence analysis results
        """
        quotes = interview_data.get('quotes', [])
        coherence_issues = []
        
        # Group quotes by speaker for self-connection analysis
        speaker_quotes = {}
        for quote in quotes:
            speaker = quote.get('speaker_name')
            if speaker:
                if speaker not in speaker_quotes:
                    speaker_quotes[speaker] = []
                speaker_quotes[speaker].append(quote)
        
        # Analyze connections for thematic coherence
        for quote in quotes:
            if quote.get('thematic_connection') != 'none':
                connection_target = quote.get('connection_target')
                quote_codes = set(quote.get('code_ids', []))
                
                # Find target quote(s) to check code overlap
                target_quotes = []
                if connection_target:
                    target_quotes = [
                        q for q in quotes 
                        if q.get('speaker_name') == connection_target
                    ]
                
                # Check for code overlap with target
                if target_quotes:
                    for target_quote in target_quotes:
                        target_codes = set(target_quote.get('code_ids', []))
                        code_overlap = quote_codes.intersection(target_codes)
                        
                        if not code_overlap:
                            coherence_issues.append({
                                'quote_text': quote.get('text', '')[:100],
                                'target_text': target_quote.get('text', '')[:100],
                                'connection_type': quote.get('thematic_connection'),
                                'quote_codes': list(quote_codes),
                                'target_codes': list(target_codes),
                                'issue': 'no_code_overlap'
                            })
        
        return {
            'coherence_issues_count': len(coherence_issues),
            'coherence_issues': coherence_issues,
            'total_connections_analyzed': len([q for q in quotes if q.get('thematic_connection') != 'none'])
        }
    
    def _detect_interview_type(self, interview_data: Dict[str, Any]) -> str:
        """Detect if interview is focus group or individual."""
        speakers = interview_data.get('speakers', [])
        if len(speakers) > 2:
            return 'focus_group'
        elif len(speakers) <= 2:
            return 'individual'
        else:
            return 'unknown'
    
    def generate_quality_report(self, metrics_list: List[ConnectionQualityMetrics]) -> Dict[str, Any]:
        """
        Generate comprehensive quality report from multiple interviews.
        
        Args:
            metrics_list: List of connection quality metrics
            
        Returns:
            Dict containing comprehensive quality report
        """
        if not metrics_list:
            return {'error': 'No metrics provided'}
        
        # Aggregate metrics
        total_interviews = len(metrics_list)
        focus_groups = [m for m in metrics_list if m.interview_type == 'focus_group']
        individual_interviews = [m for m in metrics_list if m.interview_type == 'individual']
        
        # Connection rate statistics
        connection_rates = [m.connection_rate for m in metrics_list]
        avg_connection_rate = sum(connection_rates) / len(connection_rates)
        
        focus_group_rates = [m.connection_rate for m in focus_groups]
        individual_rates = [m.connection_rate for m in individual_interviews]
        
        # Self-connection analysis
        self_connection_rates = [m.self_connection_rate for m in metrics_list]
        avg_self_connection_rate = sum(self_connection_rates) / len(self_connection_rates) if self_connection_rates else 0
        
        # Generate alerts summary
        all_alerts = []
        for metrics in metrics_list:
            all_alerts.extend(self.generate_quality_alerts(metrics))
        
        alerts_by_type = {}
        for alert in all_alerts:
            alert_type = alert.alert_type
            if alert_type not in alerts_by_type:
                alerts_by_type[alert_type] = 0
            alerts_by_type[alert_type] += 1
        
        return {
            'report_timestamp': datetime.now().isoformat(),
            'summary': {
                'total_interviews': total_interviews,
                'focus_groups': len(focus_groups),
                'individual_interviews': len(individual_interviews),
                'avg_connection_rate': avg_connection_rate,
                'avg_self_connection_rate': avg_self_connection_rate
            },
            'connection_rates': {
                'overall_average': avg_connection_rate,
                'focus_group_average': sum(focus_group_rates) / len(focus_group_rates) if focus_group_rates else 0,
                'individual_average': sum(individual_rates) / len(individual_rates) if individual_rates else 0,
                'range': f"{min(connection_rates):.1%} - {max(connection_rates):.1%}" if connection_rates else "N/A"
            },
            'quality_alerts': {
                'total_alerts': len(all_alerts),
                'alerts_by_type': alerts_by_type,
                'interviews_with_alerts': len(set(alert.interview_id for alert in all_alerts))
            },
            'recommendations': self._generate_recommendations(metrics_list, all_alerts)
        }
    
    def _generate_recommendations(self, metrics_list: List[ConnectionQualityMetrics], 
                                alerts: List[QualityAlert]) -> List[str]:
        """Generate recommendations based on quality analysis."""
        recommendations = []
        
        # Check for high connection rates
        high_connection_alerts = [a for a in alerts if a.alert_type == 'high_connection_rate']
        if len(high_connection_alerts) > len(metrics_list) * 0.5:
            recommendations.append(
                "Consider enhancing prompt with stronger conservative detection guidance - "
                "over 50% of interviews show high connection rates"
            )
        
        # Check for confidence clustering
        clustering_alerts = [a for a in alerts if a.alert_type == 'confidence_clustering']
        if clustering_alerts:
            recommendations.append(
                "Review confidence scoring - multiple interviews show narrow confidence ranges"
            )
        
        # Check connection rate patterns
        connection_rates = [m.connection_rate for m in metrics_list]
        if connection_rates and max(connection_rates) > 0.9:
            recommendations.append(
                "Review interviews with >90% connection rates for over-assignment patterns"
            )
        
        return recommendations


def analyze_interview_file(file_path: Path) -> Tuple[ConnectionQualityMetrics, List[QualityAlert]]:
    """
    Analyze a single interview file for connection quality.
    
    Args:
        file_path: Path to interview JSON file
        
    Returns:
        Tuple of (metrics, alerts)
    """
    monitor = ConnectionQualityMonitor()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        interview_data = json.load(f)
    
    metrics = monitor.analyze_connection_quality(interview_data)
    alerts = monitor.generate_quality_alerts(metrics)
    
    return metrics, alerts


if __name__ == "__main__":
    # Example usage
    output_dir = Path("output_production/interviews")
    if output_dir.exists():
        monitor = ConnectionQualityMonitor()
        all_metrics = []
        
        for json_file in output_dir.glob("*.json"):
            try:
                metrics, alerts = analyze_interview_file(json_file)
                all_metrics.append(metrics)
                
                if alerts:
                    print(f"\nAlerts for {json_file.name}:")
                    for alert in alerts:
                        print(f"  {alert.severity.upper()}: {alert.message}")
                        
            except Exception as e:
                print(f"Error analyzing {json_file}: {e}")
        
        if all_metrics:
            report = monitor.generate_quality_report(all_metrics)
            print(f"\n=== QUALITY REPORT ===")
            print(json.dumps(report, indent=2))