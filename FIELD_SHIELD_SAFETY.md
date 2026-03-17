# Field Shield Safety Notes

Practical hardening path for production use.

## Encryption at rest

Minimum:
- Full-disk encryption on hosts
- Encrypted backups/snapshots
- Encrypted volumes for any persisted Field Shield artifacts

Next:
- Envelope encryption for sensitive records
- Per-environment key separation (dev/stage/prod)

## Key management

Minimum:
- No secrets in git
- Secrets stored via env manager / secret store
- Rotation policy for tokens and credentials

Next:
- KMS/HSM-backed keys
- Documented revocation + emergency rotation runbook

## Access control

Minimum:
- MFA on git + cloud accounts
- Least privilege for deploy/service accounts
- Restrict production shell/database access to maintainers

Next:
- RBAC for sensitive operational endpoints
- Signed audit trail for privileged actions

## Legal and ethical constraints

- This tool is for safety planning, not targeting or surveillance.
- Use lawful, ethically sourced data only.
- Avoid collecting personal data unless there is explicit legal basis.
- Keep user-facing disclaimers clear: risk signals are advisory, not certainty.
- Validate local legal requirements for data retention and disclosure.

If deploying to support vulnerable communities, get legal review for:
- subpoena exposure and retention minimization
- incident response obligations
- jurisdiction-specific privacy requirements

## High-impact next steps

1. Add request-body redaction middleware for sensitive endpoints
2. Add API auth + rate limiting for write routes
3. Add retention/deletion policy docs and automated cleanup
4. Add security tests for redaction + no-store behavior
5. Add deploy checklist item verifying hardened env settings
