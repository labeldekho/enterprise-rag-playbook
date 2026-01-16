# Hybrid Search

Combining semantic and keyword search for better retrieval.

## Why Hybrid Search?

### Vector Search Limitations
- Misses exact matches (product codes, IDs)
- Can retrieve semantically similar but wrong results
- Struggles with rare terms and proper nouns

### Keyword Search Limitations
- Misses synonyms and paraphrases
- No understanding of meaning
- Exact match or nothing

### Hybrid Advantage
```
Query: "Error 404 in user authentication module"

Vector search finds:
  - "Authentication failures and error handling"
  - "User login troubleshooting guide"

Keyword search finds:
  - "Error code 404: page not found"
  - "Module authentication: error 404 fix"

Hybrid finds the best of both.
```

## Hybrid Search Architecture

```
                 ┌─────────────────┐
                 │      Query      │
                 └────────┬────────┘
                          │
           ┌──────────────┴──────────────┐
           ▼                              ▼
    ┌─────────────┐                ┌─────────────┐
    │   Vector    │                │   Keyword   │
    │   Search    │                │   Search    │
    │  (Semantic) │                │   (BM25)    │
    └──────┬──────┘                └──────┬──────┘
           │                              │
           │    ┌─────────────────┐      │
           └───▶│     Fusion      │◀─────┘
                │   Algorithm     │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  Ranked Results │
                └─────────────────┘
```

## Fusion Algorithms

### Reciprocal Rank Fusion (RRF)

Most common and effective approach:

```python
def reciprocal_rank_fusion(result_lists, k=60):
    """
    Combine multiple ranked lists using RRF.

    score(doc) = Σ 1 / (k + rank_i(doc))

    k=60 is standard, prevents top results from dominating
    """
    scores = defaultdict(float)

    for result_list in result_lists:
        for rank, doc in enumerate(result_list):
            scores[doc.id] += 1.0 / (k + rank + 1)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

**Pros:**
- Simple and effective
- No training required
- Works with any number of lists

**Cons:**
- Ignores actual scores
- Fixed weighting between sources

### Weighted Linear Combination

Combine normalized scores with weights:

```python
def weighted_combination(vector_results, keyword_results, vector_weight=0.5):
    """
    Combine results using weighted scores.
    Requires score normalization first.
    """
    keyword_weight = 1 - vector_weight

    # Normalize scores to [0, 1]
    vector_scores = normalize_scores(vector_results)
    keyword_scores = normalize_scores(keyword_results)

    combined = {}
    for doc_id, score in vector_scores.items():
        combined[doc_id] = score * vector_weight

    for doc_id, score in keyword_scores.items():
        if doc_id in combined:
            combined[doc_id] += score * keyword_weight
        else:
            combined[doc_id] = score * keyword_weight

    return sorted(combined.items(), key=lambda x: x[1], reverse=True)
```

**Pros:**
- Uses actual relevance scores
- Tunable weights

**Cons:**
- Needs score normalization
- Requires weight tuning

### Convex Combination (Weaviate Style)

```python
def convex_combination(vector_score, keyword_score, alpha=0.5):
    """
    alpha * vector_score + (1 - alpha) * keyword_score

    alpha = 1.0 → pure vector
    alpha = 0.0 → pure keyword
    alpha = 0.5 → equal weight
    """
    return alpha * vector_score + (1 - alpha) * keyword_score
```

## Query-Dependent Weighting

Different queries benefit from different weights:

```python
def adaptive_weights(query):
    """
    Adjust weights based on query characteristics.
    """
    # Queries with codes/IDs → favor keyword
    if contains_code_pattern(query):
        return {'vector': 0.3, 'keyword': 0.7}

    # Questions (how, why, what) → favor semantic
    if starts_with_question_word(query):
        return {'vector': 0.7, 'keyword': 0.3}

    # Quoted terms → favor keyword for quotes
    if contains_quotes(query):
        return {'vector': 0.4, 'keyword': 0.6}

    # Default balanced
    return {'vector': 0.5, 'keyword': 0.5}
