"""
Performance Monitoring for Speaker Detection
Tracks metrics and provides optimization insights
"""
import time
import logging
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics for speaker detection"""
    total_detections: int = 0
    llm_detections: int = 0
    regex_fallbacks: int = 0
    total_time: float = 0.0
    llm_time: float = 0.0
    failure_count: int = 0
    avg_response_time: float = 0.0
    detection_accuracy: float = 0.0
    timestamps: List[datetime] = field(default_factory=list)

class SpeakerDetectionMonitor:
    """Monitor performance and quality of speaker detection"""
    
    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.recent_results: List[Dict[str, Any]] = []
        self.max_recent_results = 100
    
    def record_detection(
        self,
        text: str,
        result: str,
        method: str,
        execution_time: float,
        success: bool = True
    ):
        """Record a speaker detection event"""
        self.metrics.total_detections += 1
        self.metrics.total_time += execution_time
        
        if method == "llm":
            self.metrics.llm_detections += 1
            self.metrics.llm_time += execution_time
        else:
            self.metrics.regex_fallbacks += 1
        
        if not success:
            self.metrics.failure_count += 1
        
        # Update averages
        self.metrics.avg_response_time = (
            self.metrics.total_time / self.metrics.total_detections
        )
        
        # Store recent result
        self.recent_results.append({
            "timestamp": datetime.now(),
            "text_preview": text[:100] + "..." if len(text) > 100 else text,
            "result": result,
            "method": method,
            "execution_time": execution_time,
            "success": success
        })
        
        # Maintain recent results limit
        if len(self.recent_results) > self.max_recent_results:
            self.recent_results.pop(0)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        total = self.metrics.total_detections
        
        if total == 0:
            return {"status": "no_data", "message": "No detections recorded"}
        
        llm_percentage = (self.metrics.llm_detections / total) * 100
        fallback_percentage = (self.metrics.regex_fallbacks / total) * 100
        failure_rate = (self.metrics.failure_count / total) * 100
        
        return {
            "summary": {
                "total_detections": total,
                "llm_success_rate": f"{100 - failure_rate:.1f}%",
                "average_response_time": f"{self.metrics.avg_response_time:.3f}s"
            },
            "method_distribution": {
                "llm_detections": f"{llm_percentage:.1f}%",
                "regex_fallbacks": f"{fallback_percentage:.1f}%"
            },
            "performance": {
                "total_time": f"{self.metrics.total_time:.2f}s",
                "avg_llm_time": f"{self.metrics.llm_time / max(1, self.metrics.llm_detections):.3f}s",
                "failure_count": self.metrics.failure_count,
                "failure_rate": f"{failure_rate:.1f}%"
            },
            "recent_activity": len(self.recent_results),
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        if self.metrics.failure_count > 0:
            failure_rate = (self.metrics.failure_count / max(1, self.metrics.total_detections)) * 100
            if failure_rate > 10:
                recommendations.append("High failure rate detected - consider adjusting circuit breaker threshold")
        
        if self.metrics.avg_response_time > 5.0:
            recommendations.append("High average response time - consider reducing max_tokens or timeout")
        
        fallback_rate = (self.metrics.regex_fallbacks / max(1, self.metrics.total_detections)) * 100
        if fallback_rate > 50:
            recommendations.append("High fallback rate - LLM may be unreliable, consider configuration adjustment")
        
        if not recommendations:
            recommendations.append("Performance metrics within acceptable ranges")
        
        return recommendations

# Global monitor instance
performance_monitor = SpeakerDetectionMonitor()