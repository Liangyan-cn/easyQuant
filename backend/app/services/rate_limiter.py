import asyncio
import functools
import logging
import random
import threading
import time
from collections import deque
from typing import Any, Callable, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RateLimiter:
    def __init__(
        self,
        calls_per_second: float = 1.0,
        burst_size: int = 3,
        name: str = "default",
    ):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.burst_size = burst_size
        self.name = name
        
        self._tokens = float(burst_size)
        self._last_update = time.monotonic()
        self._lock = threading.Lock()
        self._async_lock: Optional[asyncio.Lock] = None
        
        self._call_times: deque = deque(maxlen=100)
        
    def _get_async_lock(self) -> asyncio.Lock:
        if self._async_lock is None:
            self._async_lock = asyncio.Lock()
        return self._async_lock
    
    def _refill_tokens(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_update
        self._tokens = min(
            self.burst_size,
            self._tokens + elapsed * self.calls_per_second
        )
        self._last_update = now
    
    def acquire_sync(self, timeout: Optional[float] = None) -> bool:
        start_time = time.monotonic()
        
        while True:
            with self._lock:
                self._refill_tokens()
                
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    self._call_times.append(time.monotonic())
                    return True
                
                wait_time = (1.0 - self._tokens) / self.calls_per_second
            
            if timeout is not None:
                elapsed = time.monotonic() - start_time
                if elapsed + wait_time > timeout:
                    logger.warning(f"RateLimiter[{self.name}]: Timeout waiting for token")
                    return False
            
            time.sleep(min(wait_time, 0.1))
    
    async def acquire_async(self, timeout: Optional[float] = None) -> bool:
        start_time = time.monotonic()
        lock = self._get_async_lock()
        
        while True:
            async with lock:
                self._refill_tokens()
                
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    self._call_times.append(time.monotonic())
                    return True
                
                wait_time = (1.0 - self._tokens) / self.calls_per_second
            
            if timeout is not None:
                elapsed = time.monotonic() - start_time
                if elapsed + wait_time > timeout:
                    logger.warning(f"RateLimiter[{self.name}]: Timeout waiting for token")
                    return False
            
            await asyncio.sleep(min(wait_time, 0.1))
    
    def get_stats(self) -> dict:
        now = time.monotonic()
        recent_calls = sum(1 for t in self._call_times if now - t < 60)
        return {
            "name": self.name,
            "tokens_available": self._tokens,
            "calls_per_second": self.calls_per_second,
            "burst_size": self.burst_size,
            "calls_last_minute": recent_calls,
        }


class RetryConfig:
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: tuple = (
            ConnectionError,
            TimeoutError,
            RuntimeError,
        ),
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions
    
    def get_delay(self, attempt: int) -> float:
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            delay = delay * (0.5 + random.random())
        
        return delay
    
    def is_retryable(self, exception: Exception) -> bool:
        if isinstance(exception, self.retryable_exceptions):
            return True
        
        error_msg = str(exception).lower()
        retryable_patterns = [
            "connection aborted",
            "remote end closed",
            "connection reset",
            "timeout",
            "rate limit",
            "too many requests",
            "服务繁忙",
        ]
        return any(pattern in error_msg for pattern in retryable_patterns)


_akshare_limiter: Optional[RateLimiter] = None
_default_retry_config: Optional[RetryConfig] = None


def _get_settings():
    try:
        from app.config import settings
        return settings
    except ImportError:
        return None


def get_akshare_limiter() -> RateLimiter:
    global _akshare_limiter
    if _akshare_limiter is None:
        settings = _get_settings()
        qps = settings.AKSHARE_RATE_LIMIT_QPS if settings else 0.5
        burst = settings.AKSHARE_RATE_LIMIT_BURST if settings else 3
        _akshare_limiter = RateLimiter(
            calls_per_second=qps,
            burst_size=burst,
            name="akshare",
        )
        logger.info(f"Initialized AKShare rate limiter: {qps} QPS, burst={burst}")
    return _akshare_limiter


def get_default_retry_config() -> RetryConfig:
    global _default_retry_config
    if _default_retry_config is None:
        settings = _get_settings()
        max_retries = settings.AKSHARE_RETRY_MAX_ATTEMPTS if settings else 3
        base_delay = settings.AKSHARE_RETRY_BASE_DELAY if settings else 2.0
        max_delay = settings.AKSHARE_RETRY_MAX_DELAY if settings else 120.0
        _default_retry_config = RetryConfig(
            max_retries=max_retries,
            base_delay=base_delay,
            max_delay=max_delay,
            exponential_base=2.0,
            jitter=True,
        )
        logger.info(
            f"Initialized retry config: max_retries={max_retries}, "
            f"base_delay={base_delay}s, max_delay={max_delay}s"
        )
    return _default_retry_config


def configure_rate_limiter(
    calls_per_second: float = 0.5,
    burst_size: int = 3,
) -> None:
    global _akshare_limiter
    _akshare_limiter = RateLimiter(
        calls_per_second=calls_per_second,
        burst_size=burst_size,
        name="akshare",
    )
    logger.info(
        f"Configured AKShare rate limiter: {calls_per_second} calls/sec, "
        f"burst={burst_size}"
    )


def configure_retry(
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 120.0,
) -> None:
    global _default_retry_config
    _default_retry_config = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
    )
    logger.info(
        f"Configured retry: max_retries={max_retries}, "
        f"base_delay={base_delay}s, max_delay={max_delay}s"
    )


