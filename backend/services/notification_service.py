"""NotificationService: in-memory notification management."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from backend.models.learning_plan_model import LearningPlan


@dataclass
class Notification:
    user_id: str
    type: str        # "delay_reminder" | "lms_error" | ...
    message: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


class NotificationService:
    """In-memory notification store.

    In production this would be replaced by a DB-backed or push-notification
    implementation.  The interface is intentionally kept identical so the
    swap is transparent to callers.
    """

    def __init__(self) -> None:
        # user_id -> list[Notification]
        self._store: dict[str, list[Notification]] = {}

    def _save(self, notification: Notification) -> None:
        self._store.setdefault(notification.user_id, []).append(notification)

    async def send_delay_reminder(
        self, user_id: str, plan: LearningPlan
    ) -> Notification:
        """Create and store a delay-reminder notification for the given plan."""
        notification = Notification(
            user_id=user_id,
            type="delay_reminder",
            message=(
                f"'{plan.title}' planında hedeflerinizin gerisinde kalıyorsunuz. "
                "Planınızı gözden geçirmenizi öneririz."
            ),
        )
        self._save(notification)
        return notification

    async def send_lms_error(self, user_id: str, error_msg: str) -> Notification:
        """Create and store an LMS-connection-error notification."""
        notification = Notification(
            user_id=user_id,
            type="lms_error",
            message=(
                f"LMS bağlantısı kurulamadı: {error_msg}. "
                "Yerel veriler kullanılmaya devam ediliyor."
            ),
        )
        self._save(notification)
        return notification

    async def get_pending(self, user_id: str) -> list[Notification]:
        """Return all pending (unread) notifications for a user."""
        return list(self._store.get(user_id, []))
