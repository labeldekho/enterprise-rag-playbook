# Conversation RAG

RAG in multi-turn dialogues.

## The Conversational Challenge

Single-turn RAG:
```
User: "What is the refund policy?"
→ Retrieve → Answer
```

Multi-turn RAG:
```
User: "What is the refund policy?"
→ Retrieve → Answer (30 days, receipt required)

User: "What about electronics?"
→ Need to understand "What about" refers to refund policy
→ Need to search for electronics-specific refund rules
```

## Challenges in Conversational RAG

### 1. Coreference Resolution
```
Turn 1: "Tell me about the iPhone 15"
Turn 2: "How much does it cost?"

"it" = iPhone 15 (requires context)
```

### 2. Topic Continuation
```
Turn 1: "What's our vacation policy?"
Turn 2: "How do I request time off?"

Related but different retrieval needed
```

### 3. Topic Switching
```
Turn 1: "What's the refund policy?"
Turn 2: "Actually, what are your store hours?"

Must detect topic change
```

### 4. Follow-up Questions
```
Turn 1: "Who is the CEO?"
Turn 2: "When did they start?"

"they" refers to CEO, "start" means start as CEO
```

## Query Rewriting

Transform the current query using conversation context:

### LLM-Based Rewriting
```python
def rewrite_query(query, conversation_history):
    prompt = f"""
Given the conversation history and the latest query, rewrite the query
to be standalone and self-contained. Include all necessary context.

Conversation:
{format_history(conversation_history)}

Latest query: {query}

Rewritten query (standalone):
"""
    return llm.generate(prompt)
```

### Example Rewrites
```
History: "Tell me about the iPhone 15"
Query: "How much does it cost?"
Rewritten: "What is the price of the iPhone 15?"

History: "What's our vacation policy?"
Query: "How do I request time off?"
Rewritten: "How do I request vacation time off according to company policy?"
```

### Rule-Based Rewriting
```python
def simple_rewrite(query, last_query, last_response):
    # Handle pronouns
    pronouns = ['it', 'they', 'them', 'this', 'that']
    for pronoun in pronouns:
        if pronoun in query.lower():
            # Extract main entity from last exchange
            entity = extract_main_entity(last_query, last_response)
            query = query.replace(pronoun, entity)

    return query
```

## Conversation-Aware Retrieval

### Strategy 1: Rewrite Then Retrieve
```python
def conversational_rag_v1(query, history, retriever):
    # Rewrite query to be standalone
    standalone_query = rewrite_query(query, history)

    # Retrieve with standalone query
    results = retriever.search(standalone_query)

    return results, standalone_query
```

### Strategy 2: Multi-Query Retrieval
```python
def conversational_rag_v2(query, history, retriever):
    # Generate multiple query variants
    queries = [
        query,  # Original
        rewrite_query(query, history),  # Rewritten
        combine_with_context(query, history[-1])  # Last turn combined
    ]

    # Retrieve for all queries
    all_results = []
    for q in queries:
        results = retriever.search(q)
        all_results.extend(results)

    # Dedupe and rank
    return dedupe_and_rank(all_results)
```

### Strategy 3: History-Augmented Retrieval
```python
def conversational_rag_v3(query, history, retriever):
    # Include recent history in retrieval
    context = format_recent_history(history, max_turns=3)
    augmented_query = f"{context}\n\nCurrent question: {query}"

    # Some retrievers handle this well
    results = retriever.search(augmented_query)

    return results
```

## Context Management

### Sliding Window
```python
class ConversationManager:
    def __init__(self, max_turns=10, max_tokens=4000):
        self.messages = []
        self.max_turns = max_turns
        self.max_tokens = max_tokens

    def add_turn(self, user_msg, assistant_msg):
        self.messages.append({'user': user_msg, 'assistant': assistant_msg})
        self._trim()

    def _trim(self):
        # Trim by turn count
        while len(self.messages) > self.max_turns:
            self.messages.pop(0)

        # Trim by token count
        while self._token_count() > self.max_tokens:
            self.messages.pop(0)

    def get_context(self):
        return self.messages
```

