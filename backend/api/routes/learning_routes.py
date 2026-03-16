"""Learning plan API routes."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.learning_agent import LearningAgent
from backend.database.db import get_db
from backend.models.learning_plan_model import (
    LearningPlan,
    LearningPlanCreate,
    LearningPlanResponse,
)
from backend.models.user_model import UserProfileResponse
from backend.services.learning_plan_service import LearningPlanService
from config.llm_config import get_llm_config, get_openai_client

router = APIRouter(prefix="/plans", tags=["learning"])


class AIGenerateRequest(BaseModel):
    user_id: str
    name: str
    skill_level: str = "beginner"
    interests: list[str] = []
    weekly_hours: int = 5
    learning_style: str = "reading"
    goal: str = ""


@router.post("", response_model=LearningPlanResponse, status_code=201)
async def create_plan(
    payload: LearningPlanCreate,
    db: AsyncSession = Depends(get_db),
) -> LearningPlanResponse:
    """Create a new learning plan via LearningPlanService."""
    service = LearningPlanService(db)
    plan = LearningPlan(
        user_id=payload.user_id,
        title=payload.title,
        total_weeks=payload.total_weeks,
        steps=payload.steps,
    )
    created = await service.create(payload.user_id, plan)
    return LearningPlanResponse.model_validate(created.model_dump())


@router.get("/{plan_id}", response_model=LearningPlanResponse)
async def get_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
) -> LearningPlanResponse:
    """Retrieve a learning plan by ID."""
    service = LearningPlanService(db)
    plan = await service.get(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return LearningPlanResponse.model_validate(plan.model_dump())


@router.put("/{plan_id}/steps/{step_id}", response_model=LearningPlanResponse)
async def update_step_status(
    plan_id: str,
    step_id: str,
    status: str,
    db: AsyncSession = Depends(get_db),
) -> LearningPlanResponse:
    """Update the status of a learning step."""
    valid_statuses = {"pending", "in_progress", "completed"}
    if status not in valid_statuses:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status. Must be one of: {valid_statuses}",
        )
    service = LearningPlanService(db)
    try:
        plan = await service.update_step(plan_id, step_id, status)
    except Exception:
        raise HTTPException(status_code=404, detail="Plan or step not found")
    return LearningPlanResponse.model_validate(plan.model_dump())


@router.get("/{plan_id}/alternatives", response_model=list[LearningPlanResponse])
async def get_alternatives(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[LearningPlanResponse]:
    """Return alternative learning plans for the given plan."""
    service = LearningPlanService(db)
    plan = await service.get(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    alternatives = await service.get_alternatives(plan_id)
    return [LearningPlanResponse.model_validate(p.model_dump()) for p in alternatives]


@router.post("/ai-generate", response_model=LearningPlanResponse, status_code=201)
async def ai_generate_plan(
    payload: AIGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> LearningPlanResponse:
    """AI ile kullanıcı profiline göre otomatik öğrenme planı oluştur."""
    from datetime import datetime
    import uuid

    llm_client = get_openai_client()
    cfg = get_llm_config()
    llm_client._model = cfg.model  # type: ignore[attr-defined]

    # Prompts
    prompts = {
        "learning_plan": {
            "system": (
                "Sen bir uzman öğrenme koçusun. Kullanıcı profiline göre kişiselleştirilmiş "
                "bir öğrenme planı oluştur. Plan 4-8 adım içermeli. "
                "Her adımda gerçek, erişilebilir kaynaklar öner (URL'ler dahil). "
                "Türkçe yanıt ver. JSON formatında döndür: "
                '{"title": "...", "total_weeks": N, "steps": [{"title": "...", "description": "...", '
                '"estimated_hours": N, "resources": [{"title": "...", "url": "...", "type": "article|video|course", '
                '"provider": "...", "estimated_hours": N}]}]}'
            ),
            "user": (
                "Kullanıcı: {name}\n"
                "Seviye: {skill_level}\n"
                "İlgi alanları: {interests}\n"
                "Hedef: {goals}\n"
                "Haftalık çalışma saati: {weekly_hours}\n"
                "Öğrenme stili: {learning_style}\n\n"
                "Bu kullanıcı için kişiselleştirilmiş bir öğrenme planı oluştur."
            ),
        }
    }

    fake_profile = UserProfileResponse(
        id=payload.user_id,
        name=payload.name,
        email="",
        skill_level=payload.skill_level,
        interests=payload.interests + ([payload.goal] if payload.goal else []),
        learning_style=payload.learning_style,
        weekly_hours=payload.weekly_hours,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    agent = LearningAgent(llm_client=llm_client, prompts=prompts)
    try:
        plan = await agent.generate_plan(fake_profile)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI plan oluşturulamadı: {exc}")

    service = LearningPlanService(db)
    created = await service.create(payload.user_id, plan)
    return LearningPlanResponse.model_validate(created.model_dump())


@router.get("/user/{user_id}", response_model=list[LearningPlanResponse])
async def list_user_plans(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[LearningPlanResponse]:
    """Kullanıcının tüm planlarını listele."""
    service = LearningPlanService(db)
    plans = await service.list_by_user(user_id)
    return [LearningPlanResponse.model_validate(p.model_dump()) for p in plans]
