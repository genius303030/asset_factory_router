# Engineering Workflow

This document defines the first automated validation layer for the repository.
G1-029 adds workflow foundation only. It does not change owner pricing behavior,
does not add production import, and does not mutate live JSON or production
pricing data.

## Pull Request CI

GitHub Actions runs on pull requests targeting `main`:

1. Check out the repository.
2. Set up Python 3.12.
3. Install the package with development checks:

   ```bash
   python -m pip install -e ".[dev]"
   ```

4. Run the unit test suite:

   ```bash
   python -m unittest discover tests
   ```

5. Run Ruff check-only lint:

   ```bash
   ruff check .
   ```

## Local Validation

Recommended local commands before opening a PR:

```bash
py -3.12 -m pip install -e ".[dev]"
py -3.12 -m unittest discover tests
ruff check .
git diff --check
```

For a plain package install without local tooling:

```bash
py -3.12 -m pip install -e .
py -3.12 -m unittest discover tests
```

## Ruff Policy

Ruff is check-only in G1-029.

- CI runs `ruff check .`.
- CI does not run `ruff --fix`.
- CI does not enforce `ruff format --check` yet.
- The initial Ruff rule set is intentionally conservative:
  `E9`, `F63`, `F7`, and `F82`.

This catches syntax-level and undefined-name problems without forcing broad
formatting or style churn in the first workflow PR.

## Optional Pre-commit

Pre-commit is optional for local developers. It is not required to commit, but
it can run the local Ruff check before changes are committed.

Install and run:

```bash
py -3.12 -m pip install -e ".[dev]"
pre-commit install
pre-commit run --all-files
```

Configured hooks:

- Ruff check-only lint.

## G0 / G1 / G2 Use

- G1 still runs local checks and reports results in the PR.
- G2 can use CI results as the first machine-enforced validation layer.
- G0 can use CI status as merge readiness evidence, while still retaining final
  merge authority.

## Safety Boundary

- Workflow foundation only.
- No production import command added.
- No owner pricing logic refactor.
- No live JSON mutation.
- No production pricing mutation.
- No real owner pricing data added.
- Existing fake, sandbox, approval, preflight, and design-gate boundaries stay
  intact.
