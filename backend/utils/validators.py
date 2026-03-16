import re
import uuid
from typing import Optional


MIN_GOAL_LENGTH = 10
# Patterns that indicate meaningful content (at least one word with 3+ chars)
_MEANINGFUL_PATTERN = re.compile(r"\b\w{3,}\b")


def validate_goal_text(text: str) -> str:
    """
    Validate a learning goal text.

    Rules:
    - Must not be empty or whitespace-only
    - Must be at least MIN_GOAL_LENGTH characters (after stripping)
    - Must contain at least one meaningful word (3+ characters)

    Returns the stripped text if valid, raises ValueError otherwise.
    """
    if not text or not text.strip():
        raise ValueError("Hedef metni boş olamaz.")

    stripped = text.strip()

    if len(stripped) < MIN_GOAL_LENGTH:
        raise ValueError(
            f"Hedef metni en az {MIN_GOAL_LENGTH} karakter olmalıdır. "
            f"Girilen: {len(stripped)} karakter."
        )

    if not _MEANINGFUL_PATTERN.search(stripped):
        raise ValueError(
            "Hedef metni anlamlı içerik içermelidir (en az bir kelime)."
        )

    return stripped


def validate_user_id(user_id: str) -> str:
    """
    Validate a user ID (must be a valid UUID v4 string).

    Returns the user_id if valid, raises ValueError otherwise.
    """
    if not user_id or not user_id.strip():
        raise ValueError("Kullanıcı ID boş olamaz.")

    try:
        parsed = uuid.UUID(user_id.strip(), version=4)
    except ValueError:
        raise ValueError(
            f"Geçersiz kullanıcı ID formatı: '{user_id}'. UUID v4 formatı bekleniyor."
        )

    return str(parsed)
