# Vector Search

Finding similar embeddings at scale.

## How Vector Search Works

1. Query text → embedding
2. Find k nearest neighbors in vector space
3. Return most similar documents

```
Query: "How do I reset my password?"
        ↓
    [embedding]
        ↓
   Vector Index
        ↓
Top K similar chunks
```

## Vector Database Options

### Specialized Vector DBs

| Database | Hosting | Strength | Consideration |
|----------|---------|----------|---------------|
| Pinecone | Cloud | Managed, scalable | Vendor lock-in |
| Weaviate | Both | Hybrid search | Resource heavy |
| Milvus | Both | High performance | Complex setup |
| Qdrant | Both | Good filtering | Newer ecosystem |
| Chroma | Self | Simple, Python | Limited scale |

### Vector Extensions

| Database | Extension | Strength | Consideration |
|----------|-----------|----------|---------------|
| PostgreSQL | pgvector | Familiar SQL | Scale limits |
| Redis | Redis Search | Fast, in-memory | Memory cost |
| Elasticsearch | Dense vector | Existing infra | Not specialized |

### Selection Criteria

1. **Scale requirements**
   - < 100K vectors → Almost any option
   - 100K - 10M → Most options work
   - > 10M → Specialized DBs preferred

2. **Query patterns**
   - Vector only → Specialized DBs
   - Vector + filters → Check filtering support
   - Complex queries → Consider pgvector/ES

3. **Operational concerns**
   - Managed preference → Cloud options
   - Data residency → Self-hosted
   - Existing stack → Extensions

## Indexing Algorithms

### Flat (Brute Force)
- Compares query to every vector
- 100% accurate
- O(n) query time
- Only for small datasets

### IVF (Inverted File Index)
- Clusters vectors
- Searches only relevant clusters
- Trade accuracy for speed
- Good for medium datasets

```python
# Conceptual IVF
clusters = kmeans(vectors, n_clusters=100)
# At query time
nearest_clusters = find_nearest_clusters(query, n_probe=10)
candidates = get_vectors_in_clusters(nearest_clusters)
results = brute_force_search(query, candidates)
```

### HNSW (Hierarchical Navigable Small World)
- Graph-based navigation
- Fast and accurate
- Memory intensive
- Most popular choice

```
Layer 2:  A ─────────── B ─────────── C
          │                           │
Layer 1:  A ─── D ─── B ─── E ─── C
          │     │     │     │     │
Layer 0:  A─F─D─G─B─H─E─I─C─J─K─L─M
```

### Comparison

| Algorithm | Build Time | Query Time | Memory | Accuracy |
|-----------|------------|------------|--------|----------|
| Flat | O(n) | O(n) | Low | 100% |
| IVF | O(n) | O(√n) | Medium | 95-99% |
| HNSW | O(n log n) | O(log n) | High | 95-99% |

## Configuration Parameters

### HNSW Parameters

| Parameter | Description | Impact |
|-----------|-------------|--------|
| M | Connections per node | Quality ↑, Memory ↑ |
| ef_construction | Build-time search width | Quality ↑, Build time ↑ |
| ef_search | Query-time search width | Quality ↑, Query time ↑ |

**Typical values:**
- M: 16-64
- ef_construction: 100-200
- ef_search: 50-200

### IVF Parameters

| Parameter | Description | Impact |
|-----------|-------------|--------|
| nlist | Number of clusters | Granularity |
| nprobe | Clusters to search | Quality ↑, Time ↑ |

**Typical values:**
- nlist: √n to 4√n (where n = vector count)
- nprobe: 1-20% of nlist

## Query Patterns

### Basic Search
```python
results = vector_db.search(
    collection="documents",
    query_vector=embed(query_text),
    top_k=10
)
```

### Filtered Search
```python
results = vector_db.search(
    collection="documents",
    query_vector=embed(query_text),
    top_k=10,
    filter={
        "category": "technical",
        "date": {"$gte": "2024-01-01"}
    }
)
```

### Multi-Vector Search
```python
# Search with multiple query variants
results = []
for variant in query_variants:
    variant_results = vector_db.search(
        query_vector=embed(variant),
        top_k=5
    )
    results.extend(variant_results)

# Deduplicate and re-rank
final_results = dedupe_and_rank(results)
```

## Performance Tuning

### Indexing Performance

```python
# Batch insertions
vectors_batch = [
    {"id": f"doc_{i}", "vector": emb, "metadata": meta}
    for i, (emb, meta) in enumerate(zip(embeddings, metadatas))
]
vector_db.upsert(vectors_batch)  # Not one at a time
```

### Query Performance

1. **Reduce dimensions** if possible
2. **Tune ef_search** for quality/speed tradeoff
3. **Use filters effectively** (pre-filtering is faster)
4. **Cache frequent queries**

### Memory Optimization

```python
# Quantization: reduce vector precision
# 32-bit float → 8-bit int = 4x memory savings

# Product quantization
# Compress vectors by splitting and codebook lookup
```

## Monitoring

### Key Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Query latency (p50) | Median response time | < 50ms |
| Query latency (p99) | Tail latency | < 200ms |
| Recall@k | Relevant results in top k | > 95% |
| QPS | Queries per second | Depends on load |
| Index size | Storage used | Within budget |

### Health Checks
```python
def vector_db_health():
    checks = {
        'connection': test_connection(),
        'latency': measure_query_latency() < threshold,
        'collection_exists': check_collection(),
        'vector_count': get_vector_count() > 0
    }
    return all(checks.values()), checks
```

## Failure Modes

### 1. Index Corruption
**Symptom:** Search returns garbage or fails
**Prevention:** Regular backups, consistency checks
**Recovery:** Rebuild from source data

### 2. Memory Exhaustion
**Symptom:** OOM errors, slow queries
**Prevention:** Capacity planning, monitoring
**Recovery:** Scale up or reduce index size

### 3. Stale Index
**Symptom:** New documents not found
**Prevention:** Verify update pipeline
**Recovery:** Check sync status, rebuild if needed

### 4. Query Timeout
**Symptom:** Queries exceed time limit
**Prevention:** Tune parameters, add resources
**Recovery:** Reduce ef_search, add capacity

## Scaling Strategies

### Vertical Scaling
- Add more memory
- Faster CPU/GPU
- Faster storage (NVMe)

### Horizontal Scaling
- Shard by document attribute
- Shard by vector range
- Replicas for read scaling

```
┌─────────────┐
│   Router    │
└──────┬──────┘
       │
┌──────┴──────┐
│             │
▼             ▼
┌─────┐    ┌─────┐
│Shard│    │Shard│
│  1  │    │  2  │
└─────┘    └─────┘
```

## Checklist

- [ ] Vector database selected
- [ ] Index algorithm chosen (HNSW typical)
- [ ] Parameters tuned for use case
- [ ] Batch insertion implemented
- [ ] Filtering strategy defined
- [ ] Performance baselines established
- [ ] Monitoring in place
- [ ] Backup strategy defined
- [ ] Scaling plan documented

---

**Previous:** [Embeddings](./embeddings.md)
**Next:** [Hybrid Search](./hybrid-search.md)
