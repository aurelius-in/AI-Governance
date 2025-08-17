from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_models():
    """Get available models"""
    return {
        "models": [
            {"id": "gpt-3.5-turbo", "provider": "openai", "name": "GPT-3.5 Turbo"},
            {"id": "gpt-4", "provider": "openai", "name": "GPT-4"},
            {"id": "claude-3-sonnet", "provider": "anthropic", "name": "Claude 3 Sonnet"},
            {"id": "claude-3-opus", "provider": "anthropic", "name": "Claude 3 Opus"},
            {"id": "gemini-pro", "provider": "google", "name": "Gemini Pro"}
        ]
    }