def with_rate_limit(
    limiter: Optional[RateLimiter] = None,
    timeout: Optional[float] = 30.0,
) -> Callable:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            rate_limiter = limiter or get_akshare_limiter()
            if not rate_limiter.acquire_sync(timeout=timeout):
                raise RuntimeError(
                    f"Rate limit timeout for {func.__name__}"
                )
            logger.debug(f"Rate limit acquired for {func.__name__}")
            return func(*args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            rate_limiter = limiter or get_akshare_limiter()
            if not await rate_limiter.acquire_async(timeout=timeout):
                raise RuntimeError(
                    f"Rate limit timeout for {func.__name__}"
                )
            logger.debug(f"Rate limit acquired for {func.__name__}")
            return await func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def with_retry(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
) -> Callable:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            retry_config = config or get_default_retry_config()
            last_exception: Optional[Exception] = None
            
            for attempt in range(retry_config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if not retry_config.is_retryable(e):
                        logger.error(
                            f"{func.__name__} failed with non-retryable error: {e}"
                        )
                        raise
                    
                    if attempt >= retry_config.max_retries:
                        logger.error(
                            f"{func.__name__} failed after {attempt + 1} attempts: {e}"
                        )
                        raise
                    
                    delay = retry_config.get_delay(attempt)
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    
                    if on_retry:
                        on_retry(e, attempt)
                    
                    time.sleep(delay)
            
            raise last_exception or RuntimeError("Unexpected retry loop exit")
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            retry_config = config or get_default_retry_config()
            last_exception: Optional[Exception] = None
            
            for attempt in range(retry_config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if not retry_config.is_retryable(e):
                        logger.error(
                            f"{func.__name__} failed with non-retryable error: {e}"
                        )
                        raise
                    
                    if attempt >= retry_config.max_retries:
                        logger.error(
                            f"{func.__name__} failed after {attempt + 1} attempts: {e}"
                        )
                        raise
                    
                    delay = retry_config.get_delay(attempt)
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    
                    if on_retry:
                        on_retry(e, attempt)
                    
                    await asyncio.sleep(delay)
            
            raise last_exception or RuntimeError("Unexpected retry loop exit")
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def with_rate_limit_and_retry(
    limiter: Optional[RateLimiter] = None,
    retry_config: Optional[RetryConfig] = None,
    timeout: Optional[float] = 30.0,
) -> Callable:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        rate_limited = with_rate_limit(limiter=limiter, timeout=timeout)(func)
        return with_retry(config=retry_config)(rate_limited)
    
    return decorator


def akshare_api(
    timeout: Optional[float] = 30.0,
    max_retries: Optional[int] = None,
) -> Callable:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        retry_config = None
        if max_retries is not None:
            retry_config = RetryConfig(max_retries=max_retries)
        
        return with_rate_limit_and_retry(
            timeout=timeout,
            retry_config=retry_config,
        )(func)
    
    return decorator
