# Protest Safety Checker

Public-data risk signal tool for organizers, legal observers, medics, and support teams.

## Field Shield overview

Field Shield is the operational safety layer for in-field use. Current implementation combines backend and frontend pieces:

- **Backend API routes** for Field Shield sessions (`start`, `checkin`, `incident`, `alert`, `packet`)
- **Risk API privacy controls** (optional query/location redaction)
- **Status endpoint**: `GET /api/field-shield/status`
- **Frontend Field Shield mode UI** (`/field-shield`) for field workflows
- **Cache-hardening option** (`no-store` headers when enabled)

This is a practical v0.1 baseline for safer operations, not a complete security system.

## Quick start

```bash
git clone https://github.com/jacobarrio/protest-safety-checker.git
cd protest-safety-checker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Open: `http://localhost:5000`

## Setup / environment variables

### Core

- `PORT` (default: `5000`)

### Field Shield controls

- `FIELD_SHIELD_ENABLED` (`true|false`, default `false`)
- `FIELD_SHIELD_MODE` (`balanced|strict`, default `balanced`)
- `FIELD_SHIELD_REDACT_USER_INPUT` (`true|false`, default `true`)
- `FIELD_SHIELD_NO_STORE_HEADERS` (`true|false`, default `true`)

Example:

```bash
export FIELD_SHIELD_ENABLED=true
export FIELD_SHIELD_MODE=balanced
export FIELD_SHIELD_REDACT_USER_INPUT=true
export FIELD_SHIELD_NO_STORE_HEADERS=true
python3 app.py
```

## Threat model notes

Field Shield is meant to reduce common operational mistakes, especially accidental leakage.

### In-scope (v0.1)

- Reduce accidental query/location echo in API responses
- Reduce browser/proxy cache persistence when enabled
- Support structured field operations workflow through dedicated endpoints/UI

### Out-of-scope (v0.1)

- Full anonymity guarantees
- Device compromise protection
- Strong authz/RBAC model for all routes
- End-to-end encrypted multi-party coordination

Treat outputs as advisory. Always cross-check live local conditions.

## Data retention + privacy guidance

Recommended deployment posture:

- Avoid logging request bodies for `/api/check` and Field Shield write endpoints
- Keep access logs short-lived and rotated
- Do not store names, IDs, or identifying field notes unless legally necessary
- Use HTTPS in transit and encrypted storage at rest
- Publish a short public privacy notice (collection, retention, deletion windows)

Operational guidance for users:

- Do **not** paste names, IDs, plate numbers, or private plans into the app
- Use coarse locations whenever possible
- Assume compromised-device risk and plan fallback channels

## Testing

```bash
pip install -r requirements-dev.txt
pytest tests/ -q
```

## Safety and implementation docs

- `FIELD_SHIELD_SAFETY.md` — practical hardening roadmap
- `IMPLEMENTATION_CHECKLIST_FIELD_SHIELD.md` — v0.1 done vs v0.2 required

## License

Public domain.
