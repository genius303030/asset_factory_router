# Owner Pricing Production Import Implementation Plan V2

G1-033 is a planning-only implementation plan v2 for the owner-pricing final
application path. It does not implement production import, does not add CLI
flags, does not change owner-pricing runtime behavior, does not mutate live
JSON, and does not add real owner pricing data.

## Current Readiness State

The owner-pricing workflow has the following readiness layers:

| Layer | Status | Evidence |
| --- | --- | --- |
| Dry-run preview | Complete | `docs/OWNER_PRICING_DRY_RUN.md` |
| Sandbox apply plan | Complete | `docs/OWNER_PRICING_SANDBOX_APPLY_PLAN.md` |
| Sandbox output | Complete | `docs/OWNER_PRICING_SANDBOX_APPLY_OUTPUT.md` |
| Owner approval gate | Complete | `docs/OWNER_PRICING_APPROVAL_GATE.md` |
| Final import planning | Complete | `docs/OWNER_PRICING_FINAL_IMPORT_PLAN.md` |
| Read-only preflight | Complete | `docs/OWNER_PRICING_FINAL_IMPORT_PREFLIGHT.md` |
| Design gate | Complete | `docs/OWNER_PRICING_FINAL_IMPORT_DESIGN_GATE.md` |
| Fake-only rehearsal | Complete | `docs/OWNER_PRICING_FINAL_IMPORT_FAKE_REHEARSAL.md` |
| CI safety gate | Complete | `docs/OWNER_PRICING_CI_GATE.md` |
| Fixture registry and golden reports | Complete | `docs/OWNER_PRICING_FIXTURE_REGISTRY.md` |
| Metrics baseline | Complete | `docs/METRICS_BASELINE.md` |
| Production import implementation | Blocked | This document only plans the future path. |

## What Remains Blocked

Production import remains blocked until a separate G0-approved implementation
issue exists. The blocked work includes:

- Implementing the reserved production import command.
- Adding or changing command-line flags.
- Writing production pricing output.
- Writing real backup artifacts.
- Writing real audit artifacts.
- Mutating live JSON.
- Allowing real owner pricing data into Git.
- Changing the current safety gate from command-absence checks to
  command-contract checks.

G1-033 does not perform any of those actions.

## Future CLI Shape

The reserved future command label remains:

```text
asset-factory owner-pricing-final-import
```

This PR does not add that command. It also does not define or add new option
names. At design level, a future implementation must require these artifact
categories:

- Approved sandbox output.
- Matching owner approval record.
- Passing final-import preflight evidence.
- Explicit production target path.
- Explicit backup output path.
- Explicit audit log path.
- Explicit owner/G0 final approval artifact.
- Explicit final confirmation artifact.

Exact option names, parser wiring, help text, and error messages must be
specified in a future implementation issue and reviewed before code is added.

## Required Owner And G0 Approval Artifacts

Before a future implementation PR can be considered ready, G0 must approve an
artifact packet that includes:

- Owner-approved sandbox output path and checksum.
- Owner approval record path and checksum.
- Final-import preflight report path and PASS status.
- Production target path.
- Backup output path.
- Audit log destination.
- Rollback procedure version.
- Failure-mode handling plan.
- Implementation PR number.
- G2 review result.
- Final G0 approval decision.

The approval packet template is documented in
`docs/OWNER_PRICING_PRODUCTION_IMPORT_G0_APPROVAL_CHECKLIST.md`.

## Required G2 Review Checklist

G2 must review both the implementation design and the implementation PR before
G0 can approve a production import merge. The review checklist is documented in
`docs/OWNER_PRICING_PRODUCTION_IMPORT_G2_REVIEW_CHECKLIST.md`.

At minimum, G2 must verify:

- Every production write path fails closed.
- Backup creation happens before production write.
- Backup verification happens before production write.
- Audit logging records aborted, failed, passed, and rollback-needed states.
- Rollback restore and restore verification are tested with fake fixtures.
- No real owner pricing data is committed.
- Documentation matches command behavior.
- Metrics and fixture/golden-report updates are included or explicitly
  scheduled.

## Backup Expectations

A future implementation must:

- Read the production target before any write.
- Compute and record the pre-import checksum.
- Write a backup from the exact pre-import bytes.
- Verify the backup checksum against the pre-import checksum.
- Refuse to continue if backup creation or verification fails.
- Refuse silent overwrite of existing backup artifacts.
- Keep real backup artifacts in ignored local paths.

Backup must never be regenerated from memory, owner CSV, or sandbox output. It
must be copied from the exact production target being protected.

## Audit Expectations

A future implementation must write structured audit evidence for every attempt.
The audit must record:

