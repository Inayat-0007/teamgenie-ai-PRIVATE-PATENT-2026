# 🤝 Contributing to TeamGenie AI

First off, thank you for considering contributing to TeamGenie! This document outlines guidelines for contributing.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How Can I Contribute?](#how-can-i-contribute)
3. [Development Setup](#development-setup)
4. [Coding Standards](#coding-standards)
5. [Testing Requirements](#testing-requirements)
6. [Pull Request Process](#pull-request-process)
7. [Commit Message Guidelines](#commit-message-guidelines)

---

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behavior includes:**
- ✅ Using welcoming and inclusive language
- ✅ Being respectful of differing viewpoints
- ✅ Accepting constructive criticism gracefully
- ✅ Focusing on what's best for the community

**Unacceptable behavior includes:**
- ❌ Trolling, insulting/derogatory comments, personal attacks
- ❌ Public or private harassment
- ❌ Publishing others' private information without permission
- ❌ Other conduct reasonably considered inappropriate

### Enforcement

Instances of abusive behavior may be reported to conduct@teamgenie.app. All complaints will be reviewed and investigated.

---

## How Can I Contribute?

### Reporting Bugs

**Before submitting a bug report:**
- Check existing issues (including closed ones)
- Ensure it's reproducible in the latest version

**When submitting:**
1. Use the bug report template (`.github/ISSUE_TEMPLATE/bug_report.md`)
2. Provide steps to reproduce
3. Include screenshots/logs if applicable
4. Mention your environment (OS, browser, Node.js version)

### Suggesting Features

**Before suggesting:**
- Check if it's already requested
- Ensure it aligns with project goals

**When suggesting:**
1. Use the feature request template
2. Explain the problem it solves
3. Describe your proposed solution
4. Consider alternatives

### Code Contributions

**Good first issues:**
- Look for `good-first-issue` label
- Ask questions in issue comments before starting

**Areas needing help:**
- Documentation improvements
- Test coverage
- UI/UX enhancements
- Performance optimizations
- Security hardening

---

## Development Setup

### Prerequisites

```bash
# Required
node >= 20.0.0
python >= 3.11
bun >= 1.0.0
git >= 2.40.0

# Optional (for full setup)
docker >= 24.0.0
docker-compose >= 2.20.0
```

### Setup Steps

```bash
# 1. Fork the repository (via GitHub UI)

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/teamgenie-ai.git
cd teamgenie-ai

# 3. Add upstream remote
git remote add upstream https://github.com/Inayat-0007/teamgenie-ai.git

# 4. Install dependencies
bun install  # Root
cd apps/api && pip install -r requirements.txt  # Backend
cd apps/web && bun install  # Frontend
cd apps/mobile && bun install  # Mobile

# 5. Copy environment variables
cp .env.example .env
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local

# 6. Start development environment
docker-compose up -d  # OR manually start services

# 7. Run database migrations
cd apps/api && alembic upgrade head

# 8. Start development servers
bun dev  # Starts all apps via Turborepo
```

### Running Locally

```bash
# Backend only
cd apps/api
uvicorn main:app --reload --port 8000

# Frontend only
cd apps/web
bun dev

# Mobile only
cd apps/mobile
bun run ios  # or 'bun run android'

# All at once (recommended)
bun dev  # From root
```

---

## Coding Standards

### Python (Backend)

**Style:** PEP 8 + Black formatter

```python
# ✅ GOOD
async def get_user(user_id: str) -> User:
    """
    Retrieve user by ID.
    
    Args:
        user_id: Unique user identifier
        
    Returns:
        User object if found
        
    Raises:
        HTTPException: If user not found
    """
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

# ❌ BAD
def get_user(user_id):  # Missing type hints
    user = db.users.find_one({"id": user_id})  # Not async
    return user  # No validation
```

**Linting:**
```bash
# Install pre-commit hooks
pre-commit install

# Manual linting
black apps/api  # Format
flake8 apps/api  # Lint
mypy apps/api  # Type check
```

### TypeScript (Frontend)

**Style:** Airbnb + Prettier

```typescript
// ✅ GOOD
interface TeamGenerateRequest {
  matchId: string
  budget: number
  riskLevel: 'safe' | 'balanced' | 'aggressive'
}

async function generateTeam(
  request: TeamGenerateRequest
): Promise<Team> {
  const response = await fetch('/api/team/generate', {
    method: 'POST',
    body: JSON.stringify(request)
  })
  
  if (!response.ok) {
    throw new Error('Team generation failed')
  }
  
  return response.json()
}

// ❌ BAD
function generateTeam(request: any): any {  // 'any' type
  fetch('/api/team/generate', {  // Not async
    method: 'POST',
    body: JSON.stringify(request)
  })
}
```

**Linting:**
```bash
bun run lint  # ESLint + Prettier
bun run lint:fix  # Fix auto-fixable issues
```

### Naming Conventions

| Type | Convention | Example |
|---|---|---|
| **Files (Python)** | `snake_case.py` | `user_service.py` |
| **Files (TypeScript)** | `kebab-case.tsx` | `team-card.tsx` |
| **Classes** | `PascalCase` | `UserService` |
| **Functions** | `snake_case` (Python) | `get_user_by_id()` |
| **Functions** | `camelCase` (TypeScript) | `getUserById()` |
| **Constants** | `UPPER_SNAKE_CASE` | `MAX_TEAM_SIZE` |
| **Components** | `PascalCase` | `TeamCard` |
| **Hooks** | `use` prefix | `useAuth()` |

---

## Testing Requirements

### Backend Tests (pytest)

**Coverage target: 80%+**

```python
# apps/api/tests/test_team.py

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_generate_team_success():
    response = client.post(
        "/api/team/generate",
        json={
            "match_id": "test-match",
            "budget": 100,
            "risk_level": "balanced"
        },
        headers={"Authorization": "Bearer valid_token"}
    )
    
    assert response.status_code == 200
    assert "players" in response.json()
    assert len(response.json()["players"]) == 11

def test_generate_team_unauthorized():
    response = client.post("/api/team/generate", json={})
    assert response.status_code == 401
```

**Run tests:**
```bash
cd apps/api
pytest                          # Run all tests
pytest --cov=. --cov-report=html  # With coverage
pytest tests/test_team.py       # Specific test
pytest-watch                    # Watch mode
```

### Frontend Tests (Vitest + Testing Library)

**Coverage target: 70%+**

```typescript
// apps/web/__tests__/TeamCard.test.tsx

import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import TeamCard from '@/components/TeamCard'

describe('TeamCard', () => {
  it('renders team players', () => {
    const team = {
      players: [
        { id: '1', name: 'Virat Kohli', role: 'batsman' }
      ],
      captain: '1'
    }
    
    render(<TeamCard team={team} />)
    
    expect(screen.getByText('Virat Kohli')).toBeInTheDocument()
    expect(screen.getByText('Captain')).toBeInTheDocument()
  })
})
```

**Run tests:**
```bash
cd apps/web
bun test            # Run all tests
bun test --watch    # Watch mode
bun test --coverage # Coverage
```

### E2E Tests (Playwright)

```bash
bun playwright test           # Run all
bun playwright test --ui      # With UI
bun playwright test --project=chromium  # Specific browser
```

---

## Pull Request Process

### Before Submitting

- [ ] Code compiles/runs without errors
- [ ] Tests pass (`bun test` + `pytest`)
- [ ] Linting passes (`bun run lint` + `black` + `flake8`)
- [ ] Coverage doesn't decrease
- [ ] Documentation updated (if needed)
- [ ] Changelog entry added (`CHANGELOG.md`)

### PR Title Format

```
<type>(<scope>): <subject>

Examples:
feat(api): add team generation endpoint
fix(web): resolve infinite loop in useAuth hook
docs(readme): update installation instructions
perf(ai): optimize RAG query performance
test(api): add tests for user service
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `perf`: Performance improvement
- `test`: Adding tests
- `chore`: Maintenance (dependencies, etc.)

### Review Process

1. **Automated checks** (GitHub Actions) — Linting, Tests, Build, Security scan
2. **Code review** (1-2 reviewers) — Quality, coverage, performance, security
3. **Approval required** from code owner
4. **Merge** (squash + merge) → Auto-deploys to staging

---

## Commit Message Guidelines

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Example

```
feat(api): implement AI-powered team generation

- Add CrewAI multi-agent orchestration
- Integrate Gemini 2.0 Flash for predictions
- Add caching layer for faster response times

Closes #42
```

---

## Development Workflow

### Branching Strategy

```
main (production)
  ├── develop (staging)
  │   ├── feature/ai-team-generation
  │   ├── feature/payment-integration
  │   ├── fix/login-bug
  │   └── docs/api-reference
```

### Creating a Feature Branch

```bash
# Update your fork
git checkout develop
git pull upstream develop

# Create feature branch
git checkout -b feature/my-amazing-feature

# Make changes, commit often
git add .
git commit -m "feat(scope): description"

# Push to your fork
git push origin feature/my-amazing-feature

# Create PR via GitHub UI
```

### Keeping Your Branch Updated

```bash
git checkout develop
git pull upstream develop
git checkout feature/my-amazing-feature
git rebase develop

# Resolve conflicts if any, then force push
git push origin feature/my-amazing-feature --force
```

---

## Code Review Guidelines

### For Reviewers
- ✅ Code correctness (does it work?)
- ✅ Test coverage (edge cases covered?)
- ✅ Performance (any bottlenecks?)
- ✅ Security (any vulnerabilities?)
- ✅ Readability (clear variable names?)
- ✅ Documentation (complex logic explained?)

### For Authors
- ✅ Thank reviewers for their time
- ✅ Explain your reasoning (don't just "fix")
- ✅ Push commits (don't force-push during review)
- ✅ Re-request review after changes

---

## Questions?

- **General questions:** Open a [Discussion](https://github.com/Inayat-0007/teamgenie-ai/discussions)
- **Bug reports:** Open an [Issue](https://github.com/Inayat-0007/teamgenie-ai/issues)
- **Security issues:** Email security@teamgenie.app (private)
- **Chat:** Join our Discord (coming soon)

---

## License

By contributing, you agree that your contributions will be licensed under the **AGPL-3.0 License**.

---

**Thank you for contributing to TeamGenie!** 🏏🤖
