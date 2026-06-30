# Owner Pricing Command Contract G2 Review

This checklist defines the G2 review path for the G1-034 command contract and
for any future implementation PR that attempts to use it.

## G1-034 Review Checklist

G2 should confirm this PR:

- Adds documentation and documentation tests only.
- Does not add parser registration.
- Does not add new CLI flags to code.
- Does not change owner-pricing runtime behavior.
- Does not touch real owner data.
- Does not weaken the safety gate.
- Defines the reserved future command label at design level only.
- Defines required artifact categories.
- Defines validation categories.
- Defines fail-closed errors.
- Defines fake-fixture test matrix.
- Defines future CI gate contract changes.
- Defines docs, metrics, fixture, and golden-report update expectations.

## Future Implementation Review Checklist

For a future implementation PR, G2 must confirm:

| Area | Required Evidence |
| --- | --- |
| G0 authorization | A separate implementation issue and approval packet exist. |
| Contract match | Parser, help, docs, tests, and error messages match this contract or a G0-approved replacement. |
| Safety gate | The safety gate was redesigned in a separate reviewed task or in the approved implementation PR without weakening data protections. |
| Artifact gates | Sandbox output, approval record, preflight evidence, production target, backup output, audit log, G0 approval, and final confirmation are all required. |
| Fail-closed behavior | Every missing, stale, mismatched, unsafe, or unwritable artifact fails before production write. |
| Backup | Backup is written and verified before production write. |
| Audit | Audit state starts before backup and records abort, fail, pass, rollback-needed, rollback-passed, and rollback-failed states. |
| Validation | Pre-write and post-write validations cover schema, checksums, counts, skipped rows, and duplicate keys. |
| Rollback | Rollback uses only the verified backup and validates restored output. |
| Fixtures | Only fake fixtures and fake golden reports are committed. |
| Metrics | Metrics row is updated after PR number is known, or a committed follow-up is created. |
| Data safety | No real owner pricing data, private paths, tokens, or customer data are committed. |

## Required G2 Evidence Packet

Before G2 can mark a future implementation PASS, the PR must include:

- Command help output.
- Full unit test result.
- Owner-pricing-specific unit test result.
- Safety gate result.
- Metrics validation result.
- Ruff result.
- Diff whitespace checks.
- Fake fixture registry updates.
- Golden report updates.
- G0 approval artifact link.
- Rollback evidence.
- Audit examples.
- Confirmation that production behavior changes were explicitly G0-approved.

## Review Verdict Template

```text
Verdict: PASS / REQUEST_CHANGES
Reviewed PR:
Reviewed commit:
Command contract version:
G0 approval evidence:
CI status:
Safety gate status:
Metrics status:
Fixture/golden-report status:
Production behavior changed: no / G0-approved
Blocking issues:
Recommended next stop:
```

Use `REQUEST_CHANGES` if any required contract, test, safety, review, fixture,
metrics, rollback, audit, or approval evidence is missing.

## No-Go Review Findings

G2 must block a future implementation PR if:

- Parser registration appears without G0 approval.
- Runtime behavior changed outside the approved issue.
- Real owner data appears in Git.
- Production write can happen before backup verification.
- Production write can happen before audit state is writable.
- Production write can happen with missing or mismatched approval evidence.
- Rollback uses anything other than the verified backup.
- Safety gate or metrics validation is removed, bypassed, or weakened.
- Golden reports include private owner data.
