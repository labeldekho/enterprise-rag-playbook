# Architecture Overview

High-level architecture for enterprise RAG systems.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              RAG System                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Ingestion Pipeline                            │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │   │
│  │  │  Source  │─▶│  Loader  │─▶│ Chunker  │─▶│ Embedder │            │   │
│  │  │ Systems  │  │          │  │          │  │          │            │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └────┬─────┘            │   │
│  │                                                  │                  │   │
│  └──────────────────────────────────────────────────┼──────────────────┘   │
│                                                     ▼                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Storage Layer                                 │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │  │
│  │  │  Vector Index  │  │ Document Store │  │ Metadata Store │         │  │
│  │  │  (embeddings)  │  │  (raw chunks)  │  │  (attributes)  │         │  │
│  │  └────────────────┘  └────────────────┘  └────────────────┘         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                     ▲                       │
│  ┌──────────────────────────────────────────────────┼──────────────────┐   │
│  │                        Query Pipeline            │                   │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────┴─────┐            │   │
│  │  │  Query   │─▶│ Embedder │─▶│Retriever │─▶│ Reranker │            │   │
│  │  │          │  │          │  │          │  │          │            │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └────┬─────┘            │   │
│  │                                                  │                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │                  │   │
│  │  │ Response │◀─│Generator │◀─│ Context  │◀──────┘                  │   │
│  │  │          │  │  (LLM)   │  │ Assembly │                          │   │
│  │  └──────────┘  └──────────┘  └──────────┘                          │   │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Ingestion Pipeline

| Component | Responsibility | Interface |
|-----------|----------------|-----------|
| Loader | Fetch documents from sources | `Loader.load(source) -> [Document]` |
| Chunker | Split documents into retrievable units | `Chunker.chunk(doc) -> [Chunk]` |
| Embedder | Convert text to vector representation | `Embedder.embed(text) -> vector` |

### Storage Layer

| Component | Purpose | Technology Options |
|-----------|---------|-------------------|
| Vector Index | Fast similarity search | Pinecone, Weaviate, pgvector |
| Document Store | Original chunk content | PostgreSQL, MongoDB, S3 |
| Metadata Store | Filterable attributes | PostgreSQL, Elasticsearch |

### Query Pipeline

| Component | Responsibility | Interface |
|-----------|----------------|-----------|
| Retriever | Find relevant chunks | `Retriever.search(query, k) -> [Chunk]` |
| Reranker | Improve ranking quality | `Reranker.rerank(query, chunks) -> [Chunk]` |
| Generator | Produce final answer | `Generator.generate(query, context) -> str` |

## Data Flow

### Ingestion Flow

```python
def ingest_document(source: str):
    # 1. Load document
    document = loader.load(source)

    # 2. Chunk document
    chunks = chunker.chunk(document)

    # 3. Process each chunk
    for chunk in chunks:
        # Generate embedding
        embedding = embedder.embed(chunk.text)

        # Store in vector index
        vector_index.upsert(chunk.id, embedding)

        # Store original content
        document_store.put(chunk.id, chunk.text)

        # Store metadata
        metadata_store.put(chunk.id, chunk.metadata)
```

### Query Flow

```python
def query(question: str, user: User) -> str:
    # 1. Embed query
    query_embedding = embedder.embed(question)

    # 2. Retrieve candidates
    candidates = retriever.search(
        query_embedding,
        top_k=20,
        filters=build_access_filters(user)
    )

    # 3. Rerank (optional)
    reranked = reranker.rerank(question, candidates, top_k=5)

    # 4. Assemble context
    context = context_assembler.assemble(reranked)

    # 5. Generate response
    response = generator.generate(question, context)

    return response
```

## Interface Contracts

### Document
```python
@dataclass
class Document:
    id: str
    text: str
    metadata: dict
    source: str
```

### Chunk
```python
@dataclass
class Chunk:
    id: str
    document_id: str
    text: str
    metadata: dict
    embedding: Optional[list[float]] = None
```

### SearchResult
```python
@dataclass
class SearchResult:
    chunk: Chunk
    score: float
    rank: int
```

## Extensibility Points

### Adding New Source Types
```python
class Loader(ABC):
    @abstractmethod
    def load(self, source: str) -> list[Document]:
        pass

# Implement for new sources:
# - ConfluenceLoader
# - SharePointLoader
# - SlackLoader
# - DatabaseLoader
```

### Adding New Retrieval Strategies
```python
class Retriever(ABC):
    @abstractmethod
    def search(self, query_embedding, top_k, filters) -> list[SearchResult]:
        pass

# Implement different strategies:
# - VectorRetriever (pure vector search)
# - HybridRetriever (vector + keyword)
# - GraphRetriever (with graph traversal)
```

### Adding New Generators
```python
class Generator(ABC):
    @abstractmethod
    def generate(self, query: str, context: str) -> str:
        pass

# Implement for different providers:
# - OpenAIGenerator
# - AnthropicGenerator
# - LocalLLMGenerator
```

## Cross-Cutting Concerns

### Caching
```
┌─────────────────────────────────────────┐
│              Cache Layer                 │
├─────────────────────────────────────────┤
│  Embedding Cache  │  Result Cache       │
│  Query Cache      │  Response Cache     │
└─────────────────────────────────────────┘
```

### Monitoring
```
┌─────────────────────────────────────────┐
│            Observability                 │
├─────────────────────────────────────────┤
│  Metrics    │  Logging    │  Tracing    │
│  (latency,  │  (audit,    │  (request   │
│   costs)    │   errors)   │   flow)     │
└─────────────────────────────────────────┘
```

### Security
```
┌─────────────────────────────────────────┐
│            Security Layer                │
├─────────────────────────────────────────┤
│  AuthN/AuthZ  │  PII Filter  │  Audit   │
└─────────────────────────────────────────┘
```

## Deployment Patterns

### Simple (Single Service)
```
┌─────────────────┐
│   RAG Service   │
│  (all-in-one)   │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│VectorDB│ │  LLM  │
└───────┘ └───────┘
```

### Microservices
```
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Ingestion│  │ Retrieval│  │Generation│
│ Service  │  │ Service  │  │ Service  │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └──────┬──────┴──────┬──────┘
            ▼             ▼
      ┌──────────┐  ┌──────────┐
      │ Vector DB│  │   LLM    │
      │ Cluster  │  │ Gateway  │
      └──────────┘  └──────────┘
```

## Technology Mapping

| Component | Open Source | Managed Service |
|-----------|-------------|-----------------|
| Vector DB | Milvus, Weaviate, Chroma | Pinecone, Weaviate Cloud |
| Document Store | PostgreSQL, MongoDB | RDS, DocumentDB |
| Embeddings | Sentence Transformers | OpenAI, Cohere |
| LLM | Llama, Mistral | OpenAI, Anthropic |
| Cache | Redis | ElastiCache |
| Orchestration | Kubernetes | EKS, GKE |

---

**Next:** Review the [interface definitions](./interfaces/)
