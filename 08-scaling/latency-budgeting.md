# Latency Budgeting

Allocating time across RAG pipeline stages.

## Why Latency Budgeting?

Users have expectations:
- **< 500ms:** Feels instant
- **500ms - 2s:** Acceptable for complex queries
- **2s - 5s:** Noticeable delay, needs indicator
- **> 5s:** Frustrating, risk of abandonment

Budgeting ensures you hit targets consistently.

## RAG Latency Breakdown

### Typical Pipeline
```
┌─────────────────────────────────────────────────────────────────┐
│                    Total Latency: ~2000ms                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Query Embedding     │██░░░░░░░░░░░░░░░░│  50-100ms  (5%)      │
│  Vector Search       │██░░░░░░░░░░░░░░░░│  20-100ms  (5%)      │
│  Reranking           │████░░░░░░░░░░░░░░│  100-300ms (15%)     │
│  Context Assembly    │█░░░░░░░░░░░░░░░░░│  10-50ms   (2%)      │
│  LLM Generation      │████████████░░░░░░│  500-1500ms (60%)    │
│  Post-processing     │█░░░░░░░░░░░░░░░░░│  10-50ms   (3%)      │
│  Network/Overhead    │███░░░░░░░░░░░░░░░│  100-200ms (10%)     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Budget Allocation
```python
LATENCY_BUDGET = {
    'total_target_ms': 2000,
    'breakdown': {
        'embedding': {'target_ms': 80, 'max_ms': 150},
        'retrieval': {'target_ms': 50, 'max_ms': 100},
        'reranking': {'target_ms': 150, 'max_ms': 300},
        'context_assembly': {'target_ms': 30, 'max_ms': 50},
        'llm_generation': {'target_ms': 1200, 'max_ms': 1800},
        'post_processing': {'target_ms': 30, 'max_ms': 50},
        'buffer': {'target_ms': 460, 'max_ms': 550}
    }
}
```

## Measuring Latency

### Instrumentation
```python
import time
from dataclasses import dataclass
from typing import Dict

@dataclass
class LatencyMetrics:
    embedding_ms: float
    retrieval_ms: float
    reranking_ms: float
    context_assembly_ms: float
    llm_generation_ms: float
    post_processing_ms: float
    total_ms: float

class InstrumentedRAGPipeline:
    def query(self, query_text):
        timings = {}
        start_total = time.time()

        # Embedding
        start = time.time()
        embedding = self.embed(query_text)
        timings['embedding_ms'] = (time.time() - start) * 1000

        # Retrieval
        start = time.time()
        results = self.retrieve(embedding)
        timings['retrieval_ms'] = (time.time() - start) * 1000

        # Reranking
        start = time.time()
        reranked = self.rerank(query_text, results)
        timings['reranking_ms'] = (time.time() - start) * 1000

        # Context Assembly
        start = time.time()
        context = self.assemble_context(reranked)
        timings['context_assembly_ms'] = (time.time() - start) * 1000

        # LLM Generation
        start = time.time()
        response = self.generate(query_text, context)
        timings['llm_generation_ms'] = (time.time() - start) * 1000

        # Post-processing
        start = time.time()
        final_response = self.post_process(response)
        timings['post_processing_ms'] = (time.time() - start) * 1000

        timings['total_ms'] = (time.time() - start_total) * 1000

        self.record_metrics(LatencyMetrics(**timings))
        return final_response
```

### Percentile Tracking
```python
class LatencyTracker:
    def __init__(self):
        self.latencies = defaultdict(list)

    def record(self, stage, latency_ms):
        self.latencies[stage].append(latency_ms)

    def get_percentiles(self, stage):
        data = sorted(self.latencies[stage])
        n = len(data)
        return {
            'p50': data[int(n * 0.5)],
            'p90': data[int(n * 0.9)],
            'p95': data[int(n * 0.95)],
            'p99': data[int(n * 0.99)]
        }
```

## Optimization Techniques

### Parallel Execution
```python
import asyncio

async def parallel_rag_query(query_text):
    # Embedding (must be first)
    embedding = await embed_async(query_text)

    # Parallel: Vector search + Keyword search
    vector_task = asyncio.create_task(vector_search(embedding))
    keyword_task = asyncio.create_task(keyword_search(query_text))

    vector_results, keyword_results = await asyncio.gather(
        vector_task,
        keyword_task
    )

    # Fusion
    merged = fuse_results(vector_results, keyword_results)

    # Sequential: Reranking then generation (dependent)
    reranked = await rerank_async(query_text, merged)
    response = await generate_async(query_text, reranked)

    return response
```

### Streaming Responses
```python
async def streaming_rag_query(query_text):
    # Do retrieval
    context = await retrieve_and_assemble(query_text)

    # Stream LLM response
    async for token in llm.stream_generate(query_text, context):
        yield token

