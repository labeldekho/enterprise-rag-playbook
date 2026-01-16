# Graph RAG

When entity relationships matter more than text similarity.

## What Is Graph RAG?

Graph RAG augments retrieval with knowledge graph traversal:
- Extract entities and relationships from documents
- Build a graph connecting related concepts
- Use graph structure to improve retrieval

```
Traditional RAG:    Query → Vector Search → Chunks → LLM

Graph RAG:          Query → Entity Extraction → Graph Traversal
                              ↓                       ↓
                         Vector Search → Merge → Context → LLM
```

## When Graph RAG Helps

### Entity-Centric Questions
```
"What products did Company X acquire in 2023?"

Vector search finds:
  - "Company X had a great year in 2023..."
  - "Several acquisitions happened in tech..."

Graph RAG finds:
  - Company X → acquired → Product A (2023)
  - Company X → acquired → Product B (2023)
  - Direct, structured answers
```

### Multi-Hop Reasoning
```
"Who are the competitors of companies that John Smith invested in?"

Required hops:
1. John Smith → invested_in → [Companies]
2. [Companies] → competitor_of → [Competitors]

Vector search can't do this.
```

### Relationship-Based Queries
```
"What's the relationship between Entity A and Entity B?"

Graph provides the path:
  Entity A → works_at → Company → acquired → Entity B's startup
```

## Graph RAG Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Indexing Pipeline                        │
├─────────────────────────────────────────────────────────────┤
│  Document → Entity Extraction → Relationship Extraction     │
│                    ↓                      ↓                 │
│               [Entities]            [Relationships]         │
│                    ↓                      ↓                 │
│              ┌─────────────────────────────┐               │
│              │      Knowledge Graph        │               │
│              │   (Neo4j, Neptune, etc.)   │               │
│              └─────────────────────────────┘               │
│                          ↓                                  │
│              ┌─────────────────────────────┐               │
│              │      Vector Index           │               │
│              │   (Entities + Chunks)       │               │
│              └─────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      Query Pipeline                          │
├─────────────────────────────────────────────────────────────┤
│  Query → Entity Recognition → Graph Lookup                  │
│              ↓                     ↓                        │
│         Vector Search      Graph Traversal                  │
│              ↓                     ↓                        │
│         Chunk Results      Related Entities                 │
│              ↓                     ↓                        │
│              └──────── Merge ────────┘                      │
│                          ↓                                  │
│                   Enriched Context                          │
│                          ↓                                  │
│                        LLM                                  │
└─────────────────────────────────────────────────────────────┘
```

## Entity Extraction

### Using LLMs
```python
def extract_entities_llm(text):
    prompt = """
    Extract all named entities from the following text.
    Return as JSON with format:
    {"entities": [{"name": "...", "type": "...", "mentions": [...]}]}

    Types: PERSON, ORGANIZATION, PRODUCT, LOCATION, DATE, EVENT

    Text: {text}
    """
    response = llm.generate(prompt.format(text=text))
    return parse_json(response)
```

### Using NER Models
```python
import spacy

nlp = spacy.load("en_core_web_lg")

def extract_entities_ner(text):
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        entities.append({
            "name": ent.text,
            "type": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char
        })
    return entities
```

## Relationship Extraction

### LLM-Based Extraction
```python
def extract_relationships(text, entities):
    entity_list = ", ".join([e["name"] for e in entities])
    prompt = f"""
    Given these entities: {entity_list}

    Extract relationships between them from the text.
    Return as JSON:
    {{"relationships": [{{"source": "...", "target": "...", "type": "..."}}]}}

    Relationship types: works_at, acquired, invested_in, partner_of,
                       competitor_of, founded, located_in

    Text: {text}
    """
    response = llm.generate(prompt)
    return parse_json(response)
```

### Rule-Based Patterns
```python
# Dependency parsing patterns
patterns = [
    # "X acquired Y"
    {"source": "nsubj", "verb": "acquired", "target": "dobj"},
    # "X is the CEO of Y"
    {"source": "nsubj", "verb": "is", "relation": "CEO", "target": "pobj"},
]
```

## Graph Database Integration

### Neo4j Example
```python
from neo4j import GraphDatabase

