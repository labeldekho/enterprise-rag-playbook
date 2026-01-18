# Should You Use RAG?

A decision framework for evaluating RAG as a solution.

## The Decision Tree

```
START
  │
  ▼
┌─────────────────────────────────────────┐
│ Does the answer exist in your data?     │
└─────────────────────────────────────────┘
  │           │
  No          Yes
  │           │
  ▼           ▼
┌─────────┐  ┌─────────────────────────────────────────┐
│ RAG     │  │ Does the base model already know it?    │
│ won't   │  └─────────────────────────────────────────┘
│ help    │    │           │
└─────────┘    Yes         No
               │           │
               ▼           ▼
         ┌─────────┐  ┌─────────────────────────────────────────┐
         │ Maybe   │  │ Is the data relatively stable?          │
         │ skip    │  │ (not changing every second)             │
         │ RAG     │  └─────────────────────────────────────────┘
         └─────────┘    │           │
                        No          Yes
                        │           │
                        ▼           ▼
                  ┌─────────┐  ┌─────────────────────────────────────────┐
                  │Consider │  │ Can you accept 200-500ms latency for    │
                  │real-time│  │ retrieval?                              │
                  │APIs     │  └─────────────────────────────────────────┘
                  └─────────┘    │           │
                                 No          Yes
                                 │           │
                                 ▼           ▼
                          ┌─────────┐  ┌─────────────────────────────────┐
                          │Consider │  │ RAG is likely a good fit        │
                          │caching  │  └─────────────────────────────────┘
                          │or other │
                          │approach │
                          └─────────┘
```

## Key Questions

### 1. Does the answer exist in your data?

**If YES:** RAG can help retrieve and present it
**If NO:** RAG cannot create knowledge that doesn't exist

Examples where answer exists:
- Company policies
- Product documentation
- Historical records
- Technical specifications

Examples where answer doesn't exist:
- Future predictions
- Creative content
- Novel analysis

### 2. Does the base model already know it?

**If YES:** You might not need RAG

Test by asking the LLM directly:
- If it answers correctly and consistently → Skip RAG
- If it hallucinates or is outdated → RAG helps

Examples where model already knows:
- Common programming questions
- Public knowledge
- Standard procedures

### 3. How often does the data change?

| Change Frequency | RAG Suitability |
|------------------|-----------------|
| Never/Yearly | Excellent |
| Monthly | Good |
| Daily | Acceptable |
| Hourly | Challenging |
| Real-time | Not recommended |

### 4. What's your latency budget?

| Budget | RAG Impact |
|--------|------------|
| < 100ms | Too tight for RAG |
| 100-500ms | Possible with optimization |
| 500ms-2s | Comfortable for RAG |
| > 2s | Plenty of room |

### 5. Do users need source attribution?

**If YES:** RAG provides natural citation ability
**If NO:** Simpler approaches might suffice

## Scoring Your Use Case

Rate each factor 1-5:

| Factor | Score | Weight |
|--------|-------|--------|
| Data exists and is documented | ___ | 3x |
| Model doesn't reliably know it | ___ | 2x |
| Data changes monthly or less | ___ | 2x |
| Latency budget > 500ms | ___ | 1x |
| Source attribution valuable | ___ | 1x |
| Scale is manageable | ___ | 1x |

**Scoring:**
- 40+ points: Strong RAG candidate
- 25-39 points: RAG may help, evaluate carefully
- < 25 points: Consider alternatives

## Alternatives to RAG

### Prompt Engineering
**When to use instead of RAG:**
- Small amount of reference data
- Data fits in context window
- Static information

```python
# Instead of RAG, just include in prompt
system_prompt = """
You are a customer service agent. Here is our return policy:
- 30 day returns for most items
- Electronics: 15 days
- Receipt required

Answer customer questions based on this policy.
"""
```

### Fine-Tuning
**When to use instead of RAG:**
- Need to change model behavior/style
- Knowledge is stable and foundational
- Want faster inference without retrieval

**When NOT fine-tuning:**
- Data changes frequently
- Need source attribution
- Limited training data

### Function Calling / APIs
**When to use instead of RAG:**
- Data is highly dynamic
- Need real-time information
- Structured data access

```python
# Instead of RAG, call an API
def get_current_price(product_id):
    return api.get_price(product_id)

# LLM uses this function when needed
```

### Caching / Pre-computation
**When to use instead of RAG:**
- Common questions with stable answers
- High query volume on same questions
- Latency is critical

## Red Flags

Don't use RAG if:

1. **Data doesn't exist** - You can't retrieve what isn't there
2. **Ultra-low latency required** - Gaming, HFT, real-time processing
3. **Data changes constantly** - Stock tickers, live sensors
4. **Simple transformation** - JSON to CSV, format conversion
5. **Creative generation** - Fiction, marketing copy, brainstorming

## Green Flags

RAG is likely a good fit if:

1. **Knowledge base exists** - Documentation, policies, archives
2. **Answers need grounding** - Factual accuracy matters
3. **Sources matter** - Users want to verify
4. **Data evolves but not chaotically** - Monthly updates are fine
5. **Internal/proprietary data** - Model never saw this in training

## Case Studies

### Good RAG Use Case
**Customer support for a SaaS product**
- Extensive documentation exists ✓
- FAQ and help articles available ✓
- Data updates with product releases ✓
- Users want accurate answers ✓
- Source links help users self-serve ✓

### Poor RAG Use Case
**Real-time stock trading assistant**
- Prices change every second ✗
- Need sub-100ms responses ✗
- RAG latency unacceptable ✗
- Better: Direct API integration

### Borderline Case
**Internal HR policy questions**
- Policies exist ✓
- Model might know general HR ⚠️
- Updates are infrequent ✓
- Consider: Is the base model good enough?

## Decision Template

```markdown
## RAG Decision: [Project Name]

### Use Case Summary
[Brief description]

### Data Assessment
- [ ] Data exists in retrievable form
- [ ] Data is documented/structured
- [ ] Volume: ___ documents
- [ ] Update frequency: ___

### Model Assessment
- [ ] Tested base model on sample queries
- [ ] Base model accuracy: ___%
- [ ] Hallucination rate: ___%

### Requirements
- [ ] Latency budget: ___ ms
- [ ] Source attribution needed: Yes/No
- [ ] Accuracy requirement: ___%

### Decision
[ ] Proceed with RAG
[ ] Consider alternative: ___
[ ] Need more information

### Rationale
[Explain the decision]
```

---

**Next:** [RAG vs Fine-Tuning](./rag-vs-finetuning.md)
