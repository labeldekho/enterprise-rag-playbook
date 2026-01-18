"""
RAG Reference Implementation - Interface Definitions

This module provides abstract base classes for building RAG pipelines.
Implement these interfaces to create your own RAG system.

Example:
    from interfaces import Loader, Chunker, Embedder, Retriever

    class MyLoader(Loader):
        def load(self, source: str) -> list[Document]:
            # Your implementation
            pass
"""

from .loaders import Loader, Document
from .chunkers import Chunker, Chunk
from .embedders import Embedder
from .retrievers import Retriever, SearchResult
from .evaluators import Evaluator, EvaluationResult

__all__ = [
    'Loader',
    'Document',
    'Chunker',
    'Chunk',
    'Embedder',
    'Retriever',
    'SearchResult',
    'Evaluator',
    'EvaluationResult',
]
