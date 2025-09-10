#!/usr/bin/env python3
"""
System Monitoring and Health Checks

Provides comprehensive system monitoring capabilities with proactive
error detection and recovery recommendations.
"""

import logging
import asyncio
import psutil
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from ..core.graceful_degradation import fail_fast_manager, DegradationLevel

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthMetric:
    """Individual health metric"""
    name: str
    value: float
    threshold_warning: float
    threshold_critical: float
    status: HealthStatus
    message: str
    timestamp: datetime
    unit: str = ""


@dataclass
class SystemHealth:
    """Complete system health report"""
    overall_status: HealthStatus
    degradation_level: DegradationLevel
    metrics: Dict[str, HealthMetric]
    recommendations: List[str]
    timestamp: datetime
    uptime_seconds: float


class SystemMonitor:
    """
    Comprehensive system monitoring with health checks and alerting
    """
    
    def __init__(self, monitoring_interval: int = 60):
        self.monitoring_interval = monitoring_interval
        self.start_time = time.time()
        self.health_history = []
        self.alert_thresholds = self._initialize_thresholds()
        self.is_monitoring = False
        self._monitoring_task = None
    
    def _initialize_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize health check thresholds"""
        return {
            'cpu_usage': {'warning': 70.0, 'critical': 85.0},
            'memory_usage': {'warning': 75.0, 'critical': 90.0},
            'disk_usage': {'warning': 80.0, 'critical': 95.0},
            'llm_response_time': {'warning': 5.0, 'critical': 15.0},  # seconds
            'error_rate': {'warning': 0.05, 'critical': 0.15},  # percentage
            'degradation_score': {'warning': 0.3, 'critical': 0.6},  # 0-1 scale
        }
    
    async def start_monitoring(self):
        """Start continuous system monitoring"""
        if self.is_monitoring:
            logger.warning("Monitoring already started")
            return
        
        self.is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"System monitoring started (interval: {self.monitoring_interval}s)")
    
    async def stop_monitoring(self):
        """Stop system monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("System monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                health_report = await self.get_system_health()
                self.health_history.append(health_report)
                
                # Keep only last 100 reports
                if len(self.health_history) > 100:
                    self.health_history = self.health_history[-100:]
                
                # Check for alerts
                await self._check_alerts(health_report)
                
                # Wait for next check
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def get_system_health(self) -> SystemHealth:
        """Get comprehensive system health report"""
        now = datetime.now()
        uptime = time.time() - self.start_time
        
        # Collect all metrics
        metrics = {}
        
        # System resource metrics
        metrics.update(await self._get_resource_metrics())
        
        # Application-specific metrics
        metrics.update(await self._get_application_metrics())
        
        # Degradation metrics
        metrics.update(await self._get_degradation_metrics())
        
        # Determine overall status
        overall_status = self._calculate_overall_status(metrics)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, overall_status)
        
        # Get current system status  
        system_status_level = fail_fast_manager.system_status
        
        return SystemHealth(
            overall_status=overall_status,
            degradation_level=system_status_level,
            metrics=metrics,
            recommendations=recommendations,
            timestamp=now,
            uptime_seconds=uptime
        )
    
    async def _get_resource_metrics(self) -> Dict[str, HealthMetric]:
        """Get system resource metrics"""
        metrics = {}
        now = datetime.now()
        
        # CPU usage
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            metrics['cpu_usage'] = HealthMetric(
                name='CPU Usage',
                value=cpu_usage,
                threshold_warning=self.alert_thresholds['cpu_usage']['warning'],
                threshold_critical=self.alert_thresholds['cpu_usage']['critical'],
                status=self._get_metric_status(cpu_usage, 'cpu_usage'),
                message=f"CPU usage at {cpu_usage:.1f}%",
                timestamp=now,
                unit='%'
            )
        except Exception as e:
            logger.error(f"Failed to get CPU metrics: {e}")
            metrics['cpu_usage'] = self._create_error_metric('CPU Usage', str(e), now)
        
        # Memory usage
        try:
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            metrics['memory_usage'] = HealthMetric(
                name='Memory Usage',
                value=memory_usage,
                threshold_warning=self.alert_thresholds['memory_usage']['warning'],
                threshold_critical=self.alert_thresholds['memory_usage']['critical'],
                status=self._get_metric_status(memory_usage, 'memory_usage'),
                message=f"Memory usage at {memory_usage:.1f}% ({memory.used // (1024**3):.1f}GB used)",
                timestamp=now,
                unit='%'
            )
        except Exception as e:
            logger.error(f"Failed to get memory metrics: {e}")
            metrics['memory_usage'] = self._create_error_metric('Memory Usage', str(e), now)
        
        # Disk usage
        try:
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            metrics['disk_usage'] = HealthMetric(
                name='Disk Usage',
                value=disk_usage,
                threshold_warning=self.alert_thresholds['disk_usage']['warning'],
                threshold_critical=self.alert_thresholds['disk_usage']['critical'],
                status=self._get_metric_status(disk_usage, 'disk_usage'),
                message=f"Disk usage at {disk_usage:.1f}% ({disk.used // (1024**3):.1f}GB used)",
                timestamp=now,
                unit='%'
            )
        except Exception as e:
            logger.error(f"Failed to get disk metrics: {e}")
            metrics['disk_usage'] = self._create_error_metric('Disk Usage', str(e), now)
        
        return metrics
    
    async def _get_application_metrics(self) -> Dict[str, HealthMetric]:
        """Get application-specific metrics"""
        metrics = {}
        now = datetime.now()
        
        # LLM API response time (test call)
        try:
            start_time = time.time()
            # Mock LLM test - in real implementation, make actual test call
            await asyncio.sleep(0.1)  # Simulate API call
            response_time = time.time() - start_time
            
            metrics['llm_response_time'] = HealthMetric(
                name='LLM Response Time',
                value=response_time,
                threshold_warning=self.alert_thresholds['llm_response_time']['warning'],
                threshold_critical=self.alert_thresholds['llm_response_time']['critical'],
                status=self._get_metric_status(response_time, 'llm_response_time'),
                message=f"LLM API responding in {response_time:.2f}s",
                timestamp=now,
                unit='seconds'
            )
        except Exception as e:
            logger.error(f"Failed to test LLM API: {e}")
            metrics['llm_response_time'] = self._create_error_metric('LLM Response Time', str(e), now)
        
        # Database connectivity
        try:
            # Test Neo4j connectivity
            db_available = fail_fast_manager.is_capability_available('neo4j_database')
            db_status = HealthStatus.HEALTHY if db_available else HealthStatus.WARNING
            
            metrics['database_connectivity'] = HealthMetric(
                name='Database Connectivity',
                value=1.0 if db_available else 0.0,
                threshold_warning=0.5,
                threshold_critical=0.0,
                status=db_status,
                message="Database connected" if db_available else "Database unavailable (file storage active)",
                timestamp=now,
                unit='boolean'
            )
        except Exception as e:
            logger.error(f"Failed to check database connectivity: {e}")
            metrics['database_connectivity'] = self._create_error_metric('Database Connectivity', str(e), now)
        
        return metrics
    
    async def _get_degradation_metrics(self) -> Dict[str, HealthMetric]:
        """Get system degradation metrics"""
        metrics = {}
        now = datetime.now()
        
        try:
            system_status = fail_fast_manager.get_system_status()
            
            # Calculate degradation score (0 = no degradation, 1 = complete degradation)
            total_capabilities = len(system_status['capabilities'])
            failed_capabilities = sum(1 for cap in system_status['capabilities'].values() 
                                    if not cap['available'])
            
            degradation_score = failed_capabilities / total_capabilities if total_capabilities > 0 else 0
            
            metrics['degradation_score'] = HealthMetric(
                name='System Degradation',
                value=degradation_score,
                threshold_warning=self.alert_thresholds['degradation_score']['warning'],
                threshold_critical=self.alert_thresholds['degradation_score']['critical'],
                status=self._get_metric_status(degradation_score, 'degradation_score'),
                message=f"System operating at {(1-degradation_score)*100:.1f}% capability",
                timestamp=now,
                unit='ratio'
            )
            
            # Error rate metric
            total_errors = sum(cap['error_count'] for cap in system_status['capabilities'].values())
            error_rate = total_errors / 100  # Normalize to percentage
            
            metrics['error_rate'] = HealthMetric(
                name='Error Rate',
                value=error_rate,
                threshold_warning=self.alert_thresholds['error_rate']['warning'],
                threshold_critical=self.alert_thresholds['error_rate']['critical'],
                status=self._get_metric_status(error_rate, 'error_rate'),
                message=f"System error rate: {error_rate:.1%}",
                timestamp=now,
                unit='%'
            )
            
        except Exception as e:
            logger.error(f"Failed to get degradation metrics: {e}")
            metrics['degradation_score'] = self._create_error_metric('System Degradation', str(e), now)
            metrics['error_rate'] = self._create_error_metric('Error Rate', str(e), now)
        
        return metrics
    
    def _get_metric_status(self, value: float, metric_type: str) -> HealthStatus:
        """Determine health status for a metric value"""
        thresholds = self.alert_thresholds.get(metric_type, {})
        warning_threshold = thresholds.get('warning', float('inf'))
        critical_threshold = thresholds.get('critical', float('inf'))
        
        if value >= critical_threshold:
            return HealthStatus.CRITICAL
        elif value >= warning_threshold:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY
    
    def _create_error_metric(self, name: str, error_message: str, timestamp: datetime) -> HealthMetric:
        """Create a metric representing an error condition"""
        return HealthMetric(
            name=name,
            value=0.0,
            threshold_warning=0.0,
            threshold_critical=0.0,
            status=HealthStatus.UNKNOWN,
            message=f"Metric unavailable: {error_message}",
            timestamp=timestamp,
            unit='error'
        )
    
    def _calculate_overall_status(self, metrics: Dict[str, HealthMetric]) -> HealthStatus:
        """Calculate overall system health status"""
        status_counts = {status: 0 for status in HealthStatus}
        
        for metric in metrics.values():
            status_counts[metric.status] += 1
        
        total_metrics = len(metrics)
        
        if status_counts[HealthStatus.CRITICAL] > 0:
            return HealthStatus.CRITICAL
        elif status_counts[HealthStatus.WARNING] / total_metrics > 0.3:  # More than 30% warnings
            return HealthStatus.WARNING
        elif status_counts[HealthStatus.UNKNOWN] / total_metrics > 0.5:  # More than 50% unknown
            return HealthStatus.UNKNOWN
        else:
            return HealthStatus.HEALTHY
    
    def _generate_recommendations(self, metrics: Dict[str, HealthMetric], overall_status: HealthStatus) -> List[str]:
        """Generate recommendations based on system health"""
        recommendations = []
        
        # Resource-based recommendations
        if 'cpu_usage' in metrics:
            cpu_metric = metrics['cpu_usage']
            if cpu_metric.status == HealthStatus.CRITICAL:
                recommendations.append("High CPU usage detected - consider reducing concurrent operations")
            elif cpu_metric.status == HealthStatus.WARNING:
                recommendations.append("CPU usage elevated - monitor for performance impacts")
        
        if 'memory_usage' in metrics:
            memory_metric = metrics['memory_usage']
            if memory_metric.status == HealthStatus.CRITICAL:
                recommendations.append("Critical memory usage - restart application or reduce data processing")
            elif memory_metric.status == HealthStatus.WARNING:
                recommendations.append("Memory usage elevated - consider processing smaller data batches")
        
        if 'disk_usage' in metrics:
            disk_metric = metrics['disk_usage']
            if disk_metric.status == HealthStatus.CRITICAL:
                recommendations.append("Disk space critical - clean up temporary files and old logs")
            elif disk_metric.status == HealthStatus.WARNING:
                recommendations.append("Disk space low - consider archiving old analysis results")
        
        # Application-specific recommendations
        if 'llm_response_time' in metrics:
            llm_metric = metrics['llm_response_time']
            if llm_metric.status == HealthStatus.CRITICAL:
                recommendations.append("LLM API response time critical - check network connectivity and API status")
            elif llm_metric.status == HealthStatus.WARNING:
                recommendations.append("LLM API response slow - consider reducing batch sizes")
        
        if 'degradation_score' in metrics:
            deg_metric = metrics['degradation_score']
            if deg_metric.status == HealthStatus.CRITICAL:
                recommendations.append("System severely degraded - check logs and restart components")
            elif deg_metric.status == HealthStatus.WARNING:
                recommendations.append("System partially degraded - some features may be unavailable")
        
        # General recommendations based on overall status
        if overall_status == HealthStatus.CRITICAL:
            recommendations.append("System in critical state - consider restarting application")
        elif overall_status == HealthStatus.WARNING:
            recommendations.append("System health degraded - monitor closely and address warnings")
        
        return recommendations
    
    async def _check_alerts(self, health_report: SystemHealth):
        """Check for alert conditions and log appropriately"""
        if health_report.overall_status == HealthStatus.CRITICAL:
            logger.critical(f"CRITICAL SYSTEM HEALTH: {', '.join(health_report.recommendations)}")
        elif health_report.overall_status == HealthStatus.WARNING:
            logger.warning(f"System health warning: {', '.join(health_report.recommendations[:3])}")
        
        # Log specific critical metrics
        for metric_name, metric in health_report.metrics.items():
            if metric.status == HealthStatus.CRITICAL:
                logger.critical(f"CRITICAL METRIC - {metric.name}: {metric.message}")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of recent health data"""
        if not self.health_history:
            return {'message': 'No health data available'}
        
        latest_report = self.health_history[-1]
        
        # Calculate trends if we have enough data
        trends = {}
        if len(self.health_history) >= 2:
            previous_report = self.health_history[-2]
            for metric_name in latest_report.metrics:
                if metric_name in previous_report.metrics:
                    current_value = latest_report.metrics[metric_name].value
                    previous_value = previous_report.metrics[metric_name].value
                    trend = 'stable'
                    
                    if current_value > previous_value * 1.1:
                        trend = 'increasing'
                    elif current_value < previous_value * 0.9:
                        trend = 'decreasing'
                    
                    trends[metric_name] = trend
        
        return {
            'overall_status': latest_report.overall_status.value,
            'degradation_level': latest_report.degradation_level.value,
            'uptime_hours': latest_report.uptime_seconds / 3600,
            'key_metrics': {
                name: {
                    'value': metric.value,
                    'status': metric.status.value,
                    'trend': trends.get(name, 'unknown'),
                    'unit': metric.unit
                }
                for name, metric in latest_report.metrics.items()
            },
            'recommendations': latest_report.recommendations,
            'timestamp': latest_report.timestamp.isoformat()
        }
    
    def export_health_report(self, output_file: Optional[Path] = None) -> Path:
        """Export detailed health report to file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = Path(f"health_report_{timestamp}.json")
        
        report_data = {
            'export_timestamp': datetime.now().isoformat(),
            'monitoring_duration_hours': (time.time() - self.start_time) / 3600,
            'total_reports': len(self.health_history),
            'summary': self.get_health_summary(),
            'full_history': [
                {
                    'timestamp': report.timestamp.isoformat(),
                    'overall_status': report.overall_status.value,
                    'degradation_level': report.degradation_level.value,
                    'metrics': {
                        name: {
                            'value': metric.value,
                            'status': metric.status.value,
                            'message': metric.message,
                            'unit': metric.unit
                        }
                        for name, metric in report.metrics.items()
                    },
                    'recommendations': report.recommendations
                }
                for report in self.health_history
            ]
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Health report exported to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to export health report: {e}")
            raise


# Global system monitor instance
system_monitor = SystemMonitor()


async def get_system_health() -> SystemHealth:
    """Convenience function to get current system health"""
    return await system_monitor.get_system_health()


async def start_monitoring(interval: int = 60):
    """Start system monitoring with specified interval"""
    system_monitor.monitoring_interval = interval
    await system_monitor.start_monitoring()


async def stop_monitoring():
    """Stop system monitoring"""
    await system_monitor.stop_monitoring()


def get_health_summary() -> Dict[str, Any]:
    """Get health summary"""
    return system_monitor.get_health_summary()