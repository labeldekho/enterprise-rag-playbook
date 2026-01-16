# Context Windows

Understanding the LLM's working memory.

## What Is a Context Window?

The context window is the maximum number of tokens an LLM can process in a single request:
- Input tokens (system prompt + user query + retrieved context)
- Output tokens (generated response)

```
┌──────────────────────────────────────────────────┐
│                 Context Window                    │
├──────────────────────────────────────────────────┤
│  System Prompt  │  User Query  │  Retrieved Docs │
│     (~500)      │   (~100)     │    (~3000)      │
├──────────────────────────────────────────────────┤
│              Generated Response (~500)            │
└──────────────────────────────────────────────────┘
     Total: Must fit within model's limit
```

## Current Context Window Sizes

| Model | Context Window | Notes |
|-------|---------------|-------|
| GPT-4 Turbo | 128K tokens | ~96K words |
| GPT-4o | 128K tokens | Multimodal |
| Claude 3 Opus | 200K tokens | ~150K words |
| Claude 3.5 Sonnet | 200K tokens | Fast |
| Gemini 1.5 Pro | 1M tokens | Largest |
| Llama 3 70B | 8K tokens | Open source |
| Mistral Large | 32K tokens | Open source |

## Context Window Math

### Token Estimation
- English: ~1 token per 4 characters
- Code: ~1 token per 3 characters
- 1 page of text ≈ 400-500 tokens

### Budget Allocation
```python
def calculate_context_budget(model_limit, response_reserve=1000):
    """
    Allocate context window budget.
    """
    available = model_limit - response_reserve

    # Typical allocation
    system_prompt = 500  # Instructions, few-shot examples
    user_query = 200     # User's question
    safety_margin = 500  # Buffer for tokenization variance

    retrieval_budget = available - system_prompt - user_query - safety_margin

    return {
        'system_prompt': system_prompt,
        'user_query': user_query,
        'retrieval': retrieval_budget,
        'response_reserve': response_reserve
    }

# Example for GPT-4 Turbo (128K)
budget = calculate_context_budget(128000)
# retrieval_budget ≈ 125,800 tokens
```

## The "Lost in the Middle" Problem

Research shows LLMs pay less attention to information in the middle of the context:

```
Attention Pattern:
┌────────────────────────────────────────────────────┐
│ ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████████ │
│  High   │           Low attention          │  High  │
│attention│                                  │attention│
│ (start) │                                  │  (end)  │
└────────────────────────────────────────────────────┘
```

### Mitigation Strategies

**1. Put important info at start/end**
```python
def arrange_context(chunks, query):
    # Most relevant at start and end
    ranked = rank_by_relevance(chunks, query)
    mid_point = len(ranked) // 2

    arranged = []
    for i, chunk in enumerate(ranked):
        if i % 2 == 0:
            arranged.insert(0, chunk)  # Add to start
        else:
            arranged.append(chunk)      # Add to end

    return arranged
```

**2. Summarize middle content**
```python
def compress_middle(chunks, max_middle_tokens=2000):
    start = chunks[:2]
    end = chunks[-2:]
    middle = chunks[2:-2]

    if count_tokens(middle) > max_middle_tokens:
        middle_text = " ".join([c.text for c in middle])
        middle_summary = summarize(middle_text, max_tokens=max_middle_tokens)
        middle = [Chunk(text=middle_summary)]

    return start + middle + end
```

**3. Use explicit markers**
```python
prompt = f"""
Answer based on the following documents.
The MOST RELEVANT document is marked with [IMPORTANT].

{context_with_markers}

Question: {query}
"""
```

## Context Truncation Strategies

### When Context Exceeds Limit

**1. Relevance-based truncation**
```python
def truncate_by_relevance(chunks, query, max_tokens):
    ranked = rank_by_relevance(chunks, query)
    selected = []
    current_tokens = 0

    for chunk in ranked:
        chunk_tokens = count_tokens(chunk.text)
        if current_tokens + chunk_tokens <= max_tokens:
            selected.append(chunk)
            current_tokens += chunk_tokens
        else:
            break

    return selected
```

