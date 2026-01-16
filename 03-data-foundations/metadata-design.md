# Metadata Design

Metadata is a first-class citizen, not an afterthought.

## Why Metadata Matters

Without metadata, you have:
- No filtering capability
- No source attribution
- No freshness awareness
- No access control hooks
- Blind retrieval

With metadata, you have:
- Targeted retrieval
- Traceable answers
- Time-aware search
- Permission-based filtering
- Explainable results

## Metadata Categories

### 1. Identity Metadata
Who/what is this document?

```json
{
  "document_id": "doc_abc123",
  "chunk_id": "chunk_xyz789",
  "source_uri": "s3://bucket/path/document.pdf",
  "filename": "Q4_2024_Report.pdf",
  "format": "pdf"
}
```

### 2. Structural Metadata
Where does this chunk fit?

```json
{
  "page_number": 15,
  "section": "Financial Results",
  "subsection": "Revenue Breakdown",
  "chapter": 3,
  "position_in_doc": 0.35,
  "total_chunks": 47,
  "chunk_index": 16
}
```

### 3. Temporal Metadata
When is this information from?

```json
{
  "created_at": "2024-01-15T10:30:00Z",
  "modified_at": "2024-02-01T14:22:00Z",
  "published_at": "2024-01-20T00:00:00Z",
  "effective_date": "2024-01-01",
  "expiry_date": "2024-12-31",
  "ingested_at": "2024-02-05T09:00:00Z"
}
```

### 4. Authorship Metadata
Who created/owns this?

```json
{
  "author": "Jane Smith",
  "department": "Finance",
  "team": "FP&A",
  "owner": "finance-team@company.com",
  "contributors": ["john.doe", "alice.wong"]
}
```

### 5. Classification Metadata
What type of content is this?

```json
{
  "document_type": "report",
  "content_type": "financial",
  "topic_tags": ["revenue", "quarterly", "forecast"],
  "language": "en",
  "region": "north-america"
}
```

### 6. Access Control Metadata
Who can see this?

```json
{
  "visibility": "internal",
  "access_groups": ["finance", "executive"],
  "classification": "confidential",
  "data_sensitivity": "high",
  "pii_present": false
}
```

### 7. Quality Metadata
How reliable is this?

```json
{
  "extraction_confidence": 0.95,
  "ocr_quality": "high",
  "verified": true,
  "verification_date": "2024-02-01",
  "source_reliability": "authoritative"
}
```

## Metadata Schema Design

### Principles

1. **Be explicit about types**
   - Dates as ISO 8601
   - Enums for fixed values
   - Arrays for multi-value fields

2. **Plan for filtering**
   - Index fields you'll filter on
   - Use appropriate data types
   - Consider query patterns

3. **Include operational fields**
   - Ingestion timestamps
   - Processing status
   - Error flags

### Example Full Schema

```python
class ChunkMetadata:
    # Identity
    document_id: str
    chunk_id: str
    source_uri: str

    # Structure
    page_number: Optional[int]
    section_title: Optional[str]
    chunk_index: int
    total_chunks: int

    # Temporal
    document_date: Optional[date]
    ingested_at: datetime

    # Classification
    document_type: str  # enum: report, policy, manual, etc.
    topics: List[str]
    language: str

    # Access
    access_groups: List[str]
    classification: str  # enum: public, internal, confidential

    # Quality
    extraction_confidence: float

    # Custom (domain-specific)
    custom: Dict[str, Any]
```

## Extraction Strategies

### From Document Properties
```python
# PDF metadata
from PyPDF2 import PdfReader
reader = PdfReader(file)
info = reader.metadata
title = info.get('/Title')
author = info.get('/Author')
created = info.get('/CreationDate')
```

### From Content Analysis
```python
# Extract topics using NLP
topics = extract_topics(text)

# Detect language
language = detect_language(text)

# Find dates in content
dates = extract_dates(text)
```

### From File System
```python
# File metadata
import os
stat = os.stat(filepath)
modified = datetime.fromtimestamp(stat.st_mtime)
size = stat.st_size
```

### From Source System
```python
# SharePoint metadata
metadata = sharepoint_client.get_item_metadata(item_id)
author = metadata['Author']
department = metadata['Department']
```

## Using Metadata in Retrieval

### Pre-filtering
Filter BEFORE vector search:
```python
results = vector_db.search(
    query_embedding,
    filter={
        "document_type": "policy",
        "access_groups": {"$in": user_groups},
        "document_date": {"$gte": "2024-01-01"}
    },
    top_k=10
)
```

### Post-filtering
Filter AFTER vector search (less efficient):
```python
results = vector_db.search(query_embedding, top_k=100)
filtered = [r for r in results if r.metadata['access_groups'] in user_groups]
return filtered[:10]
```

### Boosting by Metadata
Adjust scores based on metadata:
```python
def boost_score(result):
    score = result.score

    # Boost recent documents
    age_days = (today - result.metadata['document_date']).days
    recency_boost = 1.0 / (1 + age_days / 365)

    # Boost verified documents
    if result.metadata.get('verified'):
        score *= 1.2

    return score * recency_boost
```

## Metadata Indexing

### Vector Database Capabilities

| Database | Filtering | Supported Types |
|----------|-----------|-----------------|
| Pinecone | Pre-filter | string, number, list |
| Weaviate | Pre-filter | all JSON types |
| Milvus | Pre-filter | scalar, string |
| Chroma | Pre-filter | string, number |
| pgvector | SQL WHERE | all PostgreSQL types |

### Indexing Strategy
```sql
-- Example for pgvector
CREATE INDEX idx_metadata_doc_type ON chunks ((metadata->>'document_type'));
CREATE INDEX idx_metadata_date ON chunks ((metadata->>'document_date'));
CREATE INDEX idx_metadata_access ON chunks USING GIN ((metadata->'access_groups'));
```

## Common Pitfalls

### 1. Missing Temporal Context
**Problem:** No way to know if information is current
**Fix:** Always include document_date and ingested_at

### 2. Inconsistent Enums
**Problem:** "Report", "report", "REPORT", "rpt"
**Fix:** Normalize on ingestion, use enum validation

### 3. Missing Source Attribution
**Problem:** Can't trace answer back to source
**Fix:** Always include source_uri and page_number

### 4. Unindexed Filter Fields
**Problem:** Filtering is slow
**Fix:** Index fields used in filters

### 5. Metadata Drift
**Problem:** Schema changes break queries
**Fix:** Version your schema, migrate carefully

## Checklist

- [ ] Identity fields defined (doc_id, chunk_id, source)
- [ ] Temporal fields included (dates, ingested_at)
- [ ] Access control fields present
- [ ] Quality indicators included
- [ ] Schema documented
- [ ] Extraction logic implemented
- [ ] Indexes created for filter fields
- [ ] Validation on ingestion
- [ ] Migration strategy planned

---

**Previous:** [Chunking Strategies](./chunking-strategies.md)
**Next:** [Update Pipelines](./update-pipelines.md)
