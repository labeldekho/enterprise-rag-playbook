# Update Pipelines

Plan for updates on day one, not day 100.

## The Update Problem

RAG systems are useless if they serve stale information. But updates are hard:
- Documents change
- Documents are deleted
- New documents appear
- Schemas evolve
- Errors need correction

## Update Patterns

### 1. Full Rebuild

**How it works:**
- Delete everything
- Re-ingest all documents
- Replace the index atomically

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Build   │────▶│  Verify  │────▶│   Swap   │
│  New DB  │     │  Quality │     │   Live   │
└──────────┘     └──────────┘     └──────────┘
```

**Pros:**
- Simple to implement
- Guaranteed consistency
- No drift accumulation

**Cons:**
- Expensive (time and compute)
- Can't do continuously
- Downtime risk during swap

**When to use:**
- Small corpus (< 10,000 docs)
- Weekly/monthly updates acceptable
- Schema changes

### 2. Incremental Updates

**How it works:**
- Detect changed documents
- Process only changes
- Update index in place

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Detect  │────▶│  Delete  │────▶│  Process │────▶│  Insert  │
│  Changes │     │   Old    │     │   New    │     │   New    │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
```

**Pros:**
- Fast
- Resource efficient
- Near real-time possible

**Cons:**
- Complex to implement
- Can accumulate errors
- Orphaned data possible

**When to use:**
- Large corpus
- Frequent updates needed
- Real-time requirements

### 3. Hybrid Approach

**How it works:**
- Incremental for daily changes
- Periodic full rebuild for consistency

```
Daily:    Incremental updates
Weekly:   Consistency check (sample validation)
Monthly:  Full rebuild (drift correction)
```

**Pros:**
- Best of both worlds
- Catches drift
- Manageable overhead

**Cons:**
- Most complex
- Requires scheduling
- Multiple processes to maintain

## Change Detection

### File-Based Sources

```python
def detect_file_changes(directory, last_check):
    changes = {
        'added': [],
        'modified': [],
        'deleted': []
    }

    current_files = scan_directory(directory)
    known_files = get_known_files()

    for filepath, mtime in current_files.items():
        if filepath not in known_files:
            changes['added'].append(filepath)
        elif mtime > known_files[filepath].mtime:
            changes['modified'].append(filepath)

    for filepath in known_files:
        if filepath not in current_files:
            changes['deleted'].append(filepath)

    return changes
```

### API-Based Sources

```python
def detect_api_changes(source, since_timestamp):
    # Use source's change tracking if available
    if source.supports_delta():
        return source.get_changes(since=since_timestamp)

    # Otherwise, fetch and compare
    current_items = source.list_all()
    known_items = get_known_items(source.id)
    return compare_item_sets(current_items, known_items)
```

### Content Hashing

```python
def detect_content_changes(document):
    current_hash = hash_content(document.content)
    stored_hash = get_stored_hash(document.id)
    return current_hash != stored_hash
```

## Update Operations

### Adding Documents
```python
def add_document(document):
    # 1. Process document
    chunks = chunk_document(document)
    embeddings = embed_chunks(chunks)

    # 2. Store with metadata
    for chunk, embedding in zip(chunks, embeddings):
        store_chunk(
            chunk_id=generate_id(),
            document_id=document.id,
            content=chunk.text,
            embedding=embedding,
            metadata=chunk.metadata
        )

    # 3. Update tracking
    mark_document_indexed(document.id, document.hash)
```

### Updating Documents
```python
def update_document(document):
    # 1. Delete old chunks
    delete_chunks_for_document(document.id)

    # 2. Add new version
    add_document(document)

    # Note: This is the safest approach
    # In-place updates are error-prone
```

### Deleting Documents
```python
def delete_document(document_id):
    # 1. Delete all chunks
    delete_chunks_for_document(document_id)

    # 2. Update tracking
    mark_document_deleted(document_id)

    # 3. Optional: Keep audit record
    log_deletion(document_id)
```

## Consistency Guarantees

### Eventual Consistency
- Updates propagate over time
- Queries may see stale data briefly
- Simplest to implement

```python
# Accept some inconsistency
def update_async(document):
    queue.publish('document.updated', document.id)
    # Consumer processes eventually
```

### Read-Your-Writes
- User sees their own changes immediately
- Others may see stale data
- Moderate complexity

```python
# Track user's pending updates
def search_with_pending(query, user_id):
    results = vector_search(query)
    pending = get_pending_updates(user_id)
    return merge_results(results, pending)
```

### Strong Consistency
- All queries see latest data
- Requires careful coordination
- Highest complexity

```python
# Synchronous update with locking
def update_sync(document):
    with document_lock(document.id):
        delete_old_chunks(document.id)
        add_new_chunks(document)
        # Only then is update visible
```

## Error Handling

### Transient Failures
```python
@retry(max_attempts=3, backoff=exponential)
def process_document(document):
    try:
        chunks = chunk_document(document)
        embed_and_store(chunks)
    except TransientError:
        raise  # Will retry
    except PermanentError:
        quarantine(document)
        raise
```

### Partial Failures
```python
def update_batch(documents):
    results = {'success': [], 'failed': []}

    for doc in documents:
        try:
            update_document(doc)
            results['success'].append(doc.id)
        except Exception as e:
            results['failed'].append((doc.id, str(e)))
            log_failure(doc.id, e)

    return results
```

### Recovery Procedures
```python
def recover_from_failure():
    # 1. Find incomplete updates
    incomplete = find_incomplete_updates()

    # 2. Roll back or complete each
    for update in incomplete:
        if update.can_complete():
            complete_update(update)
        else:
            rollback_update(update)

    # 3. Verify consistency
    run_consistency_check()
```

## Monitoring Updates

### Key Metrics
- Documents processed per hour
- Update latency (detection → indexed)
- Failure rate
- Queue depth
- Index freshness (age of newest doc)

### Alerts
```python
alerts = [
    ("update_queue_depth > 10000", "critical"),
    ("update_failure_rate > 5%", "warning"),
    ("index_freshness > 24h", "warning"),
    ("update_latency_p99 > 1h", "warning"),
]
```

### Dashboards
- Update pipeline throughput
- Error rates by source
- Queue depths over time
- Index freshness heatmap

## Scheduling Strategies

### Event-Driven
```python
# Webhook on document change
@webhook('/document-changed')
def handle_document_change(event):
    document_id = event['document_id']
    action = event['action']  # created, updated, deleted

    if action == 'deleted':
        delete_document(document_id)
    else:
        document = fetch_document(document_id)
        update_document(document)
```

### Polling
```python
# Periodic check for changes
@scheduled(every='5 minutes')
def poll_for_changes():
    for source in sources:
        changes = detect_changes(source)
        for change in changes:
            queue_update(change)
```

### Batch Windows
```python
# Nightly batch update
@scheduled(cron='0 2 * * *')  # 2 AM daily
def nightly_batch_update():
    for source in sources:
        documents = source.get_all_modified_today()
        batch_update(documents)
```

## Checklist

- [ ] Change detection mechanism chosen
- [ ] Update strategy defined (full/incremental/hybrid)
- [ ] Consistency requirements documented
- [ ] Error handling implemented
- [ ] Retry logic in place
- [ ] Monitoring dashboards created
- [ ] Alerting rules defined
- [ ] Recovery procedures documented
- [ ] Scheduling configured
- [ ] Tested with realistic failure scenarios

---

**Previous:** [Metadata Design](./metadata-design.md)
**Next:** [Retrieval - Embeddings](../04-retrieval/embeddings.md)
