"""
Document Loader Interface

Loaders are responsible for fetching documents from various sources
and converting them to a standard Document format.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class Document:
    """
    Represents a loaded document.

    Attributes:
        id: Unique identifier for the document
        text: Full text content of the document
        metadata: Additional attributes (source, author, date, etc.)
        source: Original source location (URL, file path, etc.)
    """
    id: str
    text: str
    metadata: dict = field(default_factory=dict)
    source: str = ""

    def __post_init__(self):
        # Ensure metadata has standard fields
        self.metadata.setdefault('loaded_at', datetime.utcnow().isoformat())
        self.metadata.setdefault('source', self.source)


class Loader(ABC):
    """
    Abstract base class for document loaders.

    Implement this interface to load documents from different sources:
    - File systems (PDF, DOCX, TXT)
    - APIs (Confluence, SharePoint, Notion)
    - Databases
    - Web scraping
    """

    @abstractmethod
    def load(self, source: str) -> list[Document]:
        """
        Load documents from the specified source.

        Args:
            source: Source identifier (file path, URL, API endpoint, etc.)

        Returns:
            List of Document objects

        Raises:
            LoaderError: If loading fails
        """
        pass

    def load_batch(self, sources: list[str]) -> list[Document]:
        """
        Load documents from multiple sources.

        Override for optimized batch loading.
        """
        documents = []
        for source in sources:
            documents.extend(self.load(source))
        return documents


# =============================================================================
# Example Implementation
# =============================================================================

class FileLoader(Loader):
    """
    Simple file loader implementation.

    AGENT_ZONE: Extend this to handle more file types
    Options: PDF, DOCX, HTML, Markdown
    See: 03-data-foundations/document-ingestion.md
    """

    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding

    def load(self, source: str) -> list[Document]:
        """Load a text file."""
        import os

        with open(source, 'r', encoding=self.encoding) as f:
            content = f.read()

        return [Document(
            id=os.path.basename(source),
            text=content,
            source=source,
            metadata={
                'filename': os.path.basename(source),
                'file_size': os.path.getsize(source),
            }
        )]


# =============================================================================
# Production Considerations
# =============================================================================

"""
When implementing loaders for production:

1. Error Handling
   - Handle file not found, permission errors
   - Implement retry logic for API sources
   - Log failures for debugging

2. Metadata Extraction
   - Extract document properties (author, date, title)
   - Preserve source information for citations
   - Add custom metadata for filtering

3. Large Files
   - Stream large files instead of loading into memory
   - Consider chunking at load time for very large documents

4. Rate Limiting
   - Respect API rate limits for external sources
   - Implement backoff strategies

5. Authentication
   - Secure credential handling
   - Support multiple auth methods (API key, OAuth, etc.)
"""
