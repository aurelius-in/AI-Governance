from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_evaluations():
    """Get evaluations"""
    return {"evaluations": []}
