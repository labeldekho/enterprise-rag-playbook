# PII and Redaction

Handling personally identifiable information in RAG systems.

## The PII Challenge in RAG

RAG systems can inadvertently:
- Ingest documents containing PII
- Retrieve PII-containing chunks
- Include PII in generated responses
- Store PII in vector databases indefinitely

## What Is PII?

### Common PII Types

| Category | Examples |
|----------|----------|
| Direct Identifiers | Name, SSN, passport number |
| Contact Info | Email, phone, address |
| Financial | Credit card, bank account |
| Health | Medical records, diagnoses |
| Employment | Employee ID, salary, performance |
| Authentication | Passwords, security questions |
| Biometric | Fingerprints, facial data |

### Regulatory Definitions

| Regulation | Scope |
|------------|-------|
| GDPR | Any data relating to identified/identifiable person |
| CCPA | Information that identifies, relates to, or could be linked to consumer |
| HIPAA | Health information + identifiers |
| PCI-DSS | Cardholder data |

## PII Detection

### Rule-Based Detection
```python
import re

PII_PATTERNS = {
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone_us': r'\b\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b',
    'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
}

def detect_pii_regex(text):
    findings = []
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.finditer(pattern, text)
        for match in matches:
            findings.append({
                'type': pii_type,
                'value': match.group(),
                'start': match.start(),
                'end': match.end()
            })
    return findings
```

### NER-Based Detection
```python
import spacy

nlp = spacy.load("en_core_web_lg")

PII_ENTITY_TYPES = {'PERSON', 'ORG', 'GPE', 'DATE', 'MONEY'}

def detect_pii_ner(text):
    doc = nlp(text)
    findings = []
    for ent in doc.ents:
        if ent.label_ in PII_ENTITY_TYPES:
            findings.append({
                'type': ent.label_,
                'value': ent.text,
                'start': ent.start_char,
                'end': ent.end_char
            })
    return findings
```

### ML-Based Detection
```python
from presidio_analyzer import AnalyzerEngine

analyzer = AnalyzerEngine()

def detect_pii_ml(text):
    results = analyzer.analyze(
        text=text,
        language='en',
        entities=[
            "PHONE_NUMBER", "EMAIL_ADDRESS", "CREDIT_CARD",
            "US_SSN", "PERSON", "LOCATION", "DATE_TIME"
        ]
    )
    return [
        {
            'type': r.entity_type,
            'value': text[r.start:r.end],
            'start': r.start,
            'end': r.end,
            'confidence': r.score
        }
        for r in results
    ]
```

### Combined Detection
```python
def detect_pii_comprehensive(text):
    findings = []

    # Rule-based (high precision for known patterns)
    findings.extend(detect_pii_regex(text))

    # NER (catches names, organizations)
    findings.extend(detect_pii_ner(text))

    # ML-based (catches context-dependent PII)
    findings.extend(detect_pii_ml(text))

    # Deduplicate overlapping detections
    return deduplicate_findings(findings)
```

## Redaction Strategies

### Full Redaction
Replace PII with placeholder:
```python
def redact_full(text, findings):
    # Sort by position (reverse to not shift indices)
    sorted_findings = sorted(findings, key=lambda x: x['start'], reverse=True)

    redacted = text
    for finding in sorted_findings:
        placeholder = f"[{finding['type']}]"
        redacted = redacted[:finding['start']] + placeholder + redacted[finding['end']:]

    return redacted

# Before: "Contact John Smith at john.smith@email.com"
# After:  "Contact [PERSON] at [EMAIL]"
```

### Partial Redaction
Preserve some information:
```python
def redact_partial(text, findings):
    redacted = text
    for finding in sorted(findings, key=lambda x: x['start'], reverse=True):
        value = finding['value']

        if finding['type'] == 'email':
            # Show domain only
            parts = value.split('@')
            masked = f"***@{parts[1]}"
        elif finding['type'] == 'phone':
            # Show last 4 digits
            masked = f"***-***-{value[-4:]}"
        elif finding['type'] == 'ssn':
            # Show last 4
            masked = f"***-**-{value[-4:]}"
        else:
            masked = f"[{finding['type']}]"

        redacted = redacted[:finding['start']] + masked + redacted[finding['end']:]

    return redacted
```

### Pseudonymization
Replace with consistent fake data:
```python
from faker import Faker
import hashlib

fake = Faker()
pseudonym_cache = {}

def pseudonymize(text, findings, salt="secret"):
    result = text
    for finding in sorted(findings, key=lambda x: x['start'], reverse=True):
        # Generate consistent pseudonym for same value
        cache_key = f"{finding['type']}:{finding['value']}:{salt}"
        hash_seed = int(hashlib.sha256(cache_key.encode()).hexdigest()[:8], 16)

        if cache_key not in pseudonym_cache:
            Faker.seed(hash_seed)
            if finding['type'] == 'PERSON':
                pseudonym_cache[cache_key] = fake.name()
            elif finding['type'] == 'email':
                pseudonym_cache[cache_key] = fake.email()
            elif finding['type'] == 'phone':
                pseudonym_cache[cache_key] = fake.phone_number()
            else:
                pseudonym_cache[cache_key] = f"[{finding['type']}_{hash_seed % 1000}]"

        result = result[:finding['start']] + pseudonym_cache[cache_key] + result[finding['end']:]

    return result
```