```

## Implementation Approaches

### Separate Indexes

```python
class HybridRetriever:
    def __init__(self, vector_db, keyword_index):
        self.vector_db = vector_db
        self.keyword_index = keyword_index

    def search(self, query, top_k=10):
        # Parallel execution
        with ThreadPoolExecutor() as executor:
            vector_future = executor.submit(
                self.vector_db.search, embed(query), top_k * 2
            )
            keyword_future = executor.submit(
                self.keyword_index.search, query, top_k * 2
            )

        vector_results = vector_future.result()
        keyword_results = keyword_future.result()

        return reciprocal_rank_fusion(
            [vector_results, keyword_results]
        )[:top_k]
```

### Integrated Database

Some databases support hybrid natively:

```python
# Weaviate example
client.query.get("Document", ["content", "metadata"]) \
    .with_hybrid(query="user authentication error", alpha=0.5) \
    .with_limit(10) \
    .do()

# Elasticsearch with dense vectors
{
    "query": {
        "bool": {
            "should": [
                {"match": {"content": "user authentication error"}},
                {"knn": {
                    "field": "embedding",
                    "query_vector": embed("user authentication error"),
                    "k": 10
                }}
            ]
        }
    }
}
```

## BM25 Tuning

BM25 is the standard keyword scoring algorithm:

```
score(D,Q) = Σ IDF(qi) · (f(qi,D) · (k1 + 1)) / (f(qi,D) + k1 · (1 - b + b · |D|/avgdl))
```

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| k1 | Term frequency saturation | 1.2 - 2.0 |
| b | Length normalization | 0.75 |

### When to Adjust

- **Long documents:** Increase b (more length normalization)
- **Short queries:** Decrease k1 (less term frequency impact)
- **Technical content:** Lower b (don't over-penalize long docs)

## Deduplication

Hybrid search can return duplicates:

```python
def deduplicate_results(results):
    """
    Remove duplicate documents, keeping highest score.
    """
    seen = {}
    for result in results:
        doc_id = result['id']
        if doc_id not in seen or result['score'] > seen[doc_id]['score']:
            seen[doc_id] = result
    return list(seen.values())
```

## Database Support Matrix

| Database | Vector Search | Keyword Search | Native Hybrid |
|----------|--------------|----------------|---------------|
| Weaviate | ✓ | ✓ | ✓ |
| Pinecone | ✓ | ✓ (sparse) | ✓ |
| Qdrant | ✓ | ✓ | ✓ |
| Elasticsearch | ✓ | ✓ | Manual |
| pgvector | ✓ | ✓ (pg FTS) | Manual |
| Milvus | ✓ | ✓ | ✓ |

## Performance Considerations

### Latency
```
Parallel execution:
  max(vector_time, keyword_time) + fusion_time
  ≈ 50-100ms + 10ms = 60-110ms

Sequential execution:
  vector_time + keyword_time + fusion_time
  ≈ 50ms + 50ms + 10ms = 110ms
```

### Resource Usage
- Two indexes = ~2x storage
- Two queries = ~2x compute
- Fusion = minimal overhead

## When to Use Hybrid

### Good Fit
- Mixed query types (conceptual + exact)
- Technical documentation
- E-commerce (product names + descriptions)
- Support tickets (error codes + descriptions)

### Maybe Skip
- Pure semantic search (no exact matches needed)
- Very simple queries
- Latency critical (adds complexity)
- Limited resources (2x cost)

## Checklist

- [ ] Keyword index deployed (Elasticsearch, BM25)
- [ ] Vector index deployed
- [ ] Fusion algorithm implemented
- [ ] Parallel query execution
- [ ] Deduplication logic
- [ ] Weight tuning based on query analysis
- [ ] A/B testing vs pure vector
- [ ] Latency monitoring
- [ ] Relevance testing

---

**Previous:** [Vector Search](./vector-search.md)
**Next:** [Graph RAG](./graph-rag.md)
