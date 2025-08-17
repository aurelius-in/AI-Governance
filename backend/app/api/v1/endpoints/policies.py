from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_policies():
    """Get policies"""
    return {"policies": []}
