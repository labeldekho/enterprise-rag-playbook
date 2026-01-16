# Long-Term Memory

Beyond the context window.

## The Memory Problem

LLMs have no persistent memory:
- Each request starts fresh
- Context window is the only "memory"
- Previous conversations are forgotten

RAG provides a form of long-term memory:
- Vector database = external memory store
- Retrieval = recall mechanism
- Augmentation = memory injection

## Memory Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Memory System                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐   │
│  │   Working     │    │   Short-Term  │    │   Long-Term   │   │
│  │   Memory      │    │   Memory      │    │   Memory      │   │
│  │               │    │               │    │               │   │
│  │ Context       │    │ Session       │    │ Vector DB     │   │
│  │ Window        │    │ History       │    │ Knowledge     │   │
│  │               │    │               │    │ Base          │   │
│  │ ~128K tokens  │    │ ~10K tokens   │    │ Unlimited     │   │
│  └───────────────┘    └───────────────┘    └───────────────┘   │
│         ▲                    ▲                    ▲              │
│         │                    │                    │              │
│         └──────────── Query triggers retrieval ──┘              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Memory Types in RAG

### 1. Episodic Memory
What happened in past interactions:
- Conversation history
- User actions and preferences
- Past questions and answers

```python
class EpisodicMemory:
    def __init__(self, vector_db, user_id):
        self.vector_db = vector_db
        self.user_id = user_id

    def store_interaction(self, query, response, metadata):
        interaction = {
            'query': query,
            'response': response,
            'timestamp': datetime.now(),
            'user_id': self.user_id,
            **metadata
        }
        embedding = embed(f"Q: {query}\nA: {response}")
        self.vector_db.upsert(
            id=generate_id(),
            vector=embedding,
            metadata=interaction
        )

    def recall_similar(self, query, top_k=5):
        return self.vector_db.search(
            vector=embed(query),
            filter={'user_id': self.user_id},
            top_k=top_k
        )
```

### 2. Semantic Memory
Facts and knowledge:
- Documents and their contents
- Structured data
- Domain knowledge

```python
class SemanticMemory:
    def __init__(self, vector_db):
        self.vector_db = vector_db

    def store_document(self, document, chunks):
        for chunk in chunks:
            self.vector_db.upsert(
                id=chunk.id,
                vector=embed(chunk.text),
                metadata={
                    'document_id': document.id,
                    'source': document.source,
                    'type': 'semantic',
                    **chunk.metadata
                }
            )

    def recall(self, query, top_k=10, filters=None):
        return self.vector_db.search(
            vector=embed(query),
            filter={'type': 'semantic', **(filters or {})},
            top_k=top_k
        )
```

### 3. Procedural Memory
How to do things:
- Tool usage patterns
- Successful strategies
- Error recovery procedures

```python
class ProceduralMemory:
    def __init__(self, vector_db):
        self.vector_db = vector_db

    def store_procedure(self, task, steps, outcome):
        procedure = {
            'task': task,
            'steps': steps,
            'outcome': outcome,
            'success': outcome == 'success',
            'type': 'procedural'
        }
        embedding = embed(f"Task: {task}. Steps: {steps}")
        self.vector_db.upsert(
            id=generate_id(),
            vector=embedding,
            metadata=procedure
        )

    def recall_procedure(self, task, successful_only=True):
        filters = {'type': 'procedural'}
        if successful_only:
            filters['success'] = True
        return self.vector_db.search(
            vector=embed(task),
            filter=filters,
            top_k=5
        )
```

## Memory Consolidation

Moving information between memory tiers:

### Session to Long-Term
```python
def consolidate_session(session):
    """
    At end of session, persist important information.
    """
    # Extract key facts
    facts = extract_facts(session.messages)
    for fact in facts:
        semantic_memory.store(fact)

    # Store conversation summary
    summary = summarize_conversation(session.messages)
    episodic_memory.store(
        query="Session summary",
        response=summary,
        metadata={'session_id': session.id}
    )

    # Store successful procedures
    procedures = extract_procedures(session)
    for proc in procedures:
        if proc.successful:
            procedural_memory.store(proc)
```

