"""
IntentClassifier: Kullanıcı mesajının niyetini kural tabanlı + LLM hibrit yaklaşımla sınıflandırır.
"""
import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Desteklenen niyet türleri
INTENT_GOAL_SETTING = "goal_setting"
INTENT_QUESTION = "question"
INTENT_PROGRESS_UPDATE = "progress_update"
INTENT_MOTIVATION = "motivation"
INTENT_OTHER = "other"

_VALID_INTENTS = {
    INTENT_GOAL_SETTING,
    INTENT_QUESTION,
    INTENT_PROGRESS_UPDATE,
    INTENT_MOTIVATION,
    INTENT_OTHER,
}

# Kural tabanlı anahtar kelimeler (Türkçe + İngilizce)
_RULES: dict[str, list[str]] = {
    INTENT_GOAL_SETTING: [
        "öğrenmek istiyorum", "hedefim", "hedef", "öğrenmek", "başlamak istiyorum",
        "i want to learn", "my goal", "goal is", "i'd like to learn", "i would like to",
        "plan", "yol haritası", "roadmap",
    ],
    INTENT_QUESTION: [
        "nasıl", "nedir", "ne zaman", "neden", "hangi", "ne kadar",
        "how", "what", "when", "why", "which", "where", "who", "?",
        "açıklar mısın", "anlatır mısın", "explain", "tell me",
    ],
    INTENT_PROGRESS_UPDATE: [
        "tamamladım", "bitirdim", "yaptım", "öğrendim", "geçtim",
        "completed", "finished", "done", "learned", "passed",
        "ilerleme", "progress", "güncellemek", "update",
    ],
    INTENT_MOTIVATION: [
        "motivasyon", "sıkıldım", "yoruldum", "zor", "vazgeçmek",
        "motivation", "tired", "bored", "difficult", "give up", "struggling",
        "teşvik", "encourage", "inspire",
    ],
}

# LLM'e başvurma eşiği: kural tabanlı güven bu değerin altındaysa LLM kullanılır
_LLM_THRESHOLD = 0.6


@dataclass
class Intent:
    """Sınıflandırılmış niyet sonucu."""
    type: str          # goal_setting | question | progress_update | motivation | other
    confidence: float  # 0.0 – 1.0
    entities: dict = field(default_factory=dict)


class IntentClassifier:
    """Kural tabanlı + LLM hibrit niyet sınıflandırıcı."""

    def __init__(self, llm_client: Any | None = None) -> None:
        """
        Args:
            llm_client: Opsiyonel async LLM istemcisi.
                        Verilmezse yalnızca kural tabanlı sınıflandırma yapılır.
        """
        self._llm = llm_client

    # ── Public API ────────────────────────────────────────────────────────────

    async def classify(self, text: str) -> Intent:
        """Kullanıcı mesajının niyetini sınıflandırır.

        Args:
            text: Kullanıcı mesajı.

        Returns:
            Intent nesnesi (type, confidence, entities).
        """
        if not text or not text.strip():
            return Intent(type=INTENT_OTHER, confidence=1.0)

        # 1. Hızlı kural tabanlı sınıflandırma
        rule_intent, rule_confidence = self._rule_based_classify(text)

        # 2. Güven yeterliyse kural sonucunu döndür
        if rule_confidence >= _LLM_THRESHOLD:
            return Intent(
                type=rule_intent,
                confidence=rule_confidence,
                entities=self._extract_entities(text, rule_intent),
            )

        # 3. Belirsizse LLM'e sor
        if self._llm is not None:
            try:
                llm_intent = await self._llm_classify(text)
                return llm_intent
            except Exception as exc:
                logger.warning("IntentClassifier LLM hatası, kural sonucu kullanılıyor: %s", exc)

        # 4. LLM yoksa veya hata varsa kural sonucunu döndür
        return Intent(
            type=rule_intent,
            confidence=rule_confidence,
            entities=self._extract_entities(text, rule_intent),
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _rule_based_classify(self, text: str) -> tuple[str, float]:
        """Anahtar kelime eşleşmesiyle niyet ve güven skoru döndürür."""
        lower = text.lower()
        scores: dict[str, int] = {intent: 0 for intent in _VALID_INTENTS}

        for intent, keywords in _RULES.items():
            for kw in keywords:
                if kw in lower:
                    scores[intent] += 1

        best_intent = max(scores, key=lambda k: scores[k])
        best_score = scores[best_intent]

        if best_score == 0:
            return INTENT_OTHER, 0.5

        total = sum(scores.values())
        confidence = min(0.5 + (best_score / max(total, 1)) * 0.5, 0.95)
        return best_intent, confidence

    async def _llm_classify(self, text: str) -> Intent:
        """LLM ile niyet sınıflandırması yapar."""
        system_msg = (
            "You are an intent classifier for a learning coach app. "
            "Classify the user message into one of these intents: "
            "goal_setting, question, progress_update, motivation, other. "
            "Return JSON: {\"type\": \"<intent>\", \"confidence\": <0.0-1.0>, \"entities\": {}}"
        )
        user_msg = f'Classify: "{text[:500]}"'

        response = await self._llm.chat.completions.create(
            model=getattr(self._llm, "_model", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)
        intent_type = data.get("type", INTENT_OTHER)
        if intent_type not in _VALID_INTENTS:
            intent_type = INTENT_OTHER

        return Intent(
            type=intent_type,
            confidence=float(data.get("confidence", 0.7)),
            entities=data.get("entities", {}),
        )

    def _extract_entities(self, text: str, intent_type: str) -> dict:
        """Basit varlık çıkarımı (kural tabanlı)."""
        entities: dict = {}
        lower = text.lower()

        if intent_type == INTENT_GOAL_SETTING:
            # Konu tespiti için basit anahtar kelimeler
            topics = [
                "python", "javascript", "java", "sql", "machine learning",
                "deep learning", "data science", "web development", "react",
                "django", "fastapi", "docker", "kubernetes",
            ]
            found = [t for t in topics if t in lower]
            if found:
                entities["topics"] = found

        return entities
