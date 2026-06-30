# Fake Owner Pricing Golden Report

FAKE_ONLY

Deterministic Golden ID: `G1-037-FAKE-EVIDENCE-PACKET-V1`

## Static Review Summary

| Field | Expected value |
| --- | --- |
| Owner | `FAKE_OWNER_ALPHA` |
| Job | `FAKE_JOB_001` |
| Vendor | `FAKE_VENDOR_TEST` |
| Material A | `FAKE_MATERIAL_TEST_A` |
| Material B | `FAKE_MATERIAL_TEST_B` |
| Material C | `FAKE_MATERIAL_TEST_C` |
| Fake input rows | 3 |
| Fake output write count | 0 |
| Fake sample total | `326.90 FAKE_SAMPLE_ONLY` |
| Production behavior changed | false |
| Safety gate changed | false |
| Live JSON mutated | false |
| Sandbox JSON mutated | false |

## Expected G2 Verdict Shape

G2 can mark this fake evidence packet reviewed only when:

1. Every artifact contains `FAKE_ONLY`.
2. Every checksum in `checksums/SHA256SUMS.txt` matches the committed bytes.
3. The fake owner report, fake output JSON, fake audit JSON, fake rollback plan,
   fake metrics summary, and fake fixture registry all agree on no-write status.
4. No real owner, customer, job, material, vendor, or pricing data is present.
5. No source, parser, CLI, workflow, safety gate, live JSON, or sandbox JSON
   behavior changed.

## Stable Golden Text

This golden report is intentionally static. Do not add generated timestamps,
machine-specific paths, random IDs, or environment-dependent output.
