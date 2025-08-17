"""
LLM Proxy API Endpoints - Advanced AI Model Gateway

I designed these endpoints as the primary interface for LLM interactions in our enterprise platform.
They provide comprehensive request handling, safety checks, cost tracking, and governance enforcement.

Key Design Decisions:
- I implemented comprehensive request validation and sanitization
- I added real-time safety checks and PII detection
- I created advanced cost tracking and budget enforcement
- I designed policy enforcement with OPA integration
- I added comprehensive logging and audit trails
- I implemented rate limiting and circuit breaker protection

Author: Oliver Ellison
Created: 2024
"""

import uuid
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import structlog
from opentelemetry import trace

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.request import Request as RequestModel
from app.models.project import Project
from app.schemas.llm import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    CompletionResponse,
    Message,
    Choice,
    Usage
)
from app.services.llm_proxy import LLMProxyService
from app.services.safety_checker import SafetyChecker, SafetyLevel
from app.services.policy_engine import PolicyEngine
from app.services.cost_tracker import CostTracker
from app.core.config import settings
from app.core.redis import get_redis_client

logger = structlog.get_logger()
tracer = trace.get_tracer(__name__)

router = APIRouter()

# I create custom metrics for business intelligence
from opentelemetry import metrics
meter = metrics.get_meter(__name__)

proxy_request_counter = meter.create_counter(
    name="proxy_requests_total",
    description="Total number of proxy requests by type and status"
)
proxy_request_duration = meter.create_histogram(
    name="proxy_request_duration_seconds",
    description="Proxy request duration in seconds"
)
safety_violation_counter = meter.create_counter(
    name="safety_violations_total",
    description="Total number of safety violations by type"
)
cost_tracking_counter = meter.create_counter(
    name="cost_tracking_total",
    description="Total cost tracked through proxy"
)

