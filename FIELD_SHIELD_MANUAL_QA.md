# Field Shield Manual QA Checklist

## Smoke checks
- [ ] Home page (`/`) still loads and risk check works.
- [ ] Existing nav links still work (For Organizers, Methodology, Safety & Privacy).
- [ ] New Field Shield page loads at `/field-shield`.

## Field Shield workflow
- [ ] Click **Start Session** → status switches to active and timeline records a session event.
- [ ] Click **Quick check-in** → timeline records check-in.
- [ ] Submit incident form with sample data → timeline records incident event.
- [ ] Submit trusted contact alert form → timeline records alert success/failure.

## Offline queue behavior
- [ ] Open devtools, switch network to Offline.
- [ ] Run quick check-in and incident submission.
- [ ] Confirm timeline says events were queued offline.
- [ ] Return network to Online.
- [ ] Confirm timeline logs queue sync event.

## Panic-lock / decoy UX
- [ ] Click **Panic lock**, set unlock code if prompted.
- [ ] Verify neutral overlay appears and warns this is visual-only lock (not encryption/erase).
- [ ] Enter wrong code: stays locked.
- [ ] Enter correct code: unlocks back to field interface.

## Safety/legal copy
- [ ] Verify page includes consent/legal limitations language.
- [ ] Verify copy avoids false claims about encryption or legal guarantees.
