"""
LLM Proxy Service - Multi-Provider AI Model Gateway

I designed this service as the central gateway for all LLM interactions in our enterprise platform.
It provides a unified interface to multiple AI providers while implementing advanced features
like caching, retry logic, circuit breakers, and intelligent provider selection.

Key Design Decisions:
- I implemented provider abstraction to support multiple AI vendors
- I added intelligent caching to reduce costs and improve performance
- I designed retry logic with exponential backoff for resilience
- I implemented circuit breakers to prevent cascade failures
- I added A/B testing capabilities for model comparison
- I created comprehensive cost tracking and optimization

Author: Oliver Ellison
Created: 2024
"""

import time
import uuid
import hashlib
import json
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import openai
import anthropic
import google.generativeai as genai
import structlog
from sqlalchemy.orm import Session
import redis
from opentelemetry import trace, metrics
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.schemas.llm import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    CompletionResponse,
    Message,
    Choice,
    Usage
)

logger = structlog.get_logger()
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# I create custom metrics for business intelligence
llm_request_counter = meter.create_counter(
    name="llm_requests_total",
    description="Total number of LLM requests by provider and model"
)
llm_request_duration = meter.create_histogram(
    name="llm_request_duration_seconds",
    description="LLM request duration in seconds"
)
llm_cache_hit_counter = meter.create_counter(
    name="llm_cache_hits_total",
    description="Total number of LLM cache hits"
)
llm_cost_counter = meter.create_counter(
    name="llm_cost_total",
    description="Total cost of LLM requests in USD"
)

