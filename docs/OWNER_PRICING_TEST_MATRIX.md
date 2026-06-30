# Owner Pricing Production Import Test Matrix

G1-034 defines the test matrix for a future owner-pricing production import
implementation. These tests are design requirements only. This PR does not add
runtime tests for a command that does not exist.

## Test Matrix Rules

- Tests must use fake fixtures only.
- Tests must not require network access.
- Tests must not use real owner pricing data.
- Tests must not mutate live JSON.
- Tests must prove fail-closed behavior before any production write.
- Tests must prove rollback review behavior after any simulated production
  write failure.
- Tests must preserve current safety, review, fixture, golden-report, and
  metrics gates.

## Required Unit Test Matrix

| ID | Scenario | Expected Result | Production Write |
| --- | --- | --- | --- |
| OP-FI-001 | Missing sandbox output | Clear missing sandbox output error. | no |
| OP-FI-002 | Sandbox output parse failure | Clear parse failure and next safe step. | no |
| OP-FI-003 | Sandbox output is not sandbox-only | Abort before backup. | no |
| OP-FI-004 | Missing approval record | Clear missing approval record error. | no |
| OP-FI-005 | Approval record parse failure | Clear parse failure and next safe step. | no |
| OP-FI-006 | Approval type mismatch | Abort before backup. | no |
| OP-FI-007 | Approval checksum mismatch | Abort before backup. | no |
| OP-FI-008 | Approval references different sandbox output | Abort before backup. | no |
| OP-FI-009 | Missing preflight evidence | Abort before backup. | no |
| OP-FI-010 | Preflight evidence failing | Abort before backup. | no |
| OP-FI-011 | Missing G0 approval artifact | Abort before backup. | no |
| OP-FI-012 | G0 approval artifact references different PR or attempt | Abort before backup. | no |
| OP-FI-013 | G2 review missing | Abort before backup. | no |
| OP-FI-014 | G2 review request-changes | Abort before backup. | no |
| OP-FI-015 | Unsafe production target path | Abort before backup. | no |
| OP-FI-016 | Missing production target | Abort unless G0 approved first-time creation design. | no |
| OP-FI-017 | Production target parse failure before write | Abort before backup. | no |
| OP-FI-018 | Unsafe backup output path | Abort before backup. | no |
| OP-FI-019 | Backup output already exists | Abort unless future overwrite design is approved. | no |
| OP-FI-020 | Audit path unsafe | Abort before backup. | no |
| OP-FI-021 | Audit path unwritable before backup | Abort before backup. | no |
| OP-FI-022 | Backup write failure | Abort before production write. | no |
| OP-FI-023 | Backup checksum mismatch | Abort before production write. | no |
| OP-FI-024 | Production target changes between read and backup verification | Abort before production write. | no |
| OP-FI-025 | Duplicate material keys in importable output | Abort before production write. | no |
| OP-FI-026 | Skipped invalid row appears in importable output | Abort before production write. | no |
| OP-FI-027 | Unrelated dirty repository state | Abort before production write. | no |
| OP-FI-028 | Owner/G0 approval withdrawn | Abort before production write. | no |
| OP-FI-029 | Happy path with fake fixtures | Backup, write, validate, audit, and report succeed. | fake only |
| OP-FI-030 | Post-import schema failure | Enter rollback review. | fake only |
| OP-FI-031 | Post-import count mismatch | Enter rollback review. | fake only |
| OP-FI-032 | Post-import duplicate material key | Enter rollback review. | fake only |
| OP-FI-033 | Owner report write failure after production write | Enter rollback review. | fake only |
| OP-FI-034 | Audit write failure after production write | Enter emergency review. | fake only |
| OP-FI-035 | Rollback backup missing | Mark rollback failed and escalate to G0. | fake only |
| OP-FI-036 | Rollback backup checksum mismatch | Mark rollback failed and escalate to G0. | fake only |
| OP-FI-037 | Rollback restore succeeds | Mark rollback passed with checksum evidence. | fake only |
| OP-FI-038 | Rollback restore schema failure | Mark rollback failed and escalate to G0. | fake only |
| OP-FI-039 | Metrics row missing for implementation PR | Review gate blocks ready state. | no |
| OP-FI-040 | Real owner pricing data appears tracked | Safety gate fails. | no |

## Required CLI Help Tests

After a future implementation is approved, tests must prove:

- The production import command appears only after the approved implementation
  task.
- Required artifact slots appear in help text.
- Reserved fake-only rehearsal and preflight commands still work.
- Help text does not imply that sandbox approval equals production approval.
- Missing required slots fail with clear parser errors.

Until that future task, tests must continue proving the production import
command is absent from parser registration and CLI help.

## Required Integration-Style Fake Tests

Future integration-style tests must use fake local paths for:

- Approved sandbox output.
- Approval record.
- Preflight report.
- Production target.
- Backup output.
- Audit log.
- Owner report.
- Rollback report.

Each test must clean up only files it created and must never touch private owner
pricing paths.

## Required Golden Reports

Future golden reports must include fake-only examples for:

- Successful production import rehearsal.
- Aborted attempt before backup.
- Aborted attempt after backup but before production write.
- Rollback-required attempt.
- Rollback-passed attempt.
- Rollback-failed attempt.

Markdown and JSON/audit golden reports must agree on attempt ID, artifact paths,
checksums, counts, validation status, rollback status, and next safe step.

## Required CI Evidence

Future implementation PRs must show:

```text
py -3.12 -m pip install -e ".[dev]"
py -3.12 -B -m unittest discover tests
py -3.12 -B -m unittest discover tests -p "test_owner_pricing*.py"
py -3.12 -B scripts/check_owner_pricing_safety.py
py -3.12 -B scripts/collect_pr_metrics.py --validate --summary
ruff check .
git diff --check
git diff --cached --check
```

GitHub Actions must be green before Ready/Merge.
