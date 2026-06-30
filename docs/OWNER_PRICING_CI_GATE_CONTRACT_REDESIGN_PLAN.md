# Owner Pricing CI Gate Contract Redesign Plan

G1-035 is a planning/docs/test-contract task for a future owner-pricing CI
safety gate redesign. It does not modify `scripts/check_owner_pricing_safety.py`,
does not add parser registration, does not add CLI flags to code, does not
change runtime behavior, does not touch real owner data, and does not remove
existing checks.

## Current Gate Behavior

The active safety gate is `scripts/check_owner_pricing_safety.py`. It is
read-only and currently enforces reserved-command-absent mode:

| Current Check | Purpose |
| --- | --- |
| Expected owner-pricing commands remain present | Protects dry-run, sandbox, approval, preflight, and fake-rehearsal workflows. |
| Bare production import command is absent from CLI help | Keeps production import unavailable until G0 approves implementation. |
| Bare production import command is absent from parser registration | Blocks accidental executable registration. |
| Production-enablement flag is absent from executable surfaces | Blocks accidental production activation paths. |
| Real owner-pricing data is not tracked | Keeps private owner data out of Git. |
| Private/output paths remain ignored | Keeps local owner artifacts out of commits. |
| Safety markers remain present in source | Keeps sandbox, mutation, production-write, and backup markers visible. |
| CI workflow includes owner-pricing tests and safety gate | Keeps the gate visible in pull requests. |

## Why The Current Gate Must Stay Strict

The current implementation does not have an approved production import command.
Until a separate G0-approved implementation issue exists, the safest contract is
that executable production import remains absent.

Do not change the active safety gate during G1-035. The redesign described here
is only a future plan.

## Future Gate Modes

### Mode 1: Reserved-Command-Absent

This is the current mode and remains active after G1-035.

Required behavior:

- Production import command is absent from CLI help.
- Production import command is absent from parser registration.
- Production-enablement behavior is absent from executable code, tests, CI, and
  README.
- Existing owner-pricing commands remain present.
- Real owner-pricing data remains untracked.
- Private/output paths remain ignored.
- Safety markers remain present.
- CI still runs owner-pricing tests and the safety gate.

### Mode 2: Approved-Command-Contract

This future mode is blocked until G0 approves a separate implementation issue.
It would replace "reserved command must be absent" with "approved command must
satisfy the reviewed contract."

Required behavior:

- Command registration matches the approved command contract.
- Required artifact slots are enforced.
- Missing, stale, mismatched, unsafe, or unwritable artifacts fail closed.
- No production write can happen before approval, preflight, audit, backup, and
  backup verification pass.
- Rollback tests use fake fixtures only.
- Real owner-pricing data remains untracked.
- Private/output paths remain ignored.
- Metrics validation remains part of the review path.

## Required Future Checks

Approved-command-contract mode must check:

| Area | Future Required Check |
| --- | --- |
| Authorization | G0-approved implementation issue and approval packet are documented. |
| Parser contract | Parser command and required artifact slots match the reviewed contract. |
| Help contract | Help text communicates that sandbox approval is not production approval. |
| Approval evidence | Missing, stale, or checksum-mismatched approval artifacts fail closed. |
| Preflight evidence | Missing or failing preflight evidence fails closed. |
| Production target | Missing, unsafe, or unreadable production target fails closed. |
| Backup | Backup path is explicit, safe, absent, written before production write, and checksum-verified. |
| Audit | Audit log path is explicit, safe, and writable before backup. |
| Validation | Schema, counts, checksums, duplicate keys, and skipped rows are checked before and after write. |
| Rollback | Rollback uses only the verified backup and validates restored output. |
| Fixtures | Fake fixtures cover pass, abort, fail, rollback-required, rollback-passed, and rollback-failed states. |
| Metrics | Metrics row is updated or explicitly scheduled with durable evidence. |
| Data safety | Real owner data remains untracked and private paths remain ignored. |

## Future Gate Test Requirements

A future gate implementation must include tests for:

- Current reserved-command-absent mode still passing before implementation.
- Approved-command-contract mode refusing to run without G0 approval evidence.
- Missing artifact slot failure.
- Stale approval failure.
- Checksum mismatch failure.
- Unsafe production target failure.
- Unsafe backup path failure.
- Backup write failure.
- Backup checksum mismatch.
- Audit path unwritable before backup.
- Post-write validation failure entering rollback review.
- Rollback verification failure.
- Real owner data tracked failure.
- Metrics validation missing failure.
- CI workflow missing owner-pricing test step failure.
- CI workflow missing safety gate step failure.

Tests must be fake-fixture-only and network-free.

## Migration Criteria

The gate may move from reserved-command-absent mode to approved-command-contract
mode only when all of these are true:

- G0 approves a separate implementation issue.
- G2 reviews the command contract and test matrix.
- The implementation PR includes fake fixtures and golden reports.
- The implementation PR updates docs, metrics, and review checklists.
- The safety gate redesign is reviewed as a contract change.
- The full local validation matrix passes.
- GitHub Actions passes.
- No real owner data is committed.
- G0 explicitly approves replacing the command-absence check for the approved
  implementation scope.

## No-Go Conditions

Do not change the active gate when:

- G0 approval is missing.
- G2 review is missing or request-changes.
- Parser registration appears outside the approved implementation scope.
- Runtime behavior changes outside the approved implementation scope.
- New CLI flags are added without the approved implementation contract.
- Any current check is removed without an equivalent or stricter replacement.
- Real owner data would be tracked.
- Private/output ignore behavior would be weakened.
- Metrics validation would be skipped.
- Fixture/golden-report updates are missing.

## G0 Approval Checklist

Before the future gate changes, G0 must confirm:

- Approved implementation issue.
- Approved implementation PR.
- Reviewed command contract version.
- Reviewed CI gate redesign version.
- G2 PASS review.
- Fake fixture and golden report evidence.
- Metrics update plan.
- Rollback evidence.
- Audit evidence.
- GitHub Actions green.
- Final decision to migrate the gate mode.

## Metrics And Fixture Requirements

Future CI gate redesign work must update or schedule:

- A metrics row for the gate redesign PR.
- Fixture registry entries for any new fake artifacts.
- Golden-report documentation for any new report or audit shape.
- G2 review notes explaining whether the gate remains absent-mode or migrates to
  approved-command-contract mode.

Use `unknown` for metrics values that are not backed by durable evidence.
