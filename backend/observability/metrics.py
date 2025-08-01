import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta
import redis.asyncio as redis
import json
from prometheus_client import (
    Counter, Histogram, Gauge, Summary, Info,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
from contextlib import asynccontextmanager
import psutil
import functools
from backend.core.config import settings

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    GAUGE = "gauge"
    SUMMARY = "summary"
    INFO = "info"


@dataclass
class SLI:
    """Service Level Indicator"""
    name: str
    description: str
    query: str
    threshold: float
    comparison: str  # ">=", "<=", "<", ">"
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class SLO:
    """Service Level Objective"""
    name: str
    description: str
    sli_name: str
    target: float  # e.g., 99.9 for 99.9%
    window: str  # e.g., "7d", "30d"
    error_budget: float = None
    burn_rate_alert_threshold: float = 2.0
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Custom metrics collector for SQL Genius AI"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        self.redis_client = redis.from_url(settings.REDIS_URL)
        
        # Application metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code', 'tenant_id'],
            registry=self.registry
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint', 'tenant_id'],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )
        
        self.sql_generation_duration = Histogram(
            'sql_generation_duration_seconds',
            'SQL generation duration',
            ['model', 'complexity', 'tenant_id'],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0],
            registry=self.registry
        )
        
        self.sql_generation_total = Counter(
            'sql_generation_total',
            'Total SQL generations',
            ['model', 'status', 'tenant_id'],
            registry=self.registry
        )
        
        self.active_queries = Gauge(
            'active_queries_total',
            'Currently active queries',
            ['tenant_id'],
            registry=self.registry
        )
        
        self.query_queue_depth = Gauge(
            'query_queue_depth',
            'Depth of query processing queue',
            ['queue_name'],
            registry=self.registry
        )
        
        self.ai_api_requests = Counter(
            'ai_api_requests_total',
            'AI API requests',
            ['provider', 'model', 'status'],
            registry=self.registry
        )
        
        self.ai_api_tokens = Counter(
            'ai_api_tokens_total',
            'AI API tokens consumed',
            ['provider', 'model', 'type'],  # type: input/output
            registry=self.registry
        )
        
        self.ai_api_cost = Counter(
            'ai_api_cost_total',
            'AI API cost in USD',
            ['provider', 'model'],
            registry=self.registry
        )
        
        self.cache_hits = Counter(
            'cache_hits_total',
            'Cache hits',
            ['cache_type', 'tenant_id'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'cache_misses_total',
            'Cache misses',
            ['cache_type', 'tenant_id'],
            registry=self.registry
        )
        
        self.user_sessions = Gauge(
            'user_sessions_active',
            'Active user sessions',
            ['tenant_id'],
            registry=self.registry
        )
        
        self.auth_events = Counter(
            'auth_events_total',
            'Authentication events',
            ['event_type', 'status', 'method'],
            registry=self.registry
        )
        
        self.file_uploads = Counter(
            'file_uploads_total',
            'File uploads',
            ['file_type', 'status', 'tenant_id'],
            registry=self.registry
        )
        
        self.file_processing_duration = Histogram(
            'file_processing_duration_seconds',
            'File processing duration',
            ['file_type', 'size_bucket', 'tenant_id'],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0],
            registry=self.registry
        )
        
        # Business metrics
        self.tenant_usage = Counter(
            'tenant_usage_total',
            'Tenant usage metrics',
            ['tenant_id', 'feature', 'plan'],
            registry=self.registry
        )
        
        self.revenue_events = Counter(
            'revenue_events_total',
            'Revenue events',
            ['event_type', 'plan', 'amount_bucket'],
            registry=self.registry
        )
        
        # System metrics
        self.system_cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.system_memory_usage = Gauge(
            'system_memory_usage_bytes',
            'System memory usage in bytes',
            registry=self.registry
        )
        
        self.system_disk_usage = Gauge(
            'system_disk_usage_bytes',
            'System disk usage in bytes',
            ['mount_point'],
            registry=self.registry
        )
        
        # Database metrics
        self.db_connections_active = Gauge(
            'db_connections_active',
            'Active database connections',
            ['database'],
            registry=self.registry
        )
        
        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Database query duration',
            ['query_type', 'table'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
            registry=self.registry
        )
        
        # Error tracking
        self.errors_total = Counter(
            'errors_total',
            'Total errors',
            ['error_type', 'component', 'severity'],
            registry=self.registry
        )
        
        # Application info
        self.app_info = Info(
            'app_info',
            'Application information',
            registry=self.registry
        )
        
        # Initialize app info
        self.app_info.info({
            'version': settings.VERSION,
            'environment': getattr(settings, 'ENVIRONMENT', 'production'),
            'project': settings.PROJECT_NAME
        })
        
    async def start_system_metrics_collection(self):
        """Start collecting system metrics"""
        asyncio.create_task(self._collect_system_metrics())
        
    async def _collect_system_metrics(self):
        """Collect system metrics periodically"""
        while True:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.system_cpu_usage.set(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.system_memory_usage.set(memory.used)
                
                # Disk usage
                disk_usage = psutil.disk_usage('/')
                self.system_disk_usage.labels(mount_point='/').set(disk_usage.used)
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                logger.error(f"System metrics collection error: {e}")
                await asyncio.sleep(60)
    
    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        tenant_id: str = "unknown"
    ):
        """Record HTTP request metrics"""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code),
            tenant_id=tenant_id
        ).inc()
        
        self.http_request_duration.labels(
            method=method,
            endpoint=endpoint,
            tenant_id=tenant_id
        ).observe(duration)
    
    def record_sql_generation(
        self,
        model: str,
        duration: float,
        status: str,
        complexity: str = "medium",
        tenant_id: str = "unknown"
    ):
        """Record SQL generation metrics"""
        self.sql_generation_total.labels(
            model=model,
            status=status,
            tenant_id=tenant_id
        ).inc()
        
        self.sql_generation_duration.labels(
            model=model,
            complexity=complexity,
            tenant_id=tenant_id
        ).observe(duration)
    
    def record_ai_api_usage(
        self,
        provider: str,
        model: str,
        status: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0
    ):
        """Record AI API usage metrics"""
        self.ai_api_requests.labels(
            provider=provider,
            model=model,
            status=status
        ).inc()
        
        if input_tokens > 0:
            self.ai_api_tokens.labels(
                provider=provider,
                model=model,
                type="input"
            ).inc(input_tokens)
        
        if output_tokens > 0:
            self.ai_api_tokens.labels(
                provider=provider,
                model=model,
                type="output"
            ).inc(output_tokens)
        
        if cost > 0:
            self.ai_api_cost.labels(
                provider=provider,
                model=model
            ).inc(cost)
    
    def record_cache_event(self, cache_type: str, hit: bool, tenant_id: str = "unknown"):
        """Record cache hit/miss"""
        if hit:
            self.cache_hits.labels(cache_type=cache_type, tenant_id=tenant_id).inc()
        else:
            self.cache_misses.labels(cache_type=cache_type, tenant_id=tenant_id).inc()
    
    def record_auth_event(self, event_type: str, status: str, method: str = "password"):
        """Record authentication event"""
        self.auth_events.labels(
            event_type=event_type,
            status=status,
            method=method
        ).inc()
    
    def record_error(self, error_type: str, component: str, severity: str = "error"):
        """Record error event"""
        self.errors_total.labels(
            error_type=error_type,
            component=component,
            severity=severity
        ).inc()
    
    def get_metrics(self) -> str:
        """Get Prometheus metrics"""
        return generate_latest(self.registry).decode('utf-8')


