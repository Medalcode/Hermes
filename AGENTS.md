# Myna — Agent Guide

## Commands
```bash
PYTHONPATH=. pytest tests/ -v               # all 21 tests (8 domain + 11 API + 2 serialization)
python src/main.py                          # start local server on :8000

# Vercel dev:
vercel dev                                  # serverless mode (no session persistence)
```

## Critical Quirks

- **Hexagonal Architecture — strict layer isolation**:
  - `src/core/` = **pure domain** — `models.py`, `ports.py` (ABCs), `domain_services.py`, `agents/base.py`.
  - `src/adapters/` = **infrastructure** — `api/`, `fs/`, `repositories/`, `visualization/`.
  - **Core must NEVER import from adapters**. Adapters depend on core ports (ABCs), not the other way around.
  - New features: domain logic goes in `core/domain_services.py`, orchestration in `core/agents/`, API endpoints in `adapters/api/router.py`.
- **Two execution modes**, selected by `VERCEL` env var:
  - **Local dev** (`VERCEL` unset): server-side state via cookies + pickle persistence in `storage/`.
  - **Vercel stateless** (`VERCEL=1`): no server-side session. Frontend sends `df_json` (DataFrame as JSON split format) with every request. Backend deserializes, processes, and returns results — no persistence.
- **Zero scikit-learn/scipy dependency**: K-Means, Z-Score, and Kurtosis are implemented in pure NumPy. This is intentional — scikit-learn exceeds Vercel's 250MB serverless function limit.
- **No Docker, no CI/CD, no Makefile** — this is a Vercel-deployed app. The `vercel.json` and `.vercelignore` control deployment.
- **Agent/Skill system**: `DataPrepAgent` (in `core/agents/base.py`) orchestrates via `AgentManager.execute_skill()`. Skills are registered with `@register_skill` decorator. New skills go in `core/agents/skills/` and must be registered via `register_skill`.
- **Super-Skills are parametric** — `compute_stats(stat_type=...)`, `plot(type=...)` instead of separate files per skill. Adding a new `stat_type` or `plot` type extends the existing super-skill file.
- **Upload flow**: POST file → stored in memory as DataFrame → session holds reference. To see data in the frontend, upload first, then use other endpoints.
