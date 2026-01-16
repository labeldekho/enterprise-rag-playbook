# Reranking

Improving retrieval quality with a second-pass ranker.

## What Is Reranking?

Reranking is a two-stage retrieval approach:
1. **First stage:** Fast retrieval (vector/keyword) gets candidates
2. **Second stage:** Expensive model scores and reorders candidates

```
Query → Fast Retrieval (top 100) → Reranker → Final Results (top 10)
              ~50ms                    ~200ms
```

## Why Rerank?

### Embedding Limitations
- Bi-encoders encode query and document separately
- No cross-attention between query and document
- May miss nuanced relevance

### Reranker Advantages
- Cross-encoder sees query + document together
- Full attention between all tokens
- Much higher accuracy

```
Bi-encoder (embedding):
  Query  →  [Encoder]  →  embedding_q
  Doc    →  [Encoder]  →  embedding_d
  Score = similarity(embedding_q, embedding_d)

Cross-encoder (reranker):
  [Query, Doc] →  [Encoder]  →  relevance_score
```

## Reranking Models

### Commercial APIs

| Provider | Model | Strength |
|----------|-------|----------|
| Cohere | rerank-v3 | Production-ready, fast |
| Voyage AI | rerank-1 | Technical content |
| Jina AI | jina-reranker | Multilingual |

### Open Source

| Model | Size | Strength |
|-------|------|----------|
| bge-reranker-large | 560M | Strong general purpose |
| ms-marco-MiniLM | 22M | Fast, lightweight |
| cross-encoder/ms-marco-electra | 110M | Good balance |

## Implementation

### Basic Reranking
```python
def rerank(query, documents, top_k=10):
    """
    Rerank documents using a cross-encoder.
    """
    # Score each document
    scores = []
    for doc in documents:
        score = reranker.score(query, doc.text)
        scores.append((doc, score))

    # Sort by score descending
    scores.sort(key=lambda x: x[1], reverse=True)

    # Return top k
    return [doc for doc, score in scores[:top_k]]
```

### With Cohere API
```python
import cohere

co = cohere.Client(api_key)

def rerank_cohere(query, documents, top_k=10):
    response = co.rerank(
        model="rerank-english-v3.0",
        query=query,
        documents=[doc.text for doc in documents],
        top_n=top_k
    )

    reranked = []
    for result in response.results:
        reranked.append({
            'document': documents[result.index],
            'score': result.relevance_score
        })
    return reranked
```

### With Sentence Transformers
```python
from sentence_transformers import CrossEncoder

model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def rerank_local(query, documents, top_k=10):
    # Prepare pairs
    pairs = [[query, doc.text] for doc in documents]

    # Score all pairs
    scores = model.predict(pairs)

    # Sort and return top k
    doc_scores = list(zip(documents, scores))
    doc_scores.sort(key=lambda x: x[1], reverse=True)
    return doc_scores[:top_k]
```

## Pipeline Integration

### Full Retrieval Pipeline
```python
class RetrievalPipeline:
    def __init__(self, retriever, reranker, retrieval_k=100, final_k=10):
        self.retriever = retriever
        self.reranker = reranker
        self.retrieval_k = retrieval_k
        self.final_k = final_k

    def search(self, query):
        # Stage 1: Fast retrieval
        candidates = self.retriever.search(query, top_k=self.retrieval_k)

        # Stage 2: Rerank
        if len(candidates) > self.final_k:
            results = self.reranker.rerank(
                query,
                candidates,
                top_k=self.final_k
            )
        else:
            results = candidates

        return results
```

### With Caching
```python
def cached_rerank(query, documents, cache, top_k=10):
    # Check cache for each query-doc pair
    to_score = []
    cached_scores = {}

    for doc in documents:
        cache_key = f"{hash(query)}:{hash(doc.text)}"
        if cache_key in cache:
            cached_scores[doc.id] = cache[cache_key]
        else:
            to_score.append(doc)

    # Score uncached documents
    if to_score:
        new_scores = reranker.batch_score(query, to_score)
        for doc, score in zip(to_score, new_scores):
            cache_key = f"{hash(query)}:{hash(doc.text)}"
            cache[cache_key] = score
            cached_scores[doc.id] = score

    # Combine and sort
    all_docs = [(doc, cached_scores[doc.id]) for doc in documents]
    all_docs.sort(key=lambda x: x[1], reverse=True)
    return all_docs[:top_k]
```

