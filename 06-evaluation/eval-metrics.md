# Evaluation Metrics

Making RAG measurable.

## Why Evaluation Matters

Without evaluation:
- Can't tell if changes improve quality
- Can't compare approaches objectively
- Can't catch regressions
- Can't justify decisions to stakeholders

## The Two-Stage Problem

RAG has two components that need separate evaluation:

```
┌─────────────────────────────────────────────────────────┐
│                    RAG Pipeline                          │
├──────────────────────────┬──────────────────────────────┤
│     Retrieval Stage      │     Generation Stage         │
│                          │                              │
│  Did we find the right   │  Did we answer correctly    │
│  documents?              │  based on what we found?    │
│                          │                              │
│  Metrics:                │  Metrics:                   │
│  - Recall@k              │  - Faithfulness             │
│  - Precision@k           │  - Answer relevance         │
│  - MRR                   │  - Completeness             │
│  - NDCG                  │  - Fluency                  │
└──────────────────────────┴──────────────────────────────┘
```

## Retrieval Metrics

### Recall@k
"What fraction of relevant documents did we retrieve in top k?"

```python
def recall_at_k(retrieved_ids, relevant_ids, k):
    """
    retrieved_ids: list of document IDs returned
    relevant_ids: set of actually relevant document IDs
    k: number of top results to consider
    """
    retrieved_set = set(retrieved_ids[:k])
    relevant_set = set(relevant_ids)

    if len(relevant_set) == 0:
        return 0.0

    return len(retrieved_set & relevant_set) / len(relevant_set)
```

**Interpretation:**
- Recall@10 = 0.8 means 80% of relevant docs were in top 10
- High recall = good coverage
- Critical for RAG (can't answer if we don't retrieve)

### Precision@k
"What fraction of retrieved documents are relevant?"

```python
def precision_at_k(retrieved_ids, relevant_ids, k):
    retrieved_set = set(retrieved_ids[:k])
    relevant_set = set(relevant_ids)

    if k == 0:
        return 0.0

    return len(retrieved_set & relevant_set) / k
```

**Interpretation:**
- Precision@10 = 0.6 means 6 of top 10 were relevant
- High precision = less noise in context
- Tradeoff with recall

### Mean Reciprocal Rank (MRR)
"How high is the first relevant document?"

```python
def mrr(retrieved_ids, relevant_ids):
    relevant_set = set(relevant_ids)

    for rank, doc_id in enumerate(retrieved_ids, 1):
        if doc_id in relevant_set:
            return 1.0 / rank

    return 0.0

def mean_mrr(queries_results):
    """Average MRR across all queries."""
    return sum(mrr(r, rel) for r, rel in queries_results) / len(queries_results)
```

**Interpretation:**
- MRR = 1.0 means first result is always relevant
- MRR = 0.5 means relevant result is typically 2nd
- Good for single-answer queries

### Normalized Discounted Cumulative Gain (NDCG)
"Are highly relevant docs ranked higher than somewhat relevant ones?"

```python
import numpy as np

def dcg_at_k(relevance_scores, k):
    """relevance_scores: graded relevance (e.g., 0, 1, 2, 3)"""
    relevance = np.array(relevance_scores[:k])
    gains = 2**relevance - 1
    discounts = np.log2(np.arange(2, k + 2))
    return np.sum(gains / discounts)

def ndcg_at_k(retrieved_scores, ideal_scores, k):
    dcg = dcg_at_k(retrieved_scores, k)
    idcg = dcg_at_k(sorted(ideal_scores, reverse=True), k)
    return dcg / idcg if idcg > 0 else 0.0
```

**Interpretation:**
- NDCG = 1.0 means perfect ranking
- Useful when documents have graded relevance
- More nuanced than binary metrics

## Generation Metrics

### Faithfulness
"Is the answer grounded in the retrieved context?"

```python
def evaluate_faithfulness(answer, context, evaluator_llm):
    prompt = f"""
Given the context and answer, determine if the answer is faithful to the context.
An answer is faithful if all claims can be verified from the context.

Context:
{context}

Answer:
{answer}

Evaluate faithfulness (0-1 scale):
- 1.0: All claims supported by context
- 0.5: Some claims supported, some not verifiable
- 0.0: Contains claims contradicting or not in context

Score:
"""
    return float(evaluator_llm.generate(prompt))
```

**Also known as:** Groundedness, attribution accuracy

### Answer Relevance
"Does the answer address the question?"

```python
def evaluate_relevance(question, answer, evaluator_llm):
    prompt = f"""
Given the question and answer, determine if the answer is relevant.

Question: {question}
Answer: {answer}

Evaluate relevance (0-1 scale):
- 1.0: Directly and completely answers the question
- 0.5: Partially answers or tangentially related
- 0.0: Does not answer the question

Score:
"""
    return float(evaluator_llm.generate(prompt))
```

### Completeness
"Does the answer cover all aspects of the question?"

