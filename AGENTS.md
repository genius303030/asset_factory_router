# AGENTS.md

This repository is operated under the G0 / G1 / G2 AI-assisted engineering workflow.

## Repository Identity

Project: AI Asset Factory + Model Router
Current target status: V0.2_DEV_COMPLETE -> V0.2_LOCKED readiness
Primary language: Python
Package name: `asset-factory`
Main package path: `src/asset_factory`
CLI entry point: `asset-factory = asset_factory.main:main`

## Roles

### G0 — Owner / Command / Final Review
- Defines scope, acceptance criteria, and release direction.
- Approves or rejects pull requests.
- Protects business logic, project direction, and long-term maintainability.
- May ask G1 to implement and G2 to review, but G0 decides what gets merged.

### G1 — Codex / Main Implementation Worker
- Performs implementation tasks on feature branches.
- Makes small, controlled changes only.
- Runs tests and reports results.
- Opens pull requests with clear summaries.
- Does not merge its own work.

### G2 — Antigravity / QA / Documentation Officer
- Reviews G1 work.
- Checks tests, documentation, UX, screenshots, and edge cases.
- Produces QA reports and follow-up task lists.
- Does not rewrite large parts of the project unless explicitly assigned.

## Mandatory Workflow

1. Read `README.md`, `STATUS.md`, and this `AGENTS.md` first.
2. Understand the task before editing.
3. Work on a branch; never push directly to `main` unless G0 explicitly says so.
4. Keep changes small and reviewable.
5. Do not reformat unrelated files.
6. Do not rename major folders without explicit approval.
7. Run available checks before reporting completion.
8. Report changed files, commands run, checks, risks, and next steps.

## Standard Commands

Install local package:

```bash
pip install -e .
```

Run tests:

```bash
python -m unittest discover tests
```

Run CLI smoke checks:

```bash
asset-factory demo
asset-factory list-providers
```

Optional direct module invocation when CLI is unavailable:

```bash
python -m asset_factory.main demo
```

## Repository Map

Expected important paths:

- `README.md` — user-facing installation and CLI instructions.
- `STATUS.md` — current milestone status and readiness notes.
- `pyproject.toml` — package metadata and CLI entry point.
- `src/asset_factory/` — source package.
- `tests/` — unit tests.
- `output/` or `outputs/` — generated artifacts; normally ignored by Git.

## Safety Rules

Never commit:

- `.env`, `.env.*`, credentials, API keys, tokens, private keys, or passwords.
- Customer private data.
- Large generated outputs unless G0 explicitly asks.
- Local virtual environments, caches, or dependency folders.

Do not perform destructive actions without explicit approval:

- Deleting files or folders.
- Rewriting Git history.
- Force pushing.
- Changing remote URLs.
- Changing package names or public CLI commands.

## Pull Request Requirements

Every PR should include:

- Purpose of the change.
- Files changed.
- Commands run.
- Test results.
- Known risks or limitations.
- Recommended next step.

## Review Severity Guide

Use severity only when reviewing:

- P0: Data loss, security issue, broken main workflow, or cannot install/run.
- P1: Important bug, broken CLI command, missing required validation, or failing tests.
- P2: Maintainability, documentation, minor edge case, or UX improvement.
- P3: Nice-to-have cleanup.

## Default Completion Report Format

```md
## Summary

## Files changed

## Commands run

## Checks

## Risks / limitations

## Next step
```
