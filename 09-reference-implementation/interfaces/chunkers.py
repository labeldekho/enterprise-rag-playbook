"""
Text Chunking Interface

Chunkers split documents into smaller, retrievable units.
Chunking strategy significantly impacts retrieval quality.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from .loaders import Document


@dataclass
class Chunk:
    """
    Represents a chunk of text from a document.

    Attributes:
        id: Unique identifier for the chunk
        document_id: Parent document ID
        text: Chunk content
        metadata: Inherited and chunk-specific metadata
        position: Position in original document (0-indexed)
    """
    id: str
    document_id: str
    text: str
    metadata: dict = field(default_factory=dict)
    position: int = 0

    def __len__(self):
        return len(self.text)


class Chunker(ABC):
    """
    Abstract base class for text chunkers.

    Implement this interface for different chunking strategies:
    - Fixed-size chunking
    - Sentence-based chunking
    - Semantic chunking
    - Document-structure aware chunking

    AGENT_ZONE: Implement chunking strategies
    See: 03-data-foundations/chunking-strategies.md
    """

    @abstractmethod
    def chunk(self, document: Document) -> list[Chunk]:
        """
        Split a document into chunks.

        Args:
            document: Document to chunk

        Returns:
            List of Chunk objects
        """
        pass


# =============================================================================
# Example Implementations
# =============================================================================

class FixedSizeChunker(Chunker):
    """
    Split text into fixed-size chunks with overlap.

    Simple and fast, but may break mid-sentence.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
        length_function: callable = len
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.length_function = length_function

    def chunk(self, document: Document) -> list[Chunk]:
        text = document.text
        chunks = []
        start = 0
        position = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]

            chunks.append(Chunk(
                id=f"{document.id}_chunk_{position}",
                document_id=document.id,
                text=chunk_text,
                metadata={
                    **document.metadata,
                    'chunk_size': len(chunk_text),
                    'start_char': start,
                    'end_char': end,
                },
                position=position
            ))

            start = end - self.overlap
            position += 1

        return chunks


class SentenceChunker(Chunker):
    """
    Split text by sentences, grouping until size limit.

    Preserves sentence boundaries for more coherent chunks.
    """

    def __init__(self, max_chunk_size: int = 512):
        self.max_chunk_size = max_chunk_size

    def chunk(self, document: Document) -> list[Chunk]:
        sentences = self._split_sentences(document.text)
        chunks = []
        current_chunk = []
        current_size = 0
        position = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            if current_size + sentence_len > self.max_chunk_size and current_chunk:
                # Save current chunk
                chunks.append(Chunk(
                    id=f"{document.id}_chunk_{position}",
                    document_id=document.id,
                    text=' '.join(current_chunk),
                    metadata=document.metadata,
                    position=position
                ))
                position += 1
                current_chunk = []
                current_size = 0

            current_chunk.append(sentence)
            current_size += sentence_len

        # Don't forget the last chunk
        if current_chunk:
            chunks.append(Chunk(
                id=f"{document.id}_chunk_{position}",
                document_id=document.id,
                text=' '.join(current_chunk),
                metadata=document.metadata,
                position=position
            ))

        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        """Simple sentence splitting. Use nltk or spacy for better results."""
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]


class RecursiveChunker(Chunker):
    """
    Recursively split using multiple separators.

    AGENT_ZONE: This is a good starting point for most use cases.
    Customize separators based on your document types.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
        separators: list[str] = None
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def chunk(self, document: Document) -> list[Chunk]:
        chunks = self._recursive_split(document.text, self.separators)

        return [
            Chunk(
                id=f"{document.id}_chunk_{i}",
                document_id=document.id,
                text=chunk_text,
                metadata=document.metadata,
                position=i
            )
            for i, chunk_text in enumerate(chunks)
        ]

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        if not separators:
            return [text]

        separator = separators[0]
        remaining_separators = separators[1:]

        if separator == "":
            # Base case: character-level split
            return self._hard_split(text)

        parts = text.split(separator)
        chunks = []
        current = ""

        for part in parts:
            candidate = current + (separator if current else "") + part

            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                # Recursively split if part is too large
                if len(part) > self.chunk_size:
                    chunks.extend(self._recursive_split(part, remaining_separators))
                    current = ""
                else:
                    current = part

        if current:
            chunks.append(current)

        return chunks

    def _hard_split(self, text: str) -> list[str]:
        """Last resort: split by character count."""
        return [
            text[i:i + self.chunk_size]
            for i in range(0, len(text), self.chunk_size - self.overlap)
        ]


# =============================================================================
# Production Considerations
# =============================================================================

"""
When implementing chunkers for production:

1. Overlap Strategy
   - Always use overlap (10-20% of chunk size)
   - Prevents information loss at boundaries
   - Consider semantic overlap (last N sentences)

2. Metadata Preservation
   - Include position information
   - Preserve document hierarchy (section, page)
   - Add chunk-specific metadata

3. Content-Aware Chunking
   - Respect table boundaries
   - Keep code blocks together
   - Handle lists appropriately

4. Size Consistency
   - Track actual vs target chunk sizes
   - Monitor for outliers (very small/large chunks)

5. Testing
   - Test with real queries
   - Verify information at boundaries is retrievable
   - Compare strategies on your data
"""