### Memory Decay
```python
def apply_memory_decay(memory_db, decay_rate=0.01):
    """
    Reduce importance of old memories.
    Delete very old or unused memories.
    """
    all_memories = memory_db.get_all()
    for memory in all_memories:
        age_days = (datetime.now() - memory.timestamp).days
        decay_factor = math.exp(-decay_rate * age_days)

        if decay_factor < 0.1:  # Very old
            memory_db.delete(memory.id)
        else:
            memory.importance *= decay_factor
            memory_db.update(memory)
```

## User-Specific Memory

### Personal Knowledge Base
```python
class UserMemory:
    def __init__(self, user_id, base_memory, user_memory_db):
        self.user_id = user_id
        self.base_memory = base_memory  # Shared knowledge
        self.user_memory = user_memory_db  # User-specific

    def recall(self, query, top_k=10):
        # Search both memories
        base_results = self.base_memory.search(query, top_k=top_k)
        user_results = self.user_memory.search(
            query,
            filter={'user_id': self.user_id},
            top_k=top_k
        )

        # Merge, preferring user-specific
        merged = merge_results(
            user_results,
            base_results,
            user_boost=1.2
        )
        return merged[:top_k]
```

### Preference Learning
```python
class PreferenceMemory:
    def __init__(self, user_id, db):
        self.user_id = user_id
        self.db = db

    def record_feedback(self, query, response, feedback):
        """
        feedback: 'positive', 'negative', or specific correction
        """
        self.db.store({
            'user_id': self.user_id,
            'query': query,
            'response': response,
            'feedback': feedback,
            'timestamp': datetime.now()
        })

    def get_preferences(self, query):
        """
        Retrieve relevant past feedback to guide response.
        """
        similar = self.db.search(
            embed(query),
            filter={'user_id': self.user_id}
        )
        return [r for r in similar if r.feedback == 'positive']
```

## Memory in Prompts

### Including Memory Context
```python
def build_prompt_with_memory(query, user_id):
    # Retrieve from different memory types
    semantic_context = semantic_memory.recall(query)
    episodic_context = episodic_memory.recall(query, user_id)
    procedural_context = procedural_memory.recall(query)

    prompt = f"""
You have access to the following memory:

## Knowledge Base
{format_chunks(semantic_context)}

## Past Interactions with This User
{format_episodes(episodic_context)}

## Known Procedures
{format_procedures(procedural_context)}

## Current Query
{query}

Answer based on the memory above. Reference specific past interactions if relevant.
"""
    return prompt
```

## Memory Challenges

### 1. Memory Pollution
**Problem:** Bad or outdated information persists
**Solution:** Expiration dates, quality scores, manual curation

### 2. Privacy Concerns
**Problem:** Storing user interactions raises privacy issues
**Solution:** Anonymization, retention policies, user consent

### 3. Conflicting Memories
**Problem:** Different sources say different things
**Solution:** Recency weighting, source authority, conflict resolution

### 4. Memory Bloat
**Problem:** Too much stored, retrieval becomes slow/noisy
**Solution:** Periodic cleanup, importance ranking, summarization

## Implementation Patterns

### Memory-Augmented RAG
```python
class MemoryAugmentedRAG:
    def __init__(self, retriever, memory_system):
        self.retriever = retriever
        self.memory = memory_system

    def query(self, question, user_id=None):
        # Standard retrieval
        documents = self.retriever.search(question)

        # Memory retrieval
        memories = self.memory.recall(question, user_id)

        # Combine context
        context = {
            'documents': documents,
            'memories': memories,
            'user_context': self.memory.get_user_context(user_id)
        }

        # Generate with memory-aware prompt
        return self.generate(question, context)
```

## Checklist

- [ ] Memory types identified (episodic, semantic, procedural)
- [ ] Storage mechanism for each type
- [ ] Retrieval mechanism for each type
- [ ] Memory consolidation pipeline
- [ ] User-specific memory isolation
- [ ] Memory decay/cleanup strategy
- [ ] Privacy considerations addressed
- [ ] Conflict resolution defined
- [ ] Performance impact assessed

---

**Previous:** [Context Windows](./context-windows.md)
**Next:** [Conversation RAG](./conversation-rag.md)
