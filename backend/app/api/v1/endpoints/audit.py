from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_audit_logs():
    """Get audit logs"""
    return {"audit_logs": []}
