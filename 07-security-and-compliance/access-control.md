# Access Control

Ensuring users only see what they're authorized to see.

## The Access Control Problem in RAG

RAG retrieves documents based on semantic relevance, not permissions. Without access control:
- Sensitive documents leak to unauthorized users
- Compliance violations occur
- Trust is broken

## Access Control Models

### Role-Based Access Control (RBAC)
Users have roles, roles have permissions:

```python
# Role definitions
ROLES = {
    'admin': ['read:all', 'write:all'],
    'manager': ['read:department', 'read:public'],
    'employee': ['read:team', 'read:public'],
    'guest': ['read:public']
}

# Document permissions
DOCUMENT_PERMISSIONS = {
    'doc_123': ['read:hr'],
    'doc_456': ['read:public'],
    'doc_789': ['read:engineering', 'read:management']
}

def can_access(user_roles, document_id):
    required_permissions = DOCUMENT_PERMISSIONS.get(document_id, [])
    user_permissions = set()
    for role in user_roles:
        user_permissions.update(ROLES.get(role, []))

    # Check if user has any required permission
    for perm in required_permissions:
        if perm in user_permissions or 'read:all' in user_permissions:
            return True
    return False
```

### Attribute-Based Access Control (ABAC)
Access based on attributes of user, resource, and context:

```python
def evaluate_abac_policy(user, document, context):
    """
    Example ABAC policy evaluation.
    """
    policies = [
        # Department match
        lambda u, d, c: d.metadata.get('department') == u.department,

        # Security clearance
        lambda u, d, c: u.clearance_level >= d.metadata.get('classification_level', 0),

        # Geographic restriction
        lambda u, d, c: c.location in d.metadata.get('allowed_regions', [c.location]),

        # Time-based access
        lambda u, d, c: is_within_business_hours(c.timestamp) if d.metadata.get('business_hours_only') else True,
    ]

    # All applicable policies must pass
    return all(policy(user, document, context) for policy in policies)
```

### Access Control Lists (ACL)
Explicit list of who can access what:

```python
# Per-document ACL
DOCUMENT_ACLS = {
    'doc_123': {
        'users': ['alice', 'bob'],
        'groups': ['engineering'],
        'deny_users': ['charlie']  # Explicit deny
    }
}

def check_acl(user_id, user_groups, document_id):
    acl = DOCUMENT_ACLS.get(document_id)
    if not acl:
        return False  # Default deny

    # Check explicit deny first
    if user_id in acl.get('deny_users', []):
        return False

    # Check user allow list
    if user_id in acl.get('users', []):
        return True

    # Check group membership
    for group in user_groups:
        if group in acl.get('groups', []):
            return True

    return False
```

## Implementation Strategies

### Strategy 1: Pre-Filtering (Recommended)

Filter the search space BEFORE retrieval:

```python
class SecureRetriever:
    def __init__(self, vector_db):
        self.vector_db = vector_db

    def search(self, query, user, top_k=10):
        # Build filter based on user permissions
        access_filter = self.build_access_filter(user)

        # Search with filter applied
        results = self.vector_db.search(
            query_vector=embed(query),
            filter=access_filter,
            top_k=top_k
        )
        return results

    def build_access_filter(self, user):
        # User can see documents where:
        # - document is public, OR
        # - document department matches user department, OR
        # - user is in document's allowed_users
        return {
            "$or": [
                {"visibility": "public"},
                {"department": user.department},
                {"allowed_users": {"$contains": user.id}},
                {"allowed_groups": {"$containsAny": user.groups}}
            ]
        }
```

### Strategy 2: Post-Filtering

Retrieve first, then filter (simpler but less efficient):

```python
class PostFilterRetriever:
    def __init__(self, vector_db, access_checker):
        self.vector_db = vector_db
        self.access_checker = access_checker

    def search(self, query, user, top_k=10):
        # Retrieve more than needed
        candidates = self.vector_db.search(
            query_vector=embed(query),
            top_k=top_k * 5  # Over-fetch
        )

        # Filter by access
        accessible = []
        for result in candidates:
            if self.access_checker.can_access(user, result.document_id):
                accessible.append(result)
                if len(accessible) >= top_k:
                    break

        return accessible
```

### Strategy 3: Hybrid (Defense in Depth)

Apply both pre-filtering and post-filtering:

```python
class HybridSecureRetriever:
    def __init__(self, vector_db, access_checker):
        self.vector_db = vector_db
        self.access_checker = access_checker

    def search(self, query, user, top_k=10):
        # Pre-filter: basic access control in database
        basic_filter = {"visibility": {"$ne": "confidential"}}
        if user.clearance < 3:
            basic_filter["classification"] = {"$lt": user.clearance}

        candidates = self.vector_db.search(
            query_vector=embed(query),
            filter=basic_filter,
            top_k=top_k * 3
        )

        # Post-filter: detailed access control
        results = []
        for result in candidates:
            if self.access_checker.can_access(user, result.document_id):
                results.append(result)
                if len(results) >= top_k:
                    break

        return results
```

## Metadata Requirements