### Summarized History
```python
class SummarizedConversation:
    def __init__(self, summarize_after=5):
        self.recent_messages = []
        self.summary = ""
        self.summarize_after = summarize_after

    def add_turn(self, user_msg, assistant_msg):
        self.recent_messages.append({
            'user': user_msg,
            'assistant': assistant_msg
        })

        if len(self.recent_messages) > self.summarize_after:
            self._summarize_old()

    def _summarize_old(self):
        # Summarize oldest messages
        to_summarize = self.recent_messages[:self.summarize_after - 2]
        self.recent_messages = self.recent_messages[self.summarize_after - 2:]

        new_summary = summarize_conversation(to_summarize)
        if self.summary:
            self.summary = f"{self.summary}\n{new_summary}"
        else:
            self.summary = new_summary

    def get_context(self):
        return {
            'summary': self.summary,
            'recent': self.recent_messages
        }
```

## Intent Detection

### Topic Change Detection
```python
def detect_topic_change(current_query, history):
    if not history:
        return True  # First query

    prompt = f"""
Given the conversation history and current query, determine if the user
is continuing the same topic or switching to a new topic.

History:
{format_history(history[-3:])}

Current query: {current_query}

Is this a topic change? (yes/no):
"""
    response = llm.generate(prompt)
    return 'yes' in response.lower()
```

### Handling Topic Changes
```python
def conversational_rag_with_intent(query, history, retriever):
    # Detect intent
    is_topic_change = detect_topic_change(query, history)

    if is_topic_change:
        # Fresh retrieval, don't rewrite
        results = retriever.search(query)
        effective_query = query
    else:
        # Rewrite with context
        effective_query = rewrite_query(query, history)
        results = retriever.search(effective_query)

    return results, effective_query
```

## Prompt Design for Conversations

### Including History in Prompt
```python
def build_conversational_prompt(query, history, retrieved_docs):
    prompt = f"""
You are a helpful assistant. Use the conversation history and retrieved
documents to answer the user's question.

## Conversation History
{format_history(history)}

## Retrieved Documents
{format_documents(retrieved_docs)}

## Current Question
{query}

## Instructions
- Reference conversation history when relevant
- Base factual claims on retrieved documents
- If the question refers to previous discussion, use that context
- If information is not available, say so

Answer:
"""
    return prompt
```

### Clarification Requests
```python
def needs_clarification(query, history, retrieved_docs):
    prompt = f"""
Given this conversation and query, determine if clarification is needed.

History: {format_history(history[-3:])}
Query: {query}
Retrieved docs summary: {summarize_docs(retrieved_docs)}

Does the query need clarification? If yes, what question should we ask?
Output format: {{"needs_clarification": true/false, "question": "..."}}
"""
    response = llm.generate(prompt)
    return json.loads(response)
```

## Complete Pipeline

```python
class ConversationalRAG:
    def __init__(self, retriever, llm, max_history_turns=10):
        self.retriever = retriever
        self.llm = llm
        self.conversation = ConversationManager(max_turns=max_history_turns)

    def chat(self, user_message):
        history = self.conversation.get_context()

        # 1. Detect if topic change
        is_new_topic = detect_topic_change(user_message, history)

        # 2. Rewrite query if continuing topic
        if is_new_topic or not history:
            search_query = user_message
        else:
            search_query = rewrite_query(user_message, history)

        # 3. Retrieve relevant documents
        documents = self.retriever.search(search_query)

        # 4. Check if clarification needed
        clarification = needs_clarification(user_message, history, documents)
        if clarification['needs_clarification']:
            response = clarification['question']
        else:
            # 5. Generate response
            prompt = build_conversational_prompt(
                user_message, history, documents
            )
            response = self.llm.generate(prompt)

        # 6. Update conversation history
        self.conversation.add_turn(user_message, response)

        return response
```

## Evaluation

### Conversational Metrics
- **Turn-level relevance:** Is each response relevant to the query?
- **Context utilization:** Does the response use conversation context appropriately?
- **Topic coherence:** Does the conversation flow naturally?
- **Coreference accuracy:** Are pronouns resolved correctly?

### Test Cases
```python
test_conversations = [
    {
        "turns": [
            {"user": "What is the return policy?", "expected_topic": "returns"},
            {"user": "What about for electronics?", "expected_resolution": "return policy for electronics"},
            {"user": "Is there a restocking fee?", "expected_topic": "returns"},
        ]
    },
    # ... more test cases
]
```

## Checklist

- [ ] Query rewriting implemented
- [ ] Topic change detection
- [ ] Conversation history management
- [ ] Context summarization for long conversations
- [ ] Coreference resolution working
- [ ] Clarification handling
- [ ] Prompt includes relevant history
- [ ] Evaluation metrics defined
- [ ] Test conversations created

---

**Previous:** [Long-Term Memory](./long-term-memory.md)
**Next:** [Evaluation Metrics](../06-evaluation/eval-metrics.md)
