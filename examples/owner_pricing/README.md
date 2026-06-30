# Owner Pricing Fake Fixtures

This directory contains fake-only owner-pricing fixtures and golden references
for review. The files are committed so G1/G2 can compare dry-run, sandbox,
approval, preflight, design-gate, and fake-rehearsal behavior without using real
owner pricing data.

## Fixture Map

| File | Stage | Purpose |
| --- | --- | --- |
| `fake_owner_pricing.csv` | Dry-run | Fake owner input with valid rows, invalid rows, and duplicate-key coverage. |
| `fake_current_pricing.csv` | Dry-run / preflight | Fake baseline pricing for comparison and read-only checksum checks. |
| `fake_preview_report.md` | Dry-run | Golden preview report generated from fake input and fake baseline. |
| `fake_sandbox_apply_plan.md` | Sandbox apply plan | Golden review plan for fake rows before sandbox output is written. |
| `fake_sandbox_pricing_output.json` | Sandbox apply output | Golden sandbox-only JSON output; downstream approval and preflight checksums depend on it. |
| `fake_owner_pricing_approval_record.json` | Approval gate | Golden manual owner approval record for the fake sandbox output. |
| `fake_final_import_preflight_report.md` | Final import preflight | Golden markdown preflight report for fake files. |
| `fake_final_import_preflight_report.json` | Final import preflight | Golden structured preflight report for fake files. |
| `fake_final_import_design_gate.md` | Design gate | Golden design-gate evidence example; not implementation approval. |
| `fake_final_import_audit_log.md` | Planning audit | Golden audit-log example for final-import planning review. |
| `fake_final_import_rehearsal_production_target.csv` | Fake rehearsal | Fake target read by the fake-rehearsal command. |
| `fake_final_import_rehearsal_preflight_report.md` | Fake rehearsal | Golden markdown preflight report for the fake rehearsal packet. |
| `fake_final_import_rehearsal_preflight_report.json` | Fake rehearsal | Golden structured preflight report for the fake rehearsal packet. |
| `fake_final_import_rehearsal_audit.json` | Fake rehearsal | Golden fake-rehearsal audit with fake backup, write, and rollback evidence. |
| `fake_final_import_rehearsal_report.md` | Fake rehearsal | Golden fake-rehearsal markdown report matching the audit JSON. |

## Regeneration Notes

Use these commands only for fake fixture maintenance. Keep real owner pricing
inputs and owner-derived outputs in ignored local paths.

Dry-run preview:

```bash
asset-factory owner-pricing-dry-run \
  --csv examples/owner_pricing/fake_owner_pricing.csv \
  --current-pricing examples/owner_pricing/fake_current_pricing.csv \
  --report examples/owner_pricing/fake_preview_report.md
```

Sandbox apply plan:

```bash
asset-factory owner-pricing-plan-sandbox-apply \
  --csv examples/owner_pricing/fake_owner_pricing.csv \
  --current-pricing examples/owner_pricing/fake_current_pricing.csv \
  --dry-run-report examples/owner_pricing/fake_preview_report.md \
  --plan examples/owner_pricing/fake_sandbox_apply_plan.md \
  --overwrite
```

Sandbox output:

```bash
asset-factory owner-pricing-apply-sandbox-output \
  --csv examples/owner_pricing/fake_owner_pricing.csv \
  --current-pricing examples/owner_pricing/fake_current_pricing.csv \
  --sandbox-apply-plan examples/owner_pricing/fake_sandbox_apply_plan.md \
  --output examples/owner_pricing/fake_sandbox_pricing_output.json \
  --overwrite
```

Approval record:

```bash
asset-factory owner-pricing-approve-sandbox-output \
  --sandbox-output examples/owner_pricing/fake_sandbox_pricing_output.json \
  --sandbox-apply-plan examples/owner_pricing/fake_sandbox_apply_plan.md \
  --dry-run-report examples/owner_pricing/fake_preview_report.md \
  --owner-approval "I_APPROVE_SANDBOX_PRICING_OUTPUT" \
  --approval-record examples/owner_pricing/fake_owner_pricing_approval_record.json \
  --overwrite
```

Preflight report:

```bash
asset-factory owner-pricing-final-import-preflight \
  --sandbox-output examples/owner_pricing/fake_sandbox_pricing_output.json \
  --approval-record examples/owner_pricing/fake_owner_pricing_approval_record.json \
  --production-target examples/owner_pricing/fake_current_pricing.csv \
  --backup-output outputs/owner_pricing/fake_future_backup.json \
  --report examples/owner_pricing/fake_final_import_preflight_report.md \
  --report-json examples/owner_pricing/fake_final_import_preflight_report.json \
  --overwrite
```

Fake rehearsal preflight:

```bash
asset-factory owner-pricing-final-import-preflight \
  --sandbox-output examples/owner_pricing/fake_sandbox_pricing_output.json \
  --approval-record examples/owner_pricing/fake_owner_pricing_approval_record.json \
  --production-target examples/owner_pricing/fake_final_import_rehearsal_production_target.csv \
  --backup-output outputs/owner_pricing/fake_final_import_rehearsal_backup.csv \
  --report examples/owner_pricing/fake_final_import_rehearsal_preflight_report.md \
  --report-json examples/owner_pricing/fake_final_import_rehearsal_preflight_report.json \
  --overwrite
```

Fake rehearsal audit and report:

```bash
asset-factory owner-pricing-final-import-fake-rehearsal \
  --sandbox-output examples/owner_pricing/fake_sandbox_pricing_output.json \
  --approval-record examples/owner_pricing/fake_owner_pricing_approval_record.json \
  --preflight-report examples/owner_pricing/fake_final_import_rehearsal_preflight_report.json \
  --fake-production-target examples/owner_pricing/fake_final_import_rehearsal_production_target.csv \
  --fake-production-output outputs/owner_pricing/fake_final_import_rehearsal_output.csv \
  --backup-output outputs/owner_pricing/fake_final_import_rehearsal_backup.csv \
  --audit-log examples/owner_pricing/fake_final_import_rehearsal_audit.json \
  --report examples/owner_pricing/fake_final_import_rehearsal_report.md \
  --overwrite
```

The fake rehearsal backup path is intentionally local/ignored and refuses
overwrite. Remove stale ignored fake backup output only after G0 approves a
fixture-maintenance cleanup or use a fresh ignored output name.

## Review Requirements

- Keep `.gitattributes` LF behavior for this directory.
- Recompute downstream checksums after changing checksum-sensitive fixtures.
- Keep generated fake outputs and fake backups under ignored local paths.
- Do not commit real owner pricing data or owner-derived reports.
- See `docs/OWNER_PRICING_FIXTURE_REGISTRY.md` and
  `docs/OWNER_PRICING_GOLDEN_REPORTS.md` before reviewing fixture changes.
