"""
UserContextMemory: Kullanıcı bağlamını vektör bellek üzerinden yönetir.
"""
import json
import logging
import uuid
from datetime import datetime

from ai_core.memory.vector_store import VectorStore
from backend.models.progress_model import UserContext

logger = logging.getLogger(__name__)


class UserContextMemory:
    """Kullanıcı bağlamını vektör bellekte saklar ve günceller."""

    def __init__(self, vector_store: VectorStore, embeddings_manager) -> None:
        """
        Args:
            vector_store: VectorStore instance.
            embeddings_manager: EmbeddingsManager (embed metodu olan nesne).
        """
        self._store = vector_store
        self._embeddings = embeddings_manager
        # user_id -> UserContext in-memory cache
        self._context_cache: dict[str, UserContext] = {}

    async def get_context(self, user_id: str, query: str) -> UserContext:
        """Vektör bellekten kullanıcıya ait ilgili bağlamı getirir.

        Args:
            user_id: Kullanıcı kimliği.
            query: Bağlam araması için sorgu metni.

        Returns:
            Kullanıcının mevcut UserContext nesnesi.
        """
        try:
            query_embedding = await self._embeddings.embed(query)
            results = await self._store.search(query_embedding, top_k=5)

            # Kullanıcıya ait sonuçları filtrele
            user_results = [r for r in results if r.metadata.get("user_id") == user_id]

            if user_id in self._context_cache:
                ctx = self._context_cache[user_id]
                # Bulunan embedding ID'lerini güncelle
                ctx.embedding_ids = [r.doc_id for r in user_results]
                return ctx

            # Cache'de yoksa boş bağlam oluştur
            ctx = UserContext(
                user_id=user_id,
                embedding_ids=[r.doc_id for r in user_results],
            )
            self._context_cache[user_id] = ctx
            return ctx
        except Exception as exc:
            logger.error("Bağlam getirme hatası (user_id=%s): %s", user_id, exc)
            return self._context_cache.get(user_id, UserContext(user_id=user_id))

    async def update_context(self, user_id: str, new_info: dict) -> UserContext:
        """Mevcut bağlamı yeni bilgiyle birleştirir; eski bilgileri korur.

        Args:
            user_id: Kullanıcı kimliği.
            new_info: Bağlama eklenecek yeni bilgiler.

        Returns:
            Güncellenmiş UserContext nesnesi.
        """
        ctx = self._context_cache.get(user_id, UserContext(user_id=user_id))

        # Eski ve yeni bilgileri birleştir
        if "current_goals" in new_info:
            existing = set(ctx.current_goals)
            existing.update(new_info["current_goals"])
            ctx.current_goals = list(existing)

        if "completed_topics" in new_info:
            existing = set(ctx.completed_topics)
            existing.update(new_info["completed_topics"])
            ctx.completed_topics = list(existing)

        if "learning_preferences" in new_info:
            ctx.learning_preferences = {**ctx.learning_preferences, **new_info["learning_preferences"]}

        if "recent_interactions" in new_info:
            ctx.recent_interactions = ctx.recent_interactions + new_info["recent_interactions"]

        self._context_cache[user_id] = ctx

        # Güncellenmiş bağlamı vektör belleğe kaydet
        try:
            context_text = json.dumps({
                "user_id": user_id,
                "current_goals": ctx.current_goals,
                "completed_topics": ctx.completed_topics,
                "learning_preferences": ctx.learning_preferences,
                "recent_interactions": ctx.recent_interactions[-10:],  # son 10
            }, ensure_ascii=False)
            embedding = await self._embeddings.embed(context_text)
            doc_id = f"context_{user_id}"
            await self._store.upsert(
                doc_id=doc_id,
                embedding=embedding,
                metadata={"user_id": user_id, "type": "context", "updated_at": datetime.utcnow().isoformat()},
            )
            if doc_id not in ctx.embedding_ids:
                ctx.embedding_ids.append(doc_id)
        except Exception as exc:
            logger.error("Bağlam vektör kayıt hatası (user_id=%s): %s", user_id, exc)

        return ctx

    async def save_message(self, user_id: str, message: str, role: str) -> None:
        """Mesajı vektör belleğe kaydeder.

        Args:
            user_id: Kullanıcı kimliği.
            message: Mesaj içeriği.
            role: Mesaj rolü ("user" veya "assistant").
        """
        try:
            embedding = await self._embeddings.embed(message)
            doc_id = f"msg_{user_id}_{uuid.uuid4().hex[:8]}"
            await self._store.upsert(
                doc_id=doc_id,
                embedding=embedding,
                metadata={
                    "user_id": user_id,
                    "role": role,
                    "content": message[:500],  # metadata boyut sınırı
                    "type": "message",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            # Cache'deki bağlamı güncelle
            ctx = self._context_cache.get(user_id, UserContext(user_id=user_id))
            ctx.recent_interactions.append(f"[{role}] {message[:200]}")
            ctx.embedding_ids.append(doc_id)
            self._context_cache[user_id] = ctx
        except Exception as exc:
            logger.error("Mesaj kayıt hatası (user_id=%s): %s", user_id, exc)
