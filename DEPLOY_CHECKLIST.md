# Deploy Checklist (Railway)

## 0) Preflight
- [ ] Repo pushed to GitHub (`master` up to date)
- [ ] README includes setup/env vars
- [ ] `.env.example` exists (no secrets)
- [ ] App binds to `PORT`

## 1) Runtime
- [ ] Start command defined
- [ ] `GET /health` returns 200

## 2) Env
- [ ] `ENV=production`
- [ ] `SECRET_KEY`/`APP_SECRET`
- [ ] `DATABASE_URL` (if used)
- [ ] Required API keys only

## 3) Launch Gate
- [ ] `/health` works
- [ ] Core flow works
- [ ] No secrets committed
