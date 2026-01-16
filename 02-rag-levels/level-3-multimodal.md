# Level 3: Multimodal RAG

When text isn't enough.

## What Problem This Level Solves

- Documents contain images, charts, diagrams
- Tables hold critical data
- Visual context required for accurate answers
- Users ask about non-text content

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Document Processing                   │
├─────────────┬─────────────┬─────────────┬──────────────┤
│    Text     │   Images    │   Tables    │    Video     │
│  Extraction │  Extraction │  Extraction │  (Optional)  │
└──────┬──────┴──────┬──────┴──────┬──────┴──────┬───────┘
       │             │             │             │
       ▼             ▼             ▼             ▼
┌─────────────┬─────────────┬─────────────┬─────────────┐
│    Text     │   Vision    │   Table     │    Video    │
│  Embedding  │  Embedding  │  Embedding  │  Embedding  │
└──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┘
       │             │             │             │
       └─────────────┴──────┬──────┴─────────────┘
                            ▼
                    ┌─────────────┐
                    │  Multimodal │
                    │    Index    │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       ┌─────────────┐          ┌─────────────┐
       │   Text      │          │   Vision    │
       │   Query     │          │   Query     │
       └──────┬──────┘          └──────┬──────┘
              │                        │
              └───────────┬────────────┘
                          ▼
                   ┌─────────────┐
                   │  Multimodal │
                   │     LLM     │
                   └─────────────┘
```

## Components

### Image Processing
- Extract images from documents
- Generate descriptions using vision models
- Create embeddings (CLIP, etc.)
- Store image-text associations

### Table Extraction
- Detect table structures
- Parse rows/columns/headers
- Convert to structured format
- Embed as text or structured data

### Video Processing (Optional)
- Extract keyframes
- Transcribe audio
- Index by timestamp
- Associate with transcript chunks

### Multimodal Retrieval
- Query can match text, images, or tables
- Cross-modal search (text query → image result)
- Unified ranking across modalities

## Data Requirements

| Requirement | Level 3 Spec |
|-------------|--------------|
| Document formats | PDF, DOCX, images, video |
| Data volume | Storage-heavy (10x Level 2) |
| Processing | GPU for vision models |
| Metadata | Rich (image captions, table headers) |
| Storage | Object storage for media |

## Latency Expectations

| Operation | Typical Latency |
|-----------|-----------------|
| Query embedding | 50-100ms |
| Multimodal search | 50-100ms |
| Image retrieval | 20-50ms |
| Vision LLM processing | 1000-3000ms |
| **Total** | **1120-3250ms** |

Multimodal significantly increases latency due to vision processing.

## Failure Modes

### 1. Poor Image Extraction
**Symptom:** Images missing or corrupted
**Cause:** PDF rendering issues, format problems
**Fix:** Use robust PDF libraries, fallback extraction

### 2. Table Structure Loss
**Symptom:** Table data becomes garbled text
**Cause:** Naive text extraction
**Fix:** Use table-aware extraction (Camelot, Tabula)

### 3. Modality Confusion
**Symptom:** Text query returns irrelevant images
**Cause:** Cross-modal embeddings poorly aligned
**Fix:** Use aligned models (CLIP), separate indexes

### 4. Context Window Overflow
**Symptom:** Can't fit image + text in context
**Cause:** Vision models have context limits
**Fix:** Summarize images, selective retrieval

### 5. OCR Errors
**Symptom:** Text in images is wrong
**Cause:** Poor OCR quality
**Fix:** Better OCR models, manual correction for critical docs

## When to Stop Here

Stay at Level 3 if:
- Single-step retrieval is sufficient
- No need for multi-hop reasoning
- Latency budget allows vision processing
- Query complexity is bounded

## When to Advance

Move to Level 4 if:
- Queries require multiple retrieval steps
- Need to combine information from many sources
- Complex reasoning over retrieved data
- Dynamic tool use required

## Implementation Checklist

- [ ] Image extraction pipeline working
- [ ] Table extraction pipeline working
- [ ] Vision embedding model deployed
- [ ] Cross-modal search tested
- [ ] Image-text associations stored
- [ ] Multimodal LLM integrated
- [ ] Latency within acceptable bounds
- [ ] Storage costs understood

## Key Technologies

### Image Processing
- **Extraction:** pdf2image, PyMuPDF
- **OCR:** Tesseract, AWS Textract, Google Vision
- **Embedding:** CLIP, OpenCLIP, SigLIP

### Table Processing
- **Extraction:** Camelot, Tabula, AWS Textract
- **Parsing:** pandas, custom parsers
- **Embedding:** Text serialization or structured

### Multimodal LLMs
- GPT-4V, Claude 3 Vision, Gemini Pro Vision
- LLaVA, Qwen-VL (open source)

---

**Previous:** [Level 2: Hybrid Search](./level-2-hybrid.md)
**Next:** [Level 4: Agentic RAG](./level-4-agentic.md)