class GraphRAG:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def add_entity(self, entity):
        with self.driver.session() as session:
            session.run(
                "MERGE (e:Entity {name: $name}) "
                "SET e.type = $type",
                name=entity["name"],
                type=entity["type"]
            )

    def add_relationship(self, rel):
        with self.driver.session() as session:
            session.run(
                "MATCH (a:Entity {name: $source}) "
                "MATCH (b:Entity {name: $target}) "
                "MERGE (a)-[r:RELATED {type: $type}]->(b)",
                source=rel["source"],
                target=rel["target"],
                type=rel["type"]
            )

    def get_related_entities(self, entity_name, hops=2):
        with self.driver.session() as session:
            result = session.run(
                f"MATCH (e:Entity {{name: $name}})-[*1..{hops}]-(related) "
                "RETURN DISTINCT related.name as name, related.type as type",
                name=entity_name
            )
            return [dict(record) for record in result]
```

## Query Strategies

### Entity-First Strategy
```python
def entity_first_search(query):
    # 1. Extract entities from query
    query_entities = extract_entities(query)

    # 2. Find related entities in graph
    related = []
    for entity in query_entities:
        related.extend(graph.get_related_entities(entity["name"]))

    # 3. Retrieve chunks mentioning these entities
    entity_names = [e["name"] for e in query_entities + related]
    chunks = retrieve_chunks_by_entities(entity_names)

    # 4. Also do vector search
    vector_chunks = vector_search(query)

    # 5. Merge and rank
    return merge_and_rank(chunks, vector_chunks)
```

### Hybrid Graph-Vector Strategy
```python
def hybrid_graph_vector(query, top_k=10):
    # Parallel execution
    with ThreadPoolExecutor() as executor:
        # Vector search
        vector_future = executor.submit(vector_search, query, top_k * 2)

        # Graph search
        entities = extract_entities(query)
        graph_future = executor.submit(
            graph_expand_and_search, entities, top_k * 2
        )

    vector_results = vector_future.result()
    graph_results = graph_future.result()

    # Combine with RRF
    return reciprocal_rank_fusion([vector_results, graph_results])[:top_k]
```

## Graph Construction Strategies

### Document-Level Graph
- One node per document
- Edges = shared entities
- Coarse but fast

### Entity-Level Graph
- Nodes = entities
- Edges = relationships
- Fine-grained, expensive

### Hierarchical Graph
- Multiple levels (doc → section → entity)
- Flexible traversal
- Most complex

## Challenges and Solutions

### Entity Resolution
**Problem:** "Microsoft", "MSFT", "Microsoft Corporation" = same entity
**Solution:** Entity linking, normalization, embeddings for fuzzy matching

### Graph Quality
**Problem:** Noisy extraction creates wrong relationships
**Solution:** Confidence scores, human validation, multiple extractors

### Scalability
**Problem:** Large graphs are slow to query
**Solution:** Graph partitioning, caching, query optimization

### Freshness
**Problem:** Graph becomes stale
**Solution:** Incremental updates, timestamp tracking

## When to Use Graph RAG

### Good Fit
- Enterprise knowledge bases (people, products, orgs)
- Scientific literature (papers, authors, citations)
- Legal documents (cases, statutes, parties)
- Financial analysis (companies, relationships)

### Consider Carefully
- High implementation complexity
- Requires entity extraction pipeline
- Graph maintenance overhead
- May be overkill for simple Q&A

### Skip If
- Documents have few entities
- No relationship queries expected
- Limited engineering resources
- Pure semantic search is sufficient

## Implementation Checklist

- [ ] Entity extraction pipeline (LLM or NER)
- [ ] Relationship extraction method
- [ ] Graph database selected and deployed
- [ ] Entity resolution/deduplication
- [ ] Graph query patterns defined
- [ ] Integration with vector search
- [ ] Incremental update pipeline
- [ ] Quality monitoring for extraction
- [ ] Performance benchmarks

---

**Previous:** [Hybrid Search](./hybrid-search.md)
**Next:** [Reranking](./reranking.md)
