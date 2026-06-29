# Owner Pricing CI Gate

G1-030 adds a read-only owner-pricing safety gate to the existing Python CI.
The gate exists to make owner-pricing boundaries machine-checked on every pull
request before G2 and G0 review.

This is CI/safety workflow only. It does not add production import, does not
write backup files, does not mutate live JSON, and does not change owner
pricing production behavior.

## CI Steps

Pull requests to `main` now run:

```bash
python -m pip install -e ".[dev]"
python -m unittest discover tests
python -m unittest discover tests -p "test_owner_pricing.py"
python scripts/check_owner_pricing_safety.py
ruff check .
```

The owner-pricing unit test step is explicit even though the full test suite
also includes it. This makes owner-pricing safety visible as a named CI gate.

## Safety Script

`scripts/check_owner_pricing_safety.py` is read-only. It checks:

- Expected dry-run, sandbox, approval, preflight, and fake-rehearsal CLI
  commands remain present.
- The bare final-import production command is absent from CLI help.
- The bare final-import production command is not registered in the parser.
- The production-enable flag named in Issue #19 does not appear outside the
  previously merged future-import planning docs.
- Real owner-pricing data is not tracked.
- Private owner-pricing paths remain ignored.
- Generated sandbox, approval, preflight, audit, report, fake output, and fake
  backup patterns remain ignored.
- Key fake/sandbox/preflight safety markers remain present in owner-pricing
  source.
- The Python CI workflow still contains the owner-pricing unit test step and
  this safety gate step.

The existing planning docs are allowlisted only for future-design references.
They are not executable production import surfaces.

## Local Validation

Run these before opening or updating an owner-pricing PR:

```bash
py -3.12 -m pip install -e ".[dev]"
py -3.12 -m unittest discover tests
py -3.12 -m unittest discover tests -p "test_owner_pricing.py"
py -3.12 scripts/check_owner_pricing_safety.py
ruff check .
git diff --check
git diff --cached --check
```

## Safety Boundary

- No production import command is added.
- No production-enable flag is added to executable code, tests, scripts, CI, or
  README.
- No live JSON mutation is performed.
- No production pricing mutation is performed.
- No real owner-pricing CSV or JSON is committed.
- Existing dry-run, sandbox, approval, preflight, design-gate, and
  fake-rehearsal boundaries remain intact.
