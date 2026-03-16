"""
AIEmbeddingsManager: Metin → embedding → VectorStore pipeline.
"""
import logging

from ai_core.memory.vector_store import SearchResult, VectorStore
from backend.nlp.text_embeddings import EmbeddingsManager

logger = logging.getLogger(__name__)


class AIEmbeddingsManager:
    """Metin embedding'lerini oluşturur ve VectorStore'a kaydeder."""

    def __init__(self, embeddings: EmbeddingsManager, vector_store: VectorStore) -> None:
        """
        Args:
            embeddings: EmbeddingsManager (OpenAI embed pipeline).
            vector_store: VectorStore instance.
        """
        self._embeddings = embeddings
        self._store = vector_store

    async def index_text(self, doc_id: str, text: str, metadata: dict) -> None:
        """Metni embed eder ve VectorStore'a kaydeder.

        Args:
            doc_id: Doküman kimliği.
            text: Embed edilecek metin.
            metadata: Dokümanla ilişkili metadata.

        Raises:
            ValueError: Metin boşsa.
        """
        if not text or not text.strip():
            raise ValueError("İndekslenecek metin boş olamaz.")

        embedding = await self._embeddings.embed(text)
        await self._store.upsert(doc_id=doc_id, embedding=embedding, metadata=metadata)
        logger.debug("Metin indekslendi: doc_id=%s", doc_id)

    async def search_similar(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """Sorguyu embed eder ve benzer dokümanları bulur.

        Args:
            query: Arama sorgusu.
            top_k: Döndürülecek maksimum sonuç sayısı.

        Returns:
            Benzerlik skoruna göre azalan sırada SearchResult listesi.

        Raises:
            ValueError: Sorgu boşsa.
        """
        if not query or not query.strip():
            raise ValueError("Arama sorgusu boş olamaz.")

        query_embedding = await self._embeddings.embed(query)
        return await self._store.search(query_embedding, top_k=top_k)
