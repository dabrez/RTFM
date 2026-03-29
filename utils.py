import time
import logging
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import threading
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)

class Metrics:
    """Prometheus metrics wrapper for RTFM bot services"""
    
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Metrics, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, port: int = 8000):
        if self._initialized:
            return
        
        self.port = port
        self.messages_processed = Counter(
            'rtfm_messages_processed_total', 
            'Total number of messages processed',
            ['topic', 'status']
        )
        self.processing_latency = Histogram(
            'rtfm_processing_latency_seconds',
            'Time spent processing messages',
            ['topic']
        )
        self.errors = Counter(
            'rtfm_errors_total',
            'Total number of errors',
            ['type']
        )
        self.circuit_breaker_state = Gauge(
            'rtfm_circuit_breaker_state',
            'Current state of circuit breaker (0=closed, 1=open, 2=half-open)',
            ['service']
        )
        self.cache_hits = Counter(
            'rtfm_cache_hits_total',
            'Total number of cache hits'
        )
        self.cache_misses = Counter(
            'rtfm_cache_misses_total',
            'Total number of cache misses'
        )
        
        try:
            start_http_server(self.port)
            logger.info(f"Prometheus metrics server started on port {self.port}")
        except Exception as e:
            logger.warning(f"Could not start prometheus server on port {self.port}: {e}")
            
        self._initialized = True

class CircuitBreaker:
    """Simple Circuit Breaker implementation"""
    
    def __init__(
        self, 
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.metrics = Metrics()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                logger.info(f"Circuit Breaker {self.name} switching to HALF_OPEN")
                self.state = "HALF_OPEN"
                self.metrics.circuit_breaker_state.labels(service=self.name).set(2)
            else:
                logger.warning(f"Circuit Breaker {self.name} is OPEN, failing fast")
                raise Exception(f"Circuit Breaker {self.name} is OPEN")

        try:
            result = func(*args, **kwargs)
            
            if self.state == "HALF_OPEN" or self.state == "OPEN":
                logger.info(f"Circuit Breaker {self.name} switching to CLOSED")
                self.state = "CLOSED"
                self.failures = 0
                self.metrics.circuit_breaker_state.labels(service=self.name).set(0)
            
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            logger.error(f"Circuit Breaker {self.name} failure {self.failures}: {e}")
            
            if self.failures >= self.failure_threshold:
                logger.error(f"Circuit Breaker {self.name} switching to OPEN")
                self.state = "OPEN"
                self.metrics.circuit_breaker_state.labels(service=self.name).set(1)
            
            raise e
