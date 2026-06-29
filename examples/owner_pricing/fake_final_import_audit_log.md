# Fake Owner Pricing Final Import Audit Log

Fake sample only. This file is not evidence of a production import and does not
contain real owner pricing data.

## Import Status

- Status: `planning_sample_only`
- Final import executed: `false`
- Production pricing mutated: `false`
- Live JSON mutated: `false`
- Rollback executed: `false`

## References

- Dry-run report: `examples/owner_pricing/fake_preview_report.md`
- Sandbox apply plan: `examples/owner_pricing/fake_sandbox_apply_plan.md`
- Sandbox output: `examples/owner_pricing/fake_sandbox_pricing_output.json`
- Approval record: `examples/owner_pricing/fake_owner_pricing_approval_record.json`
- Production target: `not used in fake sample`
- Backup output: `not used in fake sample`

## Checksums

- Sandbox output SHA-256:
  `797a1164dcb965ac190bf5300f8ad3531b2f744874f8e4f8d1b8975743da07ce`
- Approval record sandbox output SHA-256:
  `797a1164dcb965ac190bf5300f8ad3531b2f744874f8e4f8d1b8975743da07ce`
- Pre-import production checksum: `not generated`
- Backup checksum: `not generated`
- Post-import production checksum: `not generated`

## Fake Summary Counts

| Metric | Count |
| --- | ---: |
| Total rows read | 7 |
| Valid rows applied | 3 |
| Invalid rows skipped | 4 |
| Duplicate keys | 1 |
| Added materials | 1 |
| Updated materials | 1 |
| Unchanged materials | 1 |
| Retained baseline materials | 1 |
| Sandbox materials written | 4 |

## Planned Future Validation

- [ ] Approval checksum matches sandbox output.
- [ ] Backup created before production write.
- [ ] Backup checksum verified before production write.
- [ ] Production target schema validated after write.
- [ ] Material count checked after write.
- [ ] Duplicate material keys checked after write.
- [ ] Rollback backup retained.
- [ ] Owner receives final report.

## Safety Notes

- This fake audit log is committed only as a planning template.
- Real audit logs must stay under ignored local paths such as
  `output/owner_pricing/`, `outputs/owner_pricing/`, or
  `owner_pricing_private/`.
- G1-025 does not add or run final import.
