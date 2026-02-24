# Railway Environment Variables (Template)

> Names only. Do not commit secret values.

## Required
- `PORT` *(injected by Railway)*
- `ENV` = `production`
- `SECRET_KEY`

## Optional (only if used)
- `DATABASE_URL`
- `REDIS_URL`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`

## Flask Runtime Notes
- App must bind to `0.0.0.0` and `port=int(os.environ.get('PORT', 5000))`
- Healthcheck path: `/health`

## Railway Service Settings
- **Root directory:** `/`
- **Build command:** *(leave default for Python or set explicitly)*
- **Start command (recommended):**
  - `gunicorn app:app --bind 0.0.0.0:$PORT`

## Pre-Deploy Check
- `GET /health` returns 200
- App starts without local-only assumptions
- No secrets in git history
