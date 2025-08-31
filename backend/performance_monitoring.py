"""Advanced performance monitoring with detailed metrics and alerting."""

import asyncio
import time
import psutil
import structlog
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import json
from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
import numpy as np

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
PREDICTION_COUNT = Counter('predictions_total', 'Total predictions made', ['model', 'result'])
PREDICTION_DURATION = Histogram('prediction_duration_seconds', 'Prediction processing time', ['model'])
CACHE_OPERATIONS = Counter('cache_operations_total', 'Cache operations', ['operation', 'result'])
ACTIVE_CONNECTIONS = Gauge('websocket_connections_active', 'Active WebSocket connections')
SYSTEM_CPU_USAGE = Gauge('system_cpu_usage_percent', 'System CPU usage percentage')
SYSTEM_MEMORY_USAGE = Gauge('system_memory_usage_percent', 'System memory usage percentage')
MODEL_ACCURACY = Gauge('model_accuracy', 'Model accuracy score', ['model'])
ERROR_RATE = Gauge('error_rate', 'Error rate percentage', ['service'])

@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    unit: str

@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    metric: str
    condition: str  # "gt", "lt", "eq"
    threshold: float
    duration: int  # seconds
    severity: str  # "critical", "warning", "info"
    enabled: bool = True

class PerformanceMonitor:
    """Comprehensive performance monitoring system."""
    
    def __init__(self):
        self.metrics_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alert_rules: List[AlertRule] = []
        self.active_alerts: Dict[str, datetime] = {}
        self.system_stats = {}
        self.request_stats = {
            "total_requests": 0,
            "total_errors": 0,
            "avg_response_time": 0.0,
            "requests_per_second": 0.0
        }
        self.prediction_stats = {
            "total_predictions": 0,
            "avg_prediction_time": 0.0,
            "model_usage": defaultdict(int),
            "accuracy_scores": defaultdict(list)
        }
        self.background_tasks: List[asyncio.Task] = []
        
    async def start_monitoring(self):
        """Start background monitoring tasks."""
        self.background_tasks = [
            asyncio.create_task(self._collect_system_metrics()),
            asyncio.create_task(self._process_alerts()),
            asyncio.create_task(self._cleanup_old_metrics()),
            asyncio.create_task(self._calculate_derived_metrics())
        ]
        
        # Initialize default alert rules
        self._setup_default_alerts()
        
        logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop all monitoring tasks."""
        for task in self.background_tasks:
            task.cancel()
        
        logger.info("Performance monitoring stopped")
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None, unit: str = ""):
        """Record a custom metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            tags=tags or {},
            unit=unit
        )
        
        self.metrics_buffer[name].append(metric)
        
        # Update Prometheus metrics
        if name == "request_duration":
            REQUEST_DURATION.labels(
                method=tags.get("method", "unknown"),
                endpoint=tags.get("endpoint", "unknown")
            ).observe(value)
        elif name == "prediction_duration":
            PREDICTION_DURATION.labels(
                model=tags.get("model", "unknown")
            ).observe(value)
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        
        self.request_stats["total_requests"] += 1
        if status_code >= 400:
            self.request_stats["total_errors"] += 1
        
        # Update average response time (rolling average)
        current_avg = self.request_stats["avg_response_time"]
        total_requests = self.request_stats["total_requests"]
        self.request_stats["avg_response_time"] = (
            (current_avg * (total_requests - 1) + duration) / total_requests
        )
        
        self.record_metric("request_duration", duration, {
            "method": method,
            "endpoint": endpoint,
            "status": str(status_code)
        }, "seconds")
    
    def record_prediction(self, model: str, duration: float, accuracy: Optional[float] = None):
        """Record ML prediction metrics."""
        PREDICTION_COUNT.labels(model=model, result="success").inc()
        PREDICTION_DURATION.labels(model=model).observe(duration)
        
        self.prediction_stats["total_predictions"] += 1
        self.prediction_stats["model_usage"][model] += 1
        
        if accuracy is not None:
            self.prediction_stats["accuracy_scores"][model].append(accuracy)
            MODEL_ACCURACY.labels(model=model).set(accuracy)
        
        # Update average prediction time
        current_avg = self.prediction_stats["avg_prediction_time"]
        total_predictions = self.prediction_stats["total_predictions"]
        self.prediction_stats["avg_prediction_time"] = (
            (current_avg * (total_predictions - 1) + duration) / total_predictions
        )
        
        self.record_metric("prediction_duration", duration, {"model": model}, "seconds")
    
    def record_cache_operation(self, operation: str, result: str):
        """Record cache operation metrics."""
        CACHE_OPERATIONS.labels(operation=operation, result=result).inc()
        
        self.record_metric("cache_operation", 1, {
            "operation": operation,
            "result": result
        })
    
    def record_websocket_connections(self, count: int):
        """Record active WebSocket connections."""
        ACTIVE_CONNECTIONS.set(count)
        self.record_metric("websocket_connections", count)
    
    async def _collect_system_metrics(self):
        """Collect system-level metrics."""
        while True:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                SYSTEM_CPU_USAGE.set(cpu_percent)
                self.record_metric("system_cpu_usage", cpu_percent, unit="percent")
                
                # Memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                SYSTEM_MEMORY_USAGE.set(memory_percent)
                self.record_metric("system_memory_usage", memory_percent, unit="percent")
                
                # Disk usage
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                self.record_metric("system_disk_usage", disk_percent, unit="percent")
                
                # Network I/O
                network = psutil.net_io_counters()
                self.record_metric("network_bytes_sent", network.bytes_sent, unit="bytes")
                self.record_metric("network_bytes_recv", network.bytes_recv, unit="bytes")
                
                # Update system stats
                self.system_stats = {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent,
                    "network_bytes_sent": network.bytes_sent,
                    "network_bytes_recv": network.bytes_recv,
                    "timestamp": datetime.now().isoformat()
                }
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error collecting system metrics", error=str(e))
                await asyncio.sleep(30)
    
    async def _process_alerts(self):
        """Process alert rules and trigger alerts."""
        while True:
            try:
                current_time = datetime.now()
                
                for rule in self.alert_rules:
                    if not rule.enabled:
                        continue
                    
                    # Get recent metrics for this rule
                    if rule.metric not in self.metrics_buffer:
                        continue
                    
                    recent_metrics = [
                        m for m in self.metrics_buffer[rule.metric]
                        if (current_time - m.timestamp).total_seconds() <= rule.duration
                    ]
                    
                    if not recent_metrics:
                        continue
                    
                    # Calculate metric value (average of recent values)
                    avg_value = sum(m.value for m in recent_metrics) / len(recent_metrics)
                    
                    # Check condition
                    alert_triggered = False
                    if rule.condition == "gt" and avg_value > rule.threshold:
                        alert_triggered = True
                    elif rule.condition == "lt" and avg_value < rule.threshold:
                        alert_triggered = True
                    elif rule.condition == "eq" and abs(avg_value - rule.threshold) < 0.01:
                        alert_triggered = True
                    
                    # Handle alert
                    if alert_triggered:
                        if rule.name not in self.active_alerts:
                            self.active_alerts[rule.name] = current_time
                            await self._trigger_alert(rule, avg_value)
                    else:
                        if rule.name in self.active_alerts:
                            del self.active_alerts[rule.name]
                            await self._resolve_alert(rule)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error processing alerts", error=str(e))
                await asyncio.sleep(10)
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics to prevent memory leaks."""
        while True:
            try:
                cutoff_time = datetime.now() - timedelta(hours=24)
                
                for metric_name, metrics in self.metrics_buffer.items():
                    # Remove old metrics
                    while metrics and metrics[0].timestamp < cutoff_time:
                        metrics.popleft()
                
                await asyncio.sleep(3600)  # Clean up every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error cleaning up metrics", error=str(e))
                await asyncio.sleep(3600)
    
    async def _calculate_derived_metrics(self):
        """Calculate derived metrics like rates and percentiles."""
        while True:
            try:
                # Calculate requests per second
                if "request_duration" in self.metrics_buffer:
                    recent_requests = [
                        m for m in self.metrics_buffer["request_duration"]
                        if (datetime.now() - m.timestamp).total_seconds() <= 60
                    ]
                    self.request_stats["requests_per_second"] = len(recent_requests) / 60.0
                
                # Calculate error rate
                if self.request_stats["total_requests"] > 0:
                    error_rate = (self.request_stats["total_errors"] / 
                                self.request_stats["total_requests"]) * 100
                    ERROR_RATE.labels(service="api").set(error_rate)
                    self.record_metric("error_rate", error_rate, {"service": "api"}, "percent")
                
                # Calculate model accuracy averages
                for model, accuracies in self.prediction_stats["accuracy_scores"].items():
                    if accuracies:
                        avg_accuracy = sum(accuracies[-100:]) / len(accuracies[-100:])  # Last 100
                        MODEL_ACCURACY.labels(model=model).set(avg_accuracy)
                
                await asyncio.sleep(60)  # Calculate every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error calculating derived metrics", error=str(e))
                await asyncio.sleep(60)
    
    def _setup_default_alerts(self):
        """Setup default alert rules."""
        self.alert_rules = [
            AlertRule(
                name="high_cpu_usage",
                metric="system_cpu_usage",
                condition="gt",
                threshold=80.0,
                duration=300,  # 5 minutes
                severity="warning"
            ),
            AlertRule(
                name="high_memory_usage",
                metric="system_memory_usage",
                condition="gt",
                threshold=85.0,
                duration=300,
                severity="critical"
            ),
            AlertRule(
                name="high_error_rate",
                metric="error_rate",
                condition="gt",
                threshold=5.0,  # 5%
                duration=180,  # 3 minutes
                severity="critical"
            ),
            AlertRule(
                name="slow_predictions",
                metric="prediction_duration",
                condition="gt",
                threshold=2.0,  # 2 seconds
                duration=300,
                severity="warning"
            ),
            AlertRule(
                name="low_model_accuracy",
                metric="model_accuracy",
                condition="lt",
                threshold=0.7,  # 70%
                duration=600,  # 10 minutes
                severity="warning"
            )
        ]
    
    async def _trigger_alert(self, rule: AlertRule, value: float):
        """Trigger an alert."""
        alert_data = {
            "rule_name": rule.name,
            "metric": rule.metric,
            "value": value,
            "threshold": rule.threshold,
            "severity": rule.severity,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.log(
            rule.severity.upper(),
            f"Alert triggered: {rule.name}",
            **alert_data
        )
        
        # Here you would integrate with alerting systems like:
        # - Slack notifications
        # - Email alerts
        # - PagerDuty
        # - Discord webhooks
        
    async def _resolve_alert(self, rule: AlertRule):
        """Resolve an alert."""
        logger.info(f"Alert resolved: {rule.name}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        return {
            "system_stats": self.system_stats,
            "request_stats": self.request_stats,
            "prediction_stats": {
                **self.prediction_stats,
                "accuracy_scores": {
                    model: {
                        "current": scores[-1] if scores else 0,
                        "average": sum(scores) / len(scores) if scores else 0,
                        "count": len(scores)
                    }
                    for model, scores in self.prediction_stats["accuracy_scores"].items()
                }
            },
            "active_alerts": [
                {
                    "name": name,
                    "triggered_at": triggered_at.isoformat(),
                    "duration": (datetime.now() - triggered_at).total_seconds()
                }
                for name, triggered_at in self.active_alerts.items()
            ],
            "metrics_buffer_sizes": {
                name: len(metrics) for name, metrics in self.metrics_buffer.items()
            }
        }
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus-formatted metrics."""
        return generate_latest()
    
    def add_alert_rule(self, rule: AlertRule):
        """Add a custom alert rule."""
        self.alert_rules.append(rule)
        logger.info(f"Alert rule added: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str) -> bool:
        """Remove an alert rule."""
        for i, rule in enumerate(self.alert_rules):
            if rule.name == rule_name:
                del self.alert_rules[i]
                logger.info(f"Alert rule removed: {rule_name}")
                return True
        return False

# Middleware for automatic request monitoring
class PerformanceMiddleware:
    """FastAPI middleware for automatic performance monitoring."""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
    
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        # Extract request info
        method = request.method
        endpoint = str(request.url.path)
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            logger.error("Request processing error", error=str(e))
            raise
        finally:
            # Record metrics
            duration = time.time() - start_time
            self.monitor.record_request(method, endpoint, status_code, duration)
        
        return response

# Global performance monitor instance
performance_monitor = PerformanceMonitor()
