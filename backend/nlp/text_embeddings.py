"""
EmbeddingsManager: OpenAI text-embedding-3-small ile metin vektörleştirme ve kosinüs benzerliği.
LRU cache ile in-memory önbellekleme (max 1000 giriş).
"""
import logging
import math
from collections import OrderedDict
from typing import Any

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL = "text-embedding-3-small"
_CACHE_MAX_SIZE = 1000


class _LRUCache:
    """Basit thread-unsafe LRU önbellek."""

    def __init__(self, max_size: int) -> None:
        self._max = max_size
        self._store: OrderedDict[str, list[float]] = OrderedDict()

    def get(self, key: str) -> list[float] | None:
        if key not in self._store:
            return None
        self._store.move_to_end(key)
        return self._store[key]

    def set(self, key: str, value: list[float]) -> None:
        if key in self._store:
            self._store.move_to_end(key)
        else:
            if len(self._store) >= self._max:
                self._store.popitem(last=False)
            self._store[key] = value

    def __len__(self) -> int:
        return len(self._store)


class EmbeddingsManager:
    """Metin embedding'leri oluşturur ve kosinüs benzerliği hesaplar."""

    def __init__(self, openai_client: Any) -> None:
        """
        Args:
            openai_client: AsyncOpenAI istemcisi (openai.AsyncOpenAI).
        """
        self._client = openai_client
        self._cache = _LRUCache(max_size=_CACHE_MAX_SIZE)

    # ── Public API ────────────────────────────────────────────────────────────

    async def embed(self, text: str) -> list[float]:
        """Metni OpenAI text-embedding-3-small ile vektörleştirir.

        Sonuçlar LRU cache'te saklanır; aynı metin için tekrar API çağrısı yapılmaz.

        Args:
            text: Vektörleştirilecek metin.

        Returns:
            Float listesi olarak embedding vektörü.

        Raises:
            ValueError: Metin boşsa.
            RuntimeError: API çağrısı başarısız olursa.
        """
        if not text or not text.strip():
            raise ValueError("Embedding için metin boş olamaz.")

        cache_key = text.strip()
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            response = await self._client.embeddings.create(
                model=_EMBEDDING_MODEL,
                input=cache_key,
            )
            vector = response.data[0].embedding
            self._cache.set(cache_key, vector)
            return vector
        except Exception as exc:
            logger.error("Embedding oluşturma hatası: %s", exc)
            raise RuntimeError(f"Embedding oluşturulamadı: {exc}") from exc

    def similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """İki vektör arasındaki kosinüs benzerliğini hesaplar.

        Args:
            vec1: Birinci vektör.
            vec2: İkinci vektör.

        Returns:
            -1.0 ile 1.0 arasında kosinüs benzerlik skoru.

        Raises:
            ValueError: Vektörler boşsa veya boyutları eşleşmiyorsa.
        """
        if not vec1 or not vec2:
            raise ValueError("Benzerlik hesabı için vektörler boş olamaz.")
        if len(vec1) != len(vec2):
            raise ValueError(
                f"Vektör boyutları eşleşmiyor: {len(vec1)} != {len(vec2)}"
            )

        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0

        return dot / (norm1 * norm2)
