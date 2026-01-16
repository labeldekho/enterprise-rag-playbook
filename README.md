# Enterprise RAG Playbook

A **decision and architecture guide** for building production-grade Retrieval Augmented Generation (RAG) systems in enterprise environments.

## What This Repository Is

This is **not** a demo, SDK, or framework.

It is:

- A **decision and architecture guide** for building RAG systems in real companies
- Backed by a **reference implementation** with clear interfaces (intentionally skeletal)
- Focused on **failure modes, tradeoffs, and scaling paths**, not "hello world"

## Who This Is For

- Senior engineers evaluating RAG architectures
- AI/ML leads building production systems
- Platform teams designing data pipelines
- CTOs and Staff engineers making technology decisions

## Core Philosophy

RAG is not about bigger models. It's about **connecting AI to company knowledge safely, accurately, and measurably**.

Key insights this guide covers:

- Chunking quality matters more than model choice
- Metadata is a first-class citizen, not an afterthought
- Hybrid search beats pure vector search
- Evaluation frameworks separate production systems from prototypes
- Most RAG failures come from bad data prep, not bad models

## Repository Structure

```
enterprise-rag-playbook/
├── 00-why-rag/                    # Conceptual grounding
├── 01-when-not-to-use-rag/        # Explicit misuse cases
├── 02-rag-levels/                 # Maturity model (5 levels)
├── 03-data-foundations/           # Where most projects fail
├── 04-retrieval/                  # Beyond "just vector search"
├── 05-memory-and-context/         # RAG as memory architecture
├── 06-evaluation/                 # Making RAG measurable
├── 07-security-and-compliance/    # Enterprise reality
├── 08-scaling/                    # Prototype to production
├── 09-reference-implementation/   # Skeletal interfaces
└── 10-decision-guides/            # Strategic decisions
```

## Quick Navigation

### Understanding RAG
- [Why RAG?](./00-why-rag/README.md) - The problems RAG solves
- [When NOT to Use RAG](./01-when-not-to-use-rag/README.md) - Save time and money

### RAG Maturity Levels
- [Level 1: Basic RAG](./02-rag-levels/level-1-basic.md)
- [Level 2: Hybrid Search](./02-rag-levels/level-2-hybrid.md)
- [Level 3: Multimodal](./02-rag-levels/level-3-multimodal.md)
- [Level 4: Agentic](./02-rag-levels/level-4-agentic.md)
- [Level 5: Enterprise](./02-rag-levels/level-5-enterprise.md)

### Building Blocks
- [Data Foundations](./03-data-foundations/) - Ingestion, chunking, metadata
- [Retrieval Strategies](./04-retrieval/) - Embeddings, search, reranking
- [Memory & Context](./05-memory-and-context/) - Context windows, long-term memory

### Production Concerns
- [Evaluation](./06-evaluation/) - Metrics, testing, failure analysis
- [Security & Compliance](./07-security-and-compliance/) - PII, access control, audit
- [Scaling](./08-scaling/) - Sharding, caching, cost optimization

### Implementation
- [Reference Implementation](./09-reference-implementation/) - Interfaces and contracts
- [Decision Guides](./10-decision-guides/) - RAG vs fine-tuning, RAG vs agents

## Reference Implementation Philosophy

The reference implementation is **intentionally skeletal**:

- **Interfaces over implementations** - Clear contracts, no framework lock-in
- **Agent-improvable zones** - Marked areas where coding agents can implement strategies
- **Human decision points** - Architecture choices remain with humans

This separation keeps humans in control of *decisions*, not syntax.

## What We Intentionally Exclude

- UI components
- Vendor-specific SDKs
- Full end-to-end pipelines
- Benchmarks pretending to be universal

This prevents repo rot and keeps focus on principles.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## License

MIT License - See LICENSE file for details.
