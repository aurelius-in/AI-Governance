import logging
import sys
from typing import Any, Dict
import structlog
from structlog.stdlib import LoggerFactory
from structlog.processors import JSONRenderer, TimeStamper, add_log_level
from structlog.contextvars import merge_contextvars


def setup_logging() -> None:
    """Setup structured logging with structlog"""
    
    # Configure structlog
    structlog.configure(
        processors=[
            merge_contextvars,
            add_log_level,
            TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    
    # Set log level for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)


def log_request(request_id: str, method: str, url: str, **kwargs: Any) -> None:
    """Log HTTP request"""
    logger = get_logger("http.request")
    logger.info(
        "HTTP request",
        request_id=request_id,
        method=method,
        url=url,
        **kwargs
    )


def log_response(request_id: str, status_code: int, duration_ms: float, **kwargs: Any) -> None:
    """Log HTTP response"""
    logger = get_logger("http.response")
    logger.info(
        "HTTP response",
        request_id=request_id,
        status_code=status_code,
        duration_ms=duration_ms,
        **kwargs
    )


def log_llm_request(
    request_id: str,
    provider: str,
    model: str,
    prompt_tokens: int,
    **kwargs: Any
) -> None:
    """Log LLM request"""
    logger = get_logger("llm.request")
    logger.info(
        "LLM request",
        request_id=request_id,
        provider=provider,
        model=model,
        prompt_tokens=prompt_tokens,
        **kwargs
    )


def log_llm_response(
    request_id: str,
    provider: str,
    model: str,
    completion_tokens: int,
    total_cost: float,
    **kwargs: Any
) -> None:
    """Log LLM response"""
    logger = get_logger("llm.response")
    logger.info(
        "LLM response",
        request_id=request_id,
        provider=provider,
        model=model,
        completion_tokens=completion_tokens,
        total_cost=total_cost,
        **kwargs
    )


def log_policy_violation(
    request_id: str,
    policy_name: str,
    violation_type: str,
    details: Dict[str, Any],
    **kwargs: Any
) -> None:
    """Log policy violation"""
    logger = get_logger("policy.violation")
    logger.warning(
        "Policy violation",
        request_id=request_id,
        policy_name=policy_name,
        violation_type=violation_type,
        details=details,
        **kwargs
    )


def log_security_event(
    event_type: str,
    severity: str,
    user_id: str = None,
    request_id: str = None,
    **kwargs: Any
) -> None:
    """Log security event"""
    logger = get_logger("security.event")
    log_method = getattr(logger, severity.lower(), logger.info)
    log_method(
        "Security event",
        event_type=event_type,
        severity=severity,
        user_id=user_id,
        request_id=request_id,
        **kwargs
    )
