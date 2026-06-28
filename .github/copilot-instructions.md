# Copilot Instructions

This repository is part of the Paul Command Center AI engineering workflow.

## Project Context

This is the AI Asset Factory + Model Router repository. It is a Python package with a CLI named `asset-factory`.

The project should be treated as a durable engineering asset, not a temporary experiment. Prefer maintainable structure, small changes, clear tests, and reproducible outputs.

## Development Rules

- Read `AGENTS.md`, `README.md`, and `STATUS.md` before making changes.
- Preserve existing CLI commands unless the task explicitly requires a breaking change.
- Prefer additive improvements over broad rewrites.
- Keep implementation and tests synchronized.
- Do not introduce production dependencies without explaining why.
- Do not commit generated outputs, credentials, caches, or local environment files.

## Required Checks

When relevant, run:

```bash
pip install -e .
python -m unittest discover tests
asset-factory list-providers
```

If a command cannot be run, report the reason and the missing dependency.

## Preferred PR Summary

Use this format:

```md
## Summary
- 

## Tests
- 

## Risks
- 

## Next step
- 
```

## G0 / G1 / G2 Workflow

- G0 defines strategy, scope, and final merge decisions.
- G1 implements small tasks and opens PRs.
- G2 reviews, tests, documents, and reports risks.

Do not merge directly into `main` without explicit G0 approval.
