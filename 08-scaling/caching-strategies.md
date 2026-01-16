# Caching Strategies

Reducing latency and cost through intelligent caching.

## Why Cache in RAG?

| Without Caching | With Caching |
|-----------------|--------------|
| Every query hits vector DB | Repeated queries served instantly |
| Every query calls embedding API | Embeddings reused |
| Every query calls LLM | Similar answers reused |
| Higher costs | Reduced API costs |
| Higher latency | Lower latency |

## What to Cache

### 1. Query Embeddings

```python
class EmbeddingCache:
    def __init__(self, cache_backend, ttl_seconds=3600):
        self.cache = cache_backend
        self.ttl = ttl_seconds

    def get_embedding(self, text):
        cache_key = f"emb:{hash_text(text)}"

        # Check cache
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # Generate and cache
        embedding = embed(text)
        self.cache.set(cache_key, embedding, ttl=self.ttl)
        return embedding
```

**Cache hit rate:** 30-60% for typical workloads
**Savings:** Embedding API costs, 50-100ms per hit

### 2. Retrieval Results

```python
class RetrievalCache:
    def __init__(self, cache_backend, ttl_seconds=300):
        self.cache = cache_backend
        self.ttl = ttl_seconds

    def search(self, query, filters, top_k):
        # Create cache key from query parameters
        cache_key = f"search:{hash_text(query)}:{hash_dict(filters)}:{top_k}"

        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # Perform search
        results = self.vector_db.search(query, filters, top_k)

        # Cache results
        self.cache.set(cache_key, results, ttl=self.ttl)
        return results
```

**Cache hit rate:** 20-40% for typical workloads
**Savings:** Vector DB load, 20-100ms per hit

### 3. LLM Responses (Semantic Cache)

```python
class SemanticCache:
    def __init__(self, cache_db, similarity_threshold=0.95):
        self.cache_db = cache_db
        self.threshold = similarity_threshold

    def get_or_generate(self, query, context, generate_fn):
        # Embed the query
        query_embedding = embed(query)

        # Search for similar cached queries
        similar = self.cache_db.search(
            query_embedding,
            top_k=1,
            filter={"context_hash": hash_text(context)}
        )

        if similar and similar[0].score >= self.threshold:
            return similar[0].metadata['response']

        # Generate new response
        response = generate_fn(query, context)

        # Cache for future
        self.cache_db.upsert({
            'id': generate_id(),
            'vector': query_embedding,
            'metadata': {
                'query': query,
                'context_hash': hash_text(context),
                'response': response,
                'created_at': datetime.utcnow()
            }
        })

        return response
```

**Cache hit rate:** 10-30% (depends on query diversity)
**Savings:** LLM costs, 500-2000ms per hit

### 4. Document Chunks

```python
class ChunkCache:
    def __init__(self, cache_backend):
        self.cache = cache_backend

    def get_chunks(self, document_ids):
        # Try cache first
        cached = {}
        missing = []

        for doc_id in document_ids:
            chunk = self.cache.get(f"chunk:{doc_id}")
            if chunk:
                cached[doc_id] = chunk
            else:
                missing.append(doc_id)

        # Fetch missing from database
        if missing:
            fetched = self.db.get_chunks(missing)
            for doc_id, chunk in fetched.items():
                self.cache.set(f"chunk:{doc_id}", chunk)
                cached[doc_id] = chunk

        return cached
```

## Cache Architecture

### Single-Layer Cache

```
Request → Cache → Miss? → Backend → Response
              ↓
            Hit → Response
```

### Multi-Layer Cache

```
Request → L1 (Local) → L2 (Redis) → Backend
              ↓              ↓
            Hit            Hit
              ↓              ↓
          Response      Response
```

```python
class MultiLayerCache:
    def __init__(self, l1_cache, l2_cache):
        self.l1 = l1_cache  # Local in-memory
        self.l2 = l2_cache  # Redis/Memcached

    def get(self, key):
        # Check L1
        value = self.l1.get(key)
        if value:
            return value

        # Check L2
        value = self.l2.get(key)
        if value:
            self.l1.set(key, value)  # Populate L1
            return value

        return None

    def set(self, key, value, ttl=None):
        self.l1.set(key, value, ttl=min(ttl, 60))  # Short L1 TTL
        self.l2.set(key, value, ttl=ttl)
```

## Cache Invalidation

### Time-Based (TTL)
```python
# Simple but may serve stale data
cache.set(key, value, ttl=300)  # 5 minutes
```

### Event-Based
```python
class EventDrivenCache:
    def __init__(self, cache, event_bus):
        self.cache = cache
        event_bus.subscribe('document.updated', self.invalidate_document)
        event_bus.subscribe('document.deleted', self.invalidate_document)

    def invalidate_document(self, event):
        document_id = event['document_id']

        # Invalidate chunk cache
        self.cache.delete(f"chunk:{document_id}")

        # Invalidate any search results containing this document
        # (This is harder - may need to scan or use tags)
        self.cache.delete_by_tag(f"contains:{document_id}")
```

