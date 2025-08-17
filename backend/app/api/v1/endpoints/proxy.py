import uuid
import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
import structlog
from opentelemetry import trace

from app.core.database import get_db, get_redis
from app.core.config import settings
from app.services.llm_proxy import LLMProxyService
from app.services.policy_engine import PolicyEngine
from app.services.safety_checker import SafetyChecker
from app.services.cost_tracker import CostTracker
from app.schemas.llm import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    CompletionResponse
)
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()
logger = structlog.get_logger()
tracer = trace.get_tracer(__name__)


@router.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    http_request: Request,
    db=Depends(get_db),
    redis=Depends(get_redis),
    current_user: User = Depends(get_current_user)
) -> ChatCompletionResponse:
    """LLM Proxy for chat completions with governance"""
    
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    with tracer.start_as_current_span("llm_proxy_chat") as span:
        span.set_attribute("request_id", request_id)
        span.set_attribute("user_id", str(current_user.id))
        span.set_attribute("model", request.model)
        span.set_attribute("provider", request.provider)
        
        try:
            # Initialize services
            policy_engine = PolicyEngine(db, redis)
            safety_checker = SafetyChecker()
            cost_tracker = CostTracker(db, redis)
            llm_proxy = LLMProxyService(db, redis)
            
            # 1. Policy checks
            policy_result = await policy_engine.check_request(
                user_id=current_user.id,
                project_id=request.project_id,
                provider=request.provider,
                model=request.model,
                request_data=request.dict()
            )
            
            if not policy_result.allowed:
                logger.warning(
                    "Policy violation",
                    request_id=request_id,
                    user_id=str(current_user.id),
                    violation=policy_result.violations
                )
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "Policy violation",
                        "violations": policy_result.violations,
                        "request_id": request_id
                    }
                )
            
            # 2. Safety checks on input
            safety_result = await safety_checker.check_input(
                messages=request.messages,
                user_id=current_user.id
            )
            
            if not safety_result.safe:
                logger.warning(
                    "Safety violation",
                    request_id=request_id,
                    user_id=str(current_user.id),
                    violation_type=safety_result.violation_type
                )
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Safety violation",
                        "violation_type": safety_result.violation_type,
                        "request_id": request_id
                    }
                )
            
            # 3. Check cost budget
            budget_check = await cost_tracker.check_budget(
                user_id=current_user.id,
                project_id=request.project_id,
                estimated_cost=request.estimated_cost
            )
            
            if not budget_check.allowed:
                logger.warning(
                    "Budget exceeded",
                    request_id=request_id,
                    user_id=str(current_user.id),
                    budget_limit=budget_check.limit
                )
                raise HTTPException(
                    status_code=402,
                    detail={
                        "error": "Budget exceeded",
                        "limit": budget_check.limit,
                        "request_id": request_id
                    }
                )
            
            # 4. Forward to LLM provider
            llm_response = await llm_proxy.chat_completion(
                request=request,
                user_id=current_user.id,
                request_id=request_id
            )
            
            # 5. Safety checks on output
            output_safety = await safety_checker.check_output(
                content=llm_response.choices[0].message.content,
                user_id=current_user.id
            )
            
            if not output_safety.safe:
                logger.warning(
                    "Output safety violation",
                    request_id=request_id,
                    user_id=str(current_user.id),
                    violation_type=output_safety.violation_type
                )
                # Return error response instead of unsafe content
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Output safety violation",
                        "violation_type": output_safety.violation_type,
                        "request_id": request_id
                    }
                )
            
            # 6. Record cost and usage
            await cost_tracker.record_usage(
                request_id=request_id,
                user_id=current_user.id,
                project_id=request.project_id,
                provider=request.provider,
                model=request.model,
                prompt_tokens=llm_response.usage.prompt_tokens,
                completion_tokens=llm_response.usage.completion_tokens,
                total_cost=llm_response.usage.total_cost
            )
            
            # 7. Log request
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                "LLM request completed",
                request_id=request_id,
                user_id=str(current_user.id),
                provider=request.provider,
                model=request.model,
                duration_ms=duration_ms,
                total_cost=llm_response.usage.total_cost
            )
            
            # Add trace ID to response
            llm_response.request_id = request_id
            llm_response.trace_id = format(span.get_span_context().trace_id, "032x")
            
            return llm_response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "LLM proxy error",
                request_id=request_id,
                user_id=str(current_user.id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Internal server error",
                    "request_id": request_id
                }
            )


