# Embeddings

Converting text to numbers that capture meaning.

## What Are Embeddings?

Embeddings are dense vector representations of text where:
- Similar meanings → similar vectors
- Semantic relationships preserved
- Enable mathematical similarity comparisons

```
"The cat sat on the mat"  →  [0.12, -0.34, 0.87, ..., 0.23]  (768 dimensions)
"A feline rested on a rug" →  [0.11, -0.32, 0.85, ..., 0.25]  (similar vector)
"Stock prices rose today"  →  [-0.45, 0.67, 0.12, ..., -0.89]  (different vector)
```

## Embedding Model Selection

### Key Properties

| Property | Description | Impact |
|----------|-------------|--------|
| Dimensions | Vector size (384-3072) | Storage, speed, quality |
| Max tokens | Input length limit | Chunk size constraints |
| Training data | What it learned from | Domain fit |
| Multilingual | Language support | International use |

### Popular Models Comparison

| Model | Dimensions | Max Tokens | Strength |
|-------|------------|------------|----------|
| OpenAI text-embedding-3-small | 1536 | 8191 | Good balance |
| OpenAI text-embedding-3-large | 3072 | 8191 | Highest quality |
| Cohere embed-v3 | 1024 | 512 | Multilingual |
| Voyage AI voyage-2 | 1024 | 4000 | Technical content |
| BGE-large-en-v1.5 | 1024 | 512 | Open source |
| all-MiniLM-L6-v2 | 384 | 256 | Fast, lightweight |
| e5-large-v2 | 1024 | 512 | Open source, strong |

### Selection Criteria

1. **Domain match**
   - General text → General models
   - Code → Code-trained models
   - Scientific → Scientific models

2. **Language requirements**
   - English only → English-optimized
   - Multilingual → Multilingual models

3. **Latency requirements**
   - Real-time → Smaller models
   - Batch → Larger models acceptable

4. **Cost constraints**
   - High volume → Open source or smaller models
   - Quality critical → Premium APIs

## Embedding Quality

### What Makes Good Embeddings?

1. **Semantic accuracy:** Similar meanings cluster together
2. **Discrimination:** Different meanings are far apart
3. **Consistency:** Same text → same embedding (deterministic)
4. **Coverage:** Handles your vocabulary/domain

### Testing Embedding Quality

```python
def test_embedding_quality(model, test_pairs):
    """
    test_pairs = [
        (query, relevant_doc, irrelevant_doc),
        ...
    ]
    """
    correct = 0
    for query, relevant, irrelevant in test_pairs:
        q_emb = model.embed(query)
        r_emb = model.embed(relevant)
        i_emb = model.embed(irrelevant)

        rel_sim = cosine_similarity(q_emb, r_emb)
        irr_sim = cosine_similarity(q_emb, i_emb)

        if rel_sim > irr_sim:
            correct += 1

    return correct / len(test_pairs)
```

## Embedding Strategies

### Document vs Query Embeddings

Some models use different embeddings for documents and queries:

```python
# Asymmetric embedding (e.g., e5, Instructor)
doc_embedding = model.embed("passage: " + document_text)
query_embedding = model.embed("query: " + query_text)

# Symmetric embedding (e.g., OpenAI, MiniLM)
doc_embedding = model.embed(document_text)
query_embedding = model.embed(query_text)
```

### Instruction-Following Embeddings

Some models accept task instructions:

```python
# Instructor model
embedding = model.embed(
    text="Company quarterly revenue was $5.2B",
    instruction="Represent the financial statement for retrieval"
)
```

### Chunked Document Embedding

```python
def embed_document(document, chunk_size=512, overlap=50):
    chunks = chunk_text(document.text, chunk_size, overlap)
    embeddings = []

    for i, chunk in enumerate(chunks):
        embedding = model.embed(chunk)
        embeddings.append({
            'chunk_id': f"{document.id}_chunk_{i}",
            'text': chunk,
            'embedding': embedding,
            'metadata': {
                'document_id': document.id,
                'chunk_index': i,
                **document.metadata
            }
        })

    return embeddings
```

## Similarity Metrics

### Cosine Similarity
Most common for normalized embeddings:
```python
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```
Range: [-1, 1], where 1 = identical direction

### Euclidean Distance
Raw distance between vectors:
```python
def euclidean_distance(a, b):
    return np.linalg.norm(a - b)
```
Range: [0, ∞), where 0 = identical

### Dot Product
For pre-normalized vectors:
```python
def dot_product(a, b):
    return np.dot(a, b)
```
Range: [-∞, ∞], higher = more similar

### Which to Use?

| Metric | When to Use |
|--------|-------------|
| Cosine | Most cases, normalized vectors |
| Euclidean | When magnitude matters |
| Dot product | Pre-normalized, speed critical |

## Performance Optimization

### Batching
```python
# Slow: one at a time
for text in texts:
    embedding = model.embed(text)

# Fast: batch processing
embeddings = model.embed_batch(texts, batch_size=32)
```

### Caching
```python
import hashlib

def cached_embed(text, cache):
    key = hashlib.sha256(text.encode()).hexdigest()
    if key in cache:
        return cache[key]
    embedding = model.embed(text)
    cache[key] = embedding
    return embedding
```

### Dimension Reduction
For storage/speed tradeoff:
```python
# OpenAI supports native dimension reduction
embedding = client.embeddings.create(
    model="text-embedding-3-large",
    input=text,
    dimensions=256  # Reduced from 3072
)
```

## Common Pitfalls

### 1. Model Mismatch
**Problem:** Different models for indexing vs querying
**Fix:** Always use the same model for both

### 2. Token Truncation
**Problem:** Long text silently truncated
**Fix:** Check input length, chunk appropriately

### 3. Empty/Short Text
**Problem:** Poor embeddings for very short text
**Fix:** Minimum text length checks, context padding

### 4. Not Normalizing
**Problem:** Inconsistent similarity scores
**Fix:** Normalize vectors or use cosine similarity

### 5. Ignoring Model Updates
**Problem:** Model version changes break retrieval
**Fix:** Pin model versions, re-embed on model change

## Embedding Infrastructure

### Self-Hosted
- Sentence Transformers (Python)
- Text Embeddings Inference (Docker)
- ONNX Runtime for speed

### Cloud APIs
- OpenAI Embeddings API
- Cohere Embed API
- Google Vertex AI
- AWS Bedrock

### Decision Factors

| Factor | Self-Hosted | Cloud API |
|--------|-------------|-----------|
| Latency | Can be lower | Network overhead |
| Cost at scale | Lower | Higher |
| Privacy | Full control | Data leaves premises |
| Maintenance | Your responsibility | Managed |
| Quality | Model-dependent | Often better |

## Checklist

- [ ] Embedding model selected based on domain and requirements
- [ ] Quality tested on representative queries
- [ ] Batch processing implemented
- [ ] Caching strategy in place
- [ ] Model version pinned
- [ ] Dimension size appropriate for storage
- [ ] Same model used for documents and queries
- [ ] Token limits understood and handled

---

**Previous:** [Update Pipelines](../03-data-foundations/update-pipelines.md)
**Next:** [Vector Search](./vector-search.md)
