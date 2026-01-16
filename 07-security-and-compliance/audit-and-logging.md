# Audit and Logging

Maintaining accountability and compliance in RAG systems.

## Why Audit Logging Matters

Audit logs provide:
- **Accountability:** Who did what, when
- **Compliance:** Evidence for auditors
- **Security:** Detect and investigate breaches
- **Debugging:** Understand system behavior
- **Analytics:** Usage patterns and optimization opportunities

## What to Log

### RAG-Specific Events

| Event Type | What to Capture |
|------------|-----------------|
| Query | User, query text (hashed if sensitive), timestamp |
| Retrieval | Documents retrieved, scores, filters applied |
| Generation | Model used, prompt template, token counts |
| Access Denied | User, attempted resource, denial reason |
| Document Ingestion | Source, document count, processing status |
| Index Updates | Changes made, affected documents |

### Security Events

| Event Type | What to Capture |
|------------|-----------------|
| Authentication | User ID, auth method, success/failure |
| Authorization | Resource, action, decision, policy applied |
| Suspicious Activity | Query patterns, anomalies detected |
| Admin Actions | Configuration changes, user management |

## Log Schema Design

### Base Event Schema
```python
@dataclass
class AuditEvent:
    # Event identification
    event_id: str
    event_type: str
    timestamp: datetime

    # Actor
    user_id: str
    session_id: str
    client_ip: str
    user_agent: str

    # Context
    request_id: str
    trace_id: str  # For distributed tracing

    # Event-specific data
    data: Dict[str, Any]

    # Outcome
    status: str  # success, failure, partial
    error_message: Optional[str]
```

### Query Event Schema
```python
@dataclass
class QueryAuditEvent(AuditEvent):
    event_type: str = 'query'
    data: QueryEventData

@dataclass
class QueryEventData:
    # Query (consider privacy - may need hashing)
    query_hash: str
    query_length: int

    # Retrieval
    retrieval_strategy: str
    documents_retrieved: int
    document_ids: List[str]  # Or hashes if sensitive
    retrieval_latency_ms: float

    # Filters applied
    access_filters: Dict[str, Any]
    user_filters: Dict[str, Any]

    # Generation
    model_used: str
    prompt_template_id: str
    input_tokens: int
    output_tokens: int
    generation_latency_ms: float

    # Response
    response_length: int
    citations_included: int
```

### Access Denied Event
```python
@dataclass
class AccessDeniedEvent(AuditEvent):
    event_type: str = 'access_denied'
    data: AccessDeniedData

@dataclass
class AccessDeniedData:
    resource_type: str
    resource_id: str
    action_attempted: str
    denial_reason: str
    policy_violated: str
    user_permissions: List[str]
    required_permissions: List[str]
```

## Implementation

### Logging Service
```python
import json
import logging
from datetime import datetime

class AuditLogger:
    def __init__(self, output='file', output_path='/var/log/rag/audit.log'):
        self.output = output
        self.logger = logging.getLogger('audit')

        if output == 'file':
            handler = logging.FileHandler(output_path)
        elif output == 'stdout':
            handler = logging.StreamHandler()

        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log(self, event: AuditEvent):
        log_entry = {
            'event_id': event.event_id,
            'event_type': event.event_type,
            'timestamp': event.timestamp.isoformat(),
            'user_id': event.user_id,
            'session_id': event.session_id,
            'request_id': event.request_id,
            'status': event.status,
            'data': event.data,
        }
        self.logger.info(json.dumps(log_entry))
```

### Integration with RAG Pipeline
```python
class AuditedRAGPipeline:
    def __init__(self, retriever, generator, audit_logger):
        self.retriever = retriever
        self.generator = generator
        self.audit = audit_logger

    def query(self, query: str, user: User, context: RequestContext):
        request_id = generate_request_id()
        start_time = time.time()

        try:
            # Retrieval with timing
            retrieval_start = time.time()
            results = self.retriever.search(query, user)
            retrieval_time = (time.time() - retrieval_start) * 1000

            # Generation with timing
            generation_start = time.time()
            response = self.generator.generate(query, results)
            generation_time = (time.time() - generation_start) * 1000

            # Log success
            self.audit.log(QueryAuditEvent(
                event_id=generate_event_id(),
                timestamp=datetime.utcnow(),
                user_id=user.id,
                session_id=context.session_id,
                client_ip=context.source_ip,
                request_id=request_id,
                status='success',
                data=QueryEventData(
                    query_hash=hash_query(query),
                    query_length=len(query),
                    retrieval_strategy=self.retriever.strategy,
                    documents_retrieved=len(results),
                    document_ids=[r.id for r in results],
                    retrieval_latency_ms=retrieval_time,
                    model_used=self.generator.model,
                    input_tokens=count_tokens(query + str(results)),
                    output_tokens=count_tokens(response),
                    generation_latency_ms=generation_time,
                    response_length=len(response),
                )
            ))

            return response

        except Exception as e:
            # Log failure
            self.audit.log(QueryAuditEvent(
                event_id=generate_event_id(),
                timestamp=datetime.utcnow(),
                user_id=user.id,
                session_id=context.session_id,
                request_id=request_id,
                status='failure',
                error_message=str(e),
                data=QueryEventData(
                    query_hash=hash_query(query),
                    query_length=len(query),
                )
            ))
            raise
```

## Log Storage and Retention

### Storage Options

