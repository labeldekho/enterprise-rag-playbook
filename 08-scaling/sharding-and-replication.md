# Sharding and Replication

Scaling RAG for millions of documents and queries.

## When to Scale

### Signs You Need to Scale

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Slow queries (> 500ms) | Index too large | Sharding |
| High error rate under load | Insufficient capacity | Replication |
| Memory pressure | Index doesn't fit | Sharding |
| Uneven load | Hot partitions | Better sharding |

### Scale Thresholds

| Metric | Single Node | Time to Consider Scaling |
|--------|-------------|--------------------------|
| Vectors | < 5M | > 1M |
| QPS | < 100 | > 50 |
| Index size | < 50GB | > 20GB |
| Latency p99 | < 200ms | > 100ms |

## Sharding Strategies

### What Is Sharding?

Splitting data across multiple nodes:

```
┌─────────────────────────────────────────────────────┐
│                    Full Index                        │
│                   (10M vectors)                      │
└─────────────────────────────────────────────────────┘
                         │
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
    ┌───────────┐  ┌───────────┐  ┌───────────┐
    │  Shard 1  │  │  Shard 2  │  │  Shard 3  │
    │ 3.3M vec  │  │ 3.3M vec  │  │ 3.3M vec  │
    └───────────┘  └───────────┘  └───────────┘
```

### Sharding by Document Attribute

Partition by a meaningful attribute:

```python
def get_shard_by_attribute(document, attribute='department'):
    """
    Route documents to shards based on attribute.
    """
    shard_mapping = {
        'engineering': 'shard_1',
        'sales': 'shard_2',
        'hr': 'shard_3',
        'finance': 'shard_4'
    }
    attr_value = document.metadata.get(attribute, 'default')
    return shard_mapping.get(attr_value, 'shard_default')
```

**Pros:**
- Queries can target specific shards
- Natural access control boundaries
- Predictable data placement

**Cons:**
- Uneven distribution if attributes are skewed
- Cross-shard queries expensive
- Requires attribute at query time

### Sharding by Hash

Distribute evenly using hash function:

```python
import hashlib

def get_shard_by_hash(document_id, num_shards=4):
    """
    Consistent hashing for even distribution.
    """
    hash_value = int(hashlib.sha256(document_id.encode()).hexdigest(), 16)
    return f"shard_{hash_value % num_shards}"
```

**Pros:**
- Even distribution
- Simple to implement
- No attribute dependency

**Cons:**
- All shards must be queried
- Resharding is expensive
- No query optimization

### Sharding by Time

Partition by document timestamp:

```python
def get_shard_by_time(document, granularity='month'):
    """
    Route documents by creation time.
    """
    created_at = document.metadata['created_at']

    if granularity == 'month':
        shard_key = created_at.strftime('%Y-%m')
    elif granularity == 'quarter':
        quarter = (created_at.month - 1) // 3 + 1
        shard_key = f"{created_at.year}-Q{quarter}"
    elif granularity == 'year':
        shard_key = str(created_at.year)

    return f"shard_{shard_key}"
```

**Pros:**
- Recent data queries hit fewer shards
- Easy archival of old shards
- Natural time-based access patterns

**Cons:**
- Uneven if recent data is hot
- Time must be known at query time
- Historical queries are expensive

## Replication Strategies

### What Is Replication?

Copying data across nodes for availability and read scaling:

```
                    ┌───────────────┐
                    │    Primary    │
                    │    (Write)    │
                    └───────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
       ┌───────────┐  ┌───────────┐  ┌───────────┐
       │  Replica  │  │  Replica  │  │  Replica  │
       │  (Read)   │  │  (Read)   │  │  (Read)   │
       └───────────┘  └───────────┘  └───────────┘
```

### Replication Factor

```python
# Typical configurations
REPLICATION_CONFIGS = {
    'development': {
        'replication_factor': 1,  # No replication
        'min_replicas': 1
    },
    'production': {
        'replication_factor': 3,  # 3 copies
        'min_replicas': 2  # Tolerate 1 failure
    },
    'high_availability': {
        'replication_factor': 5,
        'min_replicas': 3  # Tolerate 2 failures
    }
}
```

### Read/Write Distribution

```python
class ReplicatedVectorDB:
    def __init__(self, primary, replicas):
        self.primary = primary
        self.replicas = replicas
        self.replica_index = 0

    def write(self, vectors):
        """Writes go to primary only."""
        self.primary.upsert(vectors)
        # Async replication to replicas
        for replica in self.replicas:
            async_replicate(self.primary, replica)

    def search(self, query_vector, top_k):
        """Reads distributed across replicas."""
        # Round-robin load balancing
        replica = self.replicas[self.replica_index % len(self.replicas)]
        self.replica_index += 1
        return replica.search(query_vector, top_k)
```

## Combined Architecture

### Sharded and Replicated

