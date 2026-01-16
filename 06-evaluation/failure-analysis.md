# Failure Analysis

Understanding why RAG fails and how to fix it.

## RAG Failure Taxonomy

```
┌─────────────────────────────────────────────────────────────────┐
│                      RAG Failures                                │
├────────────────────────────┬────────────────────────────────────┤
│    Retrieval Failures      │      Generation Failures           │
├────────────────────────────┼────────────────────────────────────┤
│ • No relevant docs found   │ • Hallucination                    │
│ • Relevant docs ranked low │ • Wrong interpretation of context  │
│ • Wrong docs retrieved     │ • Incomplete answer                │
│ • Partial context          │ • Over-reliance on context         │
│ • Outdated docs            │ • Ignoring context                 │
└────────────────────────────┴────────────────────────────────────┘
```

## Retrieval Failures

### 1. No Relevant Documents Exist
**Symptom:** Query is valid but no documents cover the topic
**Detection:**
```python
def detect_coverage_gap(query, results):
    if not results or max(r.score for r in results) < LOW_SCORE_THRESHOLD:
        return {
            'type': 'coverage_gap',
            'query': query,
            'best_score': max(r.score for r in results) if results else 0
        }
    return None
```
**Fix:** Add content, identify common gaps, communicate limitations

### 2. Query-Document Mismatch
**Symptom:** Relevant docs exist but aren't retrieved
**Detection:**
```python
def detect_retrieval_mismatch(query, results, known_relevant_ids):
    retrieved_ids = {r.id for r in results[:10]}
    missed = known_relevant_ids - retrieved_ids

    if missed:
        return {
            'type': 'retrieval_mismatch',
            'query': query,
            'missed_docs': list(missed),
            'retrieved_docs': list(retrieved_ids)
        }
    return None
```
**Fix:**
- Improve embedding model
- Add hybrid search
- Reformulate query
- Better chunking

### 3. Semantic Gap
**Symptom:** Query uses different vocabulary than documents
**Example:** Query: "car" → Documents: "automobile", "vehicle"
**Detection:**
```python
def detect_semantic_gap(query, top_results):
    query_terms = set(tokenize(query.lower()))
    doc_terms = set()
    for r in top_results:
        doc_terms.update(tokenize(r.text.lower()))

    overlap = query_terms & doc_terms
    if len(overlap) / len(query_terms) < 0.3:
        return {
            'type': 'semantic_gap',
            'query_terms': list(query_terms),
            'doc_terms_sample': list(doc_terms)[:50]
        }
    return None
```
**Fix:** Synonym expansion, query reformulation, better embeddings

### 4. Ranking Failure
**Symptom:** Relevant docs retrieved but ranked too low
**Detection:**
```python
def detect_ranking_failure(results, relevant_ids, k=5):
    top_k_ids = {r.id for r in results[:k]}
    relevant_in_top_k = relevant_ids & top_k_ids

    if relevant_ids and not relevant_in_top_k:
        # Find where relevant docs actually ranked
        ranks = []
        for i, r in enumerate(results):
            if r.id in relevant_ids:
                ranks.append(i + 1)

        return {
            'type': 'ranking_failure',
            'relevant_doc_ranks': ranks,
            'top_k': k
        }
    return None
```
**Fix:** Reranking, fusion tuning, better scoring

## Generation Failures

### 1. Hallucination
**Symptom:** Answer contains facts not in retrieved context
**Detection:**
```python
def detect_hallucination(answer, context, llm):
    prompt = f"""
Identify any claims in the answer that are NOT supported by the context.

Context:
{context}

Answer:
{answer}

List unsupported claims (or "none" if all claims are supported):
"""
    result = llm.generate(prompt)
    if result.strip().lower() != "none":
        return {
            'type': 'hallucination',
            'unsupported_claims': result
        }
    return None
```
**Fix:** Stronger grounding prompts, lower temperature, citation requirements

### 2. Context Misinterpretation
**Symptom:** Answer misunderstands what the context says
**Detection:**
```python
def detect_misinterpretation(query, answer, context, llm):
    prompt = f"""
Check if the answer correctly interprets the context.

Query: {query}
Context: {context}
Answer: {answer}

Does the answer misinterpret any information from the context?
If yes, explain the misinterpretation:
"""
    result = llm.generate(prompt)
    if "yes" in result.lower()[:10]:
        return {
            'type': 'misinterpretation',
            'explanation': result
        }
    return None
```
**Fix:** Clearer context formatting, explicit instructions, simpler language

### 3. Incomplete Answer
**Symptom:** Answer is correct but missing key information
**Detection:**
```python
def detect_incomplete_answer(query, answer, reference, llm):
    prompt = f"""
Compare the answer to the reference for completeness.

Query: {query}
Answer: {answer}
Reference: {reference}

What key points from the reference are missing in the answer?
"""
    result = llm.generate(prompt)
    if result.strip() and "none" not in result.lower():
        return {
            'type': 'incomplete',
            'missing_points': result
        }
    return None
```
**Fix:** Retrieve more context, improve prompt instructions

