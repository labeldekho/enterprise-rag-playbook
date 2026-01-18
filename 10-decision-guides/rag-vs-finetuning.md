# RAG vs Fine-Tuning

Understanding when to use each approach.

## The Fundamental Difference

| Aspect | RAG | Fine-Tuning |
|--------|-----|-------------|
| What changes | What model can access | What model knows |
| Knowledge location | External database | Model weights |
| Updates | Index update | Retrain model |
| Latency | Higher (retrieval step) | Lower (no retrieval) |
| Explainability | High (sources visible) | Low (black box) |

## When to Choose RAG

### Strong Indicators for RAG

1. **Knowledge changes frequently**
   - Product catalogs
   - Policy documents
   - News and events

2. **Source attribution required**
   - Legal compliance
   - User verification
   - Audit requirements

3. **Large knowledge base**
   - Thousands of documents
   - Can't fit in context or training

4. **Real-time or near-real-time data**
   - Current inventory
   - Recent transactions
   - Live documentation

5. **Quick deployment needed**
   - Days instead of weeks
   - No ML infrastructure required

### Example RAG Use Cases

```
✓ Customer support with knowledge base
✓ Internal documentation Q&A
✓ Legal document research
✓ Technical documentation assistant
✓ News/research summarization
```

## When to Choose Fine-Tuning

### Strong Indicators for Fine-Tuning

1. **Behavior/style change needed**
   - Specific tone of voice
   - Domain-specific formatting
   - Consistent response patterns

2. **Knowledge is stable and foundational**
   - Core domain concepts
   - Unchanging procedures
   - Fundamental relationships

3. **Latency is critical**
   - Sub-100ms requirements
   - High-throughput systems
   - Real-time applications

4. **Structured output requirements**
   - Consistent JSON schemas
   - Specific formats
   - Predictable structure

5. **Proprietary reasoning patterns**
   - Domain-specific logic
   - Company-specific workflows

### Example Fine-Tuning Use Cases

```
✓ Code generation in company style
✓ Medical terminology understanding
✓ Legal document drafting
✓ Specific output format compliance
✓ Domain-specific classification
```

## Comparison Matrix

| Factor | RAG | Fine-Tuning |
|--------|-----|-------------|
| **Development Time** | Days | Weeks |
| **Data Requirements** | Documents | Q&A pairs / examples |
| **Update Speed** | Minutes | Hours/Days |
| **Inference Cost** | Higher | Lower |
| **Training Cost** | None | Significant |
| **Hallucination Risk** | Lower (grounded) | Higher |
| **Explainability** | High | Low |
| **Latency** | +100-500ms | Baseline |
| **Scalability** | Index grows | Fixed in weights |

## Decision Framework

### Step 1: Classify Your Need

```
┌─────────────────────────────────────────┐
│ What are you trying to improve?         │
└─────────────────────────────────────────┘
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼
Knowledge    Behavior
Access       Change
    │           │
    ▼           ▼
  RAG      Fine-Tune
```

### Step 2: Evaluate Data Characteristics

| Question | If Yes → | If No → |
|----------|----------|---------|
| Data changes monthly or more? | RAG | Either |
| Need to cite sources? | RAG | Either |
| Data > 100MB? | RAG | Either |
| Need specific output format? | Fine-tune | Either |
| Need specific tone/style? | Fine-tune | Either |
| Latency < 200ms required? | Fine-tune | RAG ok |

### Step 3: Consider Resources

| Resource | RAG Requirement | Fine-Tune Requirement |
|----------|-----------------|----------------------|
| ML expertise | Low | Medium-High |
| Compute | Inference only | Training + inference |
| Data labeling | Minimal | Significant |
| Maintenance | Index updates | Periodic retraining |

## Hybrid Approaches

### RAG + Fine-Tuned Model
Use fine-tuning to improve how the model uses retrieved context:

```python
# Fine-tune for better context utilization
training_example = {
    "context": "[Retrieved documents]",
    "question": "User question",
    "answer": "Well-grounded answer with citations"
}
```

### RAG with Embedding Fine-Tuning
Fine-tune embedding model for your domain:

```python
# Better embeddings = better retrieval
fine_tuned_embedder = train_embeddings(
    queries=domain_queries,
    relevant_docs=annotated_pairs
)
```

### Graduated Approach

```
Start with:    Base Model + RAG
If needed:     Fine-tune embeddings
If still not:  Fine-tune retrieval model
Last resort:   Fine-tune generation model
```

## Cost Comparison

### RAG Costs (Monthly, 100K queries)

| Component | Cost Range |
|-----------|------------|
| Embedding API | $50-200 |
| Vector DB | $100-500 |
| LLM (with context) | $500-2000 |
| **Total** | **$650-2700** |

### Fine-Tuning Costs

| Component | Cost Range |
|-----------|------------|
| Training (one-time) | $100-10000 |
| Inference (100K queries) | $300-1500 |
| Retraining (monthly) | $100-10000 |
| **Total** | **$500-21500** |

*Costs vary significantly based on model size and provider.*

## Migration Paths

### RAG to Fine-Tuning
When to migrate:
- RAG latency unacceptable
- Consistent response patterns needed
- Knowledge has stabilized

Migration steps:
1. Collect RAG query-response pairs
2. Curate high-quality examples
3. Fine-tune on collected data
4. Evaluate against RAG baseline
5. Gradual rollout

### Fine-Tuning to RAG
When to migrate:
- Knowledge updates too frequent
- Need source attribution
- Hallucination issues

Migration steps:
1. Build document index
2. Implement retrieval pipeline
3. Compare quality metrics
4. Add RAG as supplement first
5. Reduce fine-tuning dependency

## Decision Checklist

### Choose RAG if:
- [ ] Knowledge changes frequently
- [ ] Source citations needed
- [ ] Quick deployment required
- [ ] Large/growing knowledge base
- [ ] Latency budget > 200ms

### Choose Fine-Tuning if:
- [ ] Need specific behavior/style
- [ ] Knowledge is stable
- [ ] Strict latency requirements
- [ ] Structured output format required
- [ ] Have labeled training data

### Consider Both if:
- [ ] Complex domain requiring both knowledge and behavior change
- [ ] High-stakes application needing maximum quality
- [ ] Resources available for both approaches

---

**Previous:** [Should You Use RAG?](./should-you-use-rag.md)
**Next:** [RAG vs Agents](./rag-vs-agents.md)
