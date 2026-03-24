"""Gelişmiş özellikler: Quiz, Günlük Görev, Haftalık Rapor, Öğrenme Stili."""
import uuid
import json
import logging
from datetime import datetime, timedelta, date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.models.progress_model import MessageDB
from backend.models.learning_plan_model import LearningPlanDB, LearningStepDB
from backend.models.progress_model import ProgressDB
from config.llm_config import get_openai_client, get_llm_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/features", tags=["features"])


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class QuizRequest(BaseModel):
    user_id: str
    topic: str
    difficulty: str = "medium"  # easy / medium / hard

class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    correct_index: int
    explanation: str

class QuizResponse(BaseModel):
    topic: str
    questions: list[QuizQuestion]

class QuizEvalRequest(BaseModel):
    user_id: str
    topic: str
    questions: list[QuizQuestion]
    answers: list[int]

class QuizEvalResponse(BaseModel):
    score: int
    total: int
    percentage: float
    feedback: str
    wrong_topics: list[str]

class DailyTaskResponse(BaseModel):
    task: str
    reason: str
    estimated_minutes: int
    category: str

class WeeklyReportResponse(BaseModel):
    week_label: str
    messages_this_week: int
    messages_last_week: int
    change_pct: float
    active_days: int
    streak_days: int
    top_topics: list[str]
    summary: str
    prediction: str

class LearningStyleResponse(BaseModel):
    style: str          # visual / reading / hands-on / mixed
    confidence: float
    traits: list[str]
    recommendation: str

class HeatmapDay(BaseModel):
    date: str
    count: int
    level: int  # 0-4

