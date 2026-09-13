"""
EmbeddingProvider Interface and Deterministic FakeEmbeddingProvider for Phase 7.
Decouples domain memory operations from specific vector embedding services.
"""

from abc import ABC, abstractmethod
import math


class EmbeddingProviderInterface(ABC):
    """Abstract interface for generating vector embeddings."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate a vector embedding for a single string."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for a list of strings."""
        pass


class FakeEmbeddingProvider(EmbeddingProviderInterface):
    """
    Deterministic 128-dimensional embedding provider for testing, offline execution,
    and fallback when remote embedding models are unavailable.
    """

    def __init__(self, dimension: int = 128) -> None:
        self.dimension = dimension

    async def embed(self, text: str) -> list[float]:
        if not text:
            return [0.0] * self.dimension

        # Produce a deterministic normalized pseudo-vector based on character hash values
        vec = [0.0] * self.dimension
        for i, char in enumerate(text):
            vec[i % self.dimension] += ord(char) * (i + 1)

        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calculate cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)
