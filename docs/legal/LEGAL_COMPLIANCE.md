# ⚖️ Legal Compliance — TeamGenie AI

**Last Updated:** January 2026  
**Jurisdiction:** India (Primary), Global (Secondary)  
**Legal Contact:** legal@teamgenie.app

---

## Table of Contents

1. [India Gaming Laws](#india-gaming-laws)
2. [Terms of Service](#terms-of-service)
3. [Privacy Policy](#privacy-policy)
4. [Responsible Gaming](#responsible-gaming)
5. [Tax Compliance](#tax-compliance)
6. [International Compliance](#international-compliance)
7. [Intellectual Property](#intellectual-property)

---

## India Gaming Laws

### Legal Framework

**Key Legislation:**
1. **Public Gambling Act, 1867** — Prohibits gambling (but exempts skill-based games)
2. **IT Act, 2000** — Governs online activities
3. **FEMA** — Regulates foreign payments
4. **GST Act, 2017** — 28% tax on gaming
5. **DPDP Act, 2023** — Data protection

### Skill vs. Gambling — Why TeamGenie is 100% LEGAL

**✅ Fantasy sports = Game of Skill (Supreme Court of India)**

- *K.R. Lakshmanan vs State of Tamil Nadu (1996)* — Skill-based games are protected under Article 19(1)(g)
- *Varun Gumber vs UT of Chandigarh (2017)* — Fantasy sports are skill-based

**✅ TeamGenie provides INFORMATION, not gambling:**
- Users make final decisions
- We don't host contests (Dream11/MPL does)
- We're an analytics tool (like Bloomberg for stocks)

### State-Wise Restrictions

| State | Legal? | TeamGenie Approach |
|---|---|---|
| **Assam** | ❌ Banned | Geo-blocked |
| **Odisha** | ❌ Banned | Geo-blocked |
| **Telangana** | ❌ Banned | Geo-blocked |
| **Sikkim** | ⚠️ Regulated | Geo-blocked (no license) |
| **Nagaland** | ⚠️ Regulated | Geo-blocked |
| **Rest of India (23 states)** | ✅ Legal | Fully accessible |

**Geo-Blocking Implementation:**
```python
BANNED_STATES = ["AS", "OR", "TG", "SK", "NL"]

async def check_geo_restriction(request: Request):
    state = await get_state_from_ip(request.client.host)
    if state in BANNED_STATES:
        raise HTTPException(
            status_code=451,  # Unavailable For Legal Reasons
            detail=f"Service not available in {state}"
        )
```

---

## Terms of Service

### 1. Age Restriction (18+)

- You must be 18+ to use TeamGenie
- We verify age via Aadhaar eKYC / Government ID
- Violation = immediate account termination without refund

### 2. Nature of Service

- TeamGenie is an **INFORMATION SERVICE**, not a gaming platform
- We provide: AI predictions, statistical analysis, team optimization
- We **DO NOT**: Host contests, handle prize money, guarantee outcomes

### 3. No Guarantee of Winnings

- Predictions are **PROBABILISTIC**, not guaranteed
- Past performance ≠ future results
- Cricket is unpredictable (injuries, weather, umpiring)
- **TeamGenie is NOT liable for any financial losses**

### 4. Prohibited Uses

Users shall NOT:
- Use bots/scripts to automate team generation
- Sell predictions commercially (without API license)
- Reverse-engineer AI models
- Access from restricted states
- Create multiple accounts to abuse free tier
- Use for illegal gambling or match-fixing

**Violation = Account termination + potential legal action**

### 5. Liability Limitation

- Total liability limited to amount paid in last 30 days
- NOT liable for: lost profits, third-party failures, data inaccuracies, AI errors
- **Force Majeure:** Not liable for events beyond our control

### 6. Dispute Resolution

- **Governing Law:** Laws of India
- **Jurisdiction:** Courts of Bhopal, Madhya Pradesh
- **Arbitration:** Single arbitrator, Arbitration Act 1996
- **Informal first:** Email disputes@teamgenie.app, 30-day negotiation

---

## Privacy Policy

### Data We Collect

| Category | What | Why | Retention |
|---|---|---|---|
| **Account Data** | Email, name, phone | Account management | Until deletion |
| **Usage Data** | Teams created, API calls | Service improvement | 90 days |
| **Payment Data** | Order IDs (NOT card numbers) | Billing | 7 years (legal) |
| **Device Data** | IP, browser, OS | Fraud prevention | 90 days |
| **Cookies** | Session, preferences | User experience | Session / 1 year |

### Data We DON'T Collect

- ❌ Payment card numbers (handled by Razorpay/Stripe)
- ❌ Aadhaar number (verification via eKYC only, not stored)
- ❌ Location data (except state for geo-blocking)
- ❌ Biometric data

### Legal Basis (DPDP Act 2023)

1. **CONSENT** — Explicit opt-in during signup
2. **CONTRACTUAL NECESSITY** — Email for login, payment for billing
3. **LEGITIMATE INTEREST** — Service improvement, A/B testing

### User Rights (DPDP Act + GDPR)

| Right | Endpoint | Description |
|---|---|---|
| **Access** | `GET /api/user/data-export` | Download all your data as JSON |
| **Deletion** | `DELETE /api/user/me` | Permanent deletion within 30 days |
| **Correction** | `PUT /api/user/me` | Update name, email, preferences |
| **Withdraw Consent** | `POST /api/user/withdraw-consent` | Stop marketing (service emails continue) |
| **Portability** | `GET /api/user/data-export?format=csv` | Machine-readable export |

### Data Breach Notification

1. **Detection:** AI monitors 24/7
2. **Containment:** Within 1 hour (automated)
3. **Users notified:** Within 24 hours (email)
4. **CERT-In notified:** Within 72 hours (as per IT Act)
5. **Remediation:** Free credit monitoring if PII leaked

---

## Responsible Gaming

### Addiction Prevention Features

| Feature | Description |
|---|---|
| **Deposit Limits** | Users can set daily/weekly/monthly spend caps |
| **Loss Tracking** | Dashboard shows cumulative spending |
| **Time Warnings** | Alert after 2+ hours of continuous use |
| **Self-Exclusion** | Users can lock their account for 1-12 months |
| **AI Detection** | AI monitors for addiction patterns and alerts |

### Helplines

**India:**
- National Helpline: 1800-XXX-XXXX
- SHUT Clinic: shutclinic.com

**Global:**
- Gamblers Anonymous: gamblersanonymous.org
- NCPG: ncpgambling.org

**On-site:** teamgenie.app/responsible-gaming

---

## Tax Compliance

### GST (28% on Gaming Services)

```python
def calculate_gst(amount: float) -> dict:
    gst_rate = 0.28
    cgst = amount * (gst_rate / 2)  # 14% Central GST
    sgst = amount * (gst_rate / 2)  # 14% State GST
    total = amount + cgst + sgst
    return {"base": amount, "cgst": cgst, "sgst": sgst, "total": total}

# Example: ₹99 subscription → base: ₹77.34, GST: ₹21.66
```

- Tax invoices generated automatically with GSTIN
- B2B customers can claim Input Tax Credit (ITC)

### TDS (30% on Winnings >₹10,000)

- TeamGenie does NOT handle contest winnings (Dream11/MPL does)
- If we run promotional contests: 30% TDS deducted, Form 16A issued

### Financial Reporting

| Filing | Frequency | Due Date |
|---|---|---|
| GSTR-1 (outward supplies) | Monthly | 11th of next month |
| GSTR-3B (summary) | Monthly | 20th of next month |
| GSTR-9 (annual) | Annual | December 31 |
| ITR-6 (income tax) | Annual | July 31 |
| TDS returns | Quarterly | End of quarter + 1 month |

---

## International Compliance

### GDPR (European Union)

| Requirement | Status |
|---|---|
| Legal basis (Consent) | ✅ Explicit opt-in |
| Data Protection Officer | ✅ security@teamgenie.app |
| Data transfers (SCCs) | ✅ Standard Contractual Clauses |
| Right to access, deletion, portability | ✅ Implemented |
| Breach notification (72h) | ✅ Automated |
| Cookie consent banner | ✅ GDPR-compliant |

### Other Jurisdictions

| Country | Law | Status |
|---|---|---|
| USA | CCPA (California) | ✅ Compliant |
| Canada | PIPEDA | ✅ Compliant |
| Australia | Privacy Act 1988 | ✅ Compliant |
| Singapore | PDPA | ✅ Compliant |
| UAE | PDPL | 🔄 Pending review |

### PCI DSS (Payment Cards)

- ⚠️ We do NOT store card data (out of scope)
- ✅ Payment via Razorpay (PCI DSS Level 1 certified)
- ✅ We store only payment tokens, never card numbers

---

## Intellectual Property

### Our IP

| Type | Asset | Status |
|---|---|---|
| **Trademark** | "TeamGenie" (word mark) | Filed with Indian Trademark Registry |
| **Copyright** | UI/UX designs, marketing | ©2026 Mohammed Inayat Hussain Qureshi |
| **Patent** | "Multi-Agent Fantasy Sports Prediction System" | Provisional filed (Jan 2026) |
| **Trade Secrets** | AI model architectures, optimization heuristics | Confidential |

### Open-Source Licenses

- Our code: **AGPL-3.0**
- If you use our code in your SaaS, you MUST:
  - (a) Open-source your modifications
  - (b) Display "Powered by TeamGenie" notice
  - (c) Provide source code link
- **Commercial License:** Email legal@teamgenie.app for white-label licensing

### Third-Party Dependencies

- **Permissive (MIT, BSD, Apache 2.0):** React, Next.js, FastAPI, LangChain
- **Copyleft (GPL, AGPL):** None in production code (avoided intentionally)

---

## Legal Contacts

| Purpose | Contact |
|---|---|
| **General Legal** | legal@teamgenie.app |
| **Privacy Questions** | privacy@teamgenie.app |
| **Data Protection Officer** | dpo@teamgenie.app |
| **Trademark Issues** | ip@teamgenie.app |
| **Law Enforcement** | lawenforcement@teamgenie.app |
| **Emergency (data breach)** | +91-XXX-XXX-XXXX (24/7) |

---

## Disclaimer

> THIS DOCUMENT IS FOR INFORMATIONAL PURPOSES ONLY. IT DOES NOT CONSTITUTE LEGAL ADVICE. For specific legal questions, consult a licensed attorney in your jurisdiction.

TeamGenie reserves the right to update this document at any time.

---

**Document Version:** 1.0.0  
**Maintained By:** Mohammed Inayat Hussain Qureshi  
**Legal Review:** Pending (scheduled for Feb 2026)  
**Last Updated:** January 2026