**2. Recency-based truncation**
```python
def truncate_by_recency(chunks, max_tokens):
    # Most recent first
    sorted_chunks = sorted(chunks, key=lambda c: c.timestamp, reverse=True)
    return truncate_by_relevance(sorted_chunks, max_tokens)
```

**3. Diversity-based selection**
```python
def select_diverse(chunks, max_tokens, diversity_weight=0.3):
    """
    Balance relevance with diversity.
    Prevents redundant information.
    """
    selected = []
    remaining = chunks.copy()

    while remaining and count_tokens(selected) < max_tokens:
        # Score by relevance - similarity to already selected
        scores = []
        for chunk in remaining:
            relevance = chunk.relevance_score
            if selected:
                similarity = max_similarity(chunk, selected)
                score = relevance - diversity_weight * similarity
            else:
                score = relevance
            scores.append((chunk, score))

        # Select highest scoring
        best = max(scores, key=lambda x: x[1])[0]
        selected.append(best)
        remaining.remove(best)

    return selected
```

## Context Compression

### Extractive Compression
Keep only relevant sentences:
```python
def extractive_compress(text, query, keep_ratio=0.5):
    sentences = split_sentences(text)
    scores = score_relevance(sentences, query)
    keep_count = int(len(sentences) * keep_ratio)
    top_sentences = sorted(
        zip(sentences, scores),
        key=lambda x: x[1],
        reverse=True
    )[:keep_count]
    # Maintain original order
    return " ".join([s for s, _ in sorted(top_sentences, key=original_order)])
```

### Abstractive Compression
Summarize the content:
```python
def abstractive_compress(text, max_tokens=500):
    prompt = f"""
    Summarize the following text, preserving key facts and details.
    Keep it under {max_tokens} tokens.

    Text: {text}
    """
    return llm.generate(prompt)
```

### Hybrid Compression
```python
def hybrid_compress(chunks, query, target_tokens):
    # First: extractive per-chunk
    compressed = []
    for chunk in chunks:
        if chunk.relevance_score > 0.8:
            compressed.append(chunk.text)  # Keep high relevance
        else:
            compressed.append(extractive_compress(chunk.text, query))

    # If still too long: abstractive summary of middle
    if count_tokens(compressed) > target_tokens:
        compressed = compress_middle(compressed, target_tokens)

    return compressed
```

## Multi-Turn Context Management

### Conversation History
```python
class ConversationContext:
    def __init__(self, max_history_tokens=4000):
        self.messages = []
        self.max_history_tokens = max_history_tokens

    def add_message(self, role, content):
        self.messages.append({'role': role, 'content': content})
        self._trim_history()

    def _trim_history(self):
        while count_tokens(self.messages) > self.max_history_tokens:
            # Remove oldest non-system message
            for i, msg in enumerate(self.messages):
                if msg['role'] != 'system':
                    self.messages.pop(i)
                    break
```

### Conversation Summarization
```python
def summarize_conversation(messages, max_tokens=500):
    prompt = """
    Summarize the following conversation, keeping key points:
    - Main topics discussed
    - Decisions made
    - Unresolved questions

    Conversation:
    {conversation}
    """
    conversation = format_messages(messages)
    return llm.generate(prompt.format(conversation=conversation))
```

## Monitoring Context Usage

### Metrics to Track
```python
class ContextMetrics:
    def __init__(self):
        self.total_tokens_used = []
        self.retrieval_tokens = []
        self.utilization_ratio = []

    def record(self, request):
        total = count_tokens(request)
        retrieval = count_tokens(request.retrieved_context)
        limit = get_model_limit(request.model)

        self.total_tokens_used.append(total)
        self.retrieval_tokens.append(retrieval)
        self.utilization_ratio.append(total / limit)
```

### Alerts
- Context utilization > 90%
- Frequent truncation events
- Summarization failures

## Checklist

- [ ] Context budget calculated for target model
- [ ] Truncation strategy implemented
- [ ] Lost-in-middle mitigation applied
- [ ] Compression available for long content
- [ ] Multi-turn context management
- [ ] Token counting accurate
- [ ] Monitoring in place
- [ ] Fallback for context overflow

---

**Next:** [Long-Term Memory](./long-term-memory.md)
