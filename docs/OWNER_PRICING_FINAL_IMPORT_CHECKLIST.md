# Owner Pricing Final Import Checklist

This checklist is for a possible future final import. G1-025 only provides
planning documentation. It does not add a final import command and does not
write production pricing data.

## Before Import

- [ ] G0 approved a future final import implementation task.
- [ ] Owner CSV validated by dry-run.
- [ ] Dry-run report generated.
- [ ] Dry-run report reviewed by owner and G2.
- [ ] Sandbox apply plan generated.
- [ ] Sandbox apply plan reviewed.
- [ ] Sandbox output generated.
- [ ] Sandbox output JSON reviewed.
- [ ] Approval record generated.
- [ ] Approval record includes `approval_type: owner_pricing_sandbox_output_approval`.
- [ ] Approval record checksum matches sandbox output bytes.
- [ ] Sandbox output declares `sandbox_only: true`.
- [ ] Sandbox output declares `final_import_enabled: false`.
- [ ] Sandbox output declares `live_json_mutated: false`.
- [ ] Sandbox output declares `production_pricing_mutated: false`.
- [ ] Backup output path identified.
- [ ] Backup created before import.
- [ ] Backup checksum matches pre-import production checksum.
- [ ] Production target identified.
- [ ] Production target path is explicit.
- [ ] Production target path is allowed by safety rules.
- [ ] No unrelated dirty files in the repository.
- [ ] No real owner CSV committed.
- [ ] No duplicate material keys in sandbox output materials.
- [ ] No invalid rows appear in sandbox output materials.
- [ ] Owner explicitly approves final import after reviewing backup and rollback
      plan.
- [ ] G2 has reviewed planning, backup, validation, and rollback evidence.

## Import Execution Gate

Future command design requires:

- [ ] `--sandbox-output` provided.
- [ ] `--approval-record` provided.
- [ ] `--production-target` provided.
- [ ] `--backup-output` provided.
- [ ] `--final-confirmation` provided.
- [ ] `--enable-production-import` provided.
- [ ] Import aborts if backup cannot be created.
- [ ] Import aborts if approval checksum mismatch occurs.
- [ ] Import aborts if production target path is unsafe.
- [ ] Import aborts if repository has unrelated dirty files.

## After Import

- [ ] Output file exists.
- [ ] Production pricing schema valid.
- [ ] Production target checksum recorded.
- [ ] Material count checked.
- [ ] Added count checked against sandbox output.
- [ ] Updated count checked against sandbox output.
- [ ] Unchanged count checked against sandbox output.
- [ ] Retained baseline count checked against sandbox output.
- [ ] No duplicate material keys.
- [ ] No invalid rows imported.
- [ ] Rollback backup retained.
- [ ] Backup checksum still matches backup metadata.
- [ ] Audit log written.
- [ ] Owner receives final report.
- [ ] Owner confirms final report or requests rollback review.

## Emergency Stop Checklist

- [ ] Stop if approval record is missing.
- [ ] Stop if sandbox output checksum does not match approval record.
- [ ] Stop if backup cannot be created.
- [ ] Stop if backup checksum cannot be verified.
- [ ] Stop if production target path is missing or unsafe.
- [ ] Stop if skipped invalid rows appear in materials.
- [ ] Stop if duplicate material keys appear.
- [ ] Stop if owner or G0 withdraws approval.

## Rollback Readiness

- [ ] Backup path known.
- [ ] Backup checksum known.
- [ ] Restore procedure reviewed.
- [ ] G0 rollback approval path known.
- [ ] G2 rollback review path known.
- [ ] Rollback report template prepared.