### Document Metadata for Access Control
```python
document_metadata = {
    # Basic classification
    'visibility': 'internal',  # public, internal, confidential, restricted
    'classification_level': 2,  # 0-5 scale

    # Organizational
    'department': 'engineering',
    'team': 'platform',
    'owner': 'alice@company.com',

    # Explicit access lists
    'allowed_users': ['alice', 'bob', 'charlie'],
    'allowed_groups': ['engineering', 'leadership'],
    'denied_users': [],

    # Temporal
    'access_start_date': '2024-01-01',
    'access_end_date': '2024-12-31',

    # Geographic
    'allowed_regions': ['us', 'eu'],

    # Compliance tags
    'contains_pii': False,
    'export_controlled': False,
}
```

### Indexing for Access Control
```python
# Ensure metadata fields are indexed for efficient filtering
vector_db.create_index('visibility')
vector_db.create_index('department')
vector_db.create_index('classification_level')
vector_db.create_index('allowed_groups')  # Array index
```

## User Context

### User Object
```python
@dataclass
class User:
    id: str
    email: str
    roles: List[str]
    groups: List[str]
    department: str
    clearance_level: int
    location: str
    is_active: bool
```

### Request Context
```python
@dataclass
class RequestContext:
    user: User
    timestamp: datetime
    source_ip: str
    user_agent: str
    session_id: str
```

## Permission Inheritance

### Document Hierarchy
```
Organization
├── Department A
│   ├── Team A1 (inherits Dept A permissions)
│   │   └── Document 1 (inherits Team A1 permissions)
│   └── Team A2
└── Department B
```

```python
def get_effective_permissions(document):
    """
    Compute effective permissions including inheritance.
    """
    permissions = set(document.permissions)

    # Inherit from parent folder
    if document.folder:
        permissions.update(get_effective_permissions(document.folder))

    # Inherit from department
    if document.department:
        permissions.update(get_department_permissions(document.department))

    return permissions
```

## Security Considerations

### Defense in Depth
```
Layer 1: Authentication (Who are you?)
    ↓
Layer 2: Authorization (What can you access?)
    ↓
Layer 3: Pre-retrieval filtering (Database level)
    ↓
Layer 4: Post-retrieval filtering (Application level)
    ↓
Layer 5: Response filtering (Final check)
```

### Preventing Bypass Attacks

**Prompt injection:**
```python
def sanitize_query(query):
    # Remove potential injection attempts
    dangerous_patterns = [
        r'ignore.*previous.*instructions',
        r'show.*all.*documents',
        r'bypass.*security',
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            raise SecurityException("Potentially malicious query detected")
    return query
```

**Metadata tampering:**
```python
def validate_access_request(request):
    # Verify user identity from trusted source
    user = auth_service.get_verified_user(request.token)

    # Don't trust user-provided permissions
    # Always fetch from authoritative source
    permissions = permission_service.get_permissions(user.id)

    return user, permissions
```

## Audit Logging

### Access Log Schema
```python
@dataclass
class AccessLog:
    timestamp: datetime
    user_id: str
    action: str  # 'search', 'view', 'denied'
    query: str
    documents_accessed: List[str]
    documents_denied: List[str]
    client_ip: str
    session_id: str
```

### Logging Implementation
```python
def log_access(user, query, results, denied):
    log_entry = AccessLog(
        timestamp=datetime.utcnow(),
        user_id=user.id,
        action='search',
        query=hash_query(query),  # Hash for privacy
        documents_accessed=[r.id for r in results],
        documents_denied=[d.id for d in denied],
        client_ip=get_client_ip(),
        session_id=get_session_id()
    )
    audit_logger.log(log_entry)
```

## Testing Access Control

### Unit Tests
```python
def test_access_control():
    # User without permission
    user = User(id='guest', groups=[], department='external')
    doc = Document(id='secret', metadata={'visibility': 'confidential'})
    assert not can_access(user, doc)

    # User with permission
    user = User(id='admin', groups=['admin'], department='it')
    assert can_access(user, doc)

    # Edge case: explicit deny overrides allow
    user = User(id='bob', groups=['engineering'], department='eng')
    doc = Document(id='restricted', metadata={
        'allowed_groups': ['engineering'],
        'denied_users': ['bob']
    })
    assert not can_access(user, doc)
```

### Penetration Testing
- Test with unauthorized user credentials
- Attempt to access via manipulated metadata
- Test prompt injection attacks
- Verify audit logs capture denied attempts

## Checklist

- [ ] Access control model chosen (RBAC/ABAC/ACL)
- [ ] Document metadata schema includes permissions
- [ ] Pre-filtering implemented in retriever
- [ ] Post-filtering as defense in depth
- [ ] User context properly propagated
- [ ] Audit logging implemented
- [ ] Permission inheritance handled
- [ ] Prompt injection protection added
- [ ] Access control unit tests written
- [ ] Penetration testing scheduled

---

**Previous:** [PII and Redaction](./pii-and-redaction.md)
**Next:** [Audit and Logging](./audit-and-logging.md)
