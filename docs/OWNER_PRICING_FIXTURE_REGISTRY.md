# Owner Pricing Fixture Registry

This registry describes the committed fake owner-pricing fixtures and the
ignored local artifacts that are safe to generate during review. It is a
documentation layer only. It does not add production import behavior, does not
change owner-pricing commands, and does not allow real owner pricing data in
Git.

## Registry Rules

- `examples/owner_pricing/` is the committed fake fixture area.
- All committed owner-pricing examples must be fake, sample, or test data.
- Real owner pricing CSV, JSON, reports, audits, approvals, and backups stay in
  ignored local paths such as `output/`, `outputs/`, or
  `owner_pricing_private/`.
- `.gitattributes` must keep `examples/owner_pricing/* text eol=lf` because
  several fixture reports store SHA-256 values over exact fixture bytes.
- A fixture that contains or is referenced by a SHA-256 value is
  checksum-sensitive. Reviewers must treat line-ending-only diffs as meaningful
  for those files.
- A golden reference is a committed fake report, output, approval, audit, or
  target that tests or reviewers can compare against expected workflow shape.

## Committed Fake Fixtures

| Path | Workflow stage | Artifact kind | Golden role | Git status | Checksum-sensitive | G2 review rule |
| --- | --- | --- | --- | --- | --- | --- |
| `examples/owner_pricing/fake_owner_pricing.csv` | Dry-run | input | source fixture | committed | no | Confirm every row is fake, includes invalid/duplicate coverage, and does not resemble real owner pricing. |
| `examples/owner_pricing/fake_current_pricing.csv` | Dry-run / preflight comparison | input; checksum-sensitive | golden-reference baseline | committed | yes | Recompute downstream checksums and compare report diffs when this baseline changes. |
| `examples/owner_pricing/fake_preview_report.md` | Dry-run | report | golden-reference report | committed | no | Verify counts, invalid-row notes, duplicate warnings, and no production-write language changed unexpectedly. |
| `examples/owner_pricing/fake_sandbox_apply_plan.md` | Sandbox apply plan | report | golden-reference plan | committed | no | Confirm the plan remains review-only and still references the fake CSV and baseline fixture. |
| `examples/owner_pricing/fake_sandbox_pricing_output.json` | Sandbox apply output | output; checksum-sensitive | golden-reference output | committed | yes | Recompute approval, preflight, and rehearsal checksum references; verify sandbox safety flags stay false/true as designed. |
| `examples/owner_pricing/fake_owner_pricing_approval_record.json` | Approval gate | output; checksum-sensitive | golden-reference approval | committed | yes | Verify the approval checksum matches sandbox output bytes and final import remains disabled. |
| `examples/owner_pricing/fake_final_import_preflight_report.md` | Final import preflight | report | golden-reference report | committed | no | Compare PASS/FAIL wording, checked paths, and no-write statements against the JSON report. |
| `examples/owner_pricing/fake_final_import_preflight_report.json` | Final import preflight | report; checksum-sensitive | golden-reference structured report | committed | yes | Verify status, checked paths, checksums, and no-write flags match the current fake fixture bytes. |
| `examples/owner_pricing/fake_final_import_design_gate.md` | Final import design gate | report | golden-reference design example | committed | no | Confirm this remains design/review evidence only and does not add implementation approval. |
| `examples/owner_pricing/fake_final_import_audit_log.md` | Final import planning | audit; report | golden-reference audit example | committed | no | Confirm audit wording remains fake/planning-only and contains no real owner data. |
| `examples/owner_pricing/fake_final_import_rehearsal_production_target.csv` | Fake final import rehearsal | input; checksum-sensitive | golden-reference fake target | committed | yes | Recompute fake rehearsal preflight and audit checksums when this target changes. |
| `examples/owner_pricing/fake_final_import_rehearsal_preflight_report.md` | Fake final import rehearsal | report | golden-reference report | committed | no | Compare with the structured rehearsal preflight JSON and verify fake target references. |
| `examples/owner_pricing/fake_final_import_rehearsal_preflight_report.json` | Fake final import rehearsal | report; checksum-sensitive | golden-reference structured report | committed | yes | Verify sandbox, approval, and fake target checksums match LF-normalized fixture bytes. |
| `examples/owner_pricing/fake_final_import_rehearsal_audit.json` | Fake final import rehearsal | audit; checksum-sensitive | golden-reference audit | committed | yes | Verify state history, rollback proof, fake-write flags, and embedded checksums stay coherent. |
| `examples/owner_pricing/fake_final_import_rehearsal_report.md` | Fake final import rehearsal | report | golden-reference report | committed | no | Confirm the narrative matches the audit JSON and says real production import remains blocked. |