class SLIMonitor:
    """Service Level Indicator monitoring"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.slis = self._define_slis()
        self.slos = self._define_slos()
        
    def _define_slis(self) -> Dict[str, SLI]:
        """Define Service Level Indicators"""
        return {
            "api_availability": SLI(
                name="api_availability",
                description="API availability percentage",
                query="(sum(rate(http_requests_total{status_code!~'5..'}[5m])) / sum(rate(http_requests_total[5m]))) * 100",
                threshold=99.9,
                comparison=">=",
                unit="%"
            ),
            
            "api_latency_p95": SLI(
                name="api_latency_p95",
                description="95th percentile API latency",
                query="histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
                threshold=2.0,
                comparison="<=",
                unit="seconds"
            ),
            
            "sql_generation_success_rate": SLI(
                name="sql_generation_success_rate",
                description="SQL generation success rate",
                query="(sum(rate(sql_generation_total{status='success'}[5m])) / sum(rate(sql_generation_total[5m]))) * 100",
                threshold=95.0,
                comparison=">=",
                unit="%"
            ),
            
            "sql_generation_latency_p90": SLI(
                name="sql_generation_latency_p90",
                description="90th percentile SQL generation latency",
                query="histogram_quantile(0.90, sum(rate(sql_generation_duration_seconds_bucket[5m])) by (le))",
                threshold=30.0,
                comparison="<=",
                unit="seconds"
            ),
            
            "auth_success_rate": SLI(
                name="auth_success_rate",
                description="Authentication success rate",
                query="(sum(rate(auth_events_total{status='success'}[5m])) / sum(rate(auth_events_total[5m]))) * 100",
                threshold=99.0,
                comparison=">=",
                unit="%"
            ),
            
            "cache_hit_rate": SLI(
                name="cache_hit_rate",
                description="Cache hit rate",
                query="(sum(rate(cache_hits_total[5m])) / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m])))) * 100",
                threshold=80.0,
                comparison=">=",
                unit="%"
            ),
            
            "error_rate": SLI(
                name="error_rate",
                description="Application error rate",
                query="sum(rate(errors_total[5m]))",
                threshold=10.0,
                comparison="<=",
                unit="errors/sec"
            )
        }
    
    def _define_slos(self) -> Dict[str, SLO]:
        """Define Service Level Objectives"""
        return {
            "api_availability_slo": SLO(
                name="api_availability_slo",
                description="API should be available 99.9% of the time",
                sli_name="api_availability",
                target=99.9,
                window="7d",
                error_budget=0.1
            ),
            
            "api_latency_slo": SLO(
                name="api_latency_slo",
                description="95% of API requests should complete within 2 seconds",
                sli_name="api_latency_p95",
                target=2.0,
                window="7d"
            ),
            
            "sql_generation_reliability_slo": SLO(
                name="sql_generation_reliability_slo",
                description="SQL generation should succeed 95% of the time",
                sli_name="sql_generation_success_rate",
                target=95.0,
                window="24h",
                error_budget=5.0
            ),
            
            "sql_generation_performance_slo": SLO(
                name="sql_generation_performance_slo",
                description="90% of SQL generations should complete within 30 seconds",
                sli_name="sql_generation_latency_p90",
                target=30.0,
                window="24h"
            )
        }
    
    async def evaluate_slis(self) -> Dict[str, float]:
        """Evaluate current SLI values"""
        results = {}
        
        for sli_name, sli in self.slis.items():
            try:
                # In production, this would query Prometheus
                # For now, we'll simulate with cached metrics
                value = await self._query_metric(sli.query)
                results[sli_name] = value
                
                # Store in Redis for SLO tracking
                await self.redis_client.setex(
                    f"sli:{sli_name}:current",
                    300,  # 5 minutes
                    json.dumps({
                        "value": value,
                        "timestamp": datetime.utcnow().isoformat(),
                        "threshold": sli.threshold,
                        "in_violation": not self._check_threshold(value, sli.threshold, sli.comparison)
                    })
                )
                
            except Exception as e:
                logger.error(f"Failed to evaluate SLI {sli_name}: {e}")
                results[sli_name] = None
        
        return results
    
    async def evaluate_slos(self) -> Dict[str, Dict[str, Any]]:
        """Evaluate SLO compliance"""
        results = {}
        
        for slo_name, slo in self.slos.items():
            try:
                # Get SLI history for the window
                sli_history = await self._get_sli_history(slo.sli_name, slo.window)
                
                if not sli_history:
                    continue
                
                # Calculate compliance
                total_measurements = len(sli_history)
                compliant_measurements = sum(
                    1 for measurement in sli_history 
                    if not measurement.get("in_violation", False)
                )
                
                compliance_percentage = (compliant_measurements / total_measurements) * 100
                error_budget_consumed = 100 - compliance_percentage
                
                # Calculate burn rate
                burn_rate = self._calculate_burn_rate(sli_history, slo)
                
                results[slo_name] = {
                    "compliance_percentage": compliance_percentage,
                    "target": slo.target,
                    "in_violation": compliance_percentage < slo.target,
                    "error_budget_consumed": error_budget_consumed,
                    "burn_rate": burn_rate,
                    "window": slo.window,
                    "total_measurements": total_measurements
                }
                
            except Exception as e:
                logger.error(f"Failed to evaluate SLO {slo_name}: {e}")
                results[slo_name] = {"error": str(e)}
        
        return results
    
    async def _query_metric(self, query: str) -> float:
        """Query metric value (placeholder for Prometheus integration)"""
        # This would integrate with Prometheus in production
        # For now, return simulated values
        import random
        
        if "availability" in query:
            return random.uniform(99.5, 99.99)
        elif "latency" in query:
            return random.uniform(0.5, 3.0)
        elif "success_rate" in query:
            return random.uniform(95.0, 99.9)
        elif "cache_hit_rate" in query:
            return random.uniform(75.0, 95.0)
        elif "error_rate" in query:
            return random.uniform(0.1, 15.0)
        else:
            return random.uniform(0, 100)
    
    def _check_threshold(self, value: float, threshold: float, comparison: str) -> bool:
        """Check if value meets threshold"""
        if comparison == ">=":
            return value >= threshold
        elif comparison == "<=":
            return value <= threshold
        elif comparison == ">":
            return value > threshold
        elif comparison == "<":
            return value < threshold
        return False
    
    async def _get_sli_history(self, sli_name: str, window: str) -> List[Dict[str, Any]]:
        """Get SLI history for time window"""
        try:
            # Parse window (e.g., "7d", "24h")
            if window.endswith('d'):
                hours = int(window[:-1]) * 24
            elif window.endswith('h'):
                hours = int(window[:-1])
            else:
                hours = 24
            
            # Get historical data from Redis
            history = []
            pattern = f"sli:{sli_name}:*"
            
            async for key in self.redis_client.scan_iter(match=pattern):
                data = await self.redis_client.get(key)
                if data:
                    measurement = json.loads(data)
                    timestamp = datetime.fromisoformat(measurement["timestamp"])
                    
                    # Check if within window
                    if datetime.utcnow() - timestamp <= timedelta(hours=hours):
                        history.append(measurement)
            
            return sorted(history, key=lambda x: x["timestamp"])
            
        except Exception as e:
            logger.error(f"Failed to get SLI history for {sli_name}: {e}")
            return []
    
    def _calculate_burn_rate(self, sli_history: List[Dict[str, Any]], slo: SLO) -> float:
        """Calculate error budget burn rate"""
        if not sli_history or not slo.error_budget:
            return 0.0
        
        # Calculate current error rate
        recent_violations = sum(
            1 for measurement in sli_history[-10:]  # Last 10 measurements
            if measurement.get("in_violation", False)
        )
        
        if recent_violations == 0:
            return 0.0
        
        violation_rate = recent_violations / min(10, len(sli_history))
        normal_burn_rate = slo.error_budget / 100  # Normal burn rate per measurement
        
        return violation_rate / normal_burn_rate if normal_burn_rate > 0 else 0.0


# Decorator for automatic metrics collection
def track_duration(metric_name: str, labels: Dict[str, str] = None):
    """Decorator to track function execution duration"""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Record metric (would integrate with metrics collector)
                    logger.info(f"Function {func.__name__} completed in {duration:.3f}s")
                    
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(f"Function {func.__name__} failed after {duration:.3f}s: {e}")
                    raise
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Record metric
                    logger.info(f"Function {func.__name__} completed in {duration:.3f}s")
                    
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(f"Function {func.__name__} failed after {duration:.3f}s: {e}")
                    raise
            return sync_wrapper
    return decorator


# Global instances
metrics_collector = MetricsCollector()
sli_monitor = SLIMonitor(metrics_collector)