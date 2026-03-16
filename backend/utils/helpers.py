import uuid
from datetime import datetime, timezone


def generate_id() -> str:
    """Generate a new UUID v4 string."""
    return str(uuid.uuid4())


def format_datetime(dt: datetime) -> str:
    """Format a datetime object as an ISO 8601 string with UTC timezone."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Truncate text to max_length characters.
    Appends suffix if truncation occurs. Truncates at word boundary when possible.
    """
    if len(text) <= max_length:
        return text

    truncated = text[: max_length - len(suffix)]
    # Try to cut at the last space to avoid breaking words
    last_space = truncated.rfind(" ")
    if last_space > max_length // 2:
        truncated = truncated[:last_space]

    return truncated + suffix
