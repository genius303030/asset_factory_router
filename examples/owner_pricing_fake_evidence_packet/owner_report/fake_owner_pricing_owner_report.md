# Fake Owner Pricing Owner Report

FAKE_ONLY

## Boundary

This is a fake owner-facing report for review of the evidence packet shape. It
does not approve, perform, or simulate a real production write. It contains no
real owner, customer, job, material, vendor, or pricing data.

## Fake Packet Summary

| Field | Value |
| --- | --- |
| Owner | `FAKE_OWNER_ALPHA` |
| Job | `FAKE_JOB_001` |
| Vendor | `FAKE_VENDOR_TEST` |
| Materials | `FAKE_MATERIAL_TEST_A`, `FAKE_MATERIAL_TEST_B`, `FAKE_MATERIAL_TEST_C` |
| Fake rows reviewed | 3 |
| Fake rows written | 0 |
| Fake sample amount total | `326.90 FAKE_SAMPLE_ONLY` |
| G2 status | pending |
| G0 approval status | not requested |

## Owner Review Notes

- FAKE_ONLY evidence packet artifacts are present for input, output, audit,
  rollback, checksum, metrics, fixture registry, and golden report review.
- The fake output records `fake_review_only_no_write` for each row.
- The audit states that live JSON and sandbox JSON were not mutated.
- This report is deterministic and must remain aligned with the structured
  fake output and fake metrics summary.

## No-Go Conditions

Stop review if any future update adds real owner data, real customer data, real
job data, real material data, real pricing data, a production write path, parser
registration, formal CLI flags, safety-gate weakening, or live/sandbox JSON
mutation.
