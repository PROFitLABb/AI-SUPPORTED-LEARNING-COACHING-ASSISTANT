"""RecommendationService: topic-based resource recommendations."""
from backend.models.learning_plan_model import Resource

# Hardcoded fallback resources used when no dataset is available.
_FALLBACK_RESOURCES: list[Resource] = [
    Resource(
        id="fallback-python-1",
        title="Python for Everybody – Coursera",
        url="https://www.coursera.org/specializations/python",
        type="course",
        provider="Coursera",
        estimated_hours=10.0,
        tags=["python", "beginner", "programming"],
    ),
    Resource(
        id="fallback-ml-1",
        title="Machine Learning Specialization – Coursera",
        url="https://www.coursera.org/specializations/machine-learning-introduction",
        type="course",
        provider="Coursera / deeplearning.ai",
        estimated_hours=30.0,
        tags=["machine learning", "ai", "data science"],
    ),
    Resource(
        id="fallback-web-1",
        title="The Odin Project – Full Stack Web Development",
        url="https://www.theodinproject.com",
        type="course",
        provider="The Odin Project",
        estimated_hours=40.0,
        tags=["web development", "html", "css", "javascript"],
    ),
    Resource(
        id="fallback-ds-1",
        title="Data Science Handbook – Jake VanderPlas",
        url="https://jakevdp.github.io/PythonDataScienceHandbook/",
        type="book",
        provider="O'Reilly",
        estimated_hours=20.0,
        tags=["data science", "python", "numpy", "pandas"],
    ),
    Resource(
        id="fallback-nlp-1",
        title="Hugging Face NLP Course",
        url="https://huggingface.co/learn/nlp-course",
        type="course",
        provider="Hugging Face",
        estimated_hours=20.0,
        tags=["nlp", "transformers", "deep learning"],
    ),
    Resource(
        id="fallback-fastapi-1",
        title="FastAPI Official Documentation",
        url="https://fastapi.tiangolo.com",
        type="article",
        provider="FastAPI",
        estimated_hours=8.0,
        tags=["fastapi", "python", "api", "web"],
    ),
    Resource(
        id="fallback-docker-1",
        title="Docker Getting Started",
        url="https://docs.docker.com/get-started/",
        type="article",
        provider="Docker",
        estimated_hours=5.0,
        tags=["docker", "devops", "deployment"],
    ),
]


def _load_resources() -> list[Resource]:
    """Try to load resources from datasets/learning_resources.json; fall back to hardcoded list."""
    import json
    import os

    dataset_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "datasets", "learning_resources.json"
    )
    try:
        with open(dataset_path, encoding="utf-8") as f:
            data = json.load(f)
        return [Resource(**item) for item in data]
    except (FileNotFoundError, Exception):
        return list(_FALLBACK_RESOURCES)


class RecommendationService:
    def __init__(self) -> None:
        self._resources: list[Resource] = _load_resources()

    async def get_recommendations(
        self,
        user_id: str,
        topic: str,
        completed_resource_ids: list[str] | None = None,
    ) -> list[Resource]:
        """Return resources relevant to *topic*, excluding already-completed ones.

        Guarantees at least 1 result even when all topic-matched resources are
        completed (falls back to the full catalogue minus completed items, and
        ultimately to the first fallback resource).
        """
        if completed_resource_ids is None:
            completed_resource_ids = []

        completed_set = set(completed_resource_ids)
        topic_lower = topic.lower()

        def _matches(resource: Resource) -> bool:
            return topic_lower in resource.title.lower() or any(
                topic_lower in tag.lower() for tag in resource.tags
            )

        # 1. Topic-matched, not completed
        candidates = [
            r for r in self._resources if _matches(r) and r.id not in completed_set
        ]

        # 2. Fallback: any resource not completed
        if not candidates:
            candidates = [r for r in self._resources if r.id not in completed_set]

        # 3. Last resort: return the first fallback resource regardless
        if not candidates:
            candidates = [_FALLBACK_RESOURCES[0]]

        return candidates
