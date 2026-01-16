# When NOT to Use RAG

This section exists to **save you time and money**. RAG is powerful, but it's not always the right tool.

## Explicit Non-Use Cases

### 1. Creative Writing and Generation

**Don't use RAG for:**
- Fiction writing
- Marketing copy that should be original
- Brainstorming sessions
- Poetry and creative content

**Why:** RAG grounds responses in existing data. Creative tasks need the model to generate novel content, not retrieve existing knowledge.

### 2. Ultra-Low Latency Systems

**Don't use RAG for:**
- Real-time gaming
- High-frequency trading signals
- Live audio/video processing
- Sub-100ms response requirements

**Why:** RAG adds retrieval latency (typically 50-500ms). If your latency budget is tight, RAG may not fit.

### 3. Highly Volatile Data

**Don't use RAG for:**
- Live stock prices
- Real-time sensor data
- Streaming metrics
- Data that changes every second

**Why:** RAG indexes are not real-time. Even "fast" update pipelines have lag. Use direct API calls or streaming architectures instead.

### 4. Simple Transformations

**Don't use RAG for:**
- Format conversion (JSON to CSV)
- Data extraction with fixed schemas
- Translation of short texts
- Summarization of single documents already in context

**Why:** If the data fits in context and the task is simple, RAG adds complexity without benefit. Just pass the data directly.

### 5. When the Base Model Already Knows

**Don't use RAG for:**
- General knowledge questions
- Common programming tasks
- Well-documented public APIs
- Historical facts

**Why:** If GPT-4 or Claude already knows the answer reliably, retrieval adds latency without improving accuracy.

## Warning Signs You Might Be Misusing RAG

| Symptom | Possible Issue |
|---------|----------------|
| Retrieval never returns useful results | Wrong use case or bad data |
| Answers are worse with RAG than without | Retrieved context is confusing the model |
| Latency is unacceptable | RAG isn't right for this workload |
| Index updates can't keep up | Data is too volatile |
| Users don't care about sources | RAG's traceability benefit is wasted |

## Questions to Ask Before Building RAG

1. **Does the answer exist in my data?**
   - If no → RAG won't help

2. **Is the data relatively stable?**
   - If it changes every second → Consider alternatives

3. **Does latency budget allow for retrieval?**
   - If sub-100ms required → Probably not

4. **Would citations add value?**
   - If users need to verify → RAG shines

5. **Is the base model insufficient?**
   - If it already knows the answer → Skip RAG

## Alternative Approaches

| Scenario | Instead of RAG |
|----------|----------------|
| Need latest data | Direct API calls |
| Data fits in context | Simple prompting |
| Need to change model behavior | Fine-tuning |
| Need structured extraction | Function calling |
| Need real-time data | Streaming + caching |

## The Cost of Wrong Decisions

Building RAG when it's not needed means:
- Wasted engineering time
- Added system complexity
- Higher operational costs
- Worse user experience (latency)
- Technical debt

Building RAG poorly when it IS needed means:
- Hallucinations with false confidence
- User trust erosion
- Compliance risks
- Expensive rework

## Key Takeaways

1. RAG adds value only when retrieval adds value
2. Creative, real-time, and volatile use cases are poor fits
3. Simple tasks don't need complex solutions
4. Always validate that RAG improves outcomes before committing
5. The decision NOT to use RAG is often the right one

---

**Next:** [RAG Maturity Levels](../02-rag-levels/level-1-basic.md)
