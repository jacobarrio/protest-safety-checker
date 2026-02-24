# Feature Ticket 001 — Post-Deploy Reliability Pass

## Goal
Harden the app for first public users after Railway deploy.

## Scope (v0.1.1)
1. Add friendly no-result UX in API + UI when typo has no close match.
2. Add basic request logging (timestamp, endpoint, status) without storing sensitive user content.
3. Add a single smoke-test script for:
   - `/health`
   - `/api/cities?q=phoeni`
   - `/api/check` with a valid city

## Acceptance Criteria
- Smoke script exits `0` on success.
- App handles unknown cities without 500s.
- Logs do not include secrets or full request payloads.

## Out of Scope
- Auth system
- Database migration
- Full analytics pipeline

## Timebox
- 60–90 minutes
