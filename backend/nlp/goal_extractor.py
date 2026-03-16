"""
GoalExtractor: Ham öğrenme hedefi metnini LLM ile StructuredGoal'a dönüştürür.
"""
import asyncio
import json
import logging
from typing import Any

from backend.models.learning_goal_model import StructuredGoal
from backend.utils.validators import validate_goal_text

logger = logging.getLogger(__name__)

_RETRY_MAX = 3
_RETRY_BASE_DELAY = 1.0  # saniye


class GoalExtractor:
    """Ham metin → StructuredGoal dönüşümü için NLP bileşeni."""

    def __init__(self, llm_client: Any, prompts: dict) -> None:
        """
        Args:
            llm_client: OpenAI/Ollama uyumlu async LLM istemcisi.
            prompts: config/prompts.yaml içeriği (dict).
        """
        self._llm = llm_client
        self._prompts = prompts

    # ── Public API ────────────────────────────────────────────────────────────

    async def extract(self, raw_text: str) -> StructuredGoal:
        """Ham metni doğrulayıp LLM aracılığıyla StructuredGoal'a dönüştürür.

        Args:
            raw_text: Kullanıcının girdiği ham hedef metni.

        Returns:
            Doldurulmuş StructuredGoal nesnesi.

        Raises:
            ValueError: Metin boş veya geçersizse.
            RuntimeError: Tüm LLM denemeleri başarısız olursa.
        """
        cleaned = validate_goal_text(raw_text)  # ValueError fırlatabilir

        prompt_cfg = self._prompts.get("goal_analysis", {})
        system_msg = prompt_cfg.get("system", "")
        user_template = prompt_cfg.get("user", '"{raw_text}"')
        user_msg = user_template.replace("{raw_text}", cleaned)

        last_exc: Exception | None = None
        for attempt in range(1, _RETRY_MAX + 1):
            try:
                response_text = await self._call_llm(system_msg, user_msg)
                goal = self._parse_response(response_text)
                return goal
            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                last_exc = exc
                logger.warning("GoalExtractor parse hatası (deneme %d/%d): %s", attempt, _RETRY_MAX, exc)
            except Exception as exc:  # LLM API / ağ hataları
                last_exc = exc
                logger.warning("GoalExtractor LLM hatası (deneme %d/%d): %s", attempt, _RETRY_MAX, exc)

            if attempt < _RETRY_MAX:
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                await asyncio.sleep(delay)

        raise RuntimeError(
            f"GoalExtractor: {_RETRY_MAX} denemeden sonra hedef çıkarılamadı. "
            f"Son hata: {last_exc}"
        )

    async def detect_language(self, text: str) -> str:
        """Metnin dilini tespit eder.

        Args:
            text: Dil tespiti yapılacak metin.

        Returns:
            "tr" (Türkçe) veya "en" (İngilizce).
        """
        if not text or not text.strip():
            return "en"

        # Hızlı kural tabanlı tespit: yaygın Türkçe karakterler / kelimeler
        turkish_chars = set("çğıöşüÇĞİÖŞÜ")
        turkish_words = {
            "ve", "bir", "bu", "da", "de", "ile", "için", "olan", "olan",
            "öğrenmek", "istiyorum", "hedefim", "yapmak", "bilmek",
        }

        lower = text.lower()
        has_turkish_char = any(c in turkish_chars for c in text)
        word_set = set(lower.split())
        has_turkish_word = bool(word_set & turkish_words)

        if has_turkish_char or has_turkish_word:
            return "tr"

        # Belirsiz durumlarda LLM'e sor
        try:
            system_msg = (
                "You are a language detector. "
                "Reply with only 'tr' for Turkish or 'en' for English."
            )
            user_msg = f'Detect the language of this text: "{text[:200]}"'
            result = await self._call_llm(system_msg, user_msg)
            lang = result.strip().lower()[:2]
            return lang if lang in ("tr", "en") else "en"
        except Exception as exc:
            logger.warning("detect_language LLM hatası: %s", exc)
            return "en"

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _call_llm(self, system_msg: str, user_msg: str) -> str:
        """LLM'e istek gönderir ve metin yanıtı döndürür."""
        response = await self._llm.chat.completions.create(
            model=getattr(self._llm, "_model", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content

    def _parse_response(self, response_text: str) -> StructuredGoal:
        """LLM JSON yanıtını StructuredGoal nesnesine dönüştürür."""
        data = json.loads(response_text)
        return StructuredGoal(
            title=data["title"],
            domain=data["domain"],
            target_level=data["target_level"],
            timeline_weeks=int(data["timeline_weeks"]),
            sub_goals=data.get("sub_goals", []),
        )
