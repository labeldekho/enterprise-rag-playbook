# Chunking Strategies

Chunking quality matters more than model choice.

## Why Chunking Matters

Bad chunks cause:
- Incomplete answers (context split across chunks)
- Irrelevant retrieval (noise in chunks)
- Lost information (chunks too small)
- Context overflow (chunks too large)

## Chunking Approaches

### 1. Fixed-Size Chunking

**How it works:**
- Split by character/token count
- Add overlap between chunks

```python
def fixed_chunk(text, chunk_size=512, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
```

**Pros:**
- Simple to implement
- Predictable size
- Easy to parallelize

**Cons:**
- Breaks mid-sentence
- Breaks mid-concept
- No semantic awareness

**When to use:**
- Prototyping
- Homogeneous documents
- When simplicity matters most

### 2. Sentence-Based Chunking

**How it works:**
- Split on sentence boundaries
- Group sentences until size limit

```python
def sentence_chunk(text, max_size=512):
    sentences = split_into_sentences(text)
    chunks = []
    current_chunk = []
    current_size = 0

    for sentence in sentences:
        if current_size + len(sentence) > max_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_size = len(sentence)
        else:
            current_chunk.append(sentence)
            current_size += len(sentence)

    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks
```

**Pros:**
- Never breaks sentences
- More coherent chunks
- Better for Q&A

**Cons:**
- Variable chunk sizes
- May still break concepts
- Sentence detection can fail

### 3. Paragraph-Based Chunking

**How it works:**
- Split on paragraph boundaries
- Merge small paragraphs, split large ones

**Pros:**
- Natural document units
- Preserves author's structure
- Good for articles/reports

**Cons:**
- Paragraphs vary wildly in size
- Some documents lack clear paragraphs
- May need fallback strategy

### 4. Recursive Chunking

**How it works:**
- Try largest separators first
- Fall back to smaller separators

```python
SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

def recursive_chunk(text, chunk_size=512, separators=SEPARATORS):
    if len(text) <= chunk_size:
        return [text]

    for separator in separators:
        if separator in text:
            parts = text.split(separator)
            chunks = []
            current = ""
            for part in parts:
                if len(current) + len(part) <= chunk_size:
                    current += part + separator
                else:
                    if current:
                        chunks.append(current.strip())
                    current = part + separator
            if current:
                chunks.append(current.strip())
            return chunks

    # Last resort: hard split
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
```

**Pros:**
- Adapts to document structure
- Respects natural boundaries
- Good general-purpose solution

**Cons:**
- More complex
- Still not semantic

### 5. Semantic Chunking

**How it works:**
- Use embeddings to detect topic shifts
- Split when similarity drops below threshold

```python
def semantic_chunk(text, threshold=0.5):
    sentences = split_into_sentences(text)
    embeddings = embed(sentences)

    chunks = []
    current_chunk = [sentences[0]]

    for i in range(1, len(sentences)):
        similarity = cosine_similarity(embeddings[i-1], embeddings[i])
        if similarity < threshold:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentences[i]]
        else:
            current_chunk.append(sentences[i])

    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks
```

**Pros:**
- Respects topic boundaries
- More coherent chunks
- Better retrieval quality

**Cons:**
- Slower (embedding required)
- Threshold tuning needed
- Higher complexity

### 6. Document-Aware Chunking

**How it works:**
- Parse document structure (headers, sections)
- Chunk by structural units

**Pros:**
- Preserves document hierarchy
- Enables section-level retrieval
- Natural for structured docs

**Cons:**
- Requires structure parsing
- Not all docs have structure
- Format-specific implementation

## The Overlap Question

### Why Overlap?
- Prevents information at boundaries from being lost
- Improves retrieval for queries spanning chunks
- Provides context continuity

### How Much Overlap?
| Chunk Size | Recommended Overlap |
|------------|---------------------|
| 256 tokens | 25-50 tokens (10-20%) |
| 512 tokens | 50-100 tokens (10-20%) |
| 1024 tokens | 100-200 tokens (10-20%) |

### Overlap Strategies
- **Token overlap:** Fixed number of tokens
- **Sentence overlap:** Last N sentences of previous chunk
- **Semantic overlap:** Include context until topic shift

## Chunk Size Selection

### Factors to Consider

| Factor | Smaller Chunks | Larger Chunks |
|--------|---------------|---------------|
| Retrieval precision | Better | Worse |
| Context completeness | Worse | Better |
| Number of chunks | More | Fewer |
| Embedding cost | Higher | Lower |
| Storage | Higher | Lower |

### Recommended Starting Points

| Use Case | Chunk Size | Rationale |
|----------|------------|-----------|
| General Q&A | 512 tokens | Balance |
| Legal/technical | 1024 tokens | Complete clauses |
| Short-form content | 256 tokens | Higher precision |
| Conversational | 256-512 tokens | Quick retrieval |

## Metadata Attachment

Every chunk should carry:
```python
{
    "chunk_id": "unique_id",
    "document_id": "parent_doc_id",
    "source": "file_path_or_url",
    "position": 3,  # chunk position in document
    "total_chunks": 10,
    "section": "Chapter 2: Methods",
    "page": 15,
    "created_at": "2024-01-15T10:30:00Z"
}
```

## Testing Your Chunking

### Retrieval Quality Test
1. Create test queries
2. Manually identify ideal chunks
3. Run retrieval
4. Measure: ideal chunk in top-k?

### Boundary Test
1. Find information at chunk boundaries
2. Query for that information
3. Verify it's retrievable

### Completeness Test
1. Ask questions requiring multi-sentence context
2. Verify answer is in single chunk
3. If not, adjust strategy

## Anti-Patterns

### Don't:
- Split in the middle of sentences
- Ignore document structure entirely
- Use one strategy for all document types
- Skip overlap entirely
- Forget to attach metadata

### Do:
- Test chunking on real queries
- Adapt strategy to document type
- Include overlap
- Preserve meaningful units
- Iterate based on retrieval quality

---

**Previous:** [PDF and OCR Problems](./pdf-and-ocr-problems.md)
**Next:** [Metadata Design](./metadata-design.md)
