from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_providers():
    """Get available LLM providers"""
    return {
        "providers": [
            {"id": "openai", "name": "OpenAI", "models": ["gpt-3.5-turbo", "gpt-4"]},
            {"id": "anthropic", "name": "Anthropic", "models": ["claude-3-sonnet", "claude-3-opus"]},
            {"id": "google", "name": "Google", "models": ["gemini-pro", "gemini-pro-vision"]}
        ]
    }