```
                         Router
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
    ┌─────────┐       ┌─────────┐       ┌─────────┐
    │ Shard 1 │       │ Shard 2 │       │ Shard 3 │
    ├─────────┤       ├─────────┤       ├─────────┤
    │ Primary │       │ Primary │       │ Primary │
    │ Replica │       │ Replica │       │ Replica │
    │ Replica │       │ Replica │       │ Replica │
    └─────────┘       └─────────┘       └─────────┘
```

### Query Routing

```python
class ShardedReplicatedClient:
    def __init__(self, shard_config):
        self.shards = {}
        for shard_name, config in shard_config.items():
            self.shards[shard_name] = ReplicatedVectorDB(
                primary=config['primary'],
                replicas=config['replicas']
            )

    def search(self, query_vector, top_k, shard_hint=None):
        if shard_hint:
            # Query specific shard
            results = self.shards[shard_hint].search(query_vector, top_k)
        else:
            # Query all shards and merge
            all_results = []
            for shard in self.shards.values():
                results = shard.search(query_vector, top_k)
                all_results.extend(results)
            results = sorted(all_results, key=lambda x: x.score, reverse=True)[:top_k]

        return results
```

## Database-Specific Scaling

### Pinecone
```python
# Pinecone handles sharding automatically
# You choose pod type and replicas

index = pinecone.create_index(
    name="my-index",
    dimension=1536,
    metric="cosine",
    pods=4,          # Shards
    replicas=2,      # Replicas per shard
    pod_type="p1.x1"
)
```

### Weaviate
```yaml
# docker-compose for Weaviate cluster
services:
  weaviate-node-1:
    image: weaviate/weaviate
    environment:
      CLUSTER_HOSTNAME: 'node1'
      CLUSTER_JOIN: 'node1,node2,node3'
      REPLICATION_FACTOR: 3

  weaviate-node-2:
    # Similar config...
```

### Milvus
```python
# Milvus cluster configuration
from pymilvus import connections, Collection

connections.connect(
    alias="default",
    host="milvus-cluster-lb",  # Load balancer
    port="19530"
)

# Collection with sharding
collection = Collection(
    name="my_collection",
    schema=schema,
    shards_num=4  # Number of shards
)
```

### PostgreSQL + pgvector

```sql
-- Table partitioning for pgvector
CREATE TABLE embeddings (
    id SERIAL,
    embedding vector(1536),
    document_id TEXT,
    created_at TIMESTAMP,
    department TEXT
) PARTITION BY LIST (department);

CREATE TABLE embeddings_engineering
    PARTITION OF embeddings
    FOR VALUES IN ('engineering');

CREATE TABLE embeddings_sales
    PARTITION OF embeddings
    FOR VALUES IN ('sales');
```

## Consistency Considerations

### Eventual Consistency
```python
def write_with_eventual_consistency(vectors, timeout_ms=5000):
    """
    Write to primary, async replicate.
    Reads may see stale data briefly.
    """
    primary.write(vectors)

    # Fire-and-forget replication
    for replica in replicas:
        async_queue.enqueue(
            replicate_to,
            replica,
            vectors,
            timeout=timeout_ms
        )
```

### Strong Consistency
```python
def write_with_strong_consistency(vectors, min_acks=2):
    """
    Wait for acknowledgment from multiple nodes.
    """
    acks = 0
    primary.write(vectors)
    acks += 1

    for replica in replicas:
        if replica.write_sync(vectors):
            acks += 1
            if acks >= min_acks:
                return True

    if acks < min_acks:
        rollback(vectors)
        raise ConsistencyError("Failed to achieve quorum")
```

## Monitoring Sharded Systems

### Key Metrics

```python
SHARD_METRICS = {
    'per_shard': [
        'query_latency_p50',
        'query_latency_p99',
        'document_count',
        'index_size_bytes',
        'qps'
    ],
    'cluster': [
        'total_qps',
        'cross_shard_query_ratio',
        'replication_lag_ms',
        'shard_imbalance_ratio'
    ]
}
```

### Detecting Imbalance

```python
def check_shard_balance(shards):
    """
    Detect if shards are unbalanced.
    """
    sizes = [shard.get_document_count() for shard in shards]
    avg_size = sum(sizes) / len(sizes)
    max_deviation = max(abs(s - avg_size) / avg_size for s in sizes)

    if max_deviation > 0.2:  # 20% imbalance
        return {
            'balanced': False,
            'max_deviation': max_deviation,
            'recommendation': 'Consider resharding'
        }
    return {'balanced': True}
```

## Checklist

- [ ] Scaling triggers defined (QPS, latency, size)
- [ ] Sharding strategy chosen
- [ ] Sharding key selected
- [ ] Replication factor determined
- [ ] Consistency model chosen
- [ ] Query routing implemented
- [ ] Cross-shard query handling
- [ ] Monitoring for all shards
- [ ] Rebalancing procedure documented
- [ ] Failover tested

---

**Next:** [Caching Strategies](./caching-strategies.md)