| Option | Pros | Cons |
|--------|------|------|
| Files | Simple, cheap | Hard to query |
| Database | Queryable | Schema management |
| Elasticsearch | Powerful search | Operational overhead |
| Cloud logging | Managed, scalable | Cost, vendor lock-in |

### Retention Policy
```python
RETENTION_POLICIES = {
    'query': {
        'hot_storage_days': 30,    # Fast access
        'warm_storage_days': 90,   # Slower access
        'archive_days': 365,       # Cold storage
        'delete_after_days': 730   # Regulatory minimum
    },
    'security': {
        'hot_storage_days': 90,
        'archive_days': 365 * 7,   # 7 years for compliance
    },
    'admin': {
        'archive_days': 365 * 7,
    }
}
```

### Log Rotation
```python
# logrotate config example
/var/log/rag/audit.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 640 rag rag
    postrotate
        systemctl reload rag-service
    endscript
}
```

## Privacy Considerations

### What NOT to Log
- Full query text (if sensitive)
- Response content
- PII values
- Authentication credentials
- Full document content

### Anonymization Techniques
```python
def anonymize_for_logging(data):
    """
    Remove or hash sensitive information.
    """
    anonymized = data.copy()

    # Hash query instead of storing plaintext
    if 'query' in anonymized:
        anonymized['query_hash'] = hash_sha256(anonymized.pop('query'))

    # Remove user identifiers for aggregate analysis
    if 'user_id' in anonymized:
        anonymized['user_id_hash'] = hash_sha256(anonymized.pop('user_id'))

    # Remove IP addresses
    if 'client_ip' in anonymized:
        anonymized['client_ip'] = anonymize_ip(anonymized['client_ip'])

    return anonymized
```

## Compliance Mapping

### GDPR Requirements
```python
class GDPRCompliantLogger:
    def log(self, event):
        # Minimize data
        minimized = self.minimize_data(event)

        # Ensure lawful basis
        if not self.has_lawful_basis(event.user_id, event.event_type):
            return  # Don't log

        # Log with expiration
        self.store_with_retention(minimized, GDPR_RETENTION_DAYS)

    def handle_deletion_request(self, user_id):
        """GDPR Article 17: Right to erasure"""
        self.delete_user_logs(user_id)
        self.log_deletion_request(user_id)

    def handle_access_request(self, user_id):
        """GDPR Article 15: Right of access"""
        return self.export_user_logs(user_id)
```

### SOC 2 Requirements
- Log all access to sensitive data
- Log all authentication events
- Log all admin actions
- Maintain logs for minimum retention period
- Protect logs from tampering

## Log Analysis

### Security Monitoring
```python
def detect_anomalies(logs, user_id):
    """
    Detect suspicious patterns.
    """
    recent_logs = get_recent_logs(user_id, hours=24)

    alerts = []

    # Unusual query volume
    if len(recent_logs) > NORMAL_QUERY_VOLUME * 10:
        alerts.append({
            'type': 'high_volume',
            'detail': f"Query volume {len(recent_logs)} exceeds normal"
        })

    # Access denied spike
    denied = [l for l in recent_logs if l.status == 'access_denied']
    if len(denied) > 10:
        alerts.append({
            'type': 'access_denied_spike',
            'detail': f"{len(denied)} access denied events"
        })

    # Off-hours access
    off_hours = [l for l in recent_logs if is_off_hours(l.timestamp)]
    if off_hours and not user_has_off_hours_access(user_id):
        alerts.append({
            'type': 'off_hours_access',
            'detail': f"{len(off_hours)} queries outside business hours"
        })

    return alerts
```

### Usage Analytics
```python
def generate_usage_report(start_date, end_date):
    logs = get_logs_in_range(start_date, end_date)

    return {
        'total_queries': len(logs),
        'unique_users': len(set(l.user_id for l in logs)),
        'avg_latency_ms': mean(l.data.retrieval_latency_ms + l.data.generation_latency_ms for l in logs),
        'success_rate': sum(1 for l in logs if l.status == 'success') / len(logs),
        'top_query_types': get_top_query_types(logs),
        'busiest_hours': get_busiest_hours(logs),
    }
```

## Alerting

### Alert Rules
```python
ALERT_RULES = [
    {
        'name': 'high_error_rate',
        'condition': lambda stats: stats['error_rate'] > 0.05,
        'severity': 'critical',
        'message': 'Error rate exceeded 5%'
    },
    {
        'name': 'slow_queries',
        'condition': lambda stats: stats['p99_latency'] > 5000,
        'severity': 'warning',
        'message': 'P99 latency exceeded 5 seconds'
    },
    {
        'name': 'security_anomaly',
        'condition': lambda stats: stats['access_denied_rate'] > 0.1,
        'severity': 'critical',
        'message': 'High access denied rate detected'
    }
]
```

## Checklist

- [ ] Log schema defined for all event types
- [ ] Logging integrated into RAG pipeline
- [ ] Privacy considerations addressed (hashing, minimization)
- [ ] Storage solution selected
- [ ] Retention policies defined
- [ ] Log rotation configured
- [ ] Compliance requirements mapped
- [ ] Anomaly detection implemented
- [ ] Alerting rules configured
- [ ] Regular log review scheduled

---

**Previous:** [Access Control](./access-control.md)
**Next:** [Scaling - Sharding and Replication](../08-scaling/sharding-and-replication.md)
