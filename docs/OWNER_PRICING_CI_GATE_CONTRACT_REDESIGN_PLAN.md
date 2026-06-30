# Owner Pricing CI Gate Contract Redesign Plan

This is planning/docs/test-contract only. It recovers the G1-035 owner-pricing
CI safety gate contract redesign documentation that did not merge through PR
#31. It does not change owner-pricing runtime behavior, does not change the
active safety gate, does not add parser registration, does not add CLI flags,
does not touch live JSON or sandbox JSON, and does not add real owner,
customer, job, material, vendor, or pricing data.

## Recovery Scope

This recovery PR may add only:

- Planning documentation for the future CI gate contract redesign.
- G2 review documentation for that future redesign.
- Test-contract coverage that checks the planning documents and the existing
  safety script markers.
- README links to the recovered planning documents.

Any parser, runtime, production import, safety gate, workflow, fixture, golden
report, metric, or live/sandbox JSON change must be a separate PR with explicit
G0 approval.

## Current Gate Mode: reserved-command-absent

The current active mode is `reserved-command-absent`.

In this mode, the CI safety gate confirms that the final application path
remains blocked unless already-approved narrow preflight or fake-rehearsal
commands are present. The active safety script must continue to check:

- CLI help boundaries.
- Parser registration boundaries.
- Private or real owner-pricing data tracking.
- Ignored local owner-pricing paths.
- Owner-pricing safety markers.
- GitHub Actions workflow wiring.

This PR does not alter `scripts/check_owner_pricing_safety.py`.

## Future Gate Mode: approved-command-contract

The future target mode is `approved-command-contract`.

That mode may exist only after G0 approves a specific final application command
contract and G2 confirms the design, fixtures, golden reports, metrics, and CI
coverage. The future gate would verify an approved command contract instead of
only verifying that the reserved command remains absent.

This document does not approve that transition.

## Migration Criteria

A future PR may propose moving from `reserved-command-absent` to
`approved-command-contract` only when all criteria below are met:

1. G0 approval explicitly authorizes a scoped final application command
   contract.
2. G2 review confirms the command contract, failure modes, rollback plan, audit
   expectations, and no-go conditions.
3. Fake fixtures cover success and failure paths without real owner data.
4. Golden reports are deterministic and checksum-sensitive artifacts are
   updated intentionally.
5. Metrics updates describe PR scope, CI status, safety gate status, G2 review
   status, merge status, workflow stage, and production behavior change status.
6. CI validates unit tests, owner-pricing-specific tests, safety-gate behavior,
   fixture/golden report checks, and metrics validation.
7. Existing safety checks do not disappear; any replacement must be stricter or
   equally protective and independently reviewed.

## Required Future Artifacts

A future implementation PR must include separate evidence for:

- G0 approval.
- G2 command-contract review.
- Fake input and output fixtures.
- Fake audit and rollback artifacts.
- Golden reports.
- Checksum evidence.
- Metrics updates.
- CI gate updates.
- Failure-mode and no-go-condition coverage.

## No-Go Conditions

Stop the redesign and return to G0 if any future PR:

- Changes the active safety gate without explicit G0 approval.
- Removes existing safety checks without a stricter reviewed replacement.
- Adds parser registration before the command contract is approved.
- Adds new CLI flags before the command contract is approved.
- Changes owner-pricing runtime behavior as part of planning work.
- Adds production import behavior as part of planning work.
- Touches live JSON or sandbox JSON.
- Adds real owner, customer, job, material, vendor, or pricing data.
- Claims `approved-command-contract` mode without fake fixtures, golden
  reports, metrics, CI success, and G2 review.

## Required Validation

Before opening or updating the recovery PR, run:

```bash
py -3.12 -m pip install -e ".[dev]"
py -3.12 -B -m unittest discover tests
py -3.12 -B -m unittest discover tests -p "test_owner_pricing*.py"
py -3.12 -B scripts/check_owner_pricing_safety.py
py -3.12 -B scripts/collect_pr_metrics.py --validate --summary
ruff check .
git diff --check
git diff --cached --check
```
