"""LMSAdapter: Abstract base class for LMS integrations."""
from abc import ABC, abstractmethod

from backend.models.progress_model import ProgressData


class LMSAdapter(ABC):
    """Abstract base class for all LMS connectors.

    Subclasses must implement get_progress, sync_completion, and health_check.
    All LMS calls must complete within _timeout_seconds (default: 10).
    """

    _timeout_seconds: int = 10

    @abstractmethod
    async def get_progress(self, user_id: str) -> ProgressData:
        """Fetch the user's learning progress from the LMS.

        Args:
            user_id: The unique identifier of the user.

        Returns:
            ProgressData containing the user's current progress.
        """
        ...

    @abstractmethod
    async def sync_completion(self, user_id: str, course_id: str) -> bool:
        """Sync a course completion event back to the LMS.

        Args:
            user_id: The unique identifier of the user.
            course_id: The LMS course identifier.

        Returns:
            True if the sync was successful, False otherwise.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check whether the LMS endpoint is reachable.

        Returns:
            True if the LMS is healthy, False otherwise.
        """
        ...