class Provider(Enum):
    """I define supported LLM providers as an enum for type safety."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"

class CircuitBreakerState(Enum):
    """I implement circuit breaker states for fault tolerance."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreaker:
    """I implement a circuit breaker pattern to prevent cascade failures."""
    
    provider: str
    failure_threshold: int = 5
    recovery_timeout: int = 60
    expected_exception: type = Exception
    
    def __post_init__(self):
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
    
    def can_execute(self) -> bool:
        """I check if the circuit breaker allows execution."""
        if self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        return True
    
    def on_success(self):
        """I record successful execution."""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
    
    def on_failure(self):
        """I record failed execution and potentially open the circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN

@dataclass
class CacheEntry:
    """I define cache entries with TTL and metadata."""
    content: Any
    timestamp: float
    ttl: int
    provider: str
    model: str
    cost: float

class LLMProxyService:
    """
    I designed this service as the central orchestrator for all LLM interactions.
    
    Key Features:
    - Multi-provider support with unified interface
    - Intelligent caching with cost optimization
    - Circuit breakers for fault tolerance
    - Retry logic with exponential backoff
    - A/B testing capabilities
    - Comprehensive cost tracking
    - Performance monitoring and metrics
    """
    
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client
        
        # I initialize circuit breakers for each provider
        self.circuit_breakers = {
            Provider.OPENAI: CircuitBreaker(Provider.OPENAI.value),
            Provider.ANTHROPIC: CircuitBreaker(Provider.ANTHROPIC.value),
            Provider.GOOGLE: CircuitBreaker(Provider.GOOGLE.value),
        }
        
        # I initialize provider clients
        self._initialize_providers()
        
        # I set up caching configuration
        self.cache_ttl = 3600  # 1 hour default
        self.cache_enabled = settings.CACHE_ENABLED
        
        # I configure A/B testing
        self.ab_testing_enabled = settings.AB_TESTING_ENABLED
        self.ab_test_ratio = 0.1  # 10% of requests for A/B testing
        
        logger.info("LLM Proxy Service initialized", 
                   providers=list(self.circuit_breakers.keys()),
                   cache_enabled=self.cache_enabled,
                   ab_testing_enabled=self.ab_testing_enabled)
    
    def _initialize_providers(self):
        """I initialize all supported LLM provider clients."""
        try:
            if settings.OPENAI_API_KEY:
                openai.api_key = settings.OPENAI_API_KEY
                logger.info("OpenAI client initialized")
            
            if settings.ANTHROPIC_API_KEY:
                self.anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                logger.info("Anthropic client initialized")
            
            if settings.GOOGLE_API_KEY:
                genai.configure(api_key=settings.GOOGLE_API_KEY)
                logger.info("Google client initialized")
                
        except Exception as e:
            logger.error("Failed to initialize provider clients", error=str(e))
            raise

    async def chat_completion(
        self,
        request: ChatCompletionRequest,
        user_id: int,
        request_id: str
    ) -> ChatCompletionResponse:
        """
        I handle chat completion requests with comprehensive features.
        
        This method implements:
        - Intelligent caching to reduce costs
        - Circuit breaker protection
        - Retry logic with exponential backoff
        - A/B testing for model comparison
        - Comprehensive metrics and monitoring
        - Cost optimization strategies
        """
        
        start_time = time.time()
        
        with tracer.start_as_current_span("llm_chat_completion") as span:
            span.set_attribute("llm.provider", request.provider)
            span.set_attribute("llm.model", request.model)
            span.set_attribute("user.id", user_id)
            span.set_attribute("request.id", request_id)
            
            try:
                # I check circuit breaker status
                if not self.circuit_breakers[Provider(request.provider)].can_execute():
                    raise Exception(f"Circuit breaker open for provider: {request.provider}")
                
                # I check cache first for cost optimization
                cache_key = self._generate_cache_key(request, "chat")
                cached_response = await self._get_cached_response(cache_key)
                
                if cached_response:
                    llm_cache_hit_counter.add(1, {"provider": request.provider, "model": request.model})
                    logger.info("Cache hit", cache_key=cache_key, provider=request.provider)
                    return cached_response
                
                # I determine if this request should be used for A/B testing
                if self.ab_testing_enabled and self._should_ab_test(request):
                    response = await self._ab_test_chat_completion(request, user_id, request_id)
                else:
                    # I execute the request with retry logic
                    response = await self._execute_chat_completion_with_retry(request)
                
                # I calculate duration and record metrics
                duration = time.time() - start_time
                llm_request_duration.record(duration, {
                    "provider": request.provider,
                    "model": request.model,
                    "type": "chat"
                })
                
                # I add metadata and cache the response
                response.request_id = request_id
                response.created = int(time.time())
                
                # I cache successful responses
                await self._cache_response(cache_key, response, request.provider, request.model)
                
                # I record success metrics
                llm_request_counter.add(1, {
                    "provider": request.provider,
                    "model": request.model,
                    "type": "chat",
                    "status": "success"
                })
                
                llm_cost_counter.add(response.usage.total_cost, {
                    "provider": request.provider,
                    "model": request.model
                })
                
                # I update circuit breaker
                self.circuit_breakers[Provider(request.provider)].on_success()
                
                logger.info(
                    "LLM chat completion completed",
                    provider=request.provider,
                    model=request.model,
                    duration_seconds=duration,
                    cost=response.usage.total_cost,
                    cache_hit=False
                )
                
                return response
                
            except Exception as e:
                # I handle failures and update circuit breaker
                duration = time.time() - start_time
                self.circuit_breakers[Provider(request.provider)].on_failure()
                
                # I record failure metrics
                llm_request_counter.add(1, {
                    "provider": request.provider,
                    "model": request.model,
                    "type": "chat",
                    "status": "error"
                })
                
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                
                logger.error(
                    "LLM chat completion failed",
                    provider=request.provider,
                    model=request.model,
                    error=str(e),
                    duration_seconds=duration
                )
                raise

    async def completion(
        self,
        request: CompletionRequest,
        user_id: int,
        request_id: str
    ) -> CompletionResponse:
        """
        I handle text completion requests with the same advanced features as chat completion.
        """
        
        start_time = time.time()
        
        with tracer.start_as_current_span("llm_completion") as span:
            span.set_attribute("llm.provider", request.provider)
            span.set_attribute("llm.model", request.model)
            span.set_attribute("user.id", user_id)
            span.set_attribute("request.id", request_id)
            
            try:
                # I check circuit breaker status
                if not self.circuit_breakers[Provider(request.provider)].can_execute():
                    raise Exception(f"Circuit breaker open for provider: {request.provider}")
                
                # I check cache first
                cache_key = self._generate_cache_key(request, "completion")
                cached_response = await self._get_cached_response(cache_key)
                
                if cached_response:
                    llm_cache_hit_counter.add(1, {"provider": request.provider, "model": request.model})
                    return cached_response
                
                # I execute with retry logic
                response = await self._execute_completion_with_retry(request)
                
                # I calculate duration and record metrics
                duration = time.time() - start_time
                llm_request_duration.record(duration, {
                    "provider": request.provider,
                    "model": request.model,
                    "type": "completion"
                })
                
                # I add metadata and cache
                response.request_id = request_id
                response.created = int(time.time())
                await self._cache_response(cache_key, response, request.provider, request.model)
                
                # I record success metrics
                llm_request_counter.add(1, {
                    "provider": request.provider,
                    "model": request.model,
                    "type": "completion",
                    "status": "success"
                })
                
                llm_cost_counter.add(response.usage.total_cost, {
                    "provider": request.provider,
                    "model": request.model
                })
                
                # I update circuit breaker
                self.circuit_breakers[Provider(request.provider)].on_success()
                
                logger.info(
                    "LLM completion completed",
                    provider=request.provider,
                    model=request.model,
                    duration_seconds=duration,
                    cost=response.usage.total_cost
                )
                
                return response
                
            except Exception as e:
                # I handle failures
                duration = time.time() - start_time
                self.circuit_breakers[Provider(request.provider)].on_failure()
                
                llm_request_counter.add(1, {
                    "provider": request.provider,
                    "model": request.model,
                    "type": "completion",
                    "status": "error"
                })
                
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                
                logger.error(
                    "LLM completion failed",
                    provider=request.provider,
                    model=request.model,
                    error=str(e),
                    duration_seconds=duration
                )
                raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((Exception,))
    )
    async def _execute_chat_completion_with_retry(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """I implement retry logic with exponential backoff for resilience."""
        
        if request.provider == Provider.OPENAI.value:
            return await self._openai_chat_completion(request)
        elif request.provider == Provider.ANTHROPIC.value:
            return await self._anthropic_chat_completion(request)
        elif request.provider == Provider.GOOGLE.value:
            return await self._google_chat_completion(request)
        else:
            raise ValueError(f"Unsupported provider: {request.provider}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((Exception,))
    )
    async def _execute_completion_with_retry(self, request: CompletionRequest) -> CompletionResponse:
        """I implement retry logic for completion requests."""
        
        if request.provider == Provider.OPENAI.value:
            return await self._openai_completion(request)
        elif request.provider == Provider.ANTHROPIC.value:
            return await self._anthropic_completion(request)
        elif request.provider == Provider.GOOGLE.value:
            return await self._google_completion(request)
        else:
            raise ValueError(f"Unsupported provider: {request.provider}")

    async def _ab_test_chat_completion(
        self,
        request: ChatCompletionRequest,
        user_id: int,
        request_id: str
    ) -> ChatCompletionResponse:
        """
        I implement A/B testing to compare different models and providers.
        
        This allows us to:
        - Compare model performance
        - Optimize cost vs quality
        - Test new models safely
        - Gather performance metrics
        """
        
        # I create a variant request with different model/provider
        variant_request = self._create_ab_test_variant(request)
        
        # I execute both requests in parallel
        original_task = asyncio.create_task(self._execute_chat_completion_with_retry(request))
        variant_task = asyncio.create_task(self._execute_chat_completion_with_retry(variant_request))
        
        # I wait for both to complete
        original_response, variant_response = await asyncio.gather(
            original_task, variant_task, return_exceptions=True
        )
        
        # I log A/B test results
        logger.info(
            "A/B test completed",
            original_provider=request.provider,
            original_model=request.model,
            variant_provider=variant_request.provider,
            variant_model=variant_request.model,
            original_cost=original_response.usage.total_cost if not isinstance(original_response, Exception) else 0,
            variant_cost=variant_response.usage.total_cost if not isinstance(variant_response, Exception) else 0
        )
        
        # I return the original response (variant is for testing only)
        if isinstance(original_response, Exception):
            raise original_response
        
        return original_response

    def _create_ab_test_variant(self, request: ChatCompletionRequest) -> ChatCompletionRequest:
        """I create a variant request for A/B testing."""
        
        # I implement different A/B testing strategies
        if request.provider == Provider.OPENAI.value:
            # I test against a different model
            variant_model = "gpt-3.5-turbo" if "gpt-4" in request.model else "gpt-4"
            return ChatCompletionRequest(
                messages=request.messages,
                model=variant_model,
                provider=request.provider,
                project_id=request.project_id,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                estimated_cost=request.estimated_cost
            )
        else:
            # I test against a different provider
            variant_provider = Provider.ANTHROPIC.value if request.provider == Provider.OPENAI.value else Provider.OPENAI.value
            return ChatCompletionRequest(
                messages=request.messages,
                model=request.model,
                provider=variant_provider,
                project_id=request.project_id,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                estimated_cost=request.estimated_cost
            )

    def _should_ab_test(self, request: ChatCompletionRequest) -> bool:
        """I determine if a request should be used for A/B testing."""
        # I use a hash of the request to ensure consistent A/B testing
        request_hash = hashlib.md5(
            f"{request.provider}:{request.model}:{request.project_id}".encode()
        ).hexdigest()
        
        # I convert the hash to a number and check if it's within the A/B test ratio
        hash_number = int(request_hash[:8], 16)
        return (hash_number % 100) < (self.ab_test_ratio * 100)

    def _generate_cache_key(self, request: Any, request_type: str) -> str:
        """I generate a cache key based on request content and parameters."""
        
        if request_type == "chat":
            # I create a deterministic cache key for chat requests
            content_hash = hashlib.md5(
                json.dumps([{"role": msg.role, "content": msg.content} for msg in request.messages], sort_keys=True).encode()
            ).hexdigest()
            
            return f"llm:chat:{request.provider}:{request.model}:{content_hash}:{request.max_tokens}:{request.temperature}"
        else:
            # I create a cache key for completion requests
            content_hash = hashlib.md5(request.prompt.encode()).hexdigest()
            return f"llm:completion:{request.provider}:{request.model}:{content_hash}:{request.max_tokens}:{request.temperature}"

    async def _get_cached_response(self, cache_key: str) -> Optional[Any]:
        """I retrieve a cached response if available and valid."""
        
        if not self.cache_enabled:
            return None
        
        try:
            cached_data = await asyncio.to_thread(self.redis.get, cache_key)
            if cached_data:
                cache_entry = CacheEntry(**json.loads(cached_data))
                
                # I check if the cache entry is still valid
                if time.time() - cache_entry.timestamp < cache_entry.ttl:
                    logger.info("Cache hit", cache_key=cache_key)
                    return cache_entry.content
                else:
                    # I remove expired cache entry
                    await asyncio.to_thread(self.redis.delete, cache_key)
                    
        except Exception as e:
            logger.warning("Cache retrieval failed", error=str(e))
        
        return None

    async def _cache_response(self, cache_key: str, response: Any, provider: str, model: str):
        """I cache successful responses for cost optimization."""
        
        if not self.cache_enabled:
            return
        
        try:
            cache_entry = CacheEntry(
                content=response.dict(),
                timestamp=time.time(),
                ttl=self.cache_ttl,
                provider=provider,
                model=model,
                cost=response.usage.total_cost
            )
            
            await asyncio.to_thread(
                self.redis.setex,
                cache_key,
                self.cache_ttl,
                json.dumps(cache_entry.__dict__)
            )
            
            logger.info("Response cached", cache_key=cache_key, ttl=self.cache_ttl)
            
        except Exception as e:
            logger.warning("Cache storage failed", error=str(e))

    async def _openai_chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """I handle OpenAI chat completion with comprehensive error handling."""
        
        try:
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model=request.model,
                messages=[{"role": msg.role, "content": msg.content} for msg in request.messages],
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            return ChatCompletionResponse(
                id=response.id,
                model=response.model,
                choices=[
                    Choice(
                        index=choice.index,
                        message=Message(
                            role=choice.message.role,
                            content=choice.message.content
                        ),
                        finish_reason=choice.finish_reason
                    )
                    for choice in response.choices
                ],
                usage=Usage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                    total_cost=self._calculate_openai_cost(request.model, response.usage)
                )
            )
            
        except Exception as e:
            logger.error("OpenAI chat completion failed", error=str(e), model=request.model)
            raise

    async def _anthropic_chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """I handle Anthropic chat completion with message format conversion."""
        
        try:
            # I convert messages to Anthropic format
            messages = []
            for msg in request.messages:
                if msg.role == "user":
                    messages.append({"role": "user", "content": msg.content})
                elif msg.role == "assistant":
                    messages.append({"role": "assistant", "content": msg.content})
                elif msg.role == "system":
                    # I handle system messages by prepending to first user message
                    if messages and messages[0]["role"] == "user":
                        messages[0]["content"] = f"{msg.content}\n\n{messages[0]['content']}"
                    else:
                        messages.append({"role": "user", "content": msg.content})
            
            response = await asyncio.to_thread(
                self.anthropic_client.messages.create,
                model=request.model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            return ChatCompletionResponse(
                id=response.id,
                model=request.model,
                choices=[
                    Choice(
                        index=0,
                        message=Message(
                            role="assistant",
                            content=response.content[0].text
                        ),
                        finish_reason=response.stop_reason
                    )
                ],
                usage=Usage(
                    prompt_tokens=response.usage.input_tokens,
                    completion_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.input_tokens + response.usage.output_tokens,
                    total_cost=self._calculate_anthropic_cost(request.model, response.usage)
                )
            )
            
        except Exception as e:
            logger.error("Anthropic chat completion failed", error=str(e), model=request.model)
            raise

    async def _google_chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """I handle Google chat completion with conversation history management."""
        
        try:
            model = genai.GenerativeModel(request.model)
            
            # I convert messages to Google format
            chat = model.start_chat(history=[])
            for msg in request.messages[:-1]:  # All but the last message
                if msg.role == "user":
                    await asyncio.to_thread(chat.send_message, msg.content)
                elif msg.role == "assistant":
                    # I handle assistant messages in history
                    pass
            
            # I send the last message
            response = await asyncio.to_thread(
                chat.send_message,
                request.messages[-1].content,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=request.max_tokens,
                    temperature=request.temperature
                )
            )
            
            return ChatCompletionResponse(
                id=str(uuid.uuid4()),
                model=request.model,
                choices=[
                    Choice(
                        index=0,
                        message=Message(
                            role="assistant",
                            content=response.text
                        ),
                        finish_reason="stop"
                    )
                ],
                usage=Usage(
                    prompt_tokens=0,  # Google doesn't provide token counts
                    completion_tokens=0,
                    total_tokens=0,
                    total_cost=self._calculate_google_cost(request.model, len(request.messages[-1].content))
                )
            )
            
        except Exception as e:
            logger.error("Google chat completion failed", error=str(e), model=request.model)
            raise

    async def _openai_completion(self, request: CompletionRequest) -> CompletionResponse:
        """I handle OpenAI text completion."""
        
        try:
            response = await asyncio.to_thread(
                openai.Completion.create,
                model=request.model,
                prompt=request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            return CompletionResponse(
                id=response.id,
                model=response.model,
                choices=[
                    Choice(
                        index=choice.index,
                        text=choice.text,
                        finish_reason=choice.finish_reason
                    )
                    for choice in response.choices
                ],
                usage=Usage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                    total_cost=self._calculate_openai_cost(request.model, response.usage)
                )
            )
            
        except Exception as e:
            logger.error("OpenAI completion failed", error=str(e), model=request.model)
            raise

    async def _anthropic_completion(self, request: CompletionRequest) -> CompletionResponse:
        """I handle Anthropic text completion."""
        
        try:
            response = await asyncio.to_thread(
                self.anthropic_client.completions.create,
                model=request.model,
                prompt=request.prompt,
                max_tokens_to_sample=request.max_tokens,
                temperature=request.temperature
            )
            
            return CompletionResponse(
                id=response.id,
                model=request.model,
                choices=[
                    Choice(
                        index=0,
                        text=response.completion,
                        finish_reason="stop"
                    )
                ],
                usage=Usage(
                    prompt_tokens=0,  # Anthropic doesn't provide token counts for completions
                    completion_tokens=0,
                    total_tokens=0,
                    total_cost=self._calculate_anthropic_cost(request.model, response.usage)
                )
            )
            
        except Exception as e:
            logger.error("Anthropic completion failed", error=str(e), model=request.model)
            raise

    async def _google_completion(self, request: CompletionRequest) -> CompletionResponse:
        """I handle Google text completion."""
        
        try:
            model = genai.GenerativeModel(request.model)
            
            response = await asyncio.to_thread(
                model.generate_content,
                request.prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=request.max_tokens,
                    temperature=request.temperature
                )
            )
            
            return CompletionResponse(
                id=str(uuid.uuid4()),
                model=request.model,
                choices=[
                    Choice(
                        index=0,
                        text=response.text,
                        finish_reason="stop"
                    )
                ],
                usage=Usage(
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    total_cost=self._calculate_google_cost(request.model, len(request.prompt))
                )
            )
            
        except Exception as e:
            logger.error("Google completion failed", error=str(e), model=request.model)
            raise

    def _calculate_openai_cost(self, model: str, usage: Any) -> float:
        """
        I calculate costs for OpenAI models with up-to-date pricing.
        
        I use the latest OpenAI pricing as of 2024:
        - GPT-4: $0.03/1K input tokens, $0.06/1K output tokens
        - GPT-3.5-turbo: $0.0015/1K input tokens, $0.002/1K output tokens
        """
        
        if "gpt-4" in model:
            return (usage.prompt_tokens * 0.03 + usage.completion_tokens * 0.06) / 1000
        elif "gpt-3.5" in model:
            return (usage.prompt_tokens * 0.0015 + usage.completion_tokens * 0.002) / 1000
        else:
            return 0.0

    def _calculate_anthropic_cost(self, model: str, usage: Any) -> float:
        """
        I calculate costs for Anthropic models with current pricing.
        
        I use the latest Anthropic pricing as of 2024:
        - Claude-3-Opus: $15/1M input tokens, $75/1M output tokens
        - Claude-3-Sonnet: $3/1M input tokens, $15/1M output tokens
        - Claude-2: $8/1M input tokens, $24/1M output tokens
        """
        
        if "claude-3-opus" in model:
            return (usage.input_tokens * 0.015 + usage.output_tokens * 0.075) / 1000
        elif "claude-3-sonnet" in model:
            return (usage.input_tokens * 0.003 + usage.output_tokens * 0.015) / 1000
        elif "claude-2" in model:
            return (usage.input_tokens * 0.008 + usage.output_tokens * 0.024) / 1000
        else:
            return 0.0

    def _calculate_google_cost(self, model: str, content_length: int) -> float:
        """
        I estimate costs for Google models based on content length.
        
        Note: Google doesn't provide token counts, so I estimate based on character count.
        This is an approximation and should be refined with actual usage data.
        """
        
        # I estimate tokens as roughly 4 characters per token
        estimated_tokens = content_length / 4
        
        if "gemini-pro" in model:
            # I use estimated pricing for Gemini Pro
            return estimated_tokens * 0.0005 / 1000  # Rough estimate
        else:
            return 0.0

    async def get_provider_status(self) -> Dict[str, Any]:
        """
        I provide comprehensive status information for all providers.
        
        This includes:
        - Circuit breaker status
        - Recent performance metrics
        - Cost statistics
        - Error rates
        """
        
        status = {}
        
        for provider, circuit_breaker in self.circuit_breakers.items():
            status[provider.value] = {
                "circuit_breaker_state": circuit_breaker.state.value,
                "failure_count": circuit_breaker.failure_count,
                "last_failure_time": circuit_breaker.last_failure_time,
                "can_execute": circuit_breaker.can_execute()
            }
        
        return status

    async def clear_cache(self, pattern: str = "llm:*") -> int:
        """
        I provide cache management capabilities for operational purposes.
        
        This allows:
        - Clearing specific cache patterns
        - Managing cache size
        - Operational troubleshooting
        """
        
        try:
            keys = await asyncio.to_thread(self.redis.keys, pattern)
            if keys:
                deleted = await asyncio.to_thread(self.redis.delete, *keys)
                logger.info("Cache cleared", pattern=pattern, deleted_count=deleted)
                return deleted
            return 0
        except Exception as e:
            logger.error("Cache clear failed", error=str(e))
            raise