### Version-Based
```python
class VersionedCache:
    def __init__(self, cache, version_store):
        self.cache = cache
        self.versions = version_store

    def get(self, key, current_version):
        cached = self.cache.get(key)
        if cached and cached['version'] == current_version:
            return cached['value']
        return None

    def set(self, key, value, version):
        self.cache.set(key, {
            'value': value,
            'version': version
        })
```

## Cache Sizing

### Memory Estimation
```python
def estimate_cache_size(config):
    # Embedding cache
    embedding_size = config['embedding_dim'] * 4  # float32
    embedding_cache = config['unique_queries'] * embedding_size

    # Retrieval cache
    result_size = config['top_k'] * config['avg_chunk_size']
    retrieval_cache = config['unique_queries'] * result_size

    # Semantic cache
    semantic_cache = config['cached_responses'] * config['avg_response_size']

    return {
        'embedding_cache_mb': embedding_cache / 1024 / 1024,
        'retrieval_cache_mb': retrieval_cache / 1024 / 1024,
        'semantic_cache_mb': semantic_cache / 1024 / 1024,
        'total_mb': (embedding_cache + retrieval_cache + semantic_cache) / 1024 / 1024
    }
```

### Eviction Policies

| Policy | Description | Best For |
|--------|-------------|----------|
| LRU | Least Recently Used | General purpose |
| LFU | Least Frequently Used | Stable query patterns |
| TTL | Time-based expiration | Fresh data requirements |
| FIFO | First In First Out | Simple, predictable |

## Implementation Examples

### Redis Cache
```python
import redis
import json

class RedisCache:
    def __init__(self, host='localhost', port=6379):
        self.client = redis.Redis(host=host, port=port)

    def get(self, key):
        value = self.client.get(key)
        if value:
            return json.loads(value)
        return None

    def set(self, key, value, ttl=None):
        serialized = json.dumps(value)
        if ttl:
            self.client.setex(key, ttl, serialized)
        else:
            self.client.set(key, serialized)

    def delete(self, key):
        self.client.delete(key)
```

### In-Memory Cache with LRU
```python
from functools import lru_cache
from cachetools import TTLCache

class InMemoryCache:
    def __init__(self, maxsize=10000, ttl=300):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value, ttl=None):
        self.cache[key] = value

    def delete(self, key):
        self.cache.pop(key, None)
```

## Monitoring Cache Performance

### Key Metrics
```python
class CacheMetrics:
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.latency_sum = 0
        self.latency_count = 0

    def record_hit(self, latency_ms):
        self.hits += 1
        self.latency_sum += latency_ms
        self.latency_count += 1

    def record_miss(self, latency_ms):
        self.misses += 1
        self.latency_sum += latency_ms
        self.latency_count += 1

    def get_stats(self):
        total = self.hits + self.misses
        return {
            'hit_rate': self.hits / total if total > 0 else 0,
            'miss_rate': self.misses / total if total > 0 else 0,
            'avg_latency_ms': self.latency_sum / self.latency_count if self.latency_count > 0 else 0,
            'total_requests': total
        }
```

### Alerting
```python
CACHE_ALERTS = {
    'low_hit_rate': {
        'condition': lambda stats: stats['hit_rate'] < 0.3,
        'message': 'Cache hit rate below 30%'
    },
    'high_latency': {
        'condition': lambda stats: stats['avg_latency_ms'] > 100,
        'message': 'Cache latency above 100ms'
    }
}
```

## Cache Warming

### Pre-populate cache on startup:
```python
async def warm_cache(cache, common_queries):
    """
    Pre-populate cache with common queries.
    """
    for query in common_queries:
        embedding = await embed_async(query)
        cache.set(f"emb:{hash_text(query)}", embedding)

        results = await search_async(embedding)
        cache.set(f"search:{hash_text(query)}", results)

    logger.info(f"Warmed cache with {len(common_queries)} queries")
```

### Background refresh:
```python
async def background_refresh(cache, key, refresh_fn, ttl):
    """
    Refresh cache entry before expiration.
    """
    while True:
        await asyncio.sleep(ttl * 0.8)  # Refresh at 80% of TTL
        try:
            new_value = await refresh_fn()
            cache.set(key, new_value, ttl=ttl)
        except Exception as e:
            logger.error(f"Cache refresh failed: {e}")
```

## Checklist

- [ ] Cache layers identified (embedding, retrieval, response)
- [ ] Cache backend selected (Redis, Memcached, in-memory)
- [ ] TTLs configured appropriately
- [ ] Invalidation strategy implemented
- [ ] Cache size estimated and provisioned
- [ ] Eviction policy chosen
- [ ] Cache warming implemented
- [ ] Monitoring and alerting set up
- [ ] Hit rate baseline established

---

**Previous:** [Sharding and Replication](./sharding-and-replication.md)
**Next:** [Cost Optimization](./cost-optimization.md)