# Time to first token: ~500ms instead of ~2000ms for full response
```

### Timeout Handling
```python
async def query_with_timeout(query_text, timeout_ms=3000):
    try:
        response = await asyncio.wait_for(
            rag_pipeline.query(query_text),
            timeout=timeout_ms / 1000
        )
        return response
    except asyncio.TimeoutError:
        # Fallback to cached or simplified response
        return get_fallback_response(query_text)
```

### Progressive Enhancement
```python
async def progressive_query(query_text):
    """
    Return quick answer first, then enhance.
    """
    # Quick response (smaller model, fewer docs)
    quick_response = await quick_rag(query_text)
    yield {'type': 'quick', 'response': quick_response}

    # Enhanced response (full pipeline)
    full_response = await full_rag(query_text)
    yield {'type': 'enhanced', 'response': full_response}
```

## Stage-Specific Optimizations

### Embedding
| Optimization | Impact | Tradeoff |
|--------------|--------|----------|
| Caching | -50ms | Memory |
| Batch requests | -20ms | Complexity |
| Smaller model | -30ms | Quality |

### Retrieval
| Optimization | Impact | Tradeoff |
|--------------|--------|----------|
| HNSW tuning (lower ef) | -30ms | Recall |
| Fewer results (k) | -10ms | Coverage |
| Pre-filtering | -20ms | Implementation |

### Reranking
| Optimization | Impact | Tradeoff |
|--------------|--------|----------|
| Smaller model | -100ms | Quality |
| Fewer candidates | -50ms | Quality |
| Skip if confident | -150ms | Complexity |

### LLM Generation
| Optimization | Impact | Tradeoff |
|--------------|--------|----------|
| Smaller model | -500ms | Quality |
| Max tokens limit | -200ms | Completeness |
| Streaming | Better perceived | Complexity |

## Adaptive Quality

### Quality vs Latency Tradeoffs
```python
class AdaptiveRAG:
    def __init__(self, latency_target_ms=2000):
        self.target = latency_target_ms

    def select_config(self, time_remaining_ms):
        if time_remaining_ms > 1500:
            return {
                'rerank': True,
                'model': 'gpt-4o',
                'max_tokens': 1000,
                'top_k': 10
            }
        elif time_remaining_ms > 800:
            return {
                'rerank': False,
                'model': 'gpt-4o-mini',
                'max_tokens': 500,
                'top_k': 5
            }
        else:
            return {
                'rerank': False,
                'model': 'gpt-3.5-turbo',
                'max_tokens': 200,
                'top_k': 3
            }
```

### Dynamic Budget Adjustment
```python
async def dynamic_budget_query(query_text, total_budget_ms=2000):
    start = time.time()

    # Embedding (fixed budget)
    embedding = await embed(query_text)
    elapsed = (time.time() - start) * 1000
    remaining = total_budget_ms - elapsed

    # Retrieval (10% of remaining)
    retrieval_budget = remaining * 0.1
    results = await retrieve_with_timeout(embedding, timeout_ms=retrieval_budget)
    elapsed = (time.time() - start) * 1000
    remaining = total_budget_ms - elapsed

    # Reranking (skip if budget tight)
    if remaining > 1500:
        reranked = await rerank(query_text, results)
    else:
        reranked = results[:5]

    elapsed = (time.time() - start) * 1000
    remaining = total_budget_ms - elapsed

    # Generation (use remaining budget)
    config = select_llm_config(remaining)
    response = await generate(query_text, reranked, **config)

    return response
```

## Monitoring and Alerts

### SLO Definition
```python
SLOs = {
    'p50_latency_ms': 1000,
    'p95_latency_ms': 2500,
    'p99_latency_ms': 4000,
    'timeout_rate': 0.01,  # < 1% timeouts
    'error_rate': 0.001    # < 0.1% errors
}
```

### Alert Rules
```python
LATENCY_ALERTS = [
    {
        'name': 'p50_breach',
        'condition': lambda metrics: metrics['p50'] > SLOs['p50_latency_ms'],
        'severity': 'warning'
    },
    {
        'name': 'p95_breach',
        'condition': lambda metrics: metrics['p95'] > SLOs['p95_latency_ms'],
        'severity': 'critical'
    },
    {
        'name': 'llm_slow',
        'condition': lambda metrics: metrics['llm_p95'] > 2000,
        'severity': 'warning',
        'action': 'Consider model downgrade'
    }
]
```

## Checklist

- [ ] Latency budget defined per stage
- [ ] Instrumentation added to pipeline
- [ ] Percentile tracking in place
- [ ] Parallel execution where possible
- [ ] Timeout handling implemented
- [ ] Streaming for long responses
- [ ] Adaptive quality based on budget
- [ ] SLOs defined
- [ ] Alerts configured
- [ ] Regular latency reviews scheduled

---

**Previous:** [Cost Optimization](./cost-optimization.md)
**Next:** [Reference Implementation](../09-reference-implementation/README.md)
