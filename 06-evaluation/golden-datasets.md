# Golden Datasets

The foundation of RAG evaluation.

## What Is a Golden Dataset?

A golden dataset contains:
- Test queries
- Expected relevant documents for each query
- Reference answers (ground truth)
- Metadata for analysis

```json
{
  "query": "What is the return policy for electronics?",
  "relevant_document_ids": ["doc_123", "doc_456"],
  "reference_answer": "Electronics can be returned within 15 days with original packaging and receipt.",
  "metadata": {
    "category": "policy",
    "difficulty": "easy",
    "requires_reasoning": false
  }
}
```

## Why Golden Datasets Matter

Without them:
- Can't calculate retrieval metrics (no relevance labels)
- Can't measure correctness (no ground truth)
- Can't catch regressions objectively
- Evaluation becomes subjective

## Dataset Creation Strategies

### 1. Expert Annotation

**Process:**
1. Domain experts write queries
2. Experts identify relevant documents
3. Experts write reference answers
4. Second expert reviews

**Pros:**
- High quality
- Domain-appropriate queries
- Realistic difficulty distribution

**Cons:**
- Expensive
- Time-consuming
- May miss edge cases

### 2. Query Log Mining

**Process:**
1. Collect real user queries from logs
2. Sample diverse queries
3. Annotate relevance and answers

```python
def sample_queries_from_logs(logs, sample_size=500):
    # Deduplicate
    unique_queries = list(set(logs))

    # Cluster by embedding for diversity
    embeddings = embed_batch(unique_queries)
    clusters = kmeans(embeddings, n_clusters=sample_size)

    # Sample one from each cluster
    sampled = []
    for cluster_id in range(sample_size):
        cluster_queries = [q for q, c in zip(unique_queries, clusters) if c == cluster_id]
        sampled.append(random.choice(cluster_queries))

    return sampled
```

**Pros:**
- Real user queries
- Natural distribution
- Identifies actual pain points

**Cons:**
- Requires existing traffic
- May have quality issues
- Biased toward common queries

### 3. Synthetic Generation

**Process:**
1. For each document, generate potential queries
2. Use LLM to create question-answer pairs
3. Human review for quality

```python
def generate_synthetic_qa(document, llm):
    prompt = f"""
Given this document, generate 5 diverse questions that someone might ask,
along with the correct answers based on the document.

Document:
{document.text}

Generate questions covering:
1. Factual lookup
2. Summarization
3. Comparison (if applicable)
4. Procedure/how-to (if applicable)
5. Edge case or clarification

Output format:
[
  {{"question": "...", "answer": "...", "type": "..."}}
]
"""
    return json.loads(llm.generate(prompt))
```

**Pros:**
- Scalable
- Good coverage
- Can target specific types

**Cons:**
- May not reflect real queries
- Quality varies
- Needs validation

### 4. Hybrid Approach

Combine methods for best results:

```python
def create_golden_dataset(
    documents,
    query_logs,
    expert_queries,
    target_size=1000
):
    dataset = []

    # 40% from real queries
    real_queries = sample_and_annotate(query_logs, n=int(target_size * 0.4))
    dataset.extend(real_queries)

    # 30% from expert queries
    dataset.extend(expert_queries[:int(target_size * 0.3)])

    # 30% synthetic
    remaining = target_size - len(dataset)
    synthetic = generate_synthetic_for_documents(
        documents,
        n=remaining
    )
    dataset.extend(synthetic)

    return dataset
```

## Dataset Schema

### Minimal Schema
```python
@dataclass
class GoldenItem:
    query: str
    relevant_doc_ids: List[str]
    reference_answer: str
```

### Full Schema
```python
@dataclass
class GoldenItem:
    # Identification
    id: str
    query: str

    # Retrieval ground truth
    relevant_doc_ids: List[str]
    relevance_scores: Dict[str, int]  # Graded relevance (0-3)

    # Generation ground truth
    reference_answer: str
    alternative_answers: List[str]  # Acceptable variations

    # Metadata
    category: str
    difficulty: str  # easy, medium, hard
    query_type: str  # factual, procedural, comparative
    requires_reasoning: bool
    requires_multiple_docs: bool

    # Provenance
    source: str  # expert, synthetic, logs
    annotator: str
    created_at: datetime
    validated: bool
```

