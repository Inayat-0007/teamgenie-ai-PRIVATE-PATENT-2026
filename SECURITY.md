# 🔒 TeamGenie Security Policy

**Last Updated:** January 2026  
**Security Contact:** security@teamgenie.app  
**PGP Key:** [Download](https://teamgenie.app/.well-known/pgp-key.asc)

---

## Table of Contents

1. [Security Overview](#security-overview)
2. [Threat Model](#threat-model)
3. [Vulnerability Disclosure](#vulnerability-disclosure)
4. [Security Controls](#security-controls)
5. [Penetration Testing](#penetration-testing)
6. [Incident Response](#incident-response)
7. [Compliance](#compliance)

---

## Security Overview

TeamGenie implements **defense-in-depth** security across all layers:

```
┌─────────────────────────────────────────────┐
│         SECURITY ARCHITECTURE               │
├─────────────────────────────────────────────┤
│                                             │
│  LAYER 1: Network (Cloudflare)              │
│  ✅ DDoS mitigation (unlimited)             │
│  ✅ WAF (OWASP Top 10)                      │
│  ✅ Bot management (AI-powered)             │
│                                             │
│  LAYER 2: Application (AI Firewall)         │
│  ✅ SQL injection detection                 │
│  ✅ XSS prevention                          │
│  ✅ CSRF protection                         │
│                                             │
│  LAYER 3: Authentication (Supabase)         │
│  ✅ JWT with rotation                       │
│  ✅ MFA (TOTP + SMS)                        │
│  ✅ OAuth 2.0 (Google, Apple)               │
│                                             │
│  LAYER 4: Authorization (RLS)               │
│  ✅ Row-Level Security                      │
│  ✅ Principle of least privilege            │
│                                             │
│  LAYER 5: Data (Encryption)                 │
│  ✅ At-rest: AES-256                        │
│  ✅ In-transit: TLS 1.3                     │
│  ✅ Secrets: Doppler + Infisical            │
│                                             │
│  LAYER 6: Monitoring (AI Auditor)           │
│  ✅ Real-time anomaly detection             │
│  ✅ Automated incident response             │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Threat Model

### Assets

| Asset | Value | Threat Level |
|---|---|---|
| **User Credentials** | Critical | High |
| **Payment Data** | Critical | High |
| **User PII** | High | Medium |
| **Team Predictions** | Medium | Low |
| **Analytics Data** | Low | Low |

### Threat Actors

1. **Script Kiddies** (Low Sophistication)
   - Automated vulnerability scanners
   - Common exploits (SQLi, XSS)
   - **Mitigation:** WAF, input validation

2. **Competitor Scraping** (Medium Sophistication)
   - Mass data extraction
   - API abuse
   - **Mitigation:** Rate limiting, bot detection

3. **Account Takeover Specialists** (Medium Sophistication)
   - Credential stuffing
   - Phishing attacks
   - **Mitigation:** MFA, device fingerprinting

4. **APT (Advanced Persistent Threat)** (High Sophistication)
   - Zero-day exploits
   - Social engineering
   - **Mitigation:** AI anomaly detection, security audits

---

### STRIDE Threat Analysis

| Threat | Example | Mitigation |
|---|---|---|
| **Spoofing** | Fake user authentication | JWT with short expiry + rotation |
| **Tampering** | Modify team after submission | Cryptographic signatures |
| **Repudiation** | Deny placing bet | Immutable audit logs |
| **Information Disclosure** | Leak user emails | RLS + encryption |
| **Denial of Service** | DDoS attack | Cloudflare (unlimited) |
| **Elevation of Privilege** | Free user accesses premium | Row-Level Security |

---

## Vulnerability Disclosure

### Responsible Disclosure Policy

We welcome security researchers to report vulnerabilities responsibly.

**DO:**
- ✅ Email security@teamgenie.app with details
- ✅ Allow 90 days for fix before public disclosure
- ✅ Provide steps to reproduce
- ✅ Use our staging environment for testing

**DON'T:**
- ❌ Access user data beyond proof-of-concept
- ❌ Perform DoS attacks
- ❌ Social engineer our employees
- ❌ Publicly disclose before we've patched

---

### Rewards (Bug Bounty)

| Severity | Criteria | Reward |
|---|---|---|
| **Critical** | RCE, Auth bypass, Payment fraud | ₹50,000 + Hall of Fame |
| **High** | SQL injection, XSS (stored), IDOR | ₹25,000 + Swag |
| **Medium** | CSRF, Open redirect, Info disclosure | ₹10,000 + Thanks |
| **Low** | Rate limit bypass, Clickjacking | ₹5,000 + Thanks |

**Hall of Fame:** https://teamgenie.app/security/hall-of-fame

**Out of Scope:**
- Self-XSS
- Social engineering
- Physical attacks
- Third-party services (Supabase, Cloudflare)

---

### Reporting Template

```
Subject: [SECURITY] [Severity] Brief Description

Vulnerability Type: SQL Injection / XSS / CSRF / Other
Severity: Critical / High / Medium / Low
Affected URL: https://teamgenie.app/api/...

Steps to Reproduce:
1. ...
2. ...
3. ...

Proof of Concept: [Screenshots, code, curl commands]

Impact: [Describe potential damage]

Suggested Fix: [Optional, but appreciated]

Your Details:
  Name: [For hall of fame]
  Email: [For communication]
  Twitter: [Optional]
```

**PGP Encrypted Reports:** Use our [public key](https://teamgenie.app/.well-known/pgp-key.asc)

---

## Security Controls

### 1. Authentication

```python
# apps/api/middleware/auth.py

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
from jose import jwt, JWTError
import os

security = HTTPBearer()

async def verify_token(credentials: HTTPBearer = Depends(security)):
    token = credentials.credentials
    
    try:
        # Verify JWT signature
        payload = jwt.decode(
            token,
            os.getenv("SUPABASE_JWT_SECRET"),
            algorithms=["HS256"]
        )
        
        # Check expiration
        if payload['exp'] < time.time():
            raise HTTPException(status_code=401, detail="Token expired")
        
        # Check if user is active
        user = await db.users.find_one({"id": payload['sub']})
        if not user or not user['is_active']:
            raise HTTPException(status_code=403, detail="User inactive")
        
        return payload
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Session Management:**
- JWT expiry: 15 minutes (access token)
- Refresh token expiry: 7 days
- Refresh token rotation on use
- Device fingerprinting (IP + User-Agent hash)

---

### 2. Authorization (Row-Level Security)

```sql
-- Supabase RLS Policy

-- Users can only see their own teams
CREATE POLICY "Users can view own teams"
ON teams
FOR SELECT
USING (auth.uid() = user_id);

-- Users can only create teams for themselves
CREATE POLICY "Users can create own teams"
ON teams
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Users cannot modify teams after match starts
CREATE POLICY "Cannot modify teams after match"
ON teams
FOR UPDATE
USING (
    auth.uid() = user_id AND
    (SELECT status FROM matches WHERE id = match_id) = 'scheduled'
);
```

---

### 3. Input Validation

```python
# apps/api/models/team.py

from pydantic import BaseModel, Field, validator
from typing import List

class TeamCreateRequest(BaseModel):
    match_id: str = Field(..., min_length=1, max_length=100)
    players: List[str] = Field(..., min_items=11, max_items=11)
    captain_id: str
    vice_captain_id: str
    budget: float = Field(..., ge=0, le=100)
    
    @validator('players')
    def validate_unique_players(cls, v):
        if len(v) != len(set(v)):
            raise ValueError('Duplicate players not allowed')
        return v
    
    @validator('captain_id')
    def validate_captain_in_team(cls, v, values):
        if 'players' in values and v not in values['players']:
            raise ValueError('Captain must be in team')
        return v
    
    class Config:
        anystr_strip_whitespace = True
        extra = 'forbid'
```

---

### 4. SQL Injection Prevention

```python
# ❌ VULNERABLE CODE (Never do this)
query = f"SELECT * FROM users WHERE email = '{user_input}'"

# ✅ SAFE CODE (Always use parameterized queries)
query = "SELECT * FROM users WHERE email = ?"
cursor.execute(query, (user_input,))
```

---

### 5. XSS Prevention

```typescript
// apps/web/components/TeamCard.tsx

import DOMPurify from 'isomorphic-dompurify';

export function TeamCard({ team }) {
  // ✅ SAFE (sanitize user input)
  const cleanName = DOMPurify.sanitize(team.name);
  
  return <div dangerouslySetInnerHTML={{ __html: cleanName }} />;
}
```

**Content Security Policy (CSP):**
```javascript
// next.config.js
const ContentSecurityPolicy = `
  default-src 'self';
  script-src 'self' 'unsafe-eval' 'unsafe-inline' https://cdn.vercel-insights.com;
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self' data:;
  connect-src 'self' https://api.teamgenie.app;
  frame-ancestors 'none';
`;
```

---

### 6. Rate Limiting

```python
# apps/api/middleware/rate_limit.py

from upstash_redis import Redis
from fastapi import HTTPException

redis = Redis(url=os.getenv("UPSTASH_REDIS_URL"))

async def rate_limit(request: Request):
    identifier = request.client.host
    key = f"rate_limit:{identifier}:{int(time.time() / 60)}"
    
    current = await redis.incr(key)
    
    if current == 1:
        await redis.expire(key, 60)
    
    limit = 100  # 100 req/min for free tier
    if current > limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {60 - (time.time() % 60):.0f}s"
        )
```

---

### 7. Data Encryption

```python
# At Rest — Additional encryption for sensitive fields
from cryptography.fernet import Fernet
import os

cipher = Fernet(os.getenv("ENCRYPTION_KEY"))

def encrypt_sensitive_data(data: str) -> str:
    return cipher.encrypt(data.encode()).decode()

def decrypt_sensitive_data(encrypted: str) -> str:
    return cipher.decrypt(encrypted.encode()).decode()
```

**In Transit:**
- TLS 1.3 (enforced by Cloudflare)
- HSTS header: `max-age=31536000; includeSubDomains; preload`
- Certificate pinning (mobile app)

---

### 8. Secrets Management

```yaml
# Use Doppler or Infisical (NOT .env files in production)

# Development
.env.local  # Git-ignored, local only

# Production
Doppler:
  project: teamgenie
  environment: production
  secrets:
    - SUPABASE_URL
    - SUPABASE_ANON_KEY
    - SUPABASE_SERVICE_ROLE_KEY
    - TURSO_DATABASE_URL
    - TURSO_AUTH_TOKEN
    - CLAUDE_API_KEY
    - GEMINI_API_KEY
    - RAZORPAY_KEY_ID
    - RAZORPAY_KEY_SECRET
    - ENCRYPTION_KEY
    - JWT_SECRET
```

---

### 9. AI-Powered Firewall

```python
# apps/api/middleware/ai_firewall.py

from anthropic import Anthropic

claude = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))

async def ai_firewall_check(request: Request):
    """
    AI analyzes every request for malicious patterns
    Cost: ~$0.001 per request (Claude Haiku)
    """
    
    payload = {
        "url": str(request.url),
        "method": request.method,
        "headers": dict(request.headers),
        "body": await request.body() if request.method == "POST" else None
    }
    
    analysis = await claude.messages.create(
        model="claude-haiku-4",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"""Analyze this HTTP request for security threats:

{json.dumps(payload, indent=2)}

Respond ONLY with JSON: {{"threat": boolean, "type": string, "confidence": float}}
"""
        }]
    )
    
    result = json.loads(analysis.content[0].text)
    
    if result['threat'] and result['confidence'] > 0.8:
        await log_attack(payload, result)
        await ban_ip(request.client.host)
        await send_alert(f"🚨 Attack blocked: {result['type']}")
        raise HTTPException(status_code=403, detail="Forbidden")
```

---

## Penetration Testing

### Internal Testing (Weekly)

```bash
# Automated security scanning

# 1. Dependency scanning
npm audit --audit-level=high
pip-audit

# 2. SAST (Static Application Security Testing)
semgrep --config=auto .

# 3. Container scanning
trivy image teamgenie/api:latest

# 4. Secret scanning
trufflehog git https://github.com/Inayat-0007/teamgenie-ai

# 5. API security testing
zap-cli quick-scan https://api.teamgenie.app
```

### Security Testing Checklist

- [ ] SQL Injection (all input fields)
- [ ] XSS (stored, reflected, DOM-based)
- [ ] CSRF (all state-changing endpoints)
- [ ] Authentication bypass
- [ ] Authorization bypass (IDOR)
- [ ] Session fixation/hijacking
- [ ] SSRF (Server-Side Request Forgery)
- [ ] Open redirect
- [ ] Clickjacking
- [ ] CORS misconfiguration
- [ ] Race conditions
- [ ] Business logic flaws
- [ ] API rate limit bypass
- [ ] File upload vulnerabilities
- [ ] Directory traversal
- [ ] Information disclosure

---

## Incident Response

### Severity Levels

| Level | Definition | Response Time | Example |
|---|---|---|---|
| **P0 (Critical)** | Data breach, Auth bypass | 15 minutes | User passwords leaked |
| **P1 (High)** | Service outage, Payment fraud | 1 hour | Payment gateway down |
| **P2 (Medium)** | Feature broken, Degraded performance | 4 hours | Team generation slow |
| **P3 (Low)** | Minor bug, UI issue | 24 hours | Button misaligned |

### Incident Response Playbook

**Phase 1: Detection (Automated)**
```python
async def detect_anomaly():
    metrics = await get_current_metrics()
    
    analysis = await claude.analyze(f"""
    Current metrics:
    - Error rate: {metrics['error_rate']}% (baseline: 0.1%)
    - Login failures: {metrics['login_failures']}/min (baseline: 2/min)
    - API latency p95: {metrics['latency_p95']}ms (baseline: 320ms)
    
    Is this an incident? Severity: P0/P1/P2/P3?
    """)
    
    if analysis.is_incident and analysis.severity in ['P0', 'P1']:
        await trigger_incident_response(analysis)
```

**Phase 2: Containment**
```python
async def contain_breach():
    # 1. Rotate all secrets
    await doppler.rotate_all_secrets()
    
    # 2. Invalidate all sessions
    await supabase.auth.signOutAllUsers()
    
    # 3. Enable read-only mode
    await db.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
    
    # 4. Take database snapshot
    await turso.snapshot("incident-snapshot")
    
    # 5. Notify legal team
    await send_email(to="legal@teamgenie.app", subject="Data Breach - P0")
```

**Phase 3: Post-Mortem**
```markdown
# Incident Post-Mortem Template

## Timeline
- HH:MM — Anomaly detected (AI alert)
- HH:MM — Human confirmed
- HH:MM — Containment initiated
- HH:MM — Fix deployed
- HH:MM — Recovery complete

## Root Cause
[Description]

## Impact
- Users affected: X
- Financial loss: ₹X
- Downtime: X minutes

## Action Items
- [ ] Fix 1 (owner, due date)
- [ ] Fix 2 (owner, due date)
```

---

## Compliance

### DPDP Act 2023 (India)

- ✅ **Lawful basis for processing:** User consent
- ✅ **Data minimization:** Collect only necessary data
- ✅ **Purpose limitation:** Use data only for stated purpose
- ✅ **Storage limitation:** Delete data after 1 year
- ✅ **User rights implemented:**
  - Right to access (`GET /api/user/data-export`)
  - Right to deletion (`DELETE /api/user/me`)
  - Right to correction (`PUT /api/user/me`)
  - Right to withdraw consent (`POST /api/user/withdraw-consent`)
- ✅ **Data breach notification:** Within 72 hours to CERT-In

### GDPR (EU Users)

- ✅ Legal basis: Consent (explicit opt-in)
- ✅ Data protection officer: security@teamgenie.app
- ✅ Privacy by design: RLS, encryption, minimal data collection
- ✅ Right to be forgotten: Implemented
- ✅ Data portability: Implemented (JSON export)
- ✅ Breach notification: Within 72 hours
- ✅ Cookie consent: GDPR-compliant banner

### SOC 2 (in progress)

🔄 Target: SOC 2 Type II certification by Q3 2026

---

## Security Contacts

- **General Security:** security@teamgenie.app
- **Bug Bounty:** bugbounty@teamgenie.app
- **Data Protection Officer:** dpo@teamgenie.app
- **Emergency (24/7):** +91-XXX-XXXX-XXX (Telegram: @teamgenie_security)
- **PGP Public Key:** https://teamgenie.app/.well-known/pgp-key.asc

---

**Document Version:** 1.0.0  
**Last Review:** January 2026  
**Next Review:** April 2026  
**Maintained By:** Mohammed Inayat Hussain Qureshi
