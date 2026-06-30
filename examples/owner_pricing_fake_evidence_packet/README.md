# Owner Pricing Fake Evidence Packet

FAKE_ONLY

This directory contains a static fake-only evidence packet for future
owner-pricing final application review. It is review evidence only. It does not
execute a final application path, register a parser, add CLI flags, mutate live
JSON, mutate sandbox JSON, or contain real owner, customer, job, material, or
pricing data.

See `docs/OWNER_PRICING_FAKE_EVIDENCE_PACKET_ARTIFACTS.md` for the packet
review contract.

## Fake Artifact Inventory

| Path | Evidence kind | Review purpose |
| --- | --- | --- |
| `input/fake_owner_pricing_final_application_input.csv` | fake input | Shows the fake rows a future implementation evidence packet would identify. |
| `output/fake_owner_pricing_final_application_output.json` | fake output | Shows the expected no-write structured output shape. |
| `audit/fake_owner_pricing_audit_log.json` | fake audit | Shows the fake event trail, safety flags, and review state. |
| `owner_report/fake_owner_pricing_owner_report.md` | fake owner report | Shows the owner-facing summary G2 should compare against structured evidence. |
| `rollback/fake_owner_pricing_rollback_plan.md` | fake rollback plan | Shows rollback expectations without touching production files. |
| `checksums/SHA256SUMS.txt` | checksum evidence | Records SHA-256 values for the committed fake artifacts in this packet. |
| `metrics/fake_owner_pricing_metrics_summary.json` | fake metrics | Shows the future metrics evidence shape for this packet. |
| `fixtures/fake_fixture_registry.json` | fake fixture registry | Maps the fake artifacts and their review rules. |
| `golden/fake_owner_pricing_golden_report.md` | fake golden report | Provides a deterministic report G2 can use as the stable comparison surface. |

## Fake Identifiers

The packet uses deliberately fake identifiers:

- `FAKE_OWNER_ALPHA`
- `FAKE_JOB_001`
- `FAKE_MATERIAL_TEST_A`
- `FAKE_VENDOR_TEST`

Any future update that replaces these with real owner, customer, job, material,
vendor, or pricing data is out of scope and must stop review.

## Review Boundary

G2 should verify this directory remains static fake evidence only:

1. Confirm every artifact contains `FAKE_ONLY`.
2. Verify `checksums/SHA256SUMS.txt` against the committed bytes.
3. Compare the fake owner report with the fake output, audit, metrics, fixture
   registry, rollback plan, and golden report.
4. Confirm no source, parser, CLI, safety gate, live JSON, or sandbox JSON
   behavior changed.
5. Route any future runtime implementation request back to G0 approval before
   G1 work begins.
