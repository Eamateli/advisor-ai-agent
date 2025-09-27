# Security Documentation

This document outlines all security features implemented in the Financial Advisor AI Agent.

## 🔒 Security Features

### 1. Rate Limiting
**Implementation**: Redis-based sliding window rate limiter

**Limits**:
- Chat endpoint: 10 requests/minute, 100 requests/hour per user
- Global: 60 requests/minute, 1000 requests/hour (configurable)

**How it works**:
- Uses Redis sorted sets for sliding window tracking
- Applies rate limits per user_id + endpoint
- Returns 429 status with retry-after header when exceeded

**Configuration**:
```python
# In .env
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

**Testing**:
```bash
python test_security.py  # Includes rate limit tests
```

---

### 2. Audit Trail
**Implementation**: Database-backed audit logging

**What's logged**:
- Tool executions (with sanitized inputs/outputs)
- Proactive agent actions
- OAuth events (connect/disconnect)
- Unauthorized access attempts

**Security features**:
- Sensitive data automatically redacted (passwords, tokens, API keys)
- IP address and user agent tracking
- Immutable append-only logs

**Accessing logs**:
```bash
GET /chat/audit?limit=50&action=tool_execution
Authorization: Bearer <token>
```

**Database table**: `audit_logs`

---

### 3. User Consent System
**Implementation**: Explicit opt-in for autonomous actions

**Consent types**:
- `send_email` - Send emails on user's behalf
- `create_calendar_event` - Create calendar events
- `create_hubspot_contact` - Create HubSpot contacts
- `add_hubspot_note` - Add notes to contacts

**Features**:
- Granular scopes (all, specific contacts, work hours only)
- Conditional limits (max emails per day, etc.)
- Expiration dates
- Usage tracking

**Granting consent**:
```bash
POST /chat/consent/grant
{
  "action_type": "send_email",
  "scope": "all",
  "conditions": {"max_per_day": 10}
}
```

**How it works**:
1. Before executing autonomous action, check consent
2. If no consent: Return error with consent requirement
3. If consent exists: Execute and log usage
4. User can revoke anytime

---

### 4. Webhook Signature Verification
**Implementation**: HMAC-SHA256 signature verification

**Supported webhooks**:
- HubSpot: X-HubSpot-Signature-v3 header
- Gmail/Cloud Pub/Sub: Token verification

**HubSpot verification**:
```python
signature = request.headers.get('X-HubSpot-Signature-v3')
webhook_security.enforce_signature(
    signature=signature,
    body=body_bytes,
    secret=settings.HUBSPOT_WEBHOOK_SECRET
)
```

**Setup**:
1. Generate webhook secret:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. Add to .env:
   ```bash
   HUBSPOT_WEBHOOK_SECRET=your-secret-here
   ```

3. Configure in HubSpot app settings

**Gmail Cloud Pub/Sub**:
- Set custom token in Pub/Sub subscription
- Add to .env: `GMAIL_WEBHOOK_TOKEN=your-token`

---

### 5. Data Sanitization
**Implementation**: Automatic PII and sensitive data redaction

**What's redacted**:
- Passwords
- API keys and tokens
- OAuth tokens (access/refresh)
- Credit card numbers
- SSN
- Any field containing: "secret", "password", "token", "key"

**How it works**:
```python
# Before logging
sanitized = AuditLogger._sanitize_data(tool_input)
# Sensitive fields replaced with "***REDACTED***"
```

**Custom sensitive keys**:
```python
AuditLogger._sanitize_data(
    data, 
    sensitive_keys=['custom_field', 'private_data']
)
```

---

##  Security Best Practices

### Production Deployment

**1. Environment Variables**
```bash
# REQUIRED security variables
SECRET_KEY=<use openssl rand -base64 32>
ENCRYPTION_KEY=<use Fernet.generate_key()>
HUBSPOT_WEBHOOK_SECRET=<use secrets.token_urlsafe(32)>
GMAIL_WEBHOOK_TOKEN=<use secrets.token_urlsafe(32)>
```

**2. HTTPS Only**
- Enforce HTTPS in production
- Set `Secure` flag on cookies
- Use HSTS headers

**3. CORS Configuration**
```python
# Only allow specific origins
ALLOWED_ORIGINS=https://yourdomain.com
```

**4. Rate Limiting**
- Enable Redis for production rate limiting
- Adjust limits based on usage patterns
- Monitor for abuse

**5. Audit Monitoring**
- Review audit logs regularly
- Set up alerts for:
  - Multiple unauthorized attempts
  - Unusual tool usage patterns
  - Failed webhook verifications

---

##  Monitoring & Alerts

### Key Metrics to Monitor

1. **Rate Limit Hits**
   - Query: `SELECT COUNT(*) FROM audit_logs WHERE status='unauthorized' AND action LIKE '%rate_limit%'`

2. **Unauthorized Attempts**
   - Query: `SELECT * FROM audit_logs WHERE status='unauthorized' ORDER BY created_at DESC`

3. **Proactive Actions**
   - Query: `SELECT COUNT(*) FROM audit_logs WHERE action='proactive_action' GROUP BY DATE(created_at)`

4. **Consent Usage**
   - Query: `SELECT action_type, use_count FROM user_consents WHERE is_granted=true`

### Setting Up Alerts

**Example: Alert on unauthorized attempts**
```python
# Scheduled job
unauthorized_count = db.query(AuditLog).filter(
    AuditLog.status == "unauthorized",
    AuditLog.created_at > datetime.now() - timedelta(hours=1)
).count()

