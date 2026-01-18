"""
Embedding Interface

Embedders convert text into dense vector representations
for semantic similarity search.
"""

from abc import ABC, abstractmethod
from typing import Union
import hashlib


class Embedder(ABC):
    """
    Abstract base class for text embedders.

    Implement this interface for different embedding providers:
    - OpenAI embeddings
    - Cohere embeddings
    - Local models (Sentence Transformers)
    - Custom models

    AGENT_ZONE: Select embedding model based on requirements
    See: 04-retrieval/embeddings.md
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        pass

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector
        """
        pass

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Override for optimized batch processing.
        """
        return [self.embed(text) for text in texts]

    def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a query.

        Some models use different embeddings for queries vs documents.
        Override if your model requires this distinction.
        """
        return self.embed(query)

    def embed_document(self, document: str) -> list[float]:
        """
        Generate embedding for a document chunk.

        Override if your model uses asymmetric embeddings.
        """
        return self.embed(document)


# =============================================================================
# Example Implementations
# =============================================================================

class OpenAIEmbedder(Embedder):
    """
    OpenAI embeddings implementation.

    AGENT_ZONE: Configure model and parameters
    Options: text-embedding-3-small, text-embedding-3-large
    """

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str = None,
        dimensions: int = None
    ):
        self.model = model
        self.api_key = api_key
        self._dimensions = dimensions or self._default_dimensions()

    def _default_dimensions(self) -> int:
        defaults = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        return defaults.get(self.model, 1536)

    @property
    def dimension(self) -> int:
        return self._dimensions

    def embed(self, text: str) -> list[float]:
        # Import here to avoid dependency if not using OpenAI
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)

        kwargs = {"model": self.model, "input": text}
        if self._dimensions and self.model.startswith("text-embedding-3"):
            kwargs["dimensions"] = self._dimensions

        response = client.embeddings.create(**kwargs)
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)

        kwargs = {"model": self.model, "input": texts}
        if self._dimensions and self.model.startswith("text-embedding-3"):
            kwargs["dimensions"] = self._dimensions

        response = client.embeddings.create(**kwargs)
        return [item.embedding for item in response.data]


class SentenceTransformerEmbedder(Embedder):
    """
    Local embeddings using Sentence Transformers.

    AGENT_ZONE: Select model based on language and domain
    Options: all-MiniLM-L6-v2, all-mpnet-base-v2, multilingual models
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, text: str) -> list[float]:
        embedding = self.model.encode(text)
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts)
        return embeddings.tolist()


class CachedEmbedder(Embedder):
    """
    Wrapper that adds caching to any embedder.

    Reduces API costs and latency for repeated texts.
    """

    def __init__(self, base_embedder: Embedder, cache: dict = None):
        self.base_embedder = base_embedder
        self.cache = cache if cache is not None else {}

    @property
    def dimension(self) -> int:
        return self.base_embedder.dimension

    def _cache_key(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    def embed(self, text: str) -> list[float]:
        key = self._cache_key(text)

        if key in self.cache:
            return self.cache[key]

        embedding = self.base_embedder.embed(text)
        self.cache[key] = embedding
        return embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        results = []
        uncached_texts = []
        uncached_indices = []

        # Check cache
        for i, text in enumerate(texts):
            key = self._cache_key(text)
            if key in self.cache:
                results.append(self.cache[key])
            else:
                results.append(None)
                uncached_texts.append(text)
                uncached_indices.append(i)

        # Embed uncached
        if uncached_texts:
            new_embeddings = self.base_embedder.embed_batch(uncached_texts)
            for idx, text, embedding in zip(uncached_indices, uncached_texts, new_embeddings):
                key = self._cache_key(text)
                self.cache[key] = embedding
                results[idx] = embedding

        return results


# =============================================================================
# Production Considerations
# =============================================================================

"""
When implementing embedders for production:

1. Batching
   - Always batch API calls when possible
   - Typical batch sizes: 32-100 texts
   - Watch for rate limits

2. Caching
   - Cache embeddings for repeated texts
   - Use Redis or similar for distributed caching
   - Consider TTL for cache entries

3. Error Handling
   - Retry on transient failures
   - Handle rate limiting gracefully
   - Log failures for debugging

4. Model Consistency
   - Use the SAME model for documents and queries
   - Pin model versions
   - Re-embed all documents when changing models

5. Dimension Reduction
   - OpenAI supports native dimension reduction
   - Reduces storage and improves speed
   - Test quality impact before deploying

6. Monitoring
   - Track embedding latency
   - Monitor cache hit rates
   - Alert on error rate spikes
"""