## Pipeline Integration

### Pre-Ingestion Redaction
```python
class PIIRedactingLoader:
    def __init__(self, base_loader, redaction_strategy='full'):
        self.base_loader = base_loader
        self.redaction_strategy = redaction_strategy

    def load(self, source):
        documents = self.base_loader.load(source)

        for doc in documents:
            # Detect PII
            findings = detect_pii_comprehensive(doc.text)

            # Log PII detection for audit
            if findings:
                log_pii_detection(doc.id, findings)

            # Redact
            doc.text = self.redact(doc.text, findings)
            doc.metadata['pii_redacted'] = len(findings) > 0

        return documents

    def redact(self, text, findings):
        if self.redaction_strategy == 'full':
            return redact_full(text, findings)
        elif self.redaction_strategy == 'partial':
            return redact_partial(text, findings)
        elif self.redaction_strategy == 'pseudonymize':
            return pseudonymize(text, findings)
```

### Pre-Response Check
```python
class PIIGuardedGenerator:
    def __init__(self, base_generator):
        self.base_generator = base_generator

    def generate(self, query, context):
        # Check context for any remaining PII
        context_findings = detect_pii_comprehensive(context)
        if context_findings:
            context = redact_full(context, context_findings)
            log_warning("PII found in context at generation time")

        # Generate response
        response = self.base_generator.generate(query, context)

        # Check response for PII
        response_findings = detect_pii_comprehensive(response)
        if response_findings:
            response = redact_full(response, response_findings)
            log_warning("PII found in generated response")

        return response
```

## Handling Existing PII

### Retroactive Redaction
```python
def retroactive_pii_cleanup(vector_db, batch_size=1000):
    """
    Scan existing documents for PII and redact.
    """
    offset = 0
    total_redacted = 0

    while True:
        # Fetch batch
        documents = vector_db.fetch(limit=batch_size, offset=offset)
        if not documents:
            break

        for doc in documents:
            findings = detect_pii_comprehensive(doc.text)
            if findings:
                # Redact text
                redacted_text = redact_full(doc.text, findings)

                # Re-embed (important!)
                new_embedding = embed(redacted_text)

                # Update in database
                vector_db.update(
                    id=doc.id,
                    text=redacted_text,
                    embedding=new_embedding,
                    metadata={**doc.metadata, 'pii_redacted': True}
                )
                total_redacted += 1

        offset += batch_size

    return total_redacted
```

## PII-Aware Access Control

### Sensitivity Levels
```python
PII_SENSITIVITY = {
    'US_SSN': 'critical',
    'CREDIT_CARD': 'critical',
    'MEDICAL_RECORD': 'critical',
    'EMAIL': 'high',
    'PHONE_NUMBER': 'high',
    'PERSON': 'medium',
    'ADDRESS': 'medium',
}

def calculate_document_sensitivity(findings):
    if not findings:
        return 'low'

    max_sensitivity = 'low'
    sensitivity_order = ['low', 'medium', 'high', 'critical']

    for finding in findings:
        pii_sensitivity = PII_SENSITIVITY.get(finding['type'], 'medium')
        if sensitivity_order.index(pii_sensitivity) > sensitivity_order.index(max_sensitivity):
            max_sensitivity = pii_sensitivity

    return max_sensitivity
```

## Compliance Logging

### Audit Trail
```python
def log_pii_detection(document_id, findings, action='detected'):
    audit_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'document_id': document_id,
        'action': action,
        'pii_types': [f['type'] for f in findings],
        'count': len(findings),
        # Do NOT log actual PII values
    }
    audit_logger.log(audit_entry)
```

### Data Subject Requests
```python
def handle_deletion_request(subject_identifier):
    """
    Handle GDPR "right to be forgotten" requests.
    """
    # Find all documents mentioning the subject
    documents = search_by_subject(subject_identifier)

    for doc in documents:
        # Option 1: Delete entire document
        vector_db.delete(doc.id)

        # Option 2: Redact subject from document
        # redacted = redact_subject(doc.text, subject_identifier)
        # vector_db.update(doc.id, text=redacted)

        log_deletion(doc.id, subject_identifier)

    return len(documents)
```

## Checklist

- [ ] PII types relevant to your domain identified
- [ ] Detection pipeline implemented (regex + NER + ML)
- [ ] Redaction strategy chosen
- [ ] Pre-ingestion redaction integrated
- [ ] Pre-response filtering added
- [ ] Existing data scanned and cleaned
- [ ] Audit logging in place
- [ ] Deletion request process defined
- [ ] Regular PII audits scheduled

---

**Next:** [Access Control](./access-control.md)