## Relevance Annotation Guidelines

### Binary Relevance
- **Relevant (1):** Document contains information needed to answer
- **Not Relevant (0):** Document doesn't help answer the query

### Graded Relevance
| Score | Description |
|-------|-------------|
| 3 | Highly relevant, directly answers query |
| 2 | Relevant, contains useful information |
| 1 | Marginally relevant, tangentially related |
| 0 | Not relevant |

### Annotation Interface
```python
def create_annotation_task(query, candidate_docs):
    return {
        'query': query,
        'documents': [
            {
                'id': doc.id,
                'preview': doc.text[:500],
                'full_text_link': f'/docs/{doc.id}'
            }
            for doc in candidate_docs
        ],
        'instructions': """
            For each document, rate its relevance to the query:
            3 - Highly relevant (directly answers)
            2 - Relevant (useful information)
            1 - Marginally relevant
            0 - Not relevant

            Then provide the reference answer based on relevant documents.
        """
    }
```

## Quality Assurance

### Inter-Annotator Agreement
```python
from sklearn.metrics import cohen_kappa_score

def calculate_agreement(annotations_a, annotations_b):
    """
    Calculate agreement between two annotators.
    Kappa > 0.6 is acceptable, > 0.8 is good.
    """
    return cohen_kappa_score(annotations_a, annotations_b)
```

### Validation Checks
```python
def validate_golden_item(item, documents):
    errors = []

    # Check relevant docs exist
    for doc_id in item.relevant_doc_ids:
        if doc_id not in documents:
            errors.append(f"Document {doc_id} not found")

    # Check answer is grounded
    relevant_text = " ".join([documents[d].text for d in item.relevant_doc_ids])
    if not answer_is_grounded(item.reference_answer, relevant_text):
        errors.append("Reference answer not grounded in relevant docs")

    # Check query is not empty
    if len(item.query.strip()) < 10:
        errors.append("Query too short")

    return errors
```

### Periodic Review
- Sample and re-annotate 10% monthly
- Track annotation drift
- Update guidelines based on edge cases

## Dataset Maintenance

### Versioning
```
golden_datasets/
├── v1.0/
│   ├── train.jsonl
│   ├── test.jsonl
│   └── metadata.json
├── v1.1/
│   ├── train.jsonl
│   ├── test.jsonl
│   ├── metadata.json
│   └── CHANGELOG.md
```

### When to Update
- Documents change (answers may be stale)
- New query patterns emerge
- Coverage gaps identified
- Annotation errors found

### Update Process
```python
def update_golden_dataset(current_version, changes):
    new_version = bump_version(current_version)

    # Apply changes
    dataset = load_dataset(current_version)

    for change in changes:
        if change.type == 'add':
            dataset.append(change.item)
        elif change.type == 'remove':
            dataset = [i for i in dataset if i.id != change.id]
        elif change.type == 'update':
            for i, item in enumerate(dataset):
                if item.id == change.id:
                    dataset[i] = change.item
                    break

    # Validate
    errors = validate_dataset(dataset)
    if errors:
        raise ValidationError(errors)

    # Save with changelog
    save_dataset(dataset, new_version)
    save_changelog(current_version, new_version, changes)

    return new_version
```

## Dataset Size Guidelines

| Corpus Size | Recommended Test Set |
|-------------|---------------------|
| < 1,000 docs | 100-200 queries |
| 1,000-10,000 docs | 200-500 queries |
| 10,000-100,000 docs | 500-1,000 queries |
| > 100,000 docs | 1,000+ queries |

### Coverage Requirements
- All major document categories represented
- Mix of difficulty levels (40% easy, 40% medium, 20% hard)
- Various query types (factual, procedural, comparative)
- Edge cases included (5-10%)

## Checklist

- [ ] Dataset creation strategy chosen
- [ ] Schema defined
- [ ] Annotation guidelines written
- [ ] Annotation interface/process set up
- [ ] Inter-annotator agreement measured
- [ ] Validation checks implemented
- [ ] Versioning system in place
- [ ] Coverage analysis done
- [ ] Maintenance schedule defined

---

**Previous:** [Evaluation Metrics](./eval-metrics.md)
**Next:** [A/B Testing](./ab-testing.md)
