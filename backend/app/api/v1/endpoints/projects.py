from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.project import Project

router = APIRouter()


@router.get("/")
async def get_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all projects for the current user"""
    projects = db.query(Project).filter(Project.owner_id == current_user.id).all()
    return projects


@router.post("/")
async def create_project(
    name: str,
    description: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new project"""
    project = Project(
        name=name,
        description=description,
        owner_id=current_user.id,
        organization_id=current_user.organization_id or 1
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project
