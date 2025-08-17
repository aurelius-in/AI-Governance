from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_cost_summary():
    """Get cost summary"""
    return {"cost_summary": {}}
