"""
MemoryRetrievalService Application Layer for Phase 7.
Implements hybrid memory retrieval combining metadata filtering, scope isolation,
authority ranking, recency, and vector similarity.
"""

from typing import Any

from src.application.embedding_provider import EmbeddingProviderInterface, cosine_similarity
from src.domain.memory import (
    MemoryAuthority,
    MemoryEntry,
    MemoryScope,
    MemoryStatus,
    MemoryType,
)
from src.domain.repository import MemoryRepositoryInterface

AUTHORITY_WEIGHTS: dict[MemoryAuthority, float] = {
    MemoryAuthority.AUTHORITATIVE: 10.0,
    MemoryAuthority.CONFIRMED: 8.0,
    MemoryAuthority.OBSERVED: 5.0,
    MemoryAuthority.GENERATED: 3.0,
    MemoryAuthority.UNVERIFIED: 1.0,
}


class MemoryRetrievalService:
    def __init__(
        self,
        memory_repo: MemoryRepositoryInterface,
        embedding_provider: EmbeddingProviderInterface | None = None,
        knowledge_repo: Any | None = None,
    ) -> None:
        self.memory_repo = memory_repo
        self.embedding_provider = embedding_provider
        self.knowledge_repo = knowledge_repo

    async def retrieve_institutional_knowledge(
        self,
        query: str | None = None,
        scope: str | None = None,
        min_authority: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Retrieve Phase 18 institutional knowledge items matching query and authority constraints."""
        if not self.knowledge_repo:
            return []

        if query and hasattr(self.knowledge_repo, "search_knowledge_items"):
            res = await self.knowledge_repo.search_knowledge_items(query)
        elif hasattr(self.knowledge_repo, "list_knowledge_items"):
            res = await self.knowledge_repo.list_knowledge_items(scope=scope, authority=min_authority)
        else:
            return []

        items = list(res)[:limit]
        return [
            {
                "id": k.id,
                "statement": k.statement,
                "type": k.knowledge_type.value if hasattr(k.knowledge_type, "value") else str(k.knowledge_type),
                "authority": k.authority.value if hasattr(k.authority, "value") else str(k.authority),
                "status": k.status.value if hasattr(k.status, "value") else str(k.status),
                "confidence": k.confidence,
                "scope": k.scope.value if hasattr(k.scope, "value") else str(k.scope),
            }
            for k in items
        ]

    async def retrieve_memories(
        self,
        query: str | None = None,
        owner_ids: list[str] | None = None,
        scopes: list[MemoryScope] | None = None,
        memory_types: list[MemoryType] | None = None,
        min_authority: MemoryAuthority | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Execute hybrid memory retrieval across active memories.
        Calculates score: Authority Weight + (Similarity * 5.0) + (Confidence * 2.0).
        """
        if not self.memory_repo:
            all_memories = []
        else:
            all_memories = await self.memory_repo.list_all()

        # 1. Scope & Status Filtering
        candidates = [m for m in all_memories if m.status == MemoryStatus.ACTIVE]

        if owner_ids:
            candidates = [m for m in candidates if m.owner_id in owner_ids or m.scope == MemoryScope.COMPANY]

        if scopes:
            candidates = [m for m in candidates if m.scope in scopes]

        if memory_types:
            candidates = [m for m in candidates if m.memory_type in memory_types]

        if min_authority:
            min_weight = AUTHORITY_WEIGHTS.get(min_authority, 0.0)
            candidates = [m for m in candidates if AUTHORITY_WEIGHTS.get(m.authority, 0.0) >= min_weight]

        # 2. Query Embedding Calculation
        query_vec: list[float] | None = None
        if query and self.embedding_provider:
            try:
                query_vec = await self.embedding_provider.embed(query)
            except Exception:
                query_vec = None  # Fallback to structured filtering resilience

        # 3. Hybrid Scoring
        scored_memories: list[tuple[float, MemoryEntry]] = []
        for m in candidates:
            authority_weight = AUTHORITY_WEIGHTS.get(m.authority, 1.0)
            sim_score = 0.0
            if query_vec and m.embedding:
                sim_score = cosine_similarity(query_vec, m.embedding)

            total_score = authority_weight + (sim_score * 5.0) + (m.confidence * 2.0)
            scored_memories.append((total_score, m))

        # Sort descending by score
        scored_memories.sort(key=lambda x: x[0], reverse=True)

        results: list[dict[str, Any]] = []
        for score, m in scored_memories[:limit]:
            results.append(
                {
                    "score": round(score, 4),
                    "memory": m,
                }
            )
        return results
