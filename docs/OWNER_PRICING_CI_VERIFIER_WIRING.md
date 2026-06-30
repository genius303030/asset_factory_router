# Owner Pricing CI Verifier Wiring

FAKE_ONLY

G1-039 wires the standalone fake evidence packet verifier into GitHub Actions.
This is workflow, documentation, metrics, and test-contract work only. It does
not change owner-pricing runtime behavior, does not register a parser, does not
add `asset-factory` CLI flags, does not modify the owner-pricing safety gate,
does not touch live JSON or sandbox JSON, and does not add real owner,
customer, job, material, vendor, or pricing data.

## CI Step

The Python validation workflow now runs:

```bash
python scripts/verify_owner_pricing_fake_evidence_packet.py
```

The step is placed near the owner-pricing safety gate and metrics validation:

1. Full unittest discovery.
2. Owner-pricing unit tests.
3. Owner-pricing safety gate.
4. PR metrics baseline validation.
5. Fake evidence packet verifier.
6. Ruff check-only lint.

## Contract

The workflow contract is:

- Keep `python -m unittest discover tests`.
- Keep owner-pricing-specific unittest coverage.
- Keep `python scripts/check_owner_pricing_safety.py`.
- Keep `python scripts/collect_pr_metrics.py --validate --summary`.
- Add and keep `python scripts/verify_owner_pricing_fake_evidence_packet.py`.
- Do not add production import commands to CI.
- Do not add parser registration to CI.
- Do not add live or sandbox JSON write commands to CI.
- Do not reduce Python version or test scope.

## Metrics Update

The metrics baseline adds a G1-039 row with:

- workflow category: `owner-pricing`
- workflow stage: `ci_verifier_wiring`
- workflow changed: yes
- tests changed: yes
- source changed: no
- production behavior changed: no

## G2 Review Focus

G2 should verify:

1. The verifier is present in `.github/workflows/python-ci.yml`.
2. Existing unittest, owner-pricing tests, safety gate, metrics validation, and
   Ruff steps remain present.
3. No source runtime files changed.
4. The safety gate logic did not change.
5. The metrics baseline validates.
6. README and verifier docs describe the CI wiring consistently.
7. No live/sandbox JSON write command or real owner-pricing data appears.
