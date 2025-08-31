"""Monitoring and metrics collection for the application."""

import time
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from functools import wraps
import structlog

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

PREDICTION_COUNT = Counter(
    'predictions_total',
    'Total predictions made',
    ['home_team', 'away_team']
)

MODEL_ACCURACY = Gauge(
    'model_accuracy',
    'Current model accuracy',
    ['model_version']
)

ACTIVE_SESSIONS = Gauge(
    'active_sessions',
    'Number of active user sessions'
)

CACHE_HITS = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

DATABASE_CONNECTIONS = Gauge(
    'database_connections_active',
    'Active database connections'
)

# Structured logger
logger = structlog.get_logger()


def monitor_endpoint(func):
    """Decorator to monitor API endpoints."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        method = kwargs.get('request', {}).method if 'request' in kwargs else 'GET'
        endpoint = func.__name__
        
        try:
            result = await func(*args, **kwargs)
            status_code = getattr(result, 'status_code', 200)
            
            # Record metrics
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(time.time() - start_time)
            
            # Log request
            logger.info(
                "API request completed",
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                duration=time.time() - start_time
            )
            
            return result
            
        except Exception as e:
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=500
            ).inc()
            
            logger.error(
                "API request failed",
                method=method,
                endpoint=endpoint,
                error=str(e),
                duration=time.time() - start_time
            )
            raise
    
    return wrapper


def record_prediction(home_team: str, away_team: str):
    """Record a prediction metric."""
    PREDICTION_COUNT.labels(
        home_team=home_team,
        away_team=away_team
    ).inc()


def update_model_accuracy(model_version: str, accuracy: float):
    """Update model accuracy metric."""
    MODEL_ACCURACY.labels(model_version=model_version).set(accuracy)


def record_cache_hit(cache_type: str):
    """Record cache hit."""
    CACHE_HITS.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str):
    """Record cache miss."""
    CACHE_MISSES.labels(cache_type=cache_type).inc()


def update_active_sessions(count: int):
    """Update active sessions count."""
    ACTIVE_SESSIONS.set(count)


def get_metrics():
    """Get Prometheus metrics."""
    return generate_latest()

# Aliases for backward compatibility
monitor_request = monitor_endpoint
monitor_prediction = record_prediction
