# Field Shield Implementation Checklist

## v0.1 complete

- [x] Backend Field Shield API routes integrated in Flask app
- [x] Frontend Field Shield page integrated (`/field-shield`)
- [x] Added Field Shield status endpoint (`/api/field-shield/status`)
- [x] Added optional redaction of user query/location echoes in risk API responses
- [x] Added optional no-store cache headers when Field Shield is enabled
- [x] Updated README with feature setup, threat model notes, and privacy guidance
- [x] Added dedicated safety hardening notes (`FIELD_SHIELD_SAFETY.md`)
- [x] Ran test suite and fixed straightforward failing assertion

## v0.2 required before broader rollout

- [ ] Add auth + rate limiting for Field Shield write endpoints
- [ ] Add structured retention/deletion controls and auto-purge jobs
- [ ] Add encrypted persistence plan for sensitive artifacts
- [ ] Add KMS-backed key management + rotation runbook
- [ ] Add RBAC for operator/admin actions
- [ ] Add formal legal/ethical review checklist for deployments
- [ ] Add targeted security tests (redaction, headers, authz failures)
- [ ] Add incident response playbook (compromise, legal request, key leak)

## Remaining risks after v0.1

- No complete anonymity or metadata protection
- No robust auth boundary for all Field Shield API workflows
- Upstream infrastructure logs may still leak sensitive request data
- Key lifecycle and retention enforcement are not yet mature