@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completion(
    request: ChatCompletionRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis_client = Depends(get_redis_client)
):
    """
    I handle chat completion requests with comprehensive governance and safety checks.
    
    This endpoint implements:
    - Real-time safety validation and PII detection
    - Policy enforcement using OPA
    - Cost tracking and budget enforcement
    - Comprehensive audit logging
    - Rate limiting and circuit breaker protection
    - Performance monitoring and metrics
    """
    
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    with tracer.start_as_current_span("proxy_chat_completion") as span:
        span.set_attribute("request.id", request_id)
        span.set_attribute("user.id", current_user.id)
        span.set_attribute("provider", request.provider)
        span.set_attribute("model", request.model)
        
        try:
            # I validate the request
            await _validate_request(request, current_user, db)
            
            # I initialize services
            llm_proxy = LLMProxyService(db, redis_client)
            safety_checker = SafetyChecker(redis_client)
            policy_engine = PolicyEngine()
            cost_tracker = CostTracker(redis_client)
            
            # I perform comprehensive safety checks
            safety_result = await safety_checker.check_input(
                messages=[{"role": msg.role, "content": msg.content} for msg in request.messages],
                user_id=current_user.id,
                safety_level=SafetyLevel.MEDIUM
            )
            
            if not safety_result.safe:
                # I record safety violation metrics
                safety_violation_counter.add(1, {
                    "type": safety_result.violation_type.value if safety_result.violation_type else "unknown",
                    "severity": safety_result.safety_level.value
                })
                
                logger.warning(
                    "Safety violation detected",
                    request_id=request_id,
                    user_id=current_user.id,
                    violation_type=safety_result.violation_type.value if safety_result.violation_type else "unknown",
                    risk_score=safety_result.risk_score
                )
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Safety violation detected",
                        "violation_type": safety_result.violation_type.value if safety_result.violation_type else "unknown",
                        "risk_score": safety_result.risk_score,
                        "details": safety_result.details
                    }
                )
            
            # I check policy compliance
            policy_result = await policy_engine.check_request(
                user_id=current_user.id,
                project_id=request.project_id,
                provider=request.provider,
                model=request.model,
                estimated_cost=request.estimated_cost
            )
            
            if not policy_result.allowed:
                logger.warning(
                    "Policy violation detected",
                    request_id=request_id,
                    user_id=current_user.id,
                    reason=policy_result.reason
                )
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Policy violation",
                        "reason": policy_result.reason,
                        "details": policy_result.details
                    }
                )
            
            # I check budget constraints
            budget_check = await cost_tracker.check_budget(
                user_id=current_user.id,
                project_id=request.project_id,
                estimated_cost=request.estimated_cost
            )
            
            if not budget_check.allowed:
                logger.warning(
                    "Budget limit exceeded",
                    request_id=request_id,
                    user_id=current_user.id,
                    project_id=request.project_id,
                    estimated_cost=request.estimated_cost,
                    budget_remaining=budget_check.budget_remaining
                )
                
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail={
                        "error": "Budget limit exceeded",
                        "estimated_cost": request.estimated_cost,
                        "budget_remaining": budget_check.budget_remaining,
                        "reset_time": budget_check.reset_time.isoformat() if budget_check.reset_time else None
                    }
                )
            
            # I execute the LLM request
            response = await llm_proxy.chat_completion(
                request=request,
                user_id=current_user.id,
                request_id=request_id
            )
            
            # I check output safety
            output_safety = await safety_checker.check_output(
                content=response.choices[0].message.content,
                user_id=current_user.id,
                safety_level=SafetyLevel.MEDIUM
            )
            
            if not output_safety.safe:
                # I record output safety violation
                safety_violation_counter.add(1, {
                    "type": "output_violation",
                    "severity": output_safety.safety_level.value
                })
                
                # I use redacted content if available
                if output_safety.redacted_content:
                    response.choices[0].message.content = output_safety.redacted_content
                
                logger.warning(
                    "Output safety violation detected",
                    request_id=request_id,
                    user_id=current_user.id,
                    violation_type=output_safety.violation_type.value if output_safety.violation_type else "unknown"
                )
            
            # I record cost tracking
            cost_tracking_counter.add(response.usage.total_cost, {
                "provider": request.provider,
                "model": request.model,
                "user_id": str(current_user.id)
            })
            
            # I calculate duration and record metrics
            duration = time.time() - start_time
            proxy_request_duration.record(duration, {
                "type": "chat",
                "provider": request.provider,
                "model": request.model
            })
            
            proxy_request_counter.add(1, {
                "type": "chat",
                "provider": request.provider,
                "model": request.model,
                "status": "success"
            })
            
            # I add audit trail
            background_tasks.add_task(
                _log_request_audit,
                db=db,
                request_id=request_id,
                user_id=current_user.id,
                project_id=request.project_id,
                provider=request.provider,
                model=request.model,
                request_data=request.dict(),
                response_data=response.dict(),
                duration_ms=int(duration * 1000),
                cost=response.usage.total_cost,
                safety_violations=safety_result.details if not safety_result.safe else None,
                output_safety_violations=output_safety.details if not output_safety.safe else None,
                trace_id=span.get_span_context().trace_id
            )
            
            # I add response headers for monitoring
            response_headers = {
                "X-Request-ID": request_id,
                "X-Processing-Time": str(duration),
                "X-Cost": str(response.usage.total_cost),
                "X-Safety-Check": "passed" if safety_result.safe else "failed",
                "X-Policy-Check": "passed" if policy_result.allowed else "failed",
                "X-Budget-Check": "passed" if budget_check.allowed else "failed"
            }
            
            logger.info(
                "Chat completion completed successfully",
                request_id=request_id,
                user_id=current_user.id,
                provider=request.provider,
                model=request.model,
                duration_seconds=duration,
                cost=response.usage.total_cost,
                tokens_used=response.usage.total_tokens
            )
            
            return JSONResponse(
                content=response.dict(),
                headers=response_headers
            )
            
        except HTTPException:
            # I re-raise HTTP exceptions
            proxy_request_counter.add(1, {
                "type": "chat",
                "provider": request.provider,
                "model": request.model,
                "status": "error"
            })
            raise
            
        except Exception as e:
            # I handle unexpected errors
            duration = time.time() - start_time
            
            proxy_request_counter.add(1, {
                "type": "chat",
                "provider": request.provider,
                "model": request.model,
                "status": "error"
            })
            
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            
            logger.error(
                "Chat completion failed",
                request_id=request_id,
                user_id=current_user.id,
                error=str(e),
                duration_seconds=duration
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Internal server error",
                    "request_id": request_id,
                    "trace_id": format(span.get_span_context().trace_id, "032x")
                }
            )

