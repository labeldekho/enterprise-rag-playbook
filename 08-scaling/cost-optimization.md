# Cost Optimization

Controlling RAG expenses without sacrificing quality.

## RAG Cost Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAG Cost Breakdown                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Embedding API      │████████░░░░░░░░░░│  15-25%               │
│  Vector Database    │██████████░░░░░░░░│  20-30%               │
│  LLM Generation     │████████████████░░│  40-50%               │
│  Infrastructure     │████░░░░░░░░░░░░░░│  10-15%               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Embedding Cost Optimization

### Model Selection
```python
EMBEDDING_MODELS = {
    'openai-small': {
        'name': 'text-embedding-3-small',
        'cost_per_1m_tokens': 0.02,
        'dimensions': 1536,
        'quality': 'good'
    },
    'openai-large': {
        'name': 'text-embedding-3-large',
        'cost_per_1m_tokens': 0.13,
        'dimensions': 3072,
        'quality': 'best'
    },
    'local-minilm': {
        'name': 'all-MiniLM-L6-v2',
        'cost_per_1m_tokens': 0,  # Self-hosted
        'dimensions': 384,
        'quality': 'acceptable'
    }
}

def select_embedding_model(quality_requirement, budget):
    if quality_requirement == 'best' and budget == 'high':
        return EMBEDDING_MODELS['openai-large']
    elif quality_requirement == 'good' or budget == 'medium':
        return EMBEDDING_MODELS['openai-small']
    else:
        return EMBEDDING_MODELS['local-minilm']
```

### Batching Embeddings
```python
def embed_with_batching(texts, batch_size=100):
    """
    Batch API calls to reduce overhead.
    """
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = embedding_api.embed(batch)
        embeddings.extend(batch_embeddings)
    return embeddings
```

### Caching Embeddings
```python
def get_embedding_with_cache(text, cache):
    cache_key = f"emb:{hash(text)}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    embedding = embed(text)
    cache.set(cache_key, embedding, ttl=86400)  # 24 hours
    return embedding

# Savings: 30-60% of embedding costs
```

## Vector Database Cost Optimization

### Right-Sizing

| Workload | Recommended Tier |
|----------|-----------------|
| < 100K vectors | Serverless/free tier |
| 100K - 1M vectors | Basic paid tier |
| 1M - 10M vectors | Standard tier |
| > 10M vectors | Enterprise/self-hosted |

### Dimension Reduction
```python
# OpenAI supports native dimension reduction
embedding = client.embeddings.create(
    model="text-embedding-3-large",
    input=text,
    dimensions=256  # Reduced from 3072
)

# Storage savings: ~12x
# Quality impact: ~5-10% recall reduction
```

### Pruning Unused Data
```python
def identify_unused_documents(vector_db, days_threshold=90):
    """
    Find documents never accessed in retrieval.
    """
    all_docs = vector_db.get_all_ids()
    accessed_docs = get_accessed_documents(days=days_threshold)
    unused = set(all_docs) - set(accessed_docs)

    return {
        'unused_count': len(unused),
        'unused_ids': list(unused),
        'potential_savings': estimate_storage_savings(unused)
    }
```

## LLM Cost Optimization

### Model Selection Strategy
```python
MODEL_TIERS = {
    'simple': {
        'model': 'gpt-3.5-turbo',
        'cost_per_1k_tokens': 0.0015,
        'use_for': ['simple_qa', 'classification']
    },
    'standard': {
        'model': 'gpt-4o-mini',
        'cost_per_1k_tokens': 0.00015,
        'use_for': ['general_qa', 'summarization']
    },
    'complex': {
        'model': 'gpt-4o',
        'cost_per_1k_tokens': 0.005,
        'use_for': ['complex_reasoning', 'code_generation']
    }
}

def select_model_for_query(query, complexity_score):
    if complexity_score < 0.3:
        return MODEL_TIERS['simple']
    elif complexity_score < 0.7:
        return MODEL_TIERS['standard']
    else:
        return MODEL_TIERS['complex']
```

### Query Complexity Classification
```python
def estimate_query_complexity(query, context):
    """
    Classify query complexity to route to appropriate model.
    """
    features = {
        'query_length': len(query.split()),
        'context_length': len(context.split()),
        'has_comparison': 'compare' in query.lower() or 'vs' in query.lower(),
        'has_reasoning': any(w in query.lower() for w in ['why', 'how', 'explain']),
        'multi_hop': query.count('?') > 1 or 'and' in query.lower(),
    }

    score = 0
    if features['query_length'] > 20:
        score += 0.2
    if features['context_length'] > 2000:
        score += 0.2
    if features['has_comparison']:
        score += 0.2
    if features['has_reasoning']:
        score += 0.2
    if features['multi_hop']:
        score += 0.2

    return score
```

