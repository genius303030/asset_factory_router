# Owner Pricing Production Import G2 Review Checklist

This checklist defines what G2 must review before any future owner-pricing
production import implementation can be considered merge-ready. G1-033 is
planning-only and does not add runtime behavior.

## G1-033 Review Checklist

For this planning PR, G2 should confirm:

- The PR changes documentation and documentation tests only.
- No owner-pricing runtime behavior changed.
- No production import command was added.
- No new CLI flags were added.
- No real owner pricing data was added.
- The plan documents blocked work.
- The plan documents G0 approval artifacts.
- The plan documents this G2 review path.
- The plan documents backup, audit, validation, rollback, and failure modes.
- The plan documents future CI gate, fixture, golden-report, and metrics
  requirements.

## Future Implementation Review Checklist

For a future implementation PR, G2 must verify:

| Area | Required Review |
| --- | --- |
| Scope | PR matches the G0-approved implementation issue. |
| Command contract | Parser, help text, docs, and tests match the reviewed contract. |
| Approval gate | Missing, stale, or mismatched approval artifacts fail closed. |
| Preflight gate | Missing or failing preflight evidence fails closed. |
| Production target | Unsafe or missing target paths fail closed. |
| Backup | Backup is written and verified before production write. |
| Audit | Audit evidence is written for abort, fail, pass, and rollback-needed states. |
| Validation | Pre-write and post-write validations cover schema, counts, checksums, and duplicates. |
| Rollback | Restore uses only the verified backup and validates restored output. |
| Error handling | Every failure mode stops at the safest stage. |
| Fixtures | Only fake fixtures and fake golden reports are committed. |
| Metrics | Metrics row is updated or explicitly scheduled with durable evidence. |
| Safety gate | CI gate is updated without weakening owner-pricing boundaries. |
| Data safety | No real owner pricing data, private paths, tokens, or customer data are committed. |

## Required Test Evidence

Future implementation evidence must include tests for:

- Missing sandbox output.
- Missing approval record.
- Approval checksum mismatch.
- Stale approval record.
- Missing preflight evidence.
- Failing preflight evidence.
- Unsafe production target path.
- Unsafe backup path.
- Backup output already exists.
- Backup write failure.
- Backup checksum mismatch.
- Audit write failure before production write.
- Duplicate material keys.
- Skipped invalid row import attempt.
- Post-import schema failure.
- Post-import count mismatch.
- Rollback-required state.
- Rollback-passed state.
- Rollback-failed state.

Tests must not require network access and must not use real owner pricing data.

## Required Documentation Evidence

G2 must confirm future implementation docs explain:

- Exact command contract.
- Artifact packet requirements.
- Backup behavior.
- Audit behavior.
- Validation behavior.
- Rollback behavior.
- Emergency stop behavior.
- G0 approval procedure.
- Metrics update procedure.
- Fixture and golden-report update procedure.

## Required CI Evidence

G2 must see passing evidence for:

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

GitHub Actions must also be green before G2 marks the PR PASS.

## Review Verdict Template

```text
Verdict: PASS / REQUEST_CHANGES
Reviewed PR:
Reviewed commit:
CI status:
Safety gate status:
Fixture/golden-report status:
Metrics status:
Production behavior changed: no / G0-approved
Blocking issues:
Recommended next stop:
```

G2 should use `REQUEST_CHANGES` if any required artifact, test, safety gate,
fixture, metrics, or approval evidence is missing.
