# Owner Pricing Golden Reports

This policy defines how owner-pricing golden reports and golden outputs may be
updated. Golden files are committed fake artifacts that make G1/G2 review
repeatable. They are not production data and are not approval for production
import.

## Golden File Definition

A golden owner-pricing file is a committed fake artifact under
`examples/owner_pricing/` that represents expected workflow output or review
evidence. Golden files include:

- Dry-run preview reports.
- Sandbox apply plans.
- Sandbox pricing outputs.
- Owner approval records.
- Preflight markdown and JSON reports.
- Design-gate and audit examples.
- Fake final import rehearsal reports and audit logs.
- Fake comparison or fake target CSV files used by those reports.

## Commit Policy

Allowed in Git:

- Fake CSV inputs whose values are clearly sample data.
- Fake markdown reports generated from fake inputs.
- Fake JSON outputs, approvals, preflight reports, and audit logs.
- Documentation that explains how to review and regenerate fake fixtures.
- Tests that validate fixture shape, registry coverage, or safety boundaries.

Must remain local/ignored:

- Real owner pricing CSV, JSON, spreadsheet, report, approval, audit, or backup
  files.
- Owner-derived dry-run, sandbox, approval, preflight, or rehearsal evidence.
- Generated local output under `output/`, `outputs/`, or private owner-pricing
  folders.
- Any file containing credentials, customer private data, tokens, or secrets.

## Line Endings And Checksums

`.gitattributes` must keep this rule:

```gitattributes
examples/owner_pricing/* text eol=lf
```

Checksum-sensitive fixtures must be reviewed as byte-exact files. A report that
stores SHA-256 values must be regenerated or edited only after computing the
hash over the LF-normalized file bytes that Git will commit. Do not accept a
checksum update if the only explanation is Windows line-ending conversion.

Checksum-sensitive fixture types include:

- Sandbox output JSON referenced by an approval record.
- Approval record JSON referenced by preflight and rehearsal reports.
- Fake current pricing or fake production target CSV referenced by preflight.
- Structured preflight JSON referenced by fake rehearsal audit.
- Fake rehearsal audit JSON containing sandbox, approval, preflight, backup,
  fake-write, and restore checksums.

## Safe Regeneration Flow

When updating owner-pricing golden files:

1. Start from a clean feature branch or isolated worktree.
2. Confirm the change is fake-fixture or documentation work only.
3. Regenerate fake outputs with commands documented in
   `examples/owner_pricing/README.md`.
4. Keep generated intermediate output and backup files in ignored local paths.
5. Normalize or verify LF line endings before computing checksums.
6. Recompute every downstream checksum after changing an upstream
   checksum-sensitive fixture.
7. Review JSON and markdown diffs together so report text matches structured
   fields.
8. Run the required validation commands before opening or updating the PR.

## Downstream Update Order

Use this order when a fake fixture changes:

1. `fake_owner_pricing.csv` and `fake_current_pricing.csv`
2. `fake_preview_report.md`
3. `fake_sandbox_apply_plan.md`
4. `fake_sandbox_pricing_output.json`
5. `fake_owner_pricing_approval_record.json`
6. `fake_final_import_preflight_report.md`
7. `fake_final_import_preflight_report.json`
8. `fake_final_import_rehearsal_production_target.csv`
9. `fake_final_import_rehearsal_preflight_report.md`
10. `fake_final_import_rehearsal_preflight_report.json`
11. `fake_final_import_rehearsal_audit.json`
12. `fake_final_import_rehearsal_report.md`

If a later file embeds an earlier file's checksum, update the later file in the
same PR or explain why it is intentionally unchanged.

## G2 Review Checklist

G2 should verify:

- The PR is fixture/golden-report organization or fake-fixture update only.
- No production final-import command or production-enable flag was added.
- No owner-pricing production behavior changed.
- No real owner pricing data was added.
- `.gitattributes` still forces LF for `examples/owner_pricing/*`.
- All committed fake fixtures are listed in
  `docs/OWNER_PRICING_FIXTURE_REGISTRY.md`.
- Each checksum-sensitive diff has a clear upstream reason and updated
  downstream checksum evidence.
- Markdown reports still match the corresponding JSON output or audit file.
- Local generated outputs remain ignored and unstaged.
- CI and required local checks are green.

## Required Validation

Run these before opening or updating a PR that touches owner-pricing fixtures or
golden reports:

```bash
py -3.12 -m pip install -e ".[dev]"
py -3.12 -B -m unittest discover tests
py -3.12 -B -m unittest discover tests -p "test_owner_pricing*.py"
py -3.12 -B scripts/check_owner_pricing_safety.py
ruff check .
git diff --check
git diff --cached --check
```

GitHub Actions must be green before the PR is marked ready or merged.

## Prohibited Changes

Do not use a golden-report update PR to:

- Add production final-import behavior.
- Add a production-enable flag.
- Mutate live JSON.
- Add real owner pricing data.
- Weaken sandbox, approval, preflight, design-gate, fake-rehearsal, safety-gate,
  sandbox, or approval boundaries.
- Commit local owner-derived outputs, backups, approvals, or reports.
