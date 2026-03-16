"""Seed data for development and testing."""
import uuid
from datetime import datetime, date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user_model import UserProfileDB
from backend.models.learning_goal_model import LearningGoalDB
from backend.models.learning_plan_model import LearningPlanDB, LearningStepDB, ResourceDB


async def seed_database(db: AsyncSession) -> None:
    """Insert sample data into the database.

    Creates:
    - 2 users with different skill levels
    - 1 learning goal per user
    - 1 learning plan per user (3 steps each, with resources)
    """
    now = datetime.utcnow()

    # ── Users ────────────────────────────────────────────────────────────────
    user1_id = str(uuid.uuid4())
    user2_id = str(uuid.uuid4())

    user1 = UserProfileDB(
        id=user1_id,
        name="Ahmet Yılmaz",
        email="ahmet@example.com",
        skill_level="beginner",
        interests=["python", "web development", "data science"],
        learning_style="hands-on",
        weekly_hours=10,
        created_at=now,
        updated_at=now,
    )

    user2 = UserProfileDB(
        id=user2_id,
        name="Zeynep Kaya",
        email="zeynep@example.com",
        skill_level="intermediate",
        interests=["machine learning", "deep learning", "nlp"],
        learning_style="reading",
        weekly_hours=15,
        created_at=now,
        updated_at=now,
    )

    db.add(user1)
    db.add(user2)
    await db.flush()

    # ── Learning Goals ───────────────────────────────────────────────────────
    goal1 = LearningGoalDB(
        id=str(uuid.uuid4()),
        user_id=user1_id,
        title="Python ile Web Geliştirme Öğren",
        domain="programming",
        target_level="intermediate",
        timeline_weeks=12,
        sub_goals=["FastAPI öğren", "Veritabanı entegrasyonu yap", "REST API geliştir"],
        created_at=now,
    )

    goal2 = LearningGoalDB(
        id=str(uuid.uuid4()),
        user_id=user2_id,
        title="Makine Öğrenmesi Uzmanlaşması",
        domain="data_science",
        target_level="advanced",
        timeline_weeks=16,
        sub_goals=["Derin öğrenme mimarileri", "NLP pipeline kurulumu", "Model deployment"],
        created_at=now,
    )

    db.add(goal1)
    db.add(goal2)
    await db.flush()

    # ── Learning Plans & Steps ───────────────────────────────────────────────
    plan1_id = str(uuid.uuid4())
    plan1 = LearningPlanDB(
        id=plan1_id,
        user_id=user1_id,
        title="Python Web Geliştirme Yol Haritası",
        total_weeks=12,
        status="active",
        created_at=now,
        updated_at=now,
    )

    plan2_id = str(uuid.uuid4())
    plan2 = LearningPlanDB(
        id=plan2_id,
        user_id=user2_id,
        title="İleri Makine Öğrenmesi Programı",
        total_weeks=16,
        status="active",
        created_at=now,
        updated_at=now,
    )

    db.add(plan1)
    db.add(plan2)
    await db.flush()

    # Steps for plan1
    step1_1_id = str(uuid.uuid4())
    step1_2_id = str(uuid.uuid4())
    step1_3_id = str(uuid.uuid4())

    steps_plan1 = [
        LearningStepDB(
            id=step1_1_id,
            plan_id=plan1_id,
            title="Python Temelleri",
            description="Değişkenler, döngüler, fonksiyonlar ve OOP kavramlarını öğren.",
            estimated_hours=20.0,
            order=1,
            status="completed",
            deadline=date.today() - timedelta(weeks=8),
        ),
        LearningStepDB(
            id=step1_2_id,
            plan_id=plan1_id,
            title="FastAPI ile REST API Geliştirme",
            description="FastAPI framework kullanarak RESTful API'ler oluştur.",
            estimated_hours=25.0,
            order=2,
            status="in_progress",
            deadline=date.today() + timedelta(weeks=2),
        ),
        LearningStepDB(
            id=step1_3_id,
            plan_id=plan1_id,
            title="Veritabanı Entegrasyonu",
            description="SQLAlchemy ve PostgreSQL ile async veritabanı işlemleri.",
            estimated_hours=20.0,
            order=3,
            status="pending",
            deadline=date.today() + timedelta(weeks=6),
        ),
    ]

    # Steps for plan2
    step2_1_id = str(uuid.uuid4())
    step2_2_id = str(uuid.uuid4())
    step2_3_id = str(uuid.uuid4())

    steps_plan2 = [
        LearningStepDB(
            id=step2_1_id,
            plan_id=plan2_id,
            title="Derin Öğrenme Temelleri",
            description="Sinir ağları, aktivasyon fonksiyonları ve geri yayılım.",
            estimated_hours=30.0,
            order=1,
            status="completed",
            deadline=date.today() - timedelta(weeks=10),
        ),
        LearningStepDB(
            id=step2_2_id,
            plan_id=plan2_id,
            title="Doğal Dil İşleme",
            description="Transformer mimarileri, BERT ve GPT modellerini anlama.",
            estimated_hours=35.0,
            order=2,
            status="in_progress",
            deadline=date.today() + timedelta(weeks=3),
        ),
        LearningStepDB(
            id=step2_3_id,
            plan_id=plan2_id,
            title="Model Deployment",
            description="FastAPI ve Docker ile ML modellerini production'a alma.",
            estimated_hours=25.0,
            order=3,
            status="pending",
            deadline=date.today() + timedelta(weeks=8),
        ),
    ]

    for step in steps_plan1 + steps_plan2:
        db.add(step)
    await db.flush()

    # ── Resources ────────────────────────────────────────────────────────────
    resources = [
        # Plan 1 - Step 1
        ResourceDB(
            id=str(uuid.uuid4()),
            step_id=step1_1_id,
            title="Python Crash Course",
            url="https://nostarch.com/python-crash-course",
            type="book",
            provider="No Starch Press",
            estimated_hours=15.0,
            tags=["python", "beginner", "programming"],
        ),
        ResourceDB(
            id=str(uuid.uuid4()),
            step_id=step1_1_id,
            title="Python for Everybody - Coursera",
            url="https://www.coursera.org/specializations/python",
            type="course",
            provider="Coursera",
            estimated_hours=10.0,
            tags=["python", "beginner", "online"],
        ),
        # Plan 1 - Step 2
        ResourceDB(
            id=str(uuid.uuid4()),
            step_id=step1_2_id,
            title="FastAPI Resmi Dokümantasyon",
            url="https://fastapi.tiangolo.com",
            type="article",
            provider="FastAPI",
            estimated_hours=8.0,
            tags=["fastapi", "python", "api"],
        ),
        ResourceDB(
            id=str(uuid.uuid4()),
            step_id=step1_2_id,
            title="FastAPI Full Course - YouTube",
            url="https://www.youtube.com/watch?v=0sOvCWFmrtA",
            type="video",
            provider="YouTube",
            estimated_hours=5.0,
            tags=["fastapi", "python", "tutorial"],
        ),
        # Plan 1 - Step 3
        ResourceDB(
            id=str(uuid.uuid4()),
            step_id=step1_3_id,
            title="SQLAlchemy 2.0 Dokümantasyon",
            url="https://docs.sqlalchemy.org/en/20/",
            type="article",
            provider="SQLAlchemy",
            estimated_hours=6.0,
            tags=["sqlalchemy", "database", "orm"],
        ),
        # Plan 2 - Step 1
        ResourceDB(
            id=str(uuid.uuid4()),
            step_id=step2_1_id,
            title="Deep Learning Specialization - Coursera",
            url="https://www.coursera.org/specializations/deep-learning",
            type="course",
            provider="Coursera / deeplearning.ai",
            estimated_hours=25.0,
            tags=["deep learning", "neural networks", "ai"],
        ),
        # Plan 2 - Step 2
        ResourceDB(
            id=str(uuid.uuid4()),
            step_id=step2_2_id,
            title="Attention Is All You Need - Paper",
            url="https://arxiv.org/abs/1706.03762",
            type="article",
            provider="arXiv",
            estimated_hours=3.0,
            tags=["transformer", "nlp", "research"],
        ),
        ResourceDB(
            id=str(uuid.uuid4()),
            step_id=step2_2_id,
            title="Hugging Face NLP Course",
            url="https://huggingface.co/learn/nlp-course",
            type="course",
            provider="Hugging Face",
            estimated_hours=20.0,
            tags=["nlp", "transformers", "huggingface"],
        ),
        # Plan 2 - Step 3
        ResourceDB(
            id=str(uuid.uuid4()),
            step_id=step2_3_id,
            title="Deploying ML Models with FastAPI",
            url="https://testdriven.io/blog/fastapi-machine-learning/",
            type="article",
            provider="TestDriven.io",
            estimated_hours=4.0,
            tags=["deployment", "fastapi", "mlops"],
        ),
    ]

    for resource in resources:
        db.add(resource)

    await db.commit()