@router.post("/completions")
async def completions(
    request: CompletionRequest,
    http_request: Request,
    db=Depends(get_db),
    redis=Depends(get_redis),
    current_user: User = Depends(get_current_user)
) -> CompletionResponse:
    """LLM Proxy for text completions with governance"""
    
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    with tracer.start_as_current_span("llm_proxy_completion") as span:
        span.set_attribute("request_id", request_id)
        span.set_attribute("user_id", str(current_user.id))
        span.set_attribute("model", request.model)
        span.set_attribute("provider", request.provider)
        
        try:
            # Initialize services
            policy_engine = PolicyEngine(db, redis)
            safety_checker = SafetyChecker()
            cost_tracker = CostTracker(db, redis)
            llm_proxy = LLMProxyService(db, redis)
            
            # 1. Policy checks
            policy_result = await policy_engine.check_request(
                user_id=current_user.id,
                project_id=request.project_id,
                provider=request.provider,
                model=request.model,
                request_data=request.dict()
            )
            
            if not policy_result.allowed:
                logger.warning(
                    "Policy violation",
                    request_id=request_id,
                    user_id=str(current_user.id),
                    violation=policy_result.violations
                )
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "Policy violation",
                        "violations": policy_result.violations,
                        "request_id": request_id
                    }
                )
            
            # 2. Safety checks on input
            safety_result = await safety_checker.check_input(
                prompt=request.prompt,
                user_id=current_user.id
            )
            
            if not safety_result.safe:
                logger.warning(
                    "Safety violation",
                    request_id=request_id,
                    user_id=str(current_user.id),
                    violation_type=safety_result.violation_type
                )
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Safety violation",
                        "violation_type": safety_result.violation_type,
                        "request_id": request_id
                    }
                )
            
            # 3. Check cost budget
            budget_check = await cost_tracker.check_budget(
                user_id=current_user.id,
                project_id=request.project_id,
                estimated_cost=request.estimated_cost
            )
            
            if not budget_check.allowed:
                logger.warning(
                    "Budget exceeded",
                    request_id=request_id,
                    user_id=str(current_user.id),
                    budget_limit=budget_check.limit
                )
                raise HTTPException(
                    status_code=402,
                    detail={
                        "error": "Budget exceeded",
                        "limit": budget_check.limit,
                        "request_id": request_id
                    }
                )
            
            # 4. Forward to LLM provider
            llm_response = await llm_proxy.completion(
                request=request,
                user_id=current_user.id,
                request_id=request_id
            )
            
            # 5. Safety checks on output
            output_safety = await safety_checker.check_output(
                content=llm_response.choices[0].text,
                user_id=current_user.id
            )
            
            if not output_safety.safe:
                logger.warning(
                    "Output safety violation",
                    request_id=request_id,
                    user_id=str(current_user.id),
                    violation_type=output_safety.violation_type
                )
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Output safety violation",
                        "violation_type": output_safety.violation_type,
                        "request_id": request_id
                    }
                )
            
            # 6. Record cost and usage
            await cost_tracker.record_usage(
                request_id=request_id,
                user_id=current_user.id,
                project_id=request.project_id,
                provider=request.provider,
                model=request.model,
                prompt_tokens=llm_response.usage.prompt_tokens,
                completion_tokens=llm_response.usage.completion_tokens,
                total_cost=llm_response.usage.total_cost
            )
            
            # 7. Log request
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                "LLM request completed",
                request_id=request_id,
                user_id=str(current_user.id),
                provider=request.provider,
                model=request.model,
                duration_ms=duration_ms,
                total_cost=llm_response.usage.total_cost
            )
            
            # Add trace ID to response
            llm_response.request_id = request_id
            llm_response.trace_id = format(span.get_span_context().trace_id, "032x")
            
            return llm_response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "LLM proxy error",
                request_id=request_id,
                user_id=str(current_user.id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Internal server error",
                    "request_id": request_id
                }
            )


@router.get("/health")
async def proxy_health() -> Dict[str, Any]:
    """Health check for LLM proxy"""
    return {
        "status": "healthy",
        "service": "llm-proxy",
        "providers": ["openai", "azure", "anthropic", "google"]
    }