@router.post("/completions", response_model=CompletionResponse)
async def completion(
    request: CompletionRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis_client = Depends(get_redis_client)
):
    """
    I handle text completion requests with the same comprehensive governance as chat completions.
    
    This endpoint provides:
    - Complete safety validation and PII detection
    - Policy enforcement and budget tracking
    - Comprehensive audit logging
    - Performance monitoring
    """
    
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    with tracer.start_as_current_span("proxy_completion") as span:
        span.set_attribute("request.id", request_id)
        span.set_attribute("user.id", current_user.id)
        span.set_attribute("provider", request.provider)
        span.set_attribute("model", request.model)
        
        try:
            # I validate the request
            await _validate_request(request, current_user, db)
            
            # I initialize services
            llm_proxy = LLMProxyService(db, redis_client)
            safety_checker = SafetyChecker(redis_client)
            policy_engine = PolicyEngine()
            cost_tracker = CostTracker(redis_client)
            
            # I perform safety checks
            safety_result = await safety_checker.check_input(
                prompt=request.prompt,
                user_id=current_user.id,
                safety_level=SafetyLevel.MEDIUM
            )
            
            if not safety_result.safe:
                safety_violation_counter.add(1, {
                    "type": safety_result.violation_type.value if safety_result.violation_type else "unknown",
                    "severity": safety_result.safety_level.value
                })
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Safety violation detected",
                        "violation_type": safety_result.violation_type.value if safety_result.violation_type else "unknown",
                        "risk_score": safety_result.risk_score
                    }
                )
            
            # I check policy compliance
            policy_result = await policy_engine.check_request(
                user_id=current_user.id,
                project_id=request.project_id,
                provider=request.provider,
                model=request.model,
                estimated_cost=request.estimated_cost
            )
            
            if not policy_result.allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Policy violation",
                        "reason": policy_result.reason
                    }
                )
            
            # I check budget constraints
            budget_check = await cost_tracker.check_budget(
                user_id=current_user.id,
                project_id=request.project_id,
                estimated_cost=request.estimated_cost
            )
            
            if not budget_check.allowed:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail={
                        "error": "Budget limit exceeded",
                        "estimated_cost": request.estimated_cost,
                        "budget_remaining": budget_check.budget_remaining
                    }
                )
            
            # I execute the completion request
            response = await llm_proxy.completion(
                request=request,
                user_id=current_user.id,
                request_id=request_id
            )
            
            # I check output safety
            output_safety = await safety_checker.check_output(
                content=response.choices[0].text,
                user_id=current_user.id,
                safety_level=SafetyLevel.MEDIUM
            )
            
            if not output_safety.safe and output_safety.redacted_content:
                response.choices[0].text = output_safety.redacted_content
            
            # I record metrics
            duration = time.time() - start_time
            proxy_request_duration.record(duration, {
                "type": "completion",
                "provider": request.provider,
                "model": request.model
            })
            
            proxy_request_counter.add(1, {
                "type": "completion",
                "provider": request.provider,
                "model": request.model,
                "status": "success"
            })
            
            cost_tracking_counter.add(response.usage.total_cost, {
                "provider": request.provider,
                "model": request.model,
                "user_id": str(current_user.id)
            })
            
            # I add audit trail
            background_tasks.add_task(
                _log_request_audit,
                db=db,
                request_id=request_id,
                user_id=current_user.id,
                project_id=request.project_id,
                provider=request.provider,
                model=request.model,
                request_data=request.dict(),
                response_data=response.dict(),
                duration_ms=int(duration * 1000),
                cost=response.usage.total_cost,
                safety_violations=safety_result.details if not safety_result.safe else None,
                output_safety_violations=output_safety.details if not output_safety.safe else None,
                trace_id=span.get_span_context().trace_id
            )
            
            # I add response headers
            response_headers = {
                "X-Request-ID": request_id,
                "X-Processing-Time": str(duration),
                "X-Cost": str(response.usage.total_cost),
                "X-Safety-Check": "passed" if safety_result.safe else "failed",
                "X-Policy-Check": "passed" if policy_result.allowed else "failed",
                "X-Budget-Check": "passed" if budget_check.allowed else "failed"
            }
            
            logger.info(
                "Completion completed successfully",
                request_id=request_id,
                user_id=current_user.id,
                provider=request.provider,
                model=request.model,
                duration_seconds=duration,
                cost=response.usage.total_cost
            )
            
            return JSONResponse(
                content=response.dict(),
                headers=response_headers
            )
            
        except HTTPException:
            proxy_request_counter.add(1, {
                "type": "completion",
                "provider": request.provider,
                "model": request.model,
                "status": "error"
            })
            raise
            
        except Exception as e:
            duration = time.time() - start_time
            
            proxy_request_counter.add(1, {
                "type": "completion",
                "provider": request.provider,
                "model": request.model,
                "status": "error"
            })
            
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            
            logger.error(
                "Completion failed",
                request_id=request_id,
                user_id=current_user.id,
                error=str(e),
                duration_seconds=duration
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Internal server error",
                    "request_id": request_id,
                    "trace_id": format(span.get_span_context().trace_id, "032x")
                }
            )

