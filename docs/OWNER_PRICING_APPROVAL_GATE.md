# Owner Pricing Approval Gate

This workflow writes a manual owner approval record for a sandbox owner pricing
output. It is file-based, traceable, and reviewable, but it is not a final
production import.

## What This Command Does

`asset-factory owner-pricing-approve-sandbox-output` reads a sandbox pricing
output JSON from `owner-pricing-apply-sandbox-output`, validates that it is a
sandbox-only output, checks an explicit owner approval phrase, and writes an
approval record JSON to an explicit output path.

The approval record includes:

- Approval type.
- Sandbox output path.
- Sandbox output SHA-256 checksum.
- Sandbox apply plan path, when provided.
- Dry-run report path, when provided.
- Generated timestamp.
- Approval phrase used.
- Approved by field.
- Warnings.
- Checklist.
- `final_import_enabled: false`.
- `live_json_mutated: false`.
- `production_pricing_mutated: false`.

## What This Command Does Not Do

- It does not mutate live JSON.
- It does not mutate production pricing data.
- It does not add final import.
- It does not add automatic production apply.
- It does not allow approval output in `live/`, `prod/`, `production/`,
  `config/`, `data/`, or `src/` paths.
- It does not overwrite an existing approval record unless `--overwrite` is
  provided.

## Required Approval Phrase

The owner must provide the exact approval phrase:

```bash
--owner-approval "I_APPROVE_SANDBOX_PRICING_OUTPUT"
```

Any missing or different phrase fails the command. This approval phrase only
creates an approval record. It still does not allow production import.

## Command

```bash
asset-factory owner-pricing-approve-sandbox-output \
  --sandbox-output output/owner_pricing_sandbox_output.json \
  --sandbox-apply-plan output/owner_pricing_sandbox_apply_plan.md \
  --dry-run-report output/owner_pricing_dry_run_preview.md \
  --owner-approval "I_APPROVE_SANDBOX_PRICING_OUTPUT" \
  --approved-by "local owner / manual owner" \
  --approval-record output/owner_pricing_approval_record.json
```

Optional markdown summary:

```bash
asset-factory owner-pricing-approve-sandbox-output \
  --sandbox-output output/owner_pricing_sandbox_output.json \
  --owner-approval "I_APPROVE_SANDBOX_PRICING_OUTPUT" \
  --approval-record output/owner_pricing_approval_record.json \
  --markdown-summary output/owner_pricing_approval_record.md
```

## Owner Review Before Approval

- Review the dry-run report and confirm invalid rows are understood.
- Review duplicate material key warnings.
- Review the sandbox apply plan.
- Review the sandbox output JSON.
- Confirm the sandbox output checksum in the approval record.
- Confirm the approval record says final import is disabled.
- Confirm the approval record says no live JSON or production pricing was
  mutated.

## Safe Local Files

Real owner pricing files and local approval records should stay in ignored
paths, such as:

- `output/owner_pricing/`
- `outputs/owner_pricing/`
- `owner_pricing_private/`
- `input/owner_pricing/private/`

## Never Commit

- Real owner pricing CSV.
- Real owner pricing JSON.
- Customer private pricing data.
- Local approval records created from real owner data.
- Any credential, token, password, or secret.

## Fake Sample

The repository includes fake-only sample files:

- `examples/owner_pricing/fake_sandbox_pricing_output.json`
- `examples/owner_pricing/fake_sandbox_apply_plan.md`
- `examples/owner_pricing/fake_preview_report.md`
- `examples/owner_pricing/fake_owner_pricing_approval_record.json`

Regenerate the fake approval record:

```bash
asset-factory owner-pricing-approve-sandbox-output \
  --sandbox-output examples/owner_pricing/fake_sandbox_pricing_output.json \
  --sandbox-apply-plan examples/owner_pricing/fake_sandbox_apply_plan.md \
  --dry-run-report examples/owner_pricing/fake_preview_report.md \
  --owner-approval "I_APPROVE_SANDBOX_PRICING_OUTPUT" \
  --approval-record examples/owner_pricing/fake_owner_pricing_approval_record.json \
  --overwrite
```

## Why Final Import Is Still Disabled

Approval and final import are separate owner decisions. G1-024 creates a
traceable approval record only. A future G0-approved task must separately define
owner approval review, rollback expectations, production import behavior, and
post-import validation before any production pricing data can be changed.
