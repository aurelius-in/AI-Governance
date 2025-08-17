import time
import uuid
from typing import Dict, Any, Optional
import openai
import anthropic
import google.generativeai as genai
import structlog
from sqlalchemy.orm import Session
import redis

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


class LLMProxyService:
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client
        
        # Initialize providers
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
        
        if settings.ANTHROPIC_API_KEY:
            self.anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)

    async def chat_completion(
        self,
        request: ChatCompletionRequest,
        user_id: int,
        request_id: str
    ) -> ChatCompletionResponse:
        """Handle chat completion requests"""
        
        start_time = time.time()
        
        try:
            if request.provider == "openai":
                response = await self._openai_chat_completion(request)
            elif request.provider == "anthropic":
                response = await self._anthropic_chat_completion(request)
            elif request.provider == "google":
                response = await self._google_chat_completion(request)
            else:
                raise ValueError(f"Unsupported provider: {request.provider}")
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Add metadata
            response.request_id = request_id
            response.created = int(time.time())
            
            logger.info(
                "LLM request completed",
                provider=request.provider,
                model=request.model,
                duration_ms=duration_ms,
                cost=response.usage.total_cost
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "LLM request failed",
                provider=request.provider,
                model=request.model,
                error=str(e)
            )
            raise

    async def completion(
        self,
        request: CompletionRequest,
        user_id: int,
        request_id: str
    ) -> CompletionResponse:
        """Handle text completion requests"""
        
        start_time = time.time()
        
        try:
            if request.provider == "openai":
                response = await self._openai_completion(request)
            elif request.provider == "anthropic":
                response = await self._anthropic_completion(request)
            elif request.provider == "google":
                response = await self._google_completion(request)
            else:
                raise ValueError(f"Unsupported provider: {request.provider}")
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Add metadata
            response.request_id = request_id
            response.created = int(time.time())
            
            logger.info(
                "LLM completion completed",
                provider=request.provider,
                model=request.model,
                duration_ms=duration_ms,
                cost=response.usage.total_cost
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "LLM completion failed",
                provider=request.provider,
                model=request.model,
                error=str(e)
            )
            raise

    async def _openai_chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Handle OpenAI chat completion"""
        response = openai.ChatCompletion.create(
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

    async def _anthropic_chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Handle Anthropic chat completion"""
        # Convert messages to Anthropic format
        messages = []
        for msg in request.messages:
            if msg.role == "user":
                messages.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                messages.append({"role": "assistant", "content": msg.content})
            elif msg.role == "system":
                # Anthropic doesn't have system messages, prepend to first user message
                if messages and messages[0]["role"] == "user":
                    messages[0]["content"] = f"{msg.content}\n\n{messages[0]['content']}"
                else:
                    messages.append({"role": "user", "content": msg.content})
        
        response = self.anthropic_client.messages.create(
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

    async def _google_chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Handle Google chat completion"""
        model = genai.GenerativeModel(request.model)
        
        # Convert messages to Google format
        chat = model.start_chat(history=[])
        for msg in request.messages[:-1]:  # All but the last message
            if msg.role == "user":
                chat.send_message(msg.content)
            elif msg.role == "assistant":
                # Google doesn't support assistant messages in history for this API
                pass
        
        # Send the last message
        response = chat.send_message(
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
                total_cost=0.0  # Calculate based on model pricing
            )
        )

    async def _openai_completion(self, request: CompletionRequest) -> CompletionResponse:
        """Handle OpenAI text completion"""
        response = openai.Completion.create(
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

    async def _anthropic_completion(self, request: CompletionRequest) -> CompletionResponse:
        """Handle Anthropic text completion"""
        response = self.anthropic_client.completions.create(
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
                total_cost=0.0
            )
        )

    async def _google_completion(self, request: CompletionRequest) -> CompletionResponse:
        """Handle Google text completion"""
        model = genai.GenerativeModel(request.model)
        
        response = model.generate_content(
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
                total_cost=0.0
            )
        )

    def _calculate_openai_cost(self, model: str, usage: Any) -> float:
        """Calculate cost for OpenAI models"""
        # Simplified pricing - in production, use actual pricing tables
        if "gpt-4" in model:
            return (usage.prompt_tokens * 0.03 + usage.completion_tokens * 0.06) / 1000
        elif "gpt-3.5" in model:
            return (usage.prompt_tokens * 0.002 + usage.completion_tokens * 0.002) / 1000
        else:
            return 0.0

    def _calculate_anthropic_cost(self, model: str, usage: Any) -> float:
        """Calculate cost for Anthropic models"""
        # Simplified pricing
        if "claude-3" in model:
            return (usage.input_tokens * 0.015 + usage.output_tokens * 0.075) / 1000
        elif "claude-2" in model:
            return (usage.input_tokens * 0.008 + usage.output_tokens * 0.024) / 1000
        else:
            return 0.0
