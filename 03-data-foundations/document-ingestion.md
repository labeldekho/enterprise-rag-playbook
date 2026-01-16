# Document Ingestion

The first step where most RAG projects go wrong.

## The Ingestion Pipeline

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Source    │────▶│   Extract   │────▶│   Clean     │────▶│   Store     │
│  Discovery  │     │   Content   │     │   & Parse   │     │   Raw       │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

## Source Types

### File Systems
- Network drives
- Cloud storage (S3, GCS, Azure Blob)
- Local directories

### Document Management
- SharePoint
- Google Drive
- Confluence
- Notion

### Databases
- SQL databases
- NoSQL databases
- Data warehouses

### APIs
- REST endpoints
- GraphQL
- Internal services

### Real-time Sources
- Message queues
- Webhooks
- Streaming data

## Format-Specific Extraction

### Plain Text (.txt)
```python
# Simple, reliable
content = file.read().decode('utf-8')
```

### Markdown (.md)
```python
# Preserve structure, strip formatting
content = markdown_to_text(file_content)
# Keep headers for section metadata
```

### HTML
```python
# Extract text, preserve structure hints
content = html_to_text(page_content)
# Be careful with scripts, styles, navigation
```

### Microsoft Office (.docx, .xlsx, .pptx)
- Use python-docx, openpyxl, python-pptx
- Handle embedded objects
- Preserve table structure
- Extract images separately

### PDF
See [PDF and OCR Problems](./pdf-and-ocr-problems.md) - this needs its own section.

## Extraction Quality Checklist

- [ ] Text is complete (no truncation)
- [ ] Encoding is correct (UTF-8)
- [ ] Special characters preserved
- [ ] Tables converted meaningfully
- [ ] Lists maintain structure
- [ ] Headers identified
- [ ] Page breaks handled
- [ ] Footnotes included appropriately

## Cleaning Pipeline

### Standard Cleaning Steps

1. **Encoding normalization**
   ```python
   text = text.encode('utf-8', errors='ignore').decode('utf-8')
   ```

2. **Whitespace normalization**
   ```python
   text = ' '.join(text.split())
   ```

3. **Unicode normalization**
   ```python
   import unicodedata
   text = unicodedata.normalize('NFKC', text)
   ```

4. **Boilerplate removal**
   - Headers/footers
   - Copyright notices
   - Page numbers

### Domain-Specific Cleaning

| Domain | Special Handling |
|--------|-----------------|
| Legal | Preserve section numbers, citations |
| Medical | Preserve abbreviations, measurements |
| Code | Preserve formatting, indentation |
| Financial | Preserve numbers, currencies |

## Deduplication

### Exact Deduplication
```python
# Hash-based
doc_hash = hashlib.sha256(content.encode()).hexdigest()
if doc_hash in seen_hashes:
    skip_document()
```

### Near-Duplicate Detection
- MinHash/LSH for fuzzy matching
- Useful for versioned documents
- Set similarity threshold (e.g., 95%)

### Version Handling
- Keep latest version only?
- Keep all versions with timestamps?
- Merge changes into single doc?

Decision depends on use case.

## Storage Strategy

### Raw Document Store
```
/raw/
  /{source_type}/
    /{source_id}/
      /{document_id}/
        - original.{ext}
        - metadata.json
        - extracted_text.txt
```

### Why Store Raw?
- Reprocessing without re-fetching
- Debugging extraction issues
- Compliance requirements
- Format migration later

## Incremental Ingestion

### Change Detection
- File modification timestamps
- Document versioning APIs
- Content hashing
- Webhooks/notifications

### Update Strategies

| Strategy | Pros | Cons |
|----------|------|------|
| Full rebuild | Simple, consistent | Slow, expensive |
| Incremental | Fast | Complex, can drift |
| Hybrid | Balanced | Most complex |

### Recommended Pattern
```
1. Daily incremental updates (changed docs only)
2. Weekly consistency checks (sample verification)
3. Monthly full rebuild (catch drift)
```

## Error Handling

### Common Failures
- File not found
- Permission denied
- Encoding errors
- Timeout on large files
- Corrupted files

### Error Strategy
```python
try:
    content = extract(document)
except ExtractionError as e:
    log_error(document, e)
    quarantine(document)
    alert_if_threshold_exceeded()
```

### Quarantine Process
- Move failed docs to quarantine folder
- Log failure reason
- Retry with different extractor
- Human review queue for persistent failures

## Monitoring

### Key Metrics
- Documents processed per hour
- Extraction success rate
- Average processing time
- Queue depth
- Error rate by type

### Alerts
- Extraction success rate < 95%
- Queue depth growing
- Processing latency spike
- New error types appearing

## Implementation Considerations

### Scaling Extraction
- Parallelize by document
- Use worker pools
- Consider serverless for bursts

### Resource Management
- Memory limits per document
- Timeout per document
- Disk space monitoring

---

**Next:** [PDF and OCR Problems](./pdf-and-ocr-problems.md)