class HeatmapResponse(BaseModel):
    days: list[HeatmapDay]
    total_active_days: int
    longest_streak: int


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _call_llm(system: str, user: str) -> str:
    client = get_openai_client()
    cfg = get_llm_config()
    client._model = cfg.model  # type: ignore
    resp = await client.chat.completions.create(
        model=cfg.model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content


# ── Quiz ──────────────────────────────────────────────────────────────────────

@router.post("/quiz/generate", response_model=QuizResponse)
async def generate_quiz(payload: QuizRequest) -> QuizResponse:
    """Verilen konuda 5 soruluk quiz oluştur."""
    system = (
        "Sen bir eğitim uzmanısın. Verilen konuda quiz soruları oluştur. "
        "JSON formatında döndür: "
        '{"questions": [{"question": "...", "options": ["A","B","C","D"], '
        '"correct_index": 0, "explanation": "..."}]}'
        " Tam olarak 5 soru oluştur. Türkçe yaz."
    )
    user = f"Konu: {payload.topic}\nZorluk: {payload.difficulty}\n5 çoktan seçmeli soru oluştur."
    try:
        raw = await _call_llm(system, user)
        data = json.loads(raw)
        questions = [QuizQuestion(**q) for q in data.get("questions", [])]
        return QuizResponse(topic=payload.topic, questions=questions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz oluşturulamadı: {e}")


@router.post("/quiz/evaluate", response_model=QuizEvalResponse)
async def evaluate_quiz(payload: QuizEvalRequest) -> QuizEvalResponse:
    """Quiz cevaplarını değerlendir."""
    correct = sum(
        1 for q, a in zip(payload.questions, payload.answers)
        if q.correct_index == a
    )
    total = len(payload.questions)
    pct = round(correct / total * 100, 1) if total > 0 else 0
    wrong = [
        payload.questions[i].question[:50]
        for i, (q, a) in enumerate(zip(payload.questions, payload.answers))
        if q.correct_index != a
    ]
    if pct >= 80:
        feedback = f"Harika! {correct}/{total} doğru. Konuya hakimsin."
    elif pct >= 60:
        feedback = f"İyi! {correct}/{total} doğru. Biraz daha pratik yapabilirsin."
    else:
        feedback = f"{correct}/{total} doğru. Bu konuyu tekrar gözden geçirmen önerilir."
    return QuizEvalResponse(
        score=correct, total=total, percentage=pct,
        feedback=feedback, wrong_topics=wrong
    )


# ── Günlük Görev ──────────────────────────────────────────────────────────────

@router.get("/daily-task/{user_id}", response_model=DailyTaskResponse)
async def get_daily_task(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> DailyTaskResponse:
    """Kullanıcının durumuna göre günlük görev öner."""
    # Son mesajları al
    msgs = await db.execute(
        select(MessageDB)
        .where(MessageDB.user_id == user_id)
        .order_by(MessageDB.timestamp.desc())
        .limit(20)
    )
    recent = msgs.scalars().all()

    # Aktif planları al
    plans = await db.execute(
        select(LearningPlanDB).where(
            LearningPlanDB.user_id == user_id,
            LearningPlanDB.status == "active",
        )
    )
    active_plans = plans.scalars().all()

    context = ""
    if recent:
        context = "Son konuşmalar:\n" + "\n".join(
            f"[{m.role}] {m.content[:100]}" for m in reversed(recent[:5])
        )
    if active_plans:
        context += f"\nAktif planlar: {', '.join(p.title for p in active_plans)}"

    system = (
        "Sen bir öğrenme koçusun. Kullanıcının durumuna göre bugün için 1 somut görev öner. "
        "JSON: {\"task\": \"...\", \"reason\": \"...\", \"estimated_minutes\": 30, \"category\": \"pratik|okuma|video|proje\"}"
        " Türkçe yaz. Görev spesifik ve yapılabilir olsun."
    )
    user_msg = context or "Yeni kullanıcı, genel bir başlangıç görevi öner."

    try:
        raw = await _call_llm(system, user_msg)
        data = json.loads(raw)
        return DailyTaskResponse(**data)
    except Exception:
        return DailyTaskResponse(
            task="Bugün 25 dakika Python temellerini çalış",
            reason="Düzenli çalışma alışkanlığı oluşturmak için",
            estimated_minutes=25,
            category="pratik",
        )


# ── Haftalık Rapor ────────────────────────────────────────────────────────────

@router.get("/weekly-report/{user_id}", response_model=WeeklyReportResponse)
async def get_weekly_report(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> WeeklyReportResponse:
    """Bu hafta vs geçen hafta karşılaştırmalı rapor."""
    now = datetime.utcnow()
    week_start = now - timedelta(days=7)
    prev_week_start = now - timedelta(days=14)

    # Bu hafta mesajlar
    this_week = await db.execute(
        select(func.count(MessageDB.id)).where(
            MessageDB.user_id == user_id,
            MessageDB.timestamp >= week_start,
            MessageDB.role == "user",
        )
    )
    this_count = this_week.scalar() or 0

    # Geçen hafta mesajlar
    last_week = await db.execute(
        select(func.count(MessageDB.id)).where(
            MessageDB.user_id == user_id,
            MessageDB.timestamp >= prev_week_start,
            MessageDB.timestamp < week_start,
            MessageDB.role == "user",
        )
    )
    last_count = last_week.scalar() or 0

    change = 0.0
    if last_count > 0:
        change = round((this_count - last_count) / last_count * 100, 1)
    elif this_count > 0:
        change = 100.0

    # Aktif günler
    days_result = await db.execute(
        select(MessageDB.timestamp).where(
            MessageDB.user_id == user_id,
            MessageDB.timestamp >= week_start,
        )
    )
    timestamps = days_result.scalars().all()
    active_days = len({t.date() for t in timestamps})

    # Streak
    all_msgs = await db.execute(
        select(MessageDB.timestamp).where(MessageDB.user_id == user_id).order_by(MessageDB.timestamp.desc())
    )
    all_ts = all_msgs.scalars().all()
    streak = 0
    today = datetime.utcnow().date()
    seen_days = sorted({t.date() for t in all_ts}, reverse=True)
    for i, d in enumerate(seen_days):
        if d == today - timedelta(days=i):
            streak += 1
        else:
            break

    # Son mesajlardan konu çıkar
    recent_msgs = await db.execute(
        select(MessageDB).where(
            MessageDB.user_id == user_id,
            MessageDB.timestamp >= week_start,
            MessageDB.role == "user",
        ).limit(10)
    )
    recent_content = [m.content[:80] for m in recent_msgs.scalars().all()]
    top_topics = recent_content[:3] if recent_content else ["Henüz konu yok"]

    # Tahmin
    if this_count >= 10:
        prediction = "Bu tempoda devam edersen hedefine 4 haftada ulaşabilirsin!"
    elif this_count >= 5:
        prediction = "Biraz daha düzenli çalışırsan ilerleme hızlanacak."
    else:
        prediction = "Günde en az 1 soru sorarak başla, alışkanlık oluşturmak önemli."

    summary = f"Bu hafta {this_count} mesaj gönderdin, {active_days} gün aktif oldun."
    if change > 0:
        summary += f" Geçen haftaya göre %{change} daha aktifsin!"
    elif change < 0:
        summary += f" Geçen haftaya göre %{abs(change)} daha az aktifsin."

    return WeeklyReportResponse(
        week_label=f"{week_start.strftime('%d %b')} – {now.strftime('%d %b %Y')}",
        messages_this_week=this_count,
        messages_last_week=last_count,
        change_pct=change,
        active_days=active_days,
        streak_days=streak,
        top_topics=top_topics,
        summary=summary,
        prediction=prediction,
    )


# ── Öğrenme Stili Analizi ─────────────────────────────────────────────────────

@router.get("/learning-style/{user_id}", response_model=LearningStyleResponse)
async def analyze_learning_style(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> LearningStyleResponse:
    """Konuşma geçmişinden öğrenme stilini analiz et."""
    msgs = await db.execute(
        select(MessageDB).where(
            MessageDB.user_id == user_id,
            MessageDB.role == "user",
        ).order_by(MessageDB.timestamp.desc()).limit(30)
    )
    messages = msgs.scalars().all()

    if len(messages) < 3:
        return LearningStyleResponse(
            style="mixed",
            confidence=0.3,
            traits=["Henüz yeterli veri yok"],
            recommendation="Daha fazla sohbet ettikçe stilin netleşecek.",
        )

    conversation = "\n".join(f"- {m.content[:100]}" for m in messages)
    system = (
        "Kullanıcının mesajlarını analiz ederek öğrenme stilini belirle. "
        "Stiller: visual (görsel), reading (okuyarak), hands-on (yaparak), mixed (karma). "
        "JSON: {\"style\": \"...\", \"confidence\": 0.8, \"traits\": [\"...\"], \"recommendation\": \"...\"}"
        " Türkçe yaz."
    )
    try:
        raw = await _call_llm(system, f"Kullanıcı mesajları:\n{conversation}")
        data = json.loads(raw)
        return LearningStyleResponse(**data)
    except Exception:
        return LearningStyleResponse(
            style="mixed",
            confidence=0.5,
            traits=["Çeşitli konularda soru soruyor", "Pratik odaklı"],
            recommendation="Hem okuyarak hem yaparak öğrenme kombinasyonu dene.",
        )


# ── Isı Haritası ──────────────────────────────────────────────────────────────

@router.get("/heatmap/{user_id}", response_model=HeatmapResponse)
async def get_heatmap(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> HeatmapResponse:
    """Son 90 günlük aktivite ısı haritası verisi."""
    since = datetime.utcnow() - timedelta(days=90)
    msgs = await db.execute(
        select(MessageDB.timestamp).where(
            MessageDB.user_id == user_id,
            MessageDB.timestamp >= since,
            MessageDB.role == "user",
        )
    )
    timestamps = msgs.scalars().all()

    # Gün bazında say
    day_counts: dict[date, int] = {}
    for ts in timestamps:
        d = ts.date()
        day_counts[d] = day_counts.get(d, 0) + 1

    # Son 90 günü doldur
    today = datetime.utcnow().date()
    days = []
    for i in range(89, -1, -1):
        d = today - timedelta(days=i)
        count = day_counts.get(d, 0)
        level = 0 if count == 0 else (1 if count <= 2 else (2 if count <= 5 else (3 if count <= 10 else 4)))
        days.append(HeatmapDay(date=d.isoformat(), count=count, level=level))

    active_days = sum(1 for d in days if d.count > 0)

    # En uzun seri
    longest = cur = 0
    for d in days:
        if d.count > 0:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0

    return HeatmapResponse(days=days, total_active_days=active_days, longest_streak=longest)