## Ignored Local Artifacts

| Path or pattern | Workflow stage | Artifact kind | Git status | G2 review rule |
| --- | --- | --- | --- | --- |
| `output/owner_pricing/` | Any owner-pricing local run | input; output; report; audit | local/ignored | Do not request commit unless G0 explicitly asks and the data is proven fake. |
| `outputs/owner_pricing/` | Any owner-pricing local run | output; report; audit; backup | local/ignored | Use for generated review evidence; inspect locally but keep out of Git. |
| `owner_pricing_private/` | Owner private data | input | local/ignored | Must never be committed; if tracked, treat as a safety failure. |
| `input/owner_pricing/private/` | Owner private data | input | local/ignored | Must never be committed; if tracked, treat as a safety failure. |
| `inputs/owner_pricing/private/` | Owner private data | input | local/ignored | Must never be committed; if tracked, treat as a safety failure. |
| `data/owner_pricing/private/` | Owner private data | input | local/ignored | Must never be committed; if tracked, treat as a safety failure. |
| `*.owner-private-pricing.csv` | Owner private data | input | local/ignored | Must never be committed. |
| `*.owner-private-pricing.json` | Owner private data | input | local/ignored | Must never be committed. |
| `*.owner-pricing-sandbox-plan.md` | Sandbox apply plan | report | local/ignored | Review only as local evidence; commit only fake equivalents under `examples/owner_pricing/`. |
| `*.owner-pricing-sandbox-output.json` | Sandbox apply output | output; checksum-sensitive | local/ignored | Review checksum locally; do not commit real or owner-derived output. |
| `*.owner-pricing-approval-record.json` | Approval gate | output; checksum-sensitive | local/ignored | Review owner approval locally; do not commit real approval records. |
| `*.owner-pricing-preflight-report.md` | Final import preflight | report | local/ignored | Review locally; commit only fake regenerated golden reports. |
| `*.owner-pricing-preflight-report.json` | Final import preflight | report; checksum-sensitive | local/ignored | Review checksums locally; do not commit owner-derived preflight JSON. |
| `*.owner-pricing-fake-rehearsal-report.md` | Fake final import rehearsal | report | local/ignored | Review fake/local evidence; commit only curated golden examples. |
| `*.owner-pricing-fake-rehearsal-audit.json` | Fake final import rehearsal | audit; checksum-sensitive | local/ignored | Review fake/local audit state; commit only curated golden audit examples. |
| `*.owner-pricing-fake-rehearsal-output.csv` | Fake final import rehearsal | output; checksum-sensitive | local/ignored | Keep generated fake output local because rehearsal restores from backup. |
| `*.owner-pricing-fake-rehearsal-backup.csv` | Fake final import rehearsal | output; checksum-sensitive | local/ignored | Keep generated fake backup local; never treat it as production backup evidence. |

## Review Order

G2 should review owner-pricing fixture changes in this order:

1. Confirm no real owner pricing data, credentials, or private customer data is
   present.
2. Confirm `.gitattributes` still forces LF for `examples/owner_pricing/*`.
3. Confirm every committed fixture change is listed in this registry and in
   `examples/owner_pricing/README.md`.
4. For checksum-sensitive fixtures, recompute SHA-256 over the checked-out LF
   bytes and verify embedded checksum fields were updated intentionally.
5. Compare markdown reports with matching JSON outputs or audit logs.
6. Confirm sandbox, approval, preflight, design-gate, and fake-rehearsal safety
   boundaries were not weakened.
7. Run the owner-pricing unit tests, safety gate, Ruff, and diff whitespace
   checks before marking the PR ready.

## Safe Update Boundary

Updating this registry or fake golden files does not approve production import.
Any production import behavior, production write, real owner pricing data, or
production-enable flag remains outside this fixture-registry task.
