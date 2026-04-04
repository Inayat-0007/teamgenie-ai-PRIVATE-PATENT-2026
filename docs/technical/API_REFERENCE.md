# 🔌 TeamGenie API Reference

**Base URL:** `https://api.teamgenie.app/v1`  
**Authentication:** Bearer token (JWT)  
**Rate Limits:** 100 req/min (free), 1000 req/min (premium)  
**Version:** 1.0.0  
**Last Updated:** January 2026

---

## Table of Contents

1. [Authentication](#authentication)
2. [Team Generation](#team-generation)
3. [Player Insights](#player-insights)
4. [Match Data](#match-data)
5. [User Management](#user-management)
6. [Webhooks](#webhooks)
7. [Error Codes](#error-codes)
8. [SDKs](#sdks)

---

## Authentication

### POST /auth/login

Login with email/password or OAuth.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "dGhpcyBp...",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "tier": "free"
  }
}
```

**Error (401 Unauthorized):**
```json
{
  "error": {
    "code": "invalid_credentials",
    "message": "Email or password is incorrect."
  }
}
```

---

### POST /auth/register

Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password_123",
  "full_name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "tier": "free",
    "created_at": "2026-01-15T10:30:00Z"
  },
  "access_token": "eyJhbG...",
  "refresh_token": "dGhpcyBp..."
}
```

---

### POST /auth/refresh

Refresh an expired access token.

**Request:**
```json
{
  "refresh_token": "dGhpcyBp..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbG_new...",
  "refresh_token": "dGhpcyBp_new...",
  "expires_in": 3600
}
```

---

### POST /auth/logout

Invalidate current session.

**Headers:**
```
Authorization: Bearer eyJhbG...
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

---

### POST /auth/forgot-password

Request password reset email.

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Password reset email sent. Check your inbox."
}
```

---

## Team Generation

### POST /api/team/generate

Generate optimal fantasy team using multi-agent AI.

**Headers:**
```
Authorization: Bearer eyJhbG...
Content-Type: application/json
```

**Request:**
```json
{
  "match_id": "ind-vs-aus-2026-01-15",
  "budget": 100,
  "risk_level": "balanced",
  "user_preferences": {
    "favorite_players": ["virat_kohli"],
    "avoid_players": ["player_xyz"]
  }
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `match_id` | string | ✅ | Unique match identifier |
| `budget` | float | ✅ | Team budget constraint (max: 100) |
| `risk_level` | string | ❌ | `"safe"`, `"balanced"` (default), or `"aggressive"` |
| `user_preferences` | object | ❌ | Player inclusion/exclusion preferences |
| `user_preferences.favorite_players` | string[] | ❌ | Player IDs to prioritize |
| `user_preferences.avoid_players` | string[] | ❌ | Player IDs to exclude |

**Response (200 OK):**
```json
{
  "team": {
    "players": [
      {
        "id": "virat_kohli",
        "name": "Virat Kohli",
        "role": "batsman",
        "price": 10.5,
        "predicted_points": 85.3,
        "confidence": 0.87,
        "ownership_pct": 67.3,
        "form_trend": "improving"
      },
      {
        "id": "rohit_sharma",
        "name": "Rohit Sharma",
        "role": "batsman",
        "price": 10.0,
        "predicted_points": 72.1,
        "confidence": 0.82,
        "ownership_pct": 71.5,
        "form_trend": "stable"
      },
      {
        "id": "jasprit_bumrah",
        "name": "Jasprit Bumrah",
        "role": "bowler",
        "price": 9.5,
        "predicted_points": 68.4,
        "confidence": 0.79,
        "ownership_pct": 55.2,
        "form_trend": "improving"
      }
    ],
    "captain": "virat_kohli",
    "vice_captain": "rohit_sharma",
    "total_cost": 99.5,
    "predicted_total": 847,
    "risk_score": 0.52
  },
  "reasoning": {
    "budget_agent": "Maximized points within ₹100. Used ILP solver to find global optimum. Key picks: Kohli (high form), Bumrah (venue advantage).",
    "differential_agent": "Found 3 low-ownership gems: Player A (12% ownership, 0.78 confidence), Player B (8% ownership, 0.72 confidence), Player C (15% ownership, 0.81 confidence).",
    "risk_agent": "Balanced 60% safe picks / 40% aggressive differentials. Monte Carlo simulation shows 72% probability of top-3 finish."
  },
  "generation_time_ms": 4832,
  "cached": false,
  "model_version": "1.0.0"
}
```

**Rate Limits:**

| Tier | Limit |
|---|---|
| **Free** | 5 teams/day |
| **₹19/match** | Unlimited for that match |
| **₹99/month** | Unlimited all matches |
| **₹499/API** | 10,000 API calls/month |

---

### GET /api/team/{team_id}

Retrieve a previously generated team.

**Response (200 OK):**
```json
{
  "team_id": "uuid",
  "match_id": "ind-vs-aus-2026-01-15",
  "players": [...],
  "captain": "virat_kohli",
  "vice_captain": "rohit_sharma",
  "created_at": "2026-01-15T10:30:00Z",
  "actual_points": null
}
```

---

### GET /api/team/history

List all teams created by the authenticated user.

**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | integer | 1 | Page number |
| `limit` | integer | 20 | Results per page (max: 100) |
| `match_id` | string | — | Filter by match |
| `sort` | string | `created_at` | Sort field |
| `order` | string | `desc` | Sort order (`asc` or `desc`) |

**Response (200 OK):**
```json
{
  "teams": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 47,
    "total_pages": 3
  }
}
```

---

## Player Insights

### GET /api/player/{player_id}/insights

Get AI-powered analysis of a specific player.

**Request:**
```
GET /api/player/virat_kohli/insights?match_id=ind-vs-aus-2026-01-15
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `match_id` | string | ❌ | Context-specific analysis for a match |

**Response (200 OK):**
```json
{
  "player": {
    "id": "virat_kohli",
    "name": "Virat Kohli",
    "team": "India",
    "role": "batsman",
    "current_price": 10.5,
    "batting_style": "Right-hand bat",
    "bowling_style": "Right-arm medium"
  },
  "insights": {
    "recent_form": {
      "last_5_matches": [45, 68, 23, 89, 102],
      "average": 65.4,
      "trend": "improving",
      "consistency_score": 0.73
    },
    "vs_opponent": {
      "opponent": "Australia",
      "matches": 15,
      "average": 58.3,
      "high_score": 183,
      "strike_rate": 87.5
    },
    "at_venue": {
      "venue": "Wankhede Stadium, Mumbai",
      "matches": 8,
      "average": 72.1,
      "high_score": 115,
      "note": "Excellent record at Wankhede. Flat batting track suits aggressive style."
    },
    "ai_prediction": {
      "expected_points": 85.3,
      "confidence": 0.87,
      "range": {
        "low": 35,
        "high": 140
      },
      "reasoning": "Strong recent form (improving trend). Favorable venue history (avg 72.1). Good record vs Australia bowling attack. Weather conditions suit batting."
    },
    "risk_factors": [
      "High ownership (67.3%) — less differential value",
      "Slight groin niggle reported in practice session"
    ]
  },
  "ownership": {
    "percentage": 67.3,
    "category": "high_ownership",
    "trend": "rising"
  }
}
```

---

### GET /api/player/search

Search players by name, team, or role.

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `q` | string | ✅ | Search query (min 2 chars) |
| `role` | string | ❌ | Filter: `batsman`, `bowler`, `all_rounder`, `wicket_keeper` |
| `team` | string | ❌ | Filter by team name |
| `limit` | integer | ❌ | Max results (default: 20) |

**Response (200 OK):**
```json
{
  "players": [
    {
      "id": "virat_kohli",
      "name": "Virat Kohli",
      "team": "India",
      "role": "batsman",
      "current_price": 10.5,
      "is_active": true
    }
  ],
  "total": 1
}
```

---

### GET /api/player/{player_id}/stats

Get detailed career statistics for a player.

**Response (200 OK):**
```json
{
  "player_id": "virat_kohli",
  "formats": {
    "t20": {
      "matches": 125,
      "runs": 4200,
      "average": 52.5,
      "strike_rate": 139.7,
      "hundreds": 1,
      "fifties": 38
    },
    "odi": {
      "matches": 290,
      "runs": 13800,
      "average": 58.1,
      "strike_rate": 93.2,
      "hundreds": 50,
      "fifties": 72
    }
  },
  "fantasy_stats": {
    "avg_fantasy_points": 62.3,
    "max_fantasy_points": 187,
    "consistency": 0.78
  }
}
```

---

## Match Data

### GET /api/match/upcoming

List upcoming matches with available team generation.

**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `sport` | string | `cricket` | Sport type |
| `format` | string | — | `T20`, `ODI`, `Test` |
| `limit` | integer | 10 | Max results |

**Response (200 OK):**
```json
{
  "matches": [
    {
      "id": "ind-vs-aus-2026-01-15",
      "team_a": "India",
      "team_b": "Australia",
      "venue": "Wankhede Stadium, Mumbai",
      "match_date": "2026-01-15T14:30:00Z",
      "match_type": "T20",
      "series_name": "Border-Gavaskar Trophy 2026",
      "status": "scheduled",
      "team_generation_available": true
    }
  ],
  "total": 5
}
```

---

### GET /api/match/{match_id}

Get detailed match information.

**Response (200 OK):**
```json
{
  "match": {
    "id": "ind-vs-aus-2026-01-15",
    "team_a": "India",
    "team_b": "Australia",
    "venue": "Wankhede Stadium, Mumbai",
    "venue_city": "Mumbai",
    "venue_country": "India",
    "match_date": "2026-01-15T14:30:00Z",
    "match_type": "T20",
    "series_name": "Border-Gavaskar Trophy 2026",
    "match_number": 3,
    "status": "scheduled"
  },
  "conditions": {
    "weather": {
      "temperature": 28,
      "humidity": 65,
      "wind_speed": 12,
      "chance_of_rain": 10
    },
    "pitch_report": "Flat batting track with some turn expected in the second innings. Average first innings score: 175.",
    "dew_factor": "Moderate dew expected in the second innings. Chasing team may have advantage."
  },
  "head_to_head": {
    "total_matches": 45,
    "team_a_wins": 22,
    "team_b_wins": 20,
    "draws": 3,
    "last_5": ["India", "Australia", "India", "India", "Australia"]
  }
}
```

---

### GET /api/match/{match_id}/live

Get real-time match updates.

**Response (200 OK):**
```json
{
  "match": {
    "id": "ind-vs-aus-2026-01-15",
    "teams": ["India", "Australia"],
    "venue": "Wankhede Stadium, Mumbai",
    "date": "2026-01-15T14:30:00Z",
    "status": "live"
  },
  "toss": {
    "winner": "India",
    "decision": "bat"
  },
  "playing_xi": {
    "india": ["rohit_sharma", "virat_kohli", "suryakumar_yadav", "kl_rahul", "hardik_pandya", "ravindra_jadeja", "rishabh_pant", "axar_patel", "kuldeep_yadav", "jasprit_bumrah", "mohammed_siraj"],
    "australia": ["david_warner", "travis_head", "steve_smith", "marnus_labuschagne", "glenn_maxwell", "cameron_green", "alex_carey", "pat_cummins", "mitchell_starc", "josh_hazlewood", "adam_zampa"]
  },
  "live_score": {
    "india": {
      "runs": 156,
      "wickets": 3,
      "overs": 24.2,
      "run_rate": 6.41
    }
  },
  "fantasy_impact": {
    "top_scorers": [
      {"player_id": "virat_kohli", "points": 89, "status": "batting"},
      {"player_id": "rohit_sharma", "points": 62, "status": "out"}
    ]
  },
  "updated_at": "2026-01-15T16:45:32Z"
}
```

---

## User Management

### GET /api/user/me

Get current user profile.

**Response (200 OK):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "username": "johndoe",
  "avatar_url": null,
  "tier": "premium",
  "subscription": {
    "plan": "monthly",
    "amount": 99,
    "currency": "INR",
    "status": "active",
    "current_period_end": "2026-02-15T00:00:00Z",
    "renews_at": "2026-02-15"
  },
  "stats": {
    "teams_generated": 47,
    "accuracy": 0.68,
    "total_winnings": 15420,
    "win_rate": 0.34,
    "best_rank": 12
  },
  "preferences": {
    "risk_profile": "balanced",
    "favorite_players": ["virat_kohli", "rohit_sharma"],
    "notifications": {
      "email": true,
      "push": true,
      "match_updates": true
    }
  },
  "created_at": "2025-12-01T10:00:00Z",
  "last_login_at": "2026-01-15T10:30:00Z"
}
```

---

### PUT /api/user/me

Update user profile.

**Request:**
```json
{
  "full_name": "John Doe Updated",
  "username": "johndoe_new",
  "preferences": {
    "risk_profile": "aggressive"
  }
}
```

**Response (200 OK):**
```json
{
  "message": "Profile updated successfully",
  "user": {...}
}
```

---

### GET /api/user/data-export

Export all user data (GDPR/DPDP compliance).

**Response (200 OK):**
```json
{
  "export_url": "https://api.teamgenie.app/exports/user_abc123_20260115.json",
  "expires_at": "2026-01-16T10:30:00Z",
  "format": "json",
  "includes": ["profile", "teams", "predictions", "analytics"]
}
```

---

### DELETE /api/user/me

Permanently delete user account (Right to be Forgotten).

**Response (200 OK):**
```json
{
  "message": "Account scheduled for deletion. All data will be removed within 30 days.",
  "deletion_date": "2026-02-15T00:00:00Z"
}
```

---

## Webhooks

### POST /api/webhooks/subscribe

Subscribe to real-time events.

**Request:**
```json
{
  "url": "https://your-server.com/webhook",
  "events": ["match.toss", "match.playing_xi", "player.injury"],
  "secret": "your-webhook-secret"
}
```

**Response (201 Created):**
```json
{
  "webhook_id": "uuid",
  "url": "https://your-server.com/webhook",
  "events": ["match.toss", "match.playing_xi", "player.injury"],
  "status": "active",
  "created_at": "2026-01-15T10:30:00Z"
}
```

### Available Events

| Event | Description | Trigger |
|---|---|---|
| `match.scheduled` | New match announced | 48h before match |
| `match.toss` | Toss result available | At toss time |
| `match.playing_xi` | Playing XI announced | 30-60 min before match |
| `match.live` | Match started | Match start |
| `match.completed` | Match ended with result | Match end |
| `player.injury` | Player injury reported | Real-time |
| `player.price_change` | Player price updated | Daily |
| `prediction.updated` | AI prediction refreshed | On new data |

### Webhook Payload Example

```json
{
  "event": "match.playing_xi",
  "match_id": "ind-vs-aus-2026-01-15",
  "data": {
    "team": "india",
    "playing_xi": ["rohit_sharma", "virat_kohli", "suryakumar_yadav", "..."]
  },
  "timestamp": "2026-01-15T14:00:00Z",
  "signature": "sha256=abc123..."
}
```

### Webhook Security

All webhook payloads are signed with HMAC-SHA256 using your webhook secret:

```python
import hmac
import hashlib

def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## Error Codes

### HTTP Status Codes

| Code | Meaning | Description |
|---|---|---|
| `200` | OK | Request succeeded |
| `201` | Created | Resource created |
| `400` | Bad Request | Invalid parameters |
| `401` | Unauthorized | Missing/invalid token |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource doesn't exist |
| `429` | Too Many Requests | Rate limit exceeded |
| `451` | Unavailable For Legal Reasons | Geo-restricted (banned state) |
| `500` | Internal Server Error | AI service unavailable |
| `503` | Service Unavailable | Scheduled maintenance |

### Error Response Format

```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "You've exceeded 100 requests/min (free tier). Upgrade to premium.",
    "details": {
      "limit": 100,
      "used": 101,
      "reset_at": "2026-01-15T15:00:00Z"
    },
    "request_id": "req_abc123",
    "documentation_url": "https://docs.teamgenie.app/errors/rate_limit_exceeded"
  }
}
```

### Application Error Codes

| Error Code | HTTP Status | Description |
|---|---|---|
| `invalid_credentials` | 401 | Wrong email/password |
| `token_expired` | 401 | JWT has expired |
| `rate_limit_exceeded` | 429 | Too many requests |
| `match_not_found` | 404 | Match ID doesn't exist |
| `player_not_found` | 404 | Player ID doesn't exist |
| `team_budget_exceeded` | 400 | Team cost exceeds budget |
| `invalid_team_size` | 400 | Team doesn't have exactly 11 players |
| `duplicate_players` | 400 | Same player selected twice |
| `generation_failed` | 500 | AI model error during generation |
| `match_locked` | 403 | Match has started, team can't be modified |
| `geo_restricted` | 451 | Service unavailable in user's state |
| `subscription_required` | 403 | Feature requires paid subscription |
| `daily_limit_reached` | 429 | Free tier daily limit |

---

## SDKs

### Python

```bash
pip install teamgenie
```

```python
from teamgenie import Client

client = Client(api_key="your_api_key")

# Generate team
team = client.team.generate(
    match_id="ind-vs-aus-2026-01-15",
    budget=100,
    risk_level="balanced"
)

print(f"Team: {[p.name for p in team.players]}")
print(f"Captain: {team.captain.name}")
print(f"Predicted Points: {team.predicted_total}")
print(f"Generation Time: {team.generation_time_ms}ms")

# Get player insights
insights = client.player.insights(
    player_id="virat_kohli",
    match_id="ind-vs-aus-2026-01-15"
)

print(f"Expected Points: {insights.ai_prediction.expected_points}")
print(f"Confidence: {insights.ai_prediction.confidence}")

# List upcoming matches
matches = client.match.upcoming(sport="cricket", format="T20")
for match in matches:
    print(f"{match.team_a} vs {match.team_b} — {match.match_date}")
```

### JavaScript / TypeScript

```bash
npm install @teamgenie/sdk
```

```typescript
import { TeamGenieClient } from '@teamgenie/sdk'

const client = new TeamGenieClient({ apiKey: 'your_api_key' })

// Generate team
const team = await client.team.generate({
  matchId: 'ind-vs-aus-2026-01-15',
  budget: 100,
  riskLevel: 'balanced'
})

console.log('Players:', team.players.map(p => p.name))
console.log('Captain:', team.captain)
console.log('Predicted Points:', team.predictedTotal)

// Get player insights
const insights = await client.player.insights('virat_kohli', {
  matchId: 'ind-vs-aus-2026-01-15'
})

console.log('Expected:', insights.aiPrediction.expectedPoints)

// Subscribe to webhooks
client.webhooks.subscribe({
  url: 'https://your-server.com/webhook',
  events: ['match.toss', 'match.playing_xi']
})
```

### cURL Examples

```bash
# Login
curl -X POST https://api.teamgenie.app/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secure_password"}'

# Generate team (with auth token)
curl -X POST https://api.teamgenie.app/v1/api/team/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "match_id": "ind-vs-aus-2026-01-15",
    "budget": 100,
    "risk_level": "balanced"
  }'

# Get player insights
curl https://api.teamgenie.app/v1/api/player/virat_kohli/insights \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get upcoming matches
curl https://api.teamgenie.app/v1/api/match/upcoming?format=T20 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## API Health

### GET /health

Check API status (no authentication required).

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": "72h 15m 32s",
  "services": {
    "database": "connected",
    "cache": "connected",
    "vector_db": "connected",
    "ai_models": "available"
  },
  "timestamp": "2026-01-15T10:30:00Z"
}
```

---

## Rate Limiting Headers

All API responses include rate limit headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1705312800
X-Request-Id: req_abc123
```

---

## Pagination

All list endpoints support cursor-based pagination:

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "total_pages": 8,
    "has_next": true,
    "has_previous": false
  }
}
```

---

## Versioning

The API uses URL-based versioning:

- **Current:** `v1` (January 2026)
- **Deprecation policy:** Old versions supported for 12 months after new version release
- **Changelog:** [API Changelog](https://docs.teamgenie.app/changelog)

---

**API Documentation:** https://docs.teamgenie.app  
**Status Page:** https://status.teamgenie.app  
**Support:** api-support@teamgenie.app  

**Document Version:** 1.0.0  
**Last Updated:** January 2026  
**Maintained By:** Mohammed Inayat Hussain Qureshi
