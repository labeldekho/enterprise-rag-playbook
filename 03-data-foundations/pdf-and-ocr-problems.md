# PDF and OCR Problems

PDFs are where RAG pipelines go to die.

## Why PDFs Are Hard

### PDF Is Not a Document Format

PDF is a **print format**. It describes:
- Where to draw characters on a page
- What fonts to use
- Where images go

PDF does NOT contain:
- Paragraph structure
- Reading order
- Table semantics
- Heading hierarchy

### Types of PDFs

| Type | Description | Extraction Difficulty |
|------|-------------|----------------------|
| Native text | Created from Word/LaTeX | Easy |
| Scanned | Image of paper document | Hard (OCR needed) |
| Hybrid | Some text, some scanned | Medium-Hard |
| Forms | Fillable fields | Medium |
| Secured | Encrypted/restricted | Varies |

## Common Extraction Problems

### 1. Reading Order Chaos
**Problem:** Multi-column layouts extract as garbled text
```
Actual:     Column 1    Column 2
            Line 1      Line 1
            Line 2      Line 2

Extracted:  Line 1 Line 1 Line 2 Line 2
```
**Fix:** Use layout-aware extractors (pdfplumber, PyMuPDF with blocks)

### 2. Header/Footer Pollution
**Problem:** Every page includes header/footer in text
**Fix:** Detect repeating patterns, remove by position

### 3. Hyphenation Artifacts
**Problem:** Words broken across lines stay broken
```
Extracted: "The docu-\nment contains important infor-\nmation"
Should be: "The document contains important information"
```
**Fix:** Regex to rejoin hyphenated words at line breaks

### 4. Table Destruction
**Problem:** Tables become meaningless text strings
```
Extracted: "Product Price Qty Apple $1.50 10 Banana $0.75 20"
Should be: Structured table data
```
**Fix:** Use table-specific extraction (Camelot, Tabula)

### 5. Missing Spaces
**Problem:** Words run together or have extra spaces
```
"Thistext hasno spaces" or "T h i s   h a s   t o o   m a n y"
```
**Fix:** Font-aware spacing reconstruction

### 6. Character Encoding Issues
**Problem:** Special characters become garbage
```
"café" → "cafÃ©" or "caf?"
```
**Fix:** Proper Unicode handling, font mapping

## OCR Challenges

### When You Need OCR
- Scanned documents
- Images embedded in PDFs
- Screenshots
- Photographs of documents

### OCR Error Types

| Error Type | Example | Impact |
|------------|---------|--------|
| Character substitution | "rn" → "m" | High |
| Word breaks | "together" → "to gether" | Medium |
| Punctuation errors | "Mr." → "Mr," | Low |
| Complete misread | "total" → "1ota1" | Critical |

### OCR Quality Factors
- Scan resolution (300 DPI minimum)
- Document cleanliness
- Font clarity
- Language complexity
- Image preprocessing

## Extraction Tool Comparison

### PDF Libraries

| Tool | Strength | Weakness |
|------|----------|----------|
| PyPDF2 | Simple, fast | Poor layout handling |
| pdfplumber | Good tables | Slower |
| PyMuPDF (fitz) | Fast, accurate | Complex API |
| pdf2image + OCR | Works on scans | Slow, resource heavy |
| AWS Textract | Best accuracy | Cost, cloud dependency |
| Adobe Extract | High quality | Cost, API limits |

### OCR Engines

| Engine | Strength | Weakness |
|--------|----------|----------|
| Tesseract | Free, open source | Needs preprocessing |
| AWS Textract | Excellent accuracy | Cost |
| Google Vision | Good accuracy | Cost |
| Azure Form Recognizer | Good forms | Cost |
| EasyOCR | Multi-language | Variable accuracy |

## Best Practices

### Pre-Processing Pipeline
```
1. Detect PDF type (native vs scanned)
2. If native: use text extraction
3. If scanned: apply OCR pipeline
4. Post-process to fix common errors
5. Validate output quality
```

### Image Preprocessing for OCR
```python
# Recommended preprocessing steps
1. Convert to grayscale
2. Deskew (straighten)
3. Remove noise
4. Binarize (black/white)
5. Resize if needed (300 DPI target)
```

### Table Extraction Strategy
```
1. Detect table regions (visual or heuristic)
2. Extract with table-aware tool
3. Convert to structured format (CSV, JSON)
4. Embed as structured text for RAG:
   "Table: [headers]. Row 1: [values]. Row 2: [values]."
```

### Quality Validation
```python
def validate_extraction(original_pdf, extracted_text):
    # Check for common issues
    checks = [
        len(extracted_text) > MIN_EXPECTED_LENGTH,
        not contains_garbage_characters(extracted_text),
        word_count_reasonable(original_pdf, extracted_text),
        no_excessive_repetition(extracted_text),
    ]
    return all(checks)
```

## Handling Specific Document Types

### Legal Documents
- Preserve section numbers exactly
- Keep footnotes with references
- Maintain paragraph breaks
- Watch for multi-column layouts

### Technical Manuals
- Preserve code blocks
- Keep numbered steps intact
- Extract figures with captions
- Maintain table relationships

### Financial Reports
- Preserve number formatting
- Extract tables carefully
- Keep headers with data
- Watch for multi-page tables

### Forms
- Use form-aware extraction
- Map field names to values
- Handle checkboxes/radio buttons
- Preserve field relationships

## Cost vs Quality Tradeoffs

| Approach | Quality | Cost | Speed |
|----------|---------|------|-------|
| PyPDF2 only | Low | Free | Fast |
| PyMuPDF + rules | Medium | Free | Fast |
| Tesseract OCR | Medium | Free | Slow |
| AWS Textract | High | $$$ | Medium |
| Human review | Highest | $$$$ | Slowest |

### Recommended Strategy
1. Start with free tools
2. Build quality metrics
3. Identify problem documents
4. Apply paid services selectively
5. Human review for critical docs only

## Monitoring PDF Quality

### Metrics to Track
- Extraction confidence scores
- Character error rates (if OCR)
- Table detection success
- Processing time per page
- Failure rate by document source

### Quality Gates
```python
if extraction_confidence < 0.8:
    route_to_human_review()
elif extraction_confidence < 0.95:
    flag_for_spot_check()
else:
    proceed_to_chunking()
```

---

**Previous:** [Document Ingestion](./document-ingestion.md)
**Next:** [Chunking Strategies](./chunking-strategies.md)
