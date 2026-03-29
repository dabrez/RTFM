import time
import logging
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)

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

    def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                logger.info(f"Circuit Breaker {self.name} switching to HALF_OPEN")
                self.state = "HALF_OPEN"
            else:
                logger.warning(f"Circuit Breaker {self.name} is OPEN, failing fast")
                raise Exception(f"Circuit Breaker {self.name} is OPEN")

        try:
            result = func(*args, **kwargs)
            
            if self.state == "HALF_OPEN" or self.state == "OPEN":
                logger.info(f"Circuit Breaker {self.name} switching to CLOSED")
                self.state = "CLOSED"
                self.failures = 0
            
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            logger.error(f"Circuit Breaker {self.name} failure {self.failures}: {e}")
            
            if self.failures >= self.failure_threshold:
                logger.error(f"Circuit Breaker {self.name} switching to OPEN")
                self.state = "OPEN"
            
            raise e
