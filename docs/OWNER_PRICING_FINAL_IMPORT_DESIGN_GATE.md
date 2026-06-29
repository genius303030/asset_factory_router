# Owner Pricing Final Import Design Gate

This document defines the final design gate before any future production owner
pricing import implementation. G1-027 is design and safety review only. It does
not add a final import command, does not write backups, does not mutate live
JSON, and does not mutate production pricing data.

## Gate Purpose

The design gate prevents a production import implementation from starting until
G0 and G2 can review the exact operating rules, evidence packet, rollback
requirements, and audit schema.

A future final import remains blocked until all of these are true:

- G0 approves a separate implementation task.
- G2 reviews and signs off on the implementation design.
- G1 implements the future command in a separate PR.
- The future PR includes tests for every production write and rollback guard.
- The future PR proves backup creation and restore verification in fake/local
  fixtures only before any real owner data is considered.

## What G1-027 Does Not Do

- It does not add `asset-factory owner-pricing-final-import`.
- It does not add any command that mutates production pricing.
- It does not write backup files.
- It does not mutate live JSON.
- It does not approve production import.
- It does not weaken dry-run, sandbox output, approval, or preflight checks.
- It does not commit real owner pricing CSV or real owner prices.

## Required Evidence Before Implementation

Before a future implementation PR can be opened, the following design evidence
must exist in reviewable form:

- Current dry-run report requirements are documented.
- Current sandbox apply plan requirements are documented.
- Current sandbox output requirements are documented.
- Current owner approval gate requirements are documented.
- Current final import preflight requirements are documented.
- Rollback execution requirements are documented.
- Audit log schema is documented.
- Emergency stop conditions are documented.
- G0 approval requirements are documented.
- G2 review requirements are documented.

The implementation PR must link to this design gate and explain any deviation.
Any deviation from this document must be approved by G0 before code is merged.

## Exact Prerequisites Before Production Import Can Ever Run

A future production import must refuse to run unless every prerequisite is
present and valid:

- Owner CSV was validated by the dry-run command.
- Dry-run report was generated and reviewed by owner/G0.
- Sandbox apply plan was generated and reviewed.
- Sandbox output JSON was generated.
- Sandbox output declares `sandbox_only: true`.
- Sandbox output declares `final_import_enabled: false`.
- Sandbox output declares `live_json_mutated: false`.
- Sandbox output declares `production_pricing_mutated: false`.
- Owner approval record exists.
- Owner approval record has `approval_type:
  owner_pricing_sandbox_output_approval`.
- Owner approval record references the intended sandbox output path.
- Owner approval record checksum matches the sandbox output bytes.
- Final import preflight report exists and has `PASS` status.
- Final import preflight JSON exists if the future command requires structured
  validation input.
- Production target path is explicit.
- Production target path passes unsafe path checks.
- Production target exists unless a first-time creation exception is explicitly
  approved by G0.
- Backup output path is explicit.
- Backup output path passes unsafe path checks.
- Backup output path does not already exist unless a future overwrite design is
  explicitly approved by G0 and tested.
- Repository has no unrelated dirty files.
- No real owner pricing CSV or private pricing data is Git-tracked.
- G0 provides explicit final import approval for the exact artifact set.
- G2 approves the evidence packet for implementation readiness.

## Future Command Contract

The future command name remains reserved for a separate task:

```bash
asset-factory owner-pricing-final-import
```

The command must not exist until G0 approves a production import implementation
task. When implemented in the future, it must require:

- `--sandbox-output <sandbox-output.json>`
- `--approval-record <approval-record.json>`
- `--production-target <production-pricing.json-or-csv>`
- `--backup-output <backup-pricing.json-or-csv>`
- `--preflight-report <preflight-report.md-or-json>`
- `--audit-log <audit-log.json>`
- `--final-confirmation <exact-confirmation-phrase>`
- `--enable-production-import`

The future command must fail closed. Missing flags, mismatched checksums,
unsafe paths, stale approval, failed backup verification, dirty repo state, or
failed post-import validation must stop execution.

## G0 Owner Approval Requirements

G0 approval for final import is separate from sandbox output approval. The owner
must approve the exact final import packet:

- Sandbox output path and SHA-256.
- Approval record path and SHA-256.
- Preflight report path and status.
- Production target path.
- Backup output path.
- Rollback procedure version.
- Audit log destination.
- Final confirmation phrase.
- Implementation PR number.

The approval must be written down in an audit-friendly record before future
production import runs. Verbal approval alone is not enough.

## G2 Review Requirements

G2 must review the future implementation PR before G0 merge approval. G2 review
must verify:

- No production write can happen without all required flags.
- Backup is written and verified before production write.
- Production target is validated before and after write.
- Rollback restore path is tested with fake fixtures.
- Audit log is written for pass, fail, rollback-needed, and aborted attempts.
- Error handling fails closed.
- Tests cover checksum mismatch, stale approval, unsafe paths, dirty repo,
  backup write failure, backup checksum mismatch, post-import validation
  failure, and rollback verification failure.
- Documentation matches actual command behavior.

## Rollback Execution Gate

Rollback readiness is a merge blocker for any future final import
implementation. The future command must prove:

- Backup source is the exact production target before import.
- Backup destination is explicit and outside unsafe paths.
- Backup checksum equals pre-import production checksum.
- Restore procedure is documented and tested with fake fixtures.
- Restore verification checks checksum, schema, counts, and duplicate keys.
- Rollback report includes G0 approval reference and validation results.

Detailed requirements live in
`docs/OWNER_PRICING_FINAL_IMPORT_EXECUTION_REQUIREMENTS.md`.

## Audit Log Gate

Every future final import attempt must create or update a structured audit log.
The audit schema lives in
`docs/OWNER_PRICING_FINAL_IMPORT_AUDIT_SCHEMA.md`.

The implementation must log successful, failed, aborted, and rollback-needed
attempts. If audit logging cannot be completed, the future command must fail
before production write. If audit logging fails after production write, the
workflow must enter emergency review and rollback readiness.

## Emergency Stop Conditions

Emergency stop is required when any of these occur:

- G0 withdraws approval.
- Approval record is missing, stale, or checksum mismatched.
- Sandbox output is missing, invalid, or not sandbox-only.
- Preflight report is missing or not PASS.
- Production target path is missing or unsafe.
- Backup output path is missing, unsafe, or already exists.
- Backup cannot be created or verified.
- Repository has unrelated dirty files.
- Duplicate material keys are present in sandbox materials.
- Skipped invalid rows appear in sandbox materials.
- Post-import schema, checksum, or count validation fails.
- Audit log cannot be written at a required stage.

Emergency stop means no retry in place. G0 decides whether to rollback, preserve
evidence, regenerate artifacts, or open a new implementation task.

## Design Gate Decision

For G1-027, the decision is:

- Final import implementation: `not approved in this PR`.
- Production import command: `not added`.
- Production write: `not performed`.
- Backup write: `not performed`.
- Live JSON mutation: `not performed`.
- Next allowed work: G2 review of this design gate.