### 4. Context Ignored
**Symptom:** Model answers from parametric knowledge, ignoring context
**Detection:**
```python
def detect_context_ignored(answer, context, llm):
    # Check if answer could be derived from context
    prompt = f"""
Could this answer be generated from the context alone, or does it
require external knowledge not in the context?

Context: {context}
Answer: {answer}

Assessment (context_sufficient / requires_external):
"""
    result = llm.generate(prompt)
    if "requires_external" in result.lower():
        return {
            'type': 'context_ignored',
            'assessment': result
        }
    return None
```
**Fix:** Stronger system prompts, instruction tuning

## Failure Analysis Pipeline

```python
class FailureAnalyzer:
    def __init__(self, llm):
        self.llm = llm
        self.failure_log = []

    def analyze_query(self, query, results, answer, context,
                      relevant_ids=None, reference=None):
        failures = []

        # Retrieval analysis
        if relevant_ids:
            if mismatch := detect_retrieval_mismatch(query, results, relevant_ids):
                failures.append(mismatch)
            if ranking := detect_ranking_failure(results, relevant_ids):
                failures.append(ranking)

        if gap := detect_coverage_gap(query, results):
            failures.append(gap)

        # Generation analysis
        if halluc := detect_hallucination(answer, context, self.llm):
            failures.append(halluc)
        if misint := detect_misinterpretation(query, answer, context, self.llm):
            failures.append(misint)
        if reference and (incomplete := detect_incomplete_answer(query, answer, reference, self.llm)):
            failures.append(incomplete)

        # Log for analysis
        self.failure_log.append({
            'query': query,
            'failures': failures,
            'timestamp': datetime.now()
        })

        return failures

    def get_failure_distribution(self):
        """Aggregate failures by type."""
        distribution = defaultdict(int)
        for entry in self.failure_log:
            for failure in entry['failures']:
                distribution[failure['type']] += 1
        return dict(distribution)
```

## Systematic Debugging

### Step 1: Identify Failure Type
```python
def diagnose_failure(query, answer, context, results):
    # Is it a retrieval or generation problem?

    # Check retrieval quality
    if results_are_relevant(results, query):
        # Retrieval OK → Generation problem
        return analyze_generation_failure(query, answer, context)
    else:
        # Retrieval problem
        return analyze_retrieval_failure(query, results)
```

### Step 2: Root Cause Analysis
```
Retrieval Failure
├── No documents exist → Content gap
├── Documents exist but not retrieved
│   ├── Embedding mismatch → Model/chunking issue
│   ├── Query too vague → Query understanding
│   └── Filter too restrictive → Filter logic
└── Documents retrieved but ranked low
    └── Scoring problem → Reranking/fusion

Generation Failure
├── Hallucination
│   ├── Weak grounding prompt → Prompt engineering
│   ├── Context insufficient → Retrieval issue
│   └── Model tendency → Temperature/model choice
├── Misinterpretation
│   ├── Ambiguous context → Better chunking
│   └── Complex reasoning needed → Agentic approach
└── Incomplete
    ├── Context missing info → Retrieval K
    └── Prompt doesn't request detail → Prompt fix
```

### Step 3: Fix and Verify
```python
def verify_fix(fix_type, before_queries, after_results):
    """
    Compare failure rates before and after fix.
    """
    before_failures = analyze_batch(before_queries)
    after_failures = analyze_batch(after_results)

    improvement = {
        'before_rate': before_failures[fix_type] / len(before_queries),
        'after_rate': after_failures.get(fix_type, 0) / len(after_results),
    }
    improvement['reduction'] = (
        improvement['before_rate'] - improvement['after_rate']
    ) / improvement['before_rate']

    return improvement
```

## Failure Monitoring Dashboard

### Key Metrics
- Failure rate by type (daily/weekly trend)
- Top failure queries
- Failure rate by query category
- Time to resolution

### Alerts
```python
alerts = {
    'hallucination_rate': {
        'threshold': 0.05,
        'message': 'Hallucination rate exceeded 5%'
    },
    'retrieval_failure_rate': {
        'threshold': 0.20,
        'message': 'Retrieval failure rate exceeded 20%'
    },
    'total_failure_rate': {
        'threshold': 0.30,
        'message': 'Total failure rate exceeded 30%'
    }
}
```

## Continuous Improvement Loop

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Monitor │────▶│ Analyze │────▶│   Fix   │────▶│ Verify  │
│Failures │     │ Causes  │     │ Issues  │     │ Impact  │
└────┬────┘     └─────────┘     └─────────┘     └────┬────┘
     │                                               │
     └───────────────────────────────────────────────┘
```

## Checklist

- [ ] Failure taxonomy defined for your use case
- [ ] Detection methods implemented
- [ ] Failure logging in place
- [ ] Root cause analysis process documented
- [ ] Dashboard created
- [ ] Alerts configured
- [ ] Regular failure review scheduled
- [ ] Fix verification process defined

---

**Previous:** [A/B Testing](./ab-testing.md)
**Next:** [Security - PII and Redaction](../07-security-and-compliance/pii-and-redaction.md)
