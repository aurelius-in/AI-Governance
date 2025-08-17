from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")


class Usage(BaseModel):
    prompt_tokens: int = Field(0, description="Number of tokens in the prompt")
    completion_tokens: int = Field(0, description="Number of tokens in the completion")
    total_tokens: int = Field(0, description="Total number of tokens")
    total_cost: float = Field(0.0, description="Total cost of the request")


class Choice(BaseModel):
    index: int = Field(0, description="Index of the choice")
    message: Optional[Message] = Field(None, description="Message content")
    text: Optional[str] = Field(None, description="Text content for completions")
    finish_reason: Optional[str] = Field(None, description="Reason for finishing")


class ChatCompletionRequest(BaseModel):
    messages: List[Message] = Field(..., description="List of messages")
    model: str = Field(..., description="Model to use")
    provider: str = Field(..., description="Provider (openai, azure, anthropic, google)")
    project_id: Optional[int] = Field(None, description="Project ID")
    max_tokens: Optional[int] = Field(1000, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(0.7, description="Temperature for generation")
    estimated_cost: Optional[float] = Field(0.0, description="Estimated cost")


class ChatCompletionResponse(BaseModel):
    id: str = Field(..., description="Request ID")
    object: str = Field("chat.completion", description="Object type")
    created: int = Field(..., description="Creation timestamp")
    model: str = Field(..., description="Model used")
    choices: List[Choice] = Field(..., description="Generated choices")
    usage: Usage = Field(..., description="Token usage information")
    request_id: Optional[str] = Field(None, description="Internal request ID")
    trace_id: Optional[str] = Field(None, description="Trace ID for observability")


class CompletionRequest(BaseModel):
    prompt: str = Field(..., description="Input prompt")
    model: str = Field(..., description="Model to use")
    provider: str = Field(..., description="Provider (openai, azure, anthropic, google)")
    project_id: Optional[int] = Field(None, description="Project ID")
    max_tokens: Optional[int] = Field(1000, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(0.7, description="Temperature for generation")
    estimated_cost: Optional[float] = Field(0.0, description="Estimated cost")


class CompletionResponse(BaseModel):
    id: str = Field(..., description="Request ID")
    object: str = Field("text_completion", description="Object type")
    created: int = Field(..., description="Creation timestamp")
    model: str = Field(..., description="Model used")
    choices: List[Choice] = Field(..., description="Generated choices")
    usage: Usage = Field(..., description="Token usage information")
    request_id: Optional[str] = Field(None, description="Internal request ID")
    trace_id: Optional[str] = Field(None, description="Trace ID for observability")
