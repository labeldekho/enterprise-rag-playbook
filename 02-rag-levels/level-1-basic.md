# Level 1: Basic RAG

The foundation. Get this right before moving forward.

## What Problem This Level Solves

- LLM doesn't know about your private documents
- Users need answers grounded in your data
- You need a working prototype quickly

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Document  │────▶│  Chunking   │────▶│  Embedding  │
│   Ingestion │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│     LLM     │◀────│   Prompt    │◀────│   Vector    │
│  Generation │     │  Assembly   │     │   Search    │
└─────────────┘     └─────────────┘     └─────────────┘
                                               ▲
                                               │
                                        ┌─────────────┐
                                        │    User     │
                                        │    Query    │
                                        └─────────────┘
```

## Components

### Document Ingestion
- Load documents from files, URLs, or databases
- Parse different formats (PDF, DOCX, HTML, TXT)
- Extract clean text

### Chunking
- Split documents into smaller pieces
- Fixed-size chunks (e.g., 512 tokens)
- Overlap between chunks (e.g., 50 tokens)

### Embedding
- Convert chunks to vectors
- Single embedding model (e.g., OpenAI ada-002, all-MiniLM)
- Store in vector database

### Retrieval
- Embed user query
- Find top-k similar chunks
- Return as context

### Generation
- Combine query + retrieved chunks
- Send to LLM
- Return answer

## Data Requirements

| Requirement | Level 1 Spec |
|-------------|--------------|
| Document formats | Text-based (PDF, DOCX, TXT) |
| Data volume | < 10,000 documents |
| Update frequency | Batch (daily/weekly) |
| Metadata | Minimal (source, date) |

## Latency Expectations

| Operation | Typical Latency |
|-----------|-----------------|
| Embedding query | 50-100ms |
| Vector search | 10-50ms |
| LLM generation | 500-2000ms |
| **Total** | **600-2200ms** |

## Failure Modes

### 1. Poor Chunk Boundaries
**Symptom:** Answers are fragmented or miss context
**Cause:** Chunks split mid-sentence or mid-concept
**Fix:** Use semantic chunking or larger overlap

### 2. Irrelevant Retrieval
**Symptom:** Retrieved chunks don't answer the question
**Cause:** Embedding model mismatch or poor query
**Fix:** Try different embedding models, query reformulation

### 3. Lost in the Middle
**Symptom:** Model ignores retrieved context
**Cause:** Important info buried in middle of prompt
**Fix:** Reorder chunks, use explicit instructions

### 4. Hallucination Despite Context
**Symptom:** Model makes up facts not in retrieved chunks
**Cause:** Insufficient instruction, model override
**Fix:** Stronger system prompts, temperature reduction

## When to Stop Here

Stay at Level 1 if:
- Queries are simple, single-intent
- Document corpus is homogeneous
- Accuracy requirements are moderate (80-85%)
- Team is learning RAG patterns

## When to Advance

Move to Level 2 if:
- Keyword searches would help (product codes, names)
- Retrieval quality is limiting answer quality
- Users report "can't find obvious things"

## Implementation Checklist

- [ ] Document loader working for primary formats
- [ ] Chunking strategy defined and tested
- [ ] Embedding model selected
- [ ] Vector database deployed
- [ ] Basic retrieval pipeline functional
- [ ] Prompt template defined
- [ ] End-to-end test passing
- [ ] Basic evaluation metrics in place

## Code Patterns

See [Reference Implementation](../09-reference-implementation/README.md) for:
- `Loader` interface
- `Chunker` interface
- `Embedder` interface
- `Retriever` interface

---

**Next:** [Level 2: Hybrid Search](./level-2-hybrid.md)