```python
def evaluate_completeness(question, answer, reference_answer, evaluator_llm):
    prompt = f"""
Compare the answer to the reference answer for completeness.

Question: {question}
Reference Answer: {reference_answer}
Generated Answer: {answer}

What fraction of key points from the reference are covered?
Score (0-1):
"""
    return float(evaluator_llm.generate(prompt))
```

### Correctness
"Is the answer factually correct?"

```python
def evaluate_correctness(question, answer, ground_truth, evaluator_llm):
    prompt = f"""
Evaluate if the answer is factually correct compared to ground truth.

Question: {question}
Ground Truth: {ground_truth}
Generated Answer: {answer}

Score (0-1):
- 1.0: Completely correct
- 0.5: Partially correct, some errors
- 0.0: Incorrect

Score:
"""
    return float(evaluator_llm.generate(prompt))
```

## End-to-End Metrics

### Answer Quality Score
Combine multiple factors:

```python
def end_to_end_score(question, answer, context, reference):
    faithfulness = evaluate_faithfulness(answer, context)
    relevance = evaluate_relevance(question, answer)
    correctness = evaluate_correctness(question, answer, reference)

    # Weighted combination
    weights = {'faithfulness': 0.4, 'relevance': 0.3, 'correctness': 0.3}

    return (
        weights['faithfulness'] * faithfulness +
        weights['relevance'] * relevance +
        weights['correctness'] * correctness
    )
```

### Human Evaluation Rubric

| Score | Description |
|-------|-------------|
| 5 | Perfect answer, fully addresses question |
| 4 | Good answer, minor omissions |
| 3 | Acceptable, addresses main points |
| 2 | Partial answer, significant gaps |
| 1 | Poor answer, barely relevant |
| 0 | Wrong or completely irrelevant |

## Automated Evaluation Tools

### RAGAS
```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

results = evaluate(
    dataset,  # HuggingFace dataset format
    metrics=[faithfulness, answer_relevancy, context_precision]
)
```

### TruLens
```python
from trulens_eval import Feedback, TruChain

# Define feedback functions
f_groundedness = Feedback(groundedness_provider.groundedness).on(
    app.retrieved_context,
    app.response
)

# Track and evaluate
tru_chain = TruChain(app, feedbacks=[f_groundedness])
```

### Custom Evaluation Pipeline
```python
class RAGEvaluator:
    def __init__(self, retriever, generator, evaluator_llm):
        self.retriever = retriever
        self.generator = generator
        self.evaluator = evaluator_llm

    def evaluate_query(self, query, relevant_docs, reference_answer):
        # Run retrieval
        retrieved = self.retriever.search(query)
        retrieved_ids = [d.id for d in retrieved]

        # Run generation
        context = format_context(retrieved)
        answer = self.generator.generate(query, context)

        # Calculate metrics
        return {
            'retrieval': {
                'recall@5': recall_at_k(retrieved_ids, relevant_docs, 5),
                'precision@5': precision_at_k(retrieved_ids, relevant_docs, 5),
                'mrr': mrr(retrieved_ids, relevant_docs)
            },
            'generation': {
                'faithfulness': evaluate_faithfulness(answer, context, self.evaluator),
                'relevance': evaluate_relevance(query, answer, self.evaluator),
                'correctness': evaluate_correctness(query, answer, reference_answer, self.evaluator)
            }
        }

    def evaluate_dataset(self, test_set):
        results = []
        for item in test_set:
            result = self.evaluate_query(
                item['query'],
                item['relevant_docs'],
                item['reference_answer']
            )
            results.append(result)
        return aggregate_results(results)
```

## Metric Selection Guide

| Use Case | Primary Metrics |
|----------|-----------------|
| Search quality | Recall@k, MRR, NDCG |
| Answer accuracy | Correctness, Faithfulness |
| User satisfaction | Relevance, Completeness |
| Hallucination detection | Faithfulness |
| Ranking quality | NDCG, MRR |

## Common Pitfalls

### 1. Evaluating Only Generation
**Problem:** Good answers with bad retrieval
**Fix:** Always evaluate retrieval separately

### 2. No Ground Truth
**Problem:** Can't calculate retrieval metrics
**Fix:** Create golden datasets (see next section)

### 3. Single Metric Focus
**Problem:** Optimize one metric, others degrade
**Fix:** Track multiple metrics, use dashboards

### 4. Evaluation Data Leakage
**Problem:** Test data used in training
**Fix:** Strict train/test splits

## Checklist

- [ ] Retrieval metrics defined (Recall, Precision, MRR)
- [ ] Generation metrics defined (Faithfulness, Relevance)
- [ ] Evaluation pipeline automated
- [ ] Ground truth dataset available
- [ ] Metrics dashboard created
- [ ] Baselines established
- [ ] Regular evaluation scheduled

---

**Next:** [Golden Datasets](./golden-datasets.md)
