# Level 2: Hybrid Search RAG

When semantic search alone isn't enough.

## What Problem This Level Solves

- Users search for exact terms (product codes, IDs, names)
- Semantic search misses obvious keyword matches
- Different query types need different retrieval strategies

## Architecture

```
                                        ┌─────────────┐
                                        │    User     │
                                        │    Query    │
                                        └──────┬──────┘
                                               │
                              ┌────────────────┼────────────────┐
                              ▼                ▼                ▼
                       ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
                       │   Vector    │  │   Keyword   │  │    Query    │
                       │   Search    │  │   Search    │  │  Classifier │
                       │  (Semantic) │  │   (BM25)    │  │  (Optional) │
                       └──────┬──────┘  └──────┬──────┘  └─────────────┘
                              │                │
                              └────────┬───────┘
                                       ▼
                              ┌─────────────┐
                              │   Fusion    │
                              │  (RRF/etc)  │
                              └──────┬──────┘
                                     ▼
                              ┌─────────────┐
                              │     LLM     │
                              │  Generation │
                              └─────────────┘
```

## Components

### Keyword Search (BM25)
- Traditional full-text search
- Exact matching for codes, names, acronyms
- Elasticsearch, OpenSearch, or in-memory BM25

### Vector Search
- Same as Level 1
- Captures semantic similarity
- Handles paraphrasing, synonyms

### Fusion Strategy
**Reciprocal Rank Fusion (RRF):**
```
score(doc) = Σ 1 / (k + rank_i(doc))
```
Where k is typically 60, and rank_i is the document's rank in result list i.

**Other options:**
- Weighted linear combination
- Learn-to-rank models
- Query-dependent routing

## Data Requirements

| Requirement | Level 2 Spec |
|-------------|--------------|
| Document formats | Same as Level 1 |
| Data volume | < 100,000 documents |
| Update frequency | Near real-time possible |
| Metadata | Expanded (categories, tags) |
| Text index | Required (Elasticsearch/BM25) |

## Latency Expectations

| Operation | Typical Latency |
|-----------|-----------------|
| Query embedding | 50-100ms |
| Vector search | 10-50ms |
| Keyword search | 10-30ms |
| Fusion | 5-10ms |
| LLM generation | 500-2000ms |
| **Total** | **575-2190ms** |

Parallel execution of vector and keyword search keeps latency similar to Level 1.

## Failure Modes

### 1. Over-Reliance on Keywords
**Symptom:** Semantic matches ranked too low
**Cause:** Fusion weights favor keyword search
**Fix:** Tune fusion parameters, use query classification

### 2. Duplicate Results
**Symptom:** Same content from both search types
**Cause:** No deduplication in fusion
**Fix:** Deduplicate by document ID before fusion

### 3. Query Type Mismatch
**Symptom:** Wrong search type dominates for query
**Cause:** No query understanding
**Fix:** Add query classifier or intent detection

### 4. Index Synchronization
**Symptom:** Vector and keyword indexes disagree
**Cause:** Update pipelines not synchronized
**Fix:** Atomic updates or eventual consistency handling

## When to Stop Here

Stay at Level 2 if:
- Text-only documents
- Query complexity is moderate
- Retrieval quality meets requirements (85-90%)
- No need for image/table understanding

## When to Advance

Move to Level 3 if:
- Documents contain images, charts, tables
- Visual context matters for answers
- Users ask about diagrams or figures

## Implementation Checklist

- [ ] BM25/keyword index deployed
- [ ] Parallel search execution working
- [ ] Fusion strategy implemented and tuned
- [ ] Query classifier (optional but recommended)
- [ ] Deduplication logic in place
- [ ] Index sync pipeline reliable
- [ ] A/B testing between Level 1 and 2

## Tuning Hybrid Search

### Fusion Weight Tuning
Start with 50/50 and adjust based on query types:
- Technical docs with codes → favor keyword (60/40)
- Conceptual questions → favor semantic (40/60)

### Query Classification
Simple heuristics work well:
- Contains quotes → keyword heavy
- Contains product codes → keyword heavy
- Question words (how, why) → semantic heavy

---

**Previous:** [Level 1: Basic RAG](./level-1-basic.md)
**Next:** [Level 3: Multimodal RAG](./level-3-multimodal.md)
