# Level 4: Agentic RAG

When retrieval needs reasoning.

## What Problem This Level Solves

- Questions require multiple retrieval steps
- Need to combine information from disparate sources
- Complex reasoning over retrieved data
- Dynamic decisions about what to retrieve next

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        Agent                             │
│  ┌─────────────────────────────────────────────────┐    │
│  │                  Planning Loop                    │    │
│  │  1. Analyze query                                │    │
│  │  2. Plan retrieval steps                         │    │
│  │  3. Execute retrievals                           │    │
│  │  4. Evaluate sufficiency                         │    │
│  │  5. Synthesize or continue                       │    │
│  └─────────────────────────────────────────────────┘    │
│                          │                               │
│         ┌────────────────┼────────────────┐             │
│         ▼                ▼                ▼             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Vector    │  │   Keyword   │  │   External  │     │
│  │   Search    │  │   Search    │  │    APIs     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│         │                │                │             │
│         └────────────────┴────────────────┘             │
│                          │                               │
│                          ▼                               │
│                  ┌─────────────┐                        │
│                  │  Synthesis  │                        │
│                  │     LLM     │                        │
│                  └─────────────┘                        │
└─────────────────────────────────────────────────────────┘
```

## Components

### Agent Controller
- Orchestrates retrieval strategy
- Decides when to stop retrieving
- Manages tool selection
- Handles failures and retries

### Tool Set
- Vector search tool
- Keyword search tool
- Web search tool
- API call tools
- Calculator/code execution

### Planning Module
- Query decomposition
- Sub-question generation
- Retrieval strategy selection
- Progress tracking

### Synthesis Engine
- Combines multi-source information
- Resolves contradictions
- Generates coherent response
- Cites sources appropriately

## Data Requirements

| Requirement | Level 4 Spec |
|-------------|--------------|
| Same as Level 3 | Plus tool definitions |
| External APIs | Often required |
| State management | Required for multi-step |
| Caching | Critical for performance |
| Monitoring | Essential for debugging |

## Latency Expectations

| Operation | Typical Latency |
|-----------|-----------------|
| Query analysis | 200-500ms |
| Per retrieval step | 500-1500ms |
| Steps (2-5 typical) | 1000-7500ms |
| Final synthesis | 500-2000ms |
| **Total** | **1700-10000ms** |

Agentic RAG is significantly slower due to multi-step reasoning.

## Failure Modes

### 1. Infinite Loops
**Symptom:** Agent never stops retrieving
**Cause:** No termination criteria
**Fix:** Hard limits on steps, sufficiency checks

### 2. Retrieval Drift
**Symptom:** Each step gets further from original query
**Cause:** Poor query reformulation
**Fix:** Include original query in each step, scoring

### 3. Contradictory Sources
**Symptom:** Agent retrieves conflicting information
**Cause:** No conflict resolution strategy
**Fix:** Source ranking, recency weighting, explicit handling

### 4. Latency Explosion
**Symptom:** Response takes too long
**Cause:** Too many retrieval steps
**Fix:** Parallel execution, early termination, caching

### 5. Cost Explosion
**Symptom:** API costs skyrocket
**Cause:** Many LLM calls per query
**Fix:** Smaller models for planning, caching, limits

## When to Stop Here

Stay at Level 4 if:
- Complex queries handled adequately
- Latency acceptable for use case
- Cost manageable
- No enterprise-scale requirements

## When to Advance

Move to Level 5 if:
- Multi-tenant access control needed
- Compliance requirements (audit, PII)
- High availability required
- Massive scale (millions of queries)

## Implementation Checklist

- [ ] Agent framework selected/built
- [ ] Tool definitions complete
- [ ] Planning prompts tuned
- [ ] Termination criteria defined
- [ ] Parallel execution where possible
- [ ] Caching layer implemented
- [ ] Cost monitoring in place
- [ ] Latency budgets enforced
- [ ] Failure handling robust

## Agentic Patterns

### Query Decomposition
```
Original: "Compare the pricing models of AWS and Azure for GPU instances"
Decomposed:
  1. "What are AWS GPU instance pricing models?"
  2. "What are Azure GPU instance pricing models?"
  3. Synthesize comparison
```

### Iterative Refinement
```
Step 1: Broad retrieval → "Needs more specific information about X"
Step 2: Targeted retrieval for X → "Found X, now need Y"
Step 3: Targeted retrieval for Y → "Sufficient to answer"
Step 4: Synthesize final answer
```

### Self-Correction
```
Step 1: Retrieve and generate draft
Step 2: Check if answer is grounded
Step 3: If gaps found, retrieve more
Step 4: Regenerate with additional context
```

## Key Technologies

### Agent Frameworks
- LangChain Agents
- LlamaIndex Agents
- AutoGPT patterns
- Custom orchestration

### Tool Orchestration
- Function calling (OpenAI, Anthropic)
- ReAct pattern
- Plan-and-Execute

---

**Previous:** [Level 3: Multimodal RAG](./level-3-multimodal.md)
**Next:** [Level 5: Enterprise RAG](./level-5-enterprise.md)