if unauthorized_count > 10:
    send_alert("High number of unauthorized attempts")
```

---

##  Testing Security

### Run Security Tests
```bash
cd backend
python test_security.py
```

**Tests included**:
-  Consent grant/revoke
-  Audit logging
-  Rate limiting
-  Webhook signature verification
-  Data sanitization

### Manual Security Testing

**1. Test Rate Limiting**
```bash
# Send rapid requests
for i in {1..20}; do
  curl -X POST http://localhost:8000/chat/stream \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"message": "test"}' &
done
# Should see 429 errors after limit
```

**2. Test Webhook Security**
```bash
# Invalid signature should fail
curl -X POST http://localhost:8000/webhooks/hubspot \
  -H "X-HubSpot-Signature-v3: invalid" \
  -d '{"test": "data"}'
# Should return 401
```

**3. Test Consent Requirement**
```bash
# Try to send email without consent
# Should fail with consent requirement
```

---

##  Security Checklist

### Before Deployment

- [ ] All secrets in environment variables (not code)
- [ ] HTTPS enforced
- [ ] Rate limiting enabled with Redis
- [ ] Webhook secrets configured
- [ ] CORS properly configured
- [ ] Audit logging enabled
- [ ] Data sanitization tested
- [ ] User consent flow tested
- [ ] Security tests passing
- [ ] Error messages don't leak sensitive info
- [ ] Database backups configured
- [ ] Monitoring and alerts set up

### Regular Security Tasks

- [ ] Weekly: Review audit logs
- [ ] Monthly: Rotate webhook secrets
- [ ] Quarterly: Security audit
- [ ] As needed: Update rate limits
- [ ] As needed: Review consent usage

---

##  Incident Response

### If Security Breach Detected

1. **Immediate Actions**:
   - Revoke affected OAuth tokens
   - Rotate all secrets (webhook, JWT, encryption)
   - Block suspicious IP addresses
   - Disable affected user accounts

2. **Investigation**:
   - Query audit logs for attack pattern
   - Check for unauthorized tool executions
   - Review consent grants/usage

3. **Recovery**:
   - Notify affected users
   - Force password reset if needed
   - Update security measures
   - Document lessons learned

---

##  Security Contact

For security concerns, contact: security@yourcompany.com

**Responsible Disclosure**: Report vulnerabilities privately before public disclosure.