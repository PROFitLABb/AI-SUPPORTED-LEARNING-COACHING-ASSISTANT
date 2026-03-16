"""User API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.models.user_model import (
    UserProfileCreate,
    UserProfileDB,
    UserProfileResponse,
    UserProfileUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserProfileResponse, status_code=201)
async def create_user(
    payload: UserProfileCreate,
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Create a new user profile. Returns HTTP 422 on invalid input (Pydantic)."""
    db_user = UserProfileDB(
        name=payload.name,
        email=payload.email,
        skill_level=payload.skill_level,
        interests=payload.interests,
        learning_style=payload.learning_style,
        weekly_hours=payload.weekly_hours,
    )
    db.add(db_user)
    await db.flush()
    await db.commit()
    await db.refresh(db_user)
    return UserProfileResponse.model_validate(db_user)


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Retrieve a user by ID. Returns HTTP 404 if not found."""
    result = await db.execute(
        select(UserProfileDB).where(UserProfileDB.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfileResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserProfileResponse)
async def update_user(
    user_id: str,
    payload: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Update an existing user profile."""
    result = await db.execute(
        select(UserProfileDB).where(UserProfileDB.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return UserProfileResponse.model_validate(user)
