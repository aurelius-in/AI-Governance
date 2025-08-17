from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_prompts():
    """Get prompt templates"""
    return {"prompts": []}
