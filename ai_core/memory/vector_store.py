"""
VectorStore: ChromaDB tabanlı vektör depolama ve semantik arama.
Bağlantı hatalarında in-memory dict fallback kullanır.
"""
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    doc_id: str
    score: float
    metadata: dict = field(default_factory=dict)


class VectorStore:
    """ChromaDB ile vektör depolama; hata durumunda in-memory fallback."""

    def __init__(self, collection_name: str, chroma_client=None) -> None:
        self._collection_name = collection_name
        self._collection = None
        self._fallback: dict[str, dict] = {}  # doc_id -> {embedding, metadata}
        self._use_fallback = False

        if chroma_client is not None:
            self._client = chroma_client
        else:
            try:
                import chromadb
                self._client = chromadb.Client()  # in-memory
            except Exception as exc:
                logger.error("ChromaDB başlatılamadı, fallback kullanılıyor: %s", exc)
                self._client = None
                self._use_fallback = True

        if not self._use_fallback:
            self._init_collection()

    def _init_collection(self) -> None:
        try:
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name
            )
        except Exception as exc:
            logger.error(
                "ChromaDB koleksiyonu oluşturulamadı, fallback kullanılıyor: %s", exc
            )
            self._use_fallback = True
            self._collection = None

    async def upsert(
        self, doc_id: str, embedding: list[float], metadata: dict
    ) -> None:
        if self._use_fallback:
            self._fallback[doc_id] = {"embedding": embedding, "metadata": metadata}
            return

        try:
            self._collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                metadatas=[metadata],
            )
        except Exception as exc:
            logger.error("ChromaDB upsert hatası, fallback'e geçiliyor: %s", exc)
            self._use_fallback = True
            self._fallback[doc_id] = {"embedding": embedding, "metadata": metadata}

    async def search(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[SearchResult]:
        if self._use_fallback:
            return self._fallback_search(query_embedding, top_k)

        try:
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, self._collection.count() or 1),
                include=["metadatas", "distances"],
            )
            ids = results["ids"][0]
            distances = results["distances"][0]
            metadatas = results["metadatas"][0]

            search_results = [
                SearchResult(
                    doc_id=doc_id,
                    score=1.0 - dist,  # cosine distance -> similarity
                    metadata=meta,
                )
                for doc_id, dist, meta in zip(ids, distances, metadatas)
            ]
            # Azalan sırada sırala
            search_results.sort(key=lambda r: r.score, reverse=True)
            return search_results
        except Exception as exc:
            logger.error("ChromaDB search hatası, fallback'e geçiliyor: %s", exc)
            self._use_fallback = True
            return self._fallback_search(query_embedding, top_k)

    def _fallback_search(
        self, query_embedding: list[float], top_k: int
    ) -> list[SearchResult]:
        """In-memory dict üzerinde kosinüs benzerliği hesapla."""
        import math

        def cosine_similarity(a: list[float], b: list[float]) -> float:
            if len(a) != len(b) or not a:
                return 0.0
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(y * y for y in b))
            if norm_a == 0.0 or norm_b == 0.0:
                return 0.0
            return dot / (norm_a * norm_b)

        scored = [
            SearchResult(
                doc_id=doc_id,
                score=cosine_similarity(query_embedding, entry["embedding"]),
                metadata=entry["metadata"],
            )
            for doc_id, entry in self._fallback.items()
        ]
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]

    async def delete(self, doc_id: str) -> None:
        if self._use_fallback:
            self._fallback.pop(doc_id, None)
            return

        try:
            self._collection.delete(ids=[doc_id])
        except Exception as exc:
            logger.error("ChromaDB delete hatası: %s", exc)
            self._fallback.pop(doc_id, None)