### Context Trimming
```python
def trim_context_to_budget(context, budget_tokens=2000):
    """
    Reduce context size to control costs.
    """
    current_tokens = count_tokens(context)
    if current_tokens <= budget_tokens:
        return context

    # Keep most relevant chunks
    chunks = parse_chunks(context)
    ranked = rank_by_relevance(chunks)

    trimmed = []
    total_tokens = 0
    for chunk in ranked:
        chunk_tokens = count_tokens(chunk)
        if total_tokens + chunk_tokens <= budget_tokens:
            trimmed.append(chunk)
            total_tokens += chunk_tokens
        else:
            break

    return format_chunks(trimmed)
```

### Response Length Control
```python
def generate_with_length_control(query, context, max_tokens=500):
    """
    Control output length to manage costs.
    """
    prompt = f"""
    Answer the question concisely in {max_tokens // 4} words or less.

    Context: {context}
    Question: {query}
    """

    return llm.generate(
        prompt,
        max_tokens=max_tokens,
        stop=["\n\n"]  # Stop at paragraph breaks
    )
```

## Cost Monitoring

### Per-Query Cost Tracking
```python
def calculate_query_cost(query_metrics):
    embedding_cost = (
        query_metrics['query_tokens'] / 1_000_000 *
        EMBEDDING_COST_PER_M
    )

    retrieval_cost = (
        query_metrics['vectors_searched'] *
        VECTOR_SEARCH_COST_PER_QUERY
    )

    llm_cost = (
        (query_metrics['input_tokens'] + query_metrics['output_tokens']) /
        1000 *
        LLM_COST_PER_K
    )

    return {
        'embedding_cost': embedding_cost,
        'retrieval_cost': retrieval_cost,
        'llm_cost': llm_cost,
        'total_cost': embedding_cost + retrieval_cost + llm_cost
    }
```

### Cost Dashboard
```python
COST_METRICS = {
    'daily': [
        'total_cost',
        'cost_per_query',
        'cost_by_component',
        'cost_by_model'
    ],
    'alerts': [
        {'name': 'daily_budget_exceeded', 'threshold': 100},
        {'name': 'cost_per_query_spike', 'threshold': 0.10},
        {'name': 'llm_cost_ratio', 'threshold': 0.7}  # LLM > 70% of costs
    ]
}
```

### Budget Controls
```python
class BudgetController:
    def __init__(self, daily_budget, user_budget):
        self.daily_budget = daily_budget
        self.user_budget = user_budget
        self.daily_spend = 0
        self.user_spend = defaultdict(float)

    def can_proceed(self, user_id, estimated_cost):
        if self.daily_spend + estimated_cost > self.daily_budget:
            raise BudgetExceededError("Daily budget exceeded")

        if self.user_spend[user_id] + estimated_cost > self.user_budget:
            raise BudgetExceededError(f"User {user_id} budget exceeded")

        return True

    def record_spend(self, user_id, cost):
        self.daily_spend += cost
        self.user_spend[user_id] += cost
```

## Cost Optimization Strategies Summary

| Strategy | Potential Savings | Implementation Effort |
|----------|-------------------|----------------------|
| Embedding caching | 30-60% | Low |
| Model tiering | 40-60% | Medium |
| Context trimming | 20-40% | Low |
| Dimension reduction | 50-80% storage | Low |
| Self-hosted embeddings | 100% embedding | High |
| Query deduplication | 10-30% | Medium |

## ROI Calculation

```python
def calculate_optimization_roi(
    current_monthly_cost,
    optimization_savings_percent,
    implementation_cost,
    monthly_maintenance
):
    monthly_savings = current_monthly_cost * (optimization_savings_percent / 100)
    net_monthly_savings = monthly_savings - monthly_maintenance
    months_to_roi = implementation_cost / net_monthly_savings

    return {
        'monthly_savings': monthly_savings,
        'net_monthly_savings': net_monthly_savings,
        'months_to_roi': months_to_roi,
        'annual_savings': net_monthly_savings * 12
    }

# Example
roi = calculate_optimization_roi(
    current_monthly_cost=10000,
    optimization_savings_percent=40,
    implementation_cost=5000,
    monthly_maintenance=500
)
# months_to_roi: ~1.4 months
```

## Checklist

- [ ] Cost breakdown by component understood
- [ ] Embedding model selection optimized
- [ ] Caching implemented for embeddings
- [ ] LLM model tiering implemented
- [ ] Context trimming in place
- [ ] Per-query cost tracking
- [ ] Budget controls implemented
- [ ] Cost alerts configured
- [ ] Regular cost reviews scheduled
- [ ] ROI calculated for optimizations

---

**Previous:** [Caching Strategies](./caching-strategies.md)
**Next:** [Latency Budgeting](./latency-budgeting.md)