## Performance Optimization

### Batch Processing
```python
# Slow: one at a time
for doc in documents:
    score = model.predict([[query, doc.text]])[0]

# Fast: batch all at once
pairs = [[query, doc.text] for doc in documents]
scores = model.predict(pairs, batch_size=32)
```

### Truncation
```python
def truncate_for_reranker(text, max_tokens=512):
    """
    Rerankers have token limits.
    Truncate intelligently.
    """
    tokens = tokenizer.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return tokenizer.decode(tokens[:max_tokens])
```

### Parallel Processing
```python
from concurrent.futures import ThreadPoolExecutor

def parallel_rerank(query, documents, num_workers=4):
    def score_batch(batch):
        pairs = [[query, doc.text] for doc in batch]
        return model.predict(pairs)

    # Split into batches
    batch_size = len(documents) // num_workers
    batches = [documents[i:i+batch_size]
               for i in range(0, len(documents), batch_size)]

    # Score in parallel
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(score_batch, batches))

    # Flatten and combine
    all_scores = [score for batch_scores in results for score in batch_scores]
    return list(zip(documents, all_scores))
```

## Latency Considerations

### Latency Budget
```
Total RAG latency budget: 2000ms
- Embedding: 50ms
- Vector search: 50ms
- Reranking: 200ms (budget)
- LLM generation: 1500ms
- Other: 200ms

With 200ms for reranking:
- API call: ~100-150ms
- Local model: ~50-200ms depending on batch size
- GPU local: ~20-50ms
```

### Candidates vs Latency Tradeoff
| Candidates | Typical Latency | Quality |
|------------|-----------------|---------|
| 20 | 50-100ms | Good |
| 50 | 100-200ms | Better |
| 100 | 200-400ms | Best |
| 200+ | 400ms+ | Diminishing returns |

## Evaluation

### Reranker Quality Metrics
```python
def evaluate_reranker(test_set, retriever, reranker):
    """
    Compare retrieval with and without reranking.
    """
    results = {
        'without_rerank': {'mrr': [], 'recall': []},
        'with_rerank': {'mrr': [], 'recall': []}
    }

    for query, relevant_docs in test_set:
        # Without reranking
        retrieved = retriever.search(query, top_k=10)
        results['without_rerank']['mrr'].append(
            calculate_mrr(retrieved, relevant_docs)
        )

        # With reranking
        candidates = retriever.search(query, top_k=100)
        reranked = reranker.rerank(query, candidates, top_k=10)
        results['with_rerank']['mrr'].append(
            calculate_mrr(reranked, relevant_docs)
        )

    return {
        'without': np.mean(results['without_rerank']['mrr']),
        'with': np.mean(results['with_rerank']['mrr'])
    }
```

## When to Use Reranking

### Good Fit
- Quality is critical
- Latency budget allows 100-300ms
- First-stage retrieval has room for improvement
- High-stakes applications

### Skip If
- Latency is very tight (< 100ms total)
- First-stage retrieval is already excellent
- Cost constraints (API rerankers add up)
- Simple queries with obvious matches

## Common Pitfalls

### 1. Too Few Candidates
**Problem:** Reranker can't find good docs if they weren't retrieved
**Fix:** Increase first-stage retrieval k

### 2. Token Truncation
**Problem:** Important info at end of doc gets cut off
**Fix:** Smart truncation, multiple passages

### 3. Ignoring Reranker Limits
**Problem:** Batch size or rate limits exceeded
**Fix:** Implement proper batching and rate limiting

### 4. No Fallback
**Problem:** Reranker failure breaks pipeline
**Fix:** Fall back to first-stage results

## Checklist

- [ ] Reranking model selected
- [ ] Integration with retrieval pipeline
- [ ] Batch processing implemented
- [ ] Token truncation handled
- [ ] Caching strategy (optional)
- [ ] Latency monitoring
- [ ] Quality evaluation vs baseline
- [ ] Fallback handling
- [ ] Cost monitoring (if API)

---

**Previous:** [Graph RAG](./graph-rag.md)
**Next:** [Memory and Context](../05-memory-and-context/context-windows.md)