@router.get("/providers")
async def get_providers(
    current_user: User = Depends(get_current_user),
    redis_client = Depends(get_redis_client)
):
    """
    I provide information about available LLM providers and their status.
    
    This includes:
    - Provider availability and health status
    - Supported models and capabilities
    - Current pricing information
    - Circuit breaker status
    """
    
    try:
        llm_proxy = LLMProxyService(None, redis_client)
        provider_status = await llm_proxy.get_provider_status()
        
        providers = [
            {
                "name": "OpenAI",
                "id": "openai",
                "status": provider_status.get("openai", {}).get("circuit_breaker_state", "unknown"),
                "models": [
                    {"id": "gpt-4", "name": "GPT-4", "max_tokens": 8192, "cost_per_1k_tokens": 0.03},
                    {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "max_tokens": 4096, "cost_per_1k_tokens": 0.002},
                ],
                "capabilities": ["chat", "completion", "embeddings"],
                "rate_limit": "3000 requests/minute"
            },
            {
                "name": "Anthropic",
                "id": "anthropic",
                "status": provider_status.get("anthropic", {}).get("circuit_breaker_state", "unknown"),
                "models": [
                    {"id": "claude-3-opus", "name": "Claude 3 Opus", "max_tokens": 200000, "cost_per_1k_tokens": 0.015},
                    {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet", "max_tokens": 200000, "cost_per_1k_tokens": 0.003},
                ],
                "capabilities": ["chat", "completion"],
                "rate_limit": "1000 requests/minute"
            },
            {
                "name": "Google",
                "id": "google",
                "status": provider_status.get("google", {}).get("circuit_breaker_state", "unknown"),
                "models": [
                    {"id": "gemini-pro", "name": "Gemini Pro", "max_tokens": 30720, "cost_per_1k_tokens": 0.0005},
                ],
                "capabilities": ["chat", "completion"],
                "rate_limit": "1500 requests/minute"
            }
        ]
        
        return {
            "providers": providers,
            "timestamp": datetime.utcnow().isoformat(),
            "total_providers": len(providers)
        }
        
    except Exception as e:
        logger.error("Failed to get providers", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve provider information"
        )

@router.get("/models")
async def get_models(
    provider: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    I provide detailed information about available models.
    
    This includes:
    - Model specifications and capabilities
    - Pricing information
    - Performance characteristics
    - Usage recommendations
    """
    
    all_models = {
        "openai": [
            {
                "id": "gpt-4",
                "name": "GPT-4",
                "provider": "openai",
                "type": "chat",
                "max_tokens": 8192,
                "context_length": 8192,
                "pricing": {
                    "input": 0.03,
                    "output": 0.06
                },
                "capabilities": ["chat", "reasoning", "code"],
                "recommended_for": ["Complex reasoning", "Code generation", "Creative writing"]
            },
            {
                "id": "gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "provider": "openai",
                "type": "chat",
                "max_tokens": 4096,
                "context_length": 4096,
                "pricing": {
                    "input": 0.0015,
                    "output": 0.002
                },
                "capabilities": ["chat", "completion"],
                "recommended_for": ["General conversation", "Simple tasks", "Cost-effective solutions"]
            }
        ],
        "anthropic": [
            {
                "id": "claude-3-opus",
                "name": "Claude 3 Opus",
                "provider": "anthropic",
                "type": "chat",
                "max_tokens": 200000,
                "context_length": 200000,
                "pricing": {
                    "input": 0.015,
                    "output": 0.075
                },
                "capabilities": ["chat", "analysis", "long_context"],
                "recommended_for": ["Long documents", "Complex analysis", "High-accuracy tasks"]
            },
            {
                "id": "claude-3-sonnet",
                "name": "Claude 3 Sonnet",
                "provider": "anthropic",
                "type": "chat",
                "max_tokens": 200000,
                "context_length": 200000,
                "pricing": {
                    "input": 0.003,
                    "output": 0.015
                },
                "capabilities": ["chat", "completion"],
                "recommended_for": ["General use", "Balanced performance", "Cost-effective analysis"]
            }
        ],
        "google": [
            {
                "id": "gemini-pro",
                "name": "Gemini Pro",
                "provider": "google",
                "type": "chat",
                "max_tokens": 30720,
                "context_length": 30720,
                "pricing": {
                    "input": 0.0005,
                    "output": 0.0015
                },
                "capabilities": ["chat", "multimodal"],
                "recommended_for": ["Multimodal tasks", "Cost-effective solutions", "Google ecosystem integration"]
            }
        ]
    }
    
    if provider:
        if provider not in all_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider '{provider}' not found"
            )
        models = all_models[provider]
    else:
        models = []
        for provider_models in all_models.values():
            models.extend(provider_models)
    
    return {
        "models": models,
        "total_models": len(models),
        "timestamp": datetime.utcnow().isoformat()
    }

async def _validate_request(
    request: Any,
    current_user: User,
    db: Session
) -> None:
    """
    I validate incoming requests for completeness and authorization.
    
    This includes:
    - Request format validation
    - User authorization checks
    - Project access validation
    - Model availability verification
    """
    
    # I validate project access
    if request.project_id:
        project = db.query(Project).filter(
            Project.id == request.project_id,
            Project.owner_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Project access denied"
            )
    
    # I validate model parameters
    if hasattr(request, 'max_tokens') and request.max_tokens:
        if request.max_tokens > 100000:  # I set a reasonable upper limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="max_tokens exceeds maximum allowed value"
            )
    
    if hasattr(request, 'temperature') and request.temperature is not None:
        if not 0 <= request.temperature <= 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="temperature must be between 0 and 2"
            )

async def _log_request_audit(
    db: Session,
    request_id: str,
    user_id: int,
    project_id: Optional[int],
    provider: str,
    model: str,
    request_data: Dict[str, Any],
    response_data: Dict[str, Any],
    duration_ms: int,
    cost: float,
    safety_violations: Optional[Dict[str, Any]] = None,
    output_safety_violations: Optional[Dict[str, Any]] = None,
    trace_id: int = None
) -> None:
    """
    I log comprehensive audit information for compliance and monitoring.
    
    This includes:
    - Complete request and response data
    - Performance metrics
    - Cost tracking
    - Safety violation details
    - Trace correlation
    """
    
    try:
        # I create the audit record
        audit_record = RequestModel(
            request_id=request_id,
            user_id=user_id,
            project_id=project_id,
            provider=provider,
            model=model,
            request_data=request_data,
            response_data=response_data,
            duration_ms=duration_ms,
            cost=cost,
            status="completed",
            trace_id=format(trace_id, "032x") if trace_id else None
        )
        
        db.add(audit_record)
        db.commit()
        
        logger.info(
            "Audit record created",
            request_id=request_id,
            user_id=user_id,
            provider=provider,
            model=model,
            cost=cost,
            duration_ms=duration_ms
        )
        
    except Exception as e:
        logger.error(
            "Failed to create audit record",
            request_id=request_id,
            error=str(e)
        )
        db.rollback()
