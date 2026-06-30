# Owner Pricing Production Import G0 Approval Checklist

This checklist defines the owner/G0 approval packet for a future owner-pricing
production import implementation. G1-033 does not approve implementation and
does not add production import behavior.

## Approval Boundary

G0 approval for production import is separate from:

- Dry-run review.
- Sandbox apply plan review.
- Sandbox output approval.
- Final-import preflight review.
- Design-gate review.
- Fake-only rehearsal review.
- Metrics baseline review.

No single earlier approval authorizes production import.

## Required Approval Packet

G0 must record every item before a future implementation can be considered:

| Item | Required Evidence | Status |
| --- | --- | --- |
| Implementation issue | Issue number and title | pending |
| Implementation PR | PR number and branch | pending |
| Sandbox output | Path and checksum | pending |
| Approval record | Path and checksum | pending |
| Preflight evidence | Report path and PASS status | pending |
| Production target | Explicit local path | pending |
| Backup output | Explicit local path | pending |
| Audit destination | Explicit local path | pending |
| Rollback procedure | Document version or commit | pending |
| G2 review | PASS review evidence | pending |
| CI status | GitHub Actions passing | pending |
| Metrics update | Metrics row or follow-up issue | pending |
| Fixture update | Fake fixture and golden report evidence | pending |
| Final decision | approve / reject / defer | pending |

Use `pending`, `approved`, `rejected`, or `not_applicable`. Do not write real
owner pricing values into this checklist.

## Owner Confirmation Requirements

The owner must confirm:

- The sandbox output is the exact reviewed artifact.
- The approval record checksum matches the sandbox output.
- The preflight report is passing.
- The production target is the intended target.
- The backup output path is acceptable.
- The rollback procedure is understood.
- The audit destination is acceptable.
- The implementation PR remains planning-compliant until G0 approves runtime
  behavior.

## G0 Approval Decision Template

```text
Decision:
Implementation issue:
Implementation PR:
Approved artifact packet:
G2 review evidence:
CI evidence:
Rollback procedure:
Metrics evidence:
Fixture/golden-report evidence:
Final decision:
Decision date:
G0 owner:
```

This template is intentionally metadata-only. It must not contain private owner
pricing values or customer data.

## Approval Stop Conditions

G0 must reject or defer approval when:

- Any required artifact is missing.
- Any checksum is missing, stale, or mismatched.
- G2 review is missing or request-changes.
- GitHub Actions is failing.
- Backup behavior is untested.
- Rollback behavior is untested.
- Audit behavior is missing.
- Real owner pricing data would be committed.
- The implementation weakens existing safety boundaries.
- The future command contract differs from reviewed documentation.

## Post-Decision Requirement

If G0 approves a future implementation, the approval record must be linked from
the implementation PR before merge. If G0 rejects or defers, the PR must remain
draft or be closed without production behavior being merged.
