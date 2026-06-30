# Owner Pricing CI Gate Contract Redesign G2 Review

This checklist defines how G2 should review G1-035 and any future PR that
changes `scripts/check_owner_pricing_safety.py`.

## G1-035 Review Checklist

G2 should confirm this planning PR:

- Adds docs and documentation tests only.
- Does not modify `scripts/check_owner_pricing_safety.py`.
- Does not add parser registration.
- Does not add CLI flags to code.
- Does not change owner-pricing runtime behavior.
- Does not touch real owner data.
- Does not remove existing safety checks.
- Documents current reserved-command-absent mode.
- Documents future approved-command-contract mode.
- Documents migration criteria and no-go conditions.
- Documents future tests, metrics, fixture, and golden-report requirements.

## Future Gate-Change Review Checklist

For a future PR that changes the active safety gate, G2 must verify:

| Area | Required Evidence |
| --- | --- |
| Authorization | G0-approved implementation issue and approval packet exist. |
| Scope | Gate changes match the approved implementation scope. |
| Existing checks | Each current check is retained or replaced by an equivalent or stricter check. |
| Parser contract | Production import parser behavior matches the approved command contract. |
| Artifact gates | Approval, preflight, production target, backup, audit, G0 approval, and final confirmation artifacts are enforced. |
| Fail-closed behavior | Missing, stale, mismatched, unsafe, or unwritable artifacts stop at the safest stage. |
| Data safety | Real owner data remains untracked and private/output paths remain ignored. |
| CI wiring | Full tests, owner-pricing tests, safety gate, metrics validation, and Ruff remain visible. |
| Fixtures | Fake fixtures cover success, abort, failure, rollback-needed, rollback-passed, and rollback-failed states. |
| Metrics | Metrics row is added or explicitly scheduled with durable evidence. |

## Existing Checks That Must Not Disappear

G2 must block any future gate-change PR that removes these protections without
an equivalent or stricter replacement:

- Expected owner-pricing commands remain present.
- Bare production import command is blocked until approved.
- Parser registration is blocked until approved.
- Production-enablement behavior is blocked outside approved implementation
  scope.
- Real owner-pricing data is not tracked.
- Private/output owner-pricing paths remain ignored.
- Safety markers remain present.
- CI workflow includes owner-pricing unit tests.
- CI workflow includes the safety gate.

## Required Future Evidence Packet

Future gate-change PRs must include:

- `py -3.12 -m pip install -e ".[dev]"`.
- `py -3.12 -B -m unittest discover tests`.
- `py -3.12 -B -m unittest discover tests -p "test_owner_pricing*.py"`.
- `py -3.12 -B scripts/check_owner_pricing_safety.py`.
- `py -3.12 -B scripts/collect_pr_metrics.py --validate --summary`.
- `ruff check .`.
- `git diff --check`.
- `git diff --cached --check`.
- GitHub Actions success.
- G0 approval evidence.
- G2 review verdict.
- Fixture/golden-report update evidence.
- Metrics update evidence.

## Review Verdict Template

```text
Verdict: PASS / REQUEST_CHANGES
Reviewed PR:
Reviewed commit:
Gate mode: reserved-command-absent / approved-command-contract
G0 approval evidence:
Existing checks retained:
New checks added:
CI status:
Safety gate status:
Metrics status:
Fixture/golden-report status:
Production behavior changed: no / G0-approved
Blocking issues:
Recommended next stop:
```

Use `REQUEST_CHANGES` if any existing protection is removed, weakened,
unverified, or undocumented.

## Immediate G1-035 Verdict Standard

G1-035 can only pass G2 review if the active gate remains unchanged and the PR
clearly states that gate migration is future work requiring separate G0
approval.