- Attempt identifier.
- Operator or local owner label.
- Artifact paths.
- Checksums.
- Validation results.
- Backup result.
- Production write result.
- Rollback status.
- Final owner/G0 decision state.

Audit logging must start before backup creation. If audit logging is not
writable before production write, the command must abort. If audit logging fails
after production write, the workflow must enter emergency review.

## Validation Expectations

A future implementation must validate before production write:

- Sandbox output parses and is sandbox-only.
- Approval record exists and matches the sandbox output checksum.
- Preflight evidence is present and passing.
- Production target path is explicit and allowed.
- Backup path is explicit and allowed.
- Audit log path is explicit and allowed.
- Material keys are unique.
- Skipped invalid rows are not importable.
- Repository state is clean enough for the approved operation.

After production write, it must validate:

- Production target parses.
- Required material fields are present.
- Material counts match the approved sandbox output.
- No duplicate material keys exist.
- No skipped invalid rows were imported.
- Post-import checksum is recorded.
- Backup artifact still verifies.

## Rollback Expectations

Rollback must restore the exact verified backup created immediately before the
production write. A future implementation must document and test:

- Rollback trigger conditions.
- G0 rollback approval rules.
- Backup checksum verification before restore.
- Restore write behavior.
- Restore checksum verification.
- Post-restore schema and count validation.
- Rollback report contents.
- G2 rollback review evidence.

If rollback verification fails, the workflow must stop and escalate to G0.

## Failure Modes

No production write may happen when any of these conditions exist:

- Missing approval artifact.
- Stale approval artifact.
- Checksum mismatch.
- Missing or failing preflight evidence.
- Unsafe production target path.
- Unsafe backup path.
- Existing backup output without explicit future overwrite design.
- Backup cannot be created.
- Backup cannot be verified.
- Audit log cannot be written before production write.
- Duplicate material keys.
- Skipped invalid rows in importable materials.
- Unrelated dirty files that could hide production changes.
- G0 withdraws approval.
- G2 review is missing or request-changes.

After production write, failed validation must enter rollback review rather than
retrying in place.

## Required CI Gate Updates Before Implementation

The current safety gate protects the project by requiring the production import
command to remain absent. A future implementation PR must update that contract
only after G0 approves the implementation issue.

The future CI gate must check:

- The production import command exists only in the approved implementation PR.
- Required artifact categories are enforced.
- Missing approval artifacts fail closed.
- Mismatched checksums fail closed.
- Unsafe production and backup paths fail closed.
- Backup write and verification failures stop production write.
- Audit write failures stop or escalate at the correct stage.
- Rollback tests run with fake fixtures.
- Real owner pricing data remains untracked.
- Metrics validation runs.

The future CI workflow must continue to run the full unit test suite, the
owner-pricing subset, the safety gate, Ruff, and metrics validation.

## Fixture, Golden Report, And Metrics Requirements

A future implementation PR must update or add fake-only fixtures for:

- Successful import rehearsal.
- Aborted attempt before production write.
- Backup creation failure.
- Backup verification failure.
- Post-import validation failure.
- Rollback-required state.
- Rollback-passed state.
- Rollback-failed state.

Golden reports must document expected Markdown and JSON/audit outputs for fake
fixtures only. No real owner pricing data may be committed.

Metrics requirements:

- Add a metrics row for the implementation PR after the PR number is known.
- Record source, test, docs, workflow, and examples change flags.
- Record unit test counts and owner-pricing-specific counts when visible.
- Record CI status and safety gate status.
- Keep production behavior marked `no` until G0 explicitly approves a real
  production behavior change.
- Use `unknown` for any value not backed by durable evidence.

## No-Go Conditions

Do not start implementation while any no-go condition is true:

- G0 has not approved a separate implementation issue.
- G2 has not reviewed the implementation design.
- The future command contract is not documented.
- Backup and rollback behavior is not testable with fake fixtures.
- Audit evidence cannot be written before production write.
- Safety gate updates are not designed.
- Fixture and golden-report expectations are not defined.
- Metrics update expectations are not defined.
- Any real owner pricing data would need to be committed.
- The implementation would require weakening existing safety boundaries.

## Proposed Next Issue Split

1. G1-034: Production import command contract and test matrix only.
2. G1-035: CI safety gate redesign for an approved production command.
3. G1-036: Fake-fixture production import implementation rehearsal.
4. G1-037: Backup, rollback, and audit fixture expansion.
5. G2-038: Review the fake implementation evidence packet.
6. G0-039: Decide whether a real production import implementation is approved.

Each issue should remain independently reviewable and should preserve the
planning-only boundary until G0 explicitly approves implementation work.
