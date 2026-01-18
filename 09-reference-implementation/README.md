# Reference Implementation

A skeletal implementation with clear interfaces for RAG pipelines.

## Philosophy

This reference implementation is **intentionally incomplete**.

### Design Principles

1. **Interfaces over implementations** - Define contracts, not solutions
2. **No framework lock-in** - Works with any vector DB, any LLM
3. **Agent-improvable** - Marked zones where coding agents can implement
4. **Human decision points** - Architecture choices remain with humans

### Why Skeletal?

- Full implementations become outdated quickly
- Vendor-specific code limits applicability
- Focus on patterns, not syntax
- Allows teams to adapt to their stack

## Directory Structure

```
09-reference-implementation/
├── README.md                 # This file
├── architecture.md           # System architecture overview
└── interfaces/
    ├── __init__.py
    ├── loaders.py           # Document loading interfaces
    ├── chunkers.py          # Text chunking interfaces
    ├── embedders.py         # Embedding interfaces
    ├── retrievers.py        # Retrieval interfaces
    └── evaluators.py        # Evaluation interfaces
```

## Quick Start

### Using the Interfaces

```python
from interfaces.loaders import Loader
from interfaces.chunkers import Chunker
from interfaces.embedders import Embedder
from interfaces.retrievers import Retriever

# Implement your own or use provided examples
class MyPDFLoader(Loader):
    def load(self, source: str) -> list[Document]:
        # Your implementation
        pass

class MySemanticChunker(Chunker):
    def chunk(self, document: Document) -> list[Chunk]:
        # Your implementation
        pass
```

### Building a Pipeline

```python
class RAGPipeline:
    def __init__(
        self,
        loader: Loader,
        chunker: Chunker,
        embedder: Embedder,
        retriever: Retriever
    ):
        self.loader = loader
        self.chunker = chunker
        self.embedder = embedder
        self.retriever = retriever

    def ingest(self, source: str):
        documents = self.loader.load(source)
        for doc in documents:
            chunks = self.chunker.chunk(doc)
            for chunk in chunks:
                embedding = self.embedder.embed(chunk.text)
                self.retriever.index(chunk, embedding)

    def query(self, query: str, top_k: int = 5) -> list[Chunk]:
        query_embedding = self.embedder.embed(query)
        return self.retriever.search(query_embedding, top_k)
```

## Agent Improvable Zones

The following areas are marked for coding agent implementation:

### Chunking Strategies
```python
# AGENT_ZONE: Implement chunking strategy
# Options: fixed, sentence, semantic, recursive
# See: 03-data-foundations/chunking-strategies.md
```

### Embedding Model Selection
```python
# AGENT_ZONE: Select and configure embedding model
# Options: OpenAI, Cohere, local models
# See: 04-retrieval/embeddings.md
```

### Retrieval Strategy
```python
# AGENT_ZONE: Implement retrieval approach
# Options: vector-only, hybrid, with reranking
# See: 04-retrieval/
```

### Caching Layer
```python
# AGENT_ZONE: Add caching
# Options: Redis, in-memory, multi-layer
# See: 08-scaling/caching-strategies.md
```

## Interface Documentation

| Interface | Purpose | Key Methods |
|-----------|---------|-------------|
| `Loader` | Load documents from sources | `load(source) -> [Document]` |
| `Chunker` | Split documents into chunks | `chunk(document) -> [Chunk]` |
| `Embedder` | Convert text to vectors | `embed(text) -> vector` |
| `Retriever` | Store and search vectors | `index()`, `search()` |
| `Evaluator` | Measure RAG quality | `evaluate()` |

## Example Implementations

Each interface file includes:
- Abstract base class
- Type definitions
- Example implementation (minimal)
- Notes on production considerations

## Extending the Implementation

### Adding a New Loader

```python
from interfaces.loaders import Loader, Document

class ConfluenceLoader(Loader):
    """Load documents from Confluence."""

    def __init__(self, base_url: str, api_token: str):
        self.client = ConfluenceClient(base_url, api_token)

    def load(self, source: str) -> list[Document]:
        # source = space key or page ID
        pages = self.client.get_pages(source)
        return [
            Document(
                id=page.id,
                text=page.body,
                metadata={
                    'source': 'confluence',
                    'space': page.space,
                    'title': page.title,
                    'url': page.url
                }
            )
            for page in pages
        ]
```

### Adding a New Retriever

```python
from interfaces.retrievers import Retriever, Chunk

class PineconeRetriever(Retriever):
    """Retriever using Pinecone vector database."""

    def __init__(self, index_name: str, api_key: str):
        import pinecone
        pinecone.init(api_key=api_key)
        self.index = pinecone.Index(index_name)

    def index(self, chunk: Chunk, embedding: list[float]):
        self.index.upsert([
            (chunk.id, embedding, chunk.metadata)
        ])

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict = None
    ) -> list[Chunk]:
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            filter=filters,
            include_metadata=True
        )
        return [
            Chunk(
                id=match.id,
                text=match.metadata.get('text', ''),
                metadata=match.metadata
            )
            for match in results.matches
        ]
```

## Testing Your Implementation

```python
def test_pipeline_integration():
    # Setup
    loader = MyLoader()
    chunker = MyChunker()
    embedder = MyEmbedder()
    retriever = MyRetriever()

    pipeline = RAGPipeline(loader, chunker, embedder, retriever)

    # Ingest test document
    pipeline.ingest("test_data/sample.pdf")

    # Query
    results = pipeline.query("What is the main topic?")

    # Verify
    assert len(results) > 0
    assert results[0].text is not None
```

## Next Steps

1. Review the [Architecture](./architecture.md) document
2. Explore the [interfaces](./interfaces/) directory
3. Implement interfaces for your stack
4. Connect to the evaluation framework

---

**See Also:**
- [Architecture Overview](./architecture.md)
- [Data Foundations](../03-data-foundations/)
- [Retrieval Strategies](../04-retrieval/)
- [Evaluation](../06-evaluation/)
