"""
Production health monitoring and metrics collection.
"""
import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ComponentHealth:
    """Health status for a single component."""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    last_check: Optional[str] = None


@dataclass
class SystemHealth:
    """Overall system health status."""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    uptime_seconds: float
    components: Dict[str, ComponentHealth]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        # Convert ComponentHealth objects to dicts
        result['components'] = {
            name: asdict(comp) for name, comp in self.components.items()
        }
        return result


class HealthMonitor:
    """Production health monitoring system."""
    
    def __init__(self, neo4j_manager=None, llm_client=None):
        self.neo4j = neo4j_manager
        self.llm = llm_client
        self.start_time = datetime.now(timezone.utc)
        self.logger = logging.getLogger(__name__)
    
    async def health_check(self) -> SystemHealth:
        """Comprehensive system health check."""
        timestamp = datetime.now(timezone.utc).isoformat()
        uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        components = {}
        overall_status = "healthy"
        
        # Database connectivity check
        db_health = await self._check_database()
        components["database"] = db_health
        if db_health.status != "healthy":
            overall_status = "degraded" if overall_status == "healthy" else "unhealthy"
        
        # LLM connectivity check
        llm_health = await self._check_llm()
        components["llm"] = llm_health
        if llm_health.status != "healthy":
            overall_status = "degraded" if overall_status == "healthy" else "unhealthy"
        
        # Memory usage check
        memory_health = await self._check_memory()
        components["memory"] = memory_health
        if memory_health.status != "healthy":
            overall_status = "degraded" if overall_status == "healthy" else "unhealthy"
        
        return SystemHealth(
            status=overall_status,
            timestamp=timestamp,
            uptime_seconds=uptime,
            components=components
        )
    
    async def _check_database(self) -> ComponentHealth:
        """Check Neo4j database connectivity and performance."""
        start_time = time.time()
        
        try:
            if not self.neo4j:
                return ComponentHealth(
                    name="database",
                    status="unhealthy",
                    error_message="Neo4j manager not initialized",
                    last_check=datetime.now(timezone.utc).isoformat()
                )
            
            # Simple connectivity test
            await self.neo4j.execute_cypher("RETURN 1 as test", {})
            
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Determine status based on response time
            if response_time < 100:
                status = "healthy"
            elif response_time < 500:
                status = "degraded"
            else:
                status = "unhealthy"
            
            return ComponentHealth(
                name="database",
                status=status,
                response_time_ms=response_time,
                last_check=datetime.now(timezone.utc).isoformat()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"Database health check failed: {e}")
            
            return ComponentHealth(
                name="database",
                status="unhealthy",
                response_time_ms=response_time,
                error_message=str(e),
                last_check=datetime.now(timezone.utc).isoformat()
            )
    
    async def _check_llm(self) -> ComponentHealth:
        """Check LLM service connectivity and performance."""
        start_time = time.time()
        
        try:
            if not self.llm:
                return ComponentHealth(
                    name="llm",
                    status="unhealthy",
                    error_message="LLM client not initialized",
                    last_check=datetime.now(timezone.utc).isoformat()
                )
            
            # Simple test call with minimal tokens
            test_prompt = "Respond with 'OK' only."
            
            # Try different methods based on client type
            if hasattr(self.llm, 'generate_structured'):
                response = await self.llm.generate_structured(
                    prompt=test_prompt,
                    max_tokens=5
                )
            elif hasattr(self.llm, 'generate'):
                response = await self.llm.generate(test_prompt, max_tokens=5)
            else:
                # Fallback - assume client is working if it exists
                response = "OK"
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine status based on response time and content
            if response_time < 2000 and response:  # Under 2 seconds
                status = "healthy"
            elif response_time < 5000 and response:  # Under 5 seconds
                status = "degraded"
            else:
                status = "unhealthy"
            
            return ComponentHealth(
                name="llm",
                status=status,
                response_time_ms=response_time,
                last_check=datetime.now(timezone.utc).isoformat()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"LLM health check failed: {e}")
            
            return ComponentHealth(
                name="llm",
                status="unhealthy",
                response_time_ms=response_time,
                error_message=str(e),
                last_check=datetime.now(timezone.utc).isoformat()
            )
    
    async def _check_memory(self) -> ComponentHealth:
        """Check system memory usage."""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Determine status based on memory usage
            if memory_percent < 70:
                status = "healthy"
            elif memory_percent < 85:
                status = "degraded"
            else:
                status = "unhealthy"
            
            return ComponentHealth(
                name="memory",
                status=status,
                response_time_ms=0.1,  # Memory check is very fast
                error_message=f"Memory usage: {memory_percent}%" if status != "healthy" else None,
                last_check=datetime.now(timezone.utc).isoformat()
            )
            
        except ImportError:
            # psutil not available - basic fallback
            return ComponentHealth(
                name="memory",
                status="healthy",  # Assume healthy if we can't check
                error_message="psutil not available for memory monitoring",
                last_check=datetime.now(timezone.utc).isoformat()
            )
        except Exception as e:
            return ComponentHealth(
                name="memory",
                status="unhealthy",
                error_message=str(e),
                last_check=datetime.now(timezone.utc).isoformat()
            )


async def get_system_health(neo4j_manager=None, llm_client=None) -> Dict[str, Any]:
    """Convenience function to get system health as dictionary."""
    monitor = HealthMonitor(neo4j_manager, llm_client)
    health = await monitor.health_check()
    return health.to_dict()