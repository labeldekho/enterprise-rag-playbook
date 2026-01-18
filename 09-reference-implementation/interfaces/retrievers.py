"""
Retrieval Interface

Retrievers store and search vector embeddings to find relevant chunks.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from .chunkers import Chunk


@dataclass
class SearchResult:
    """
    Represents a search result.

    Attributes:
        chunk: The retrieved chunk
        score: Similarity score (higher is more similar)
        rank: Position in result list (1-indexed)
    """
    chunk: Chunk
    score: float
    rank: int


class Retriever(ABC):
    """
    Abstract base class for vector retrievers.

    Implement this interface for different vector databases:
    - Pinecone
    - Weaviate
    - Milvus
    - pgvector
    - Chroma

    AGENT_ZONE: Implement for your vector database choice
    See: 04-retrieval/vector-search.md
    """

    @abstractmethod
    def index(self, chunk: Chunk, embedding: list[float]) -> None:
        """
        Index a chunk with its embedding.

        Args:
            chunk: Chunk to index
            embedding: Vector embedding of the chunk
        """
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: Optional[dict] = None
    ) -> list[SearchResult]:
        """
        Search for similar chunks.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filters: Metadata filters to apply

        Returns:
            List of SearchResult objects, sorted by relevance
        """
        pass

    def delete(self, chunk_id: str) -> None:
        """Delete a chunk from the index."""
        raise NotImplementedError

    def update(self, chunk: Chunk, embedding: list[float]) -> None:
        """Update a chunk's embedding."""
        self.delete(chunk.id)
        self.index(chunk, embedding)


class HybridRetriever(Retriever):
    """
    Abstract base class for hybrid (vector + keyword) retrievers.

    AGENT_ZONE: Implement hybrid search
    See: 04-retrieval/hybrid-search.md
    """

    @abstractmethod
    def search_hybrid(
        self,
        query: str,
        query_embedding: list[float],
        top_k: int = 5,
        alpha: float = 0.5,
        filters: Optional[dict] = None
    ) -> list[SearchResult]:
        """
        Hybrid search combining vector and keyword search.

        Args:
            query: Original query text (for keyword search)
            query_embedding: Query vector (for vector search)
            top_k: Number of results
            alpha: Weight for vector search (1-alpha for keyword)
            filters: Metadata filters

        Returns:
            List of SearchResult objects
        """
        pass


# =============================================================================
# Example Implementations
# =============================================================================

class InMemoryRetriever(Retriever):
    """
    Simple in-memory retriever for testing and small datasets.

    Not suitable for production - use for prototyping only.
    """

    def __init__(self):
        self.chunks: dict[str, Chunk] = {}
        self.embeddings: dict[str, list[float]] = {}

    def index(self, chunk: Chunk, embedding: list[float]) -> None:
        self.chunks[chunk.id] = chunk
        self.embeddings[chunk.id] = embedding

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: Optional[dict] = None
    ) -> list[SearchResult]:
        import numpy as np

        query_vec = np.array(query_embedding)
        scores = []

        for chunk_id, embedding in self.embeddings.items():
            chunk = self.chunks[chunk_id]

            # Apply filters
            if filters and not self._matches_filters(chunk, filters):
                continue

            # Calculate cosine similarity
            doc_vec = np.array(embedding)
            similarity = np.dot(query_vec, doc_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)
            )
            scores.append((chunk, similarity))

        # Sort by similarity
        scores.sort(key=lambda x: x[1], reverse=True)

        return [
            SearchResult(chunk=chunk, score=score, rank=i + 1)
            for i, (chunk, score) in enumerate(scores[:top_k])
        ]

    def _matches_filters(self, chunk: Chunk, filters: dict) -> bool:
        for key, value in filters.items():
            if chunk.metadata.get(key) != value:
                return False
        return True

    def delete(self, chunk_id: str) -> None:
        self.chunks.pop(chunk_id, None)
        self.embeddings.pop(chunk_id, None)


class PineconeRetriever(Retriever):
    """
    Pinecone vector database retriever.

    AGENT_ZONE: Configure for your Pinecone index
    """

    def __init__(self, index_name: str, api_key: str, environment: str = None):
        from pinecone import Pinecone

        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)

    def index(self, chunk: Chunk, embedding: list[float]) -> None:
        self.index.upsert(vectors=[
            {
                "id": chunk.id,
                "values": embedding,
                "metadata": {
                    "text": chunk.text,
                    "document_id": chunk.document_id,
                    **chunk.metadata
                }
            }
        ])

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: Optional[dict] = None
    ) -> list[SearchResult]:
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            filter=filters,
            include_metadata=True
        )

        return [
            SearchResult(
                chunk=Chunk(
                    id=match.id,
                    document_id=match.metadata.get("document_id", ""),
                    text=match.metadata.get("text", ""),
                    metadata=match.metadata
                ),
                score=match.score,
                rank=i + 1
            )
            for i, match in enumerate(results.matches)
        ]

    def delete(self, chunk_id: str) -> None:
        self.index.delete(ids=[chunk_id])


class RerankedRetriever(Retriever):
    """
    Wrapper that adds reranking to any retriever.

    AGENT_ZONE: Configure reranking model
    See: 04-retrieval/reranking.md
    """

    def __init__(
        self,
        base_retriever: Retriever,
        reranker,  # Reranker interface
        initial_k_multiplier: int = 5
    ):
        self.base_retriever = base_retriever
        self.reranker = reranker
        self.k_multiplier = initial_k_multiplier

    def index(self, chunk: Chunk, embedding: list[float]) -> None:
        self.base_retriever.index(chunk, embedding)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: Optional[dict] = None,
        query_text: str = None
    ) -> list[SearchResult]:
        # Get more candidates for reranking
        candidates = self.base_retriever.search(
            query_embedding,
            top_k=top_k * self.k_multiplier,
            filters=filters
        )

        if not query_text or not candidates:
            return candidates[:top_k]

        # Rerank
        reranked = self.reranker.rerank(
            query=query_text,
            documents=[c.chunk.text for c in candidates],
            top_k=top_k
        )

        return [
            SearchResult(
                chunk=candidates[r.index].chunk,
                score=r.score,
                rank=i + 1
            )
            for i, r in enumerate(reranked)
        ]


# =============================================================================
# Production Considerations
# =============================================================================

"""
When implementing retrievers for production:

1. Connection Management
   - Use connection pooling
   - Handle reconnection on failures
   - Implement circuit breakers

2. Batch Operations
   - Batch upserts for efficiency
   - Consider async operations for high throughput

3. Filtering
   - Index metadata fields used in filters
   - Use pre-filtering when possible (faster)
   - Understand your DB's filter capabilities

4. Monitoring
   - Track search latency
   - Monitor index size and memory usage
   - Alert on high error rates

5. Scaling
   - Understand your DB's scaling model
   - Plan for sharding if needed
   - Consider read replicas for heavy read loads

6. Data Consistency
   - Understand consistency guarantees
   - Handle eventual consistency if applicable
   - Implement retry logic for writes
"""
