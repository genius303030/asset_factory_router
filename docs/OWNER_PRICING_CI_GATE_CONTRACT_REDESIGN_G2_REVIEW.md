# Owner Pricing CI Gate Contract Redesign G2 Review

This is planning/docs/test-contract only. It recovers the G2 review checklist
for the owner-pricing CI safety gate contract redesign that did not merge
through PR #31. It does not change the active safety gate, does not add parser
registration, does not add CLI flags, does not change owner-pricing runtime
behavior, does not touch live JSON or sandbox JSON, and does not add real owner,
customer, job, material, vendor, or pricing data.

## Review Boundary

G2 should review this recovery PR as documentation and test-contract recovery
only. Any parser, runtime, production import, active safety gate, workflow,
fixture, golden report, metric, or live/sandbox JSON change is out of scope and
must be moved to a separate G0-approved PR.

## Current And Future Gate Modes

- Current gate mode: `reserved-command-absent`
- Future gate mode: `approved-command-contract`

The current mode must remain active until G0 approves the future command
contract and G2 confirms the required fake evidence, golden reports, metrics,
and CI results.

## Existing Checks Must Not Disappear

Existing checks must not disappear during any future redesign. G2 should verify
the active safety script continues to protect:

- CLI help boundaries.
- Parser registration boundaries.
- Private or real owner-pricing data tracking.
- Ignored local owner-pricing paths.
- Owner-pricing safety markers.
- GitHub Actions workflow wiring.

If any future redesign replaces a check, the replacement must be stricter or
equally protective, documented, tested, and approved by G0 before merge.

## G2 Review Checklist

G2 should confirm:

1. The PR is planning/docs/test-contract only.
2. `scripts/check_owner_pricing_safety.py` is unchanged.
3. No parser registration was added.
4. No CLI flags were added.
5. No owner-pricing runtime behavior changed.
6. No production import behavior was added.
7. No live JSON or sandbox JSON changed.
8. No real owner, customer, job, material, vendor, or pricing data was added.
9. The docs describe `reserved-command-absent` and
   `approved-command-contract`.
10. Migration criteria require G0 approval, G2 review, fake fixtures, golden
    reports, metrics, and CI success.
11. No-go conditions are explicit and block unsafe redesign work.
12. README links point to both recovered documents.

## Future Implementation Review Checklist

For a later PR that actually proposes an approved command contract, G2 must
also verify:

- G0 approval artifact is present.
- Fake fixtures cover success, failure, rollback, and audit paths.
- Golden reports are deterministic.
- Checksum evidence matches committed fake artifacts.
- Metrics updates describe scope, tests, CI, safety gate, G2 status, merge
  state, workflow stage, and production behavior status.
- CI proves all existing safety checks still run.
- Any new gate checks are tested and fail closed.
- Existing checks must not disappear.

## No-Go Conditions

G2 must block the PR if it:

- Modifies the active safety gate in a planning-only PR.
- Removes or weakens an existing check.
- Adds parser registration.
- Adds CLI flags.
- Changes owner-pricing runtime behavior.
- Adds production import behavior.
- Touches live JSON or sandbox JSON.
- Adds real owner, customer, job, material, vendor, or pricing data.
- Claims `approved-command-contract` without G0 approval and complete fake
  evidence.
