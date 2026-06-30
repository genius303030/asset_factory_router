#!/usr/bin/env python3
"""Read-only owner-pricing CI safety gate."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
OWNER_PRICING_PREFIX = "owner-pricing-"
FINAL_IMPORT_COMMAND = OWNER_PRICING_PREFIX + "final-import"
PRODUCTION_ENABLE_FLAG = "--" + "enable" + "-production-import"

EXPECTED_OWNER_PRICING_COMMANDS = (
    OWNER_PRICING_PREFIX + "dry-run",
    OWNER_PRICING_PREFIX + "plan-sandbox-apply",
    OWNER_PRICING_PREFIX + "apply-sandbox-output",
    OWNER_PRICING_PREFIX + "sandbox-output",
    OWNER_PRICING_PREFIX + "approve-sandbox-output",
    OWNER_PRICING_PREFIX + "approval-gate",
    FINAL_IMPORT_COMMAND + "-preflight",
    OWNER_PRICING_PREFIX + "preflight-final-import",
    FINAL_IMPORT_COMMAND + "-fake-rehearsal",
)

REQUIRED_SAFETY_MARKERS = (
    "sandbox_only",
    "final_import_enabled",
    "live_json_mutated",
    "production_pricing_mutated",
    "production_write_performed",
    "backup_written",
    "fake_production_write_performed",
)

PRIVATE_OWNER_PRICING_PREFIXES = (
    "owner_pricing_private/",
    "input/owner_pricing/private/",
    "inputs/owner_pricing/private/",
    "data/owner_pricing/private/",
)

OWNER_PRICING_METADATA_FILES = {
    "examples/metrics/owner_pricing_pr_metrics.csv",
}

REQUIRED_IGNORED_PATHS = (
    "owner_pricing_private/real_owner_pricing.csv",
    "input/owner_pricing/private/real_owner_pricing.csv",
    "inputs/owner_pricing/private/real_owner_pricing.csv",
    "data/owner_pricing/private/real_owner_pricing.csv",
    "local.owner-private-pricing.csv",
    "local.owner-private-pricing.json",
    "local.owner-pricing-sandbox-plan.md",
    "local.owner-pricing-sandbox-output.json",
    "local.owner-pricing-sandbox-summary.md",
    "local.owner-pricing-approval-record.json",
    "local.owner-pricing-preflight-report.md",
    "local.owner-pricing-fake-rehearsal-report.md",
    "local.owner-pricing-fake-rehearsal-audit.json",
    "local.owner-pricing-fake-rehearsal-output.csv",
    "local.owner-pricing-fake-rehearsal-backup.csv",
    "output/owner_pricing/local_owner_pricing_report.md",
    "outputs/owner_pricing/local_owner_pricing_audit.json",
)

FUTURE_FLAG_ALLOWED_DOCS = {
    "docs/OWNER_PRICING_FINAL_IMPORT_CHECKLIST.md",
    "docs/OWNER_PRICING_FINAL_IMPORT_DESIGN_GATE.md",
    "docs/OWNER_PRICING_FINAL_IMPORT_EXECUTION_REQUIREMENTS.md",
    "docs/OWNER_PRICING_FINAL_IMPORT_PLAN.md",
}

FORBIDDEN_COMMAND_RE = re.compile(
    r"(?<![\w-])" + re.escape(FINAL_IMPORT_COMMAND) + r"(?![-\w])"
)
FORBIDDEN_PARSER_RE = re.compile(
    r"add_parser\(\s*['\"]" + re.escape(FINAL_IMPORT_COMMAND) + r"['\"]"
)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def normalize_git_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def contains_forbidden_command(text: str) -> bool:
    return FORBIDDEN_COMMAND_RE.search(text) is not None


def is_forbidden_flag_path(path: str) -> bool:
    return normalize_git_path(path) not in FUTURE_FLAG_ALLOWED_DOCS


def real_owner_pricing_data_reason(path: str) -> str | None:
    normalized = normalize_git_path(path).lower()
    suffix = Path(normalized).suffix

    if normalized in OWNER_PRICING_METADATA_FILES:
        return None

    if normalized.startswith(PRIVATE_OWNER_PRICING_PREFIXES):
        return "private owner-pricing path is tracked"

    if suffix not in {".csv", ".json", ".xlsx", ".xls"}:
        return None

    owner_pricing_path = "owner_pricing" in normalized or "owner-pricing" in normalized
    if not owner_pricing_path:
        return None

    allowed_fake_example = normalized.startswith("examples/owner_pricing/fake")
    allowed_fake_test_fixture = normalized.startswith("tests/fixtures/owner_pricing/fake")
    if allowed_fake_example or allowed_fake_test_fixture:
        return None

    basename = Path(normalized).name
    if basename.startswith(("fake_", "sample_", "test_")):
        return None

    return "owner-pricing data file is tracked outside fake/sample fixtures"


def iter_tracked_files() -> list[str]:
    result = run_command(["git", "ls-files", "-z"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git ls-files failed")
    return [path for path in result.stdout.split("\0") if path]


def iter_candidate_files() -> list[str]:
    tracked = set(iter_tracked_files())
    result = run_command(["git", "ls-files", "--others", "--exclude-standard", "-z"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git ls-files --others failed")
    untracked = {path for path in result.stdout.split("\0") if path}
    return sorted(tracked | untracked)


def iter_text_files(paths: Iterable[str]) -> Iterable[tuple[str, str]]:
    for path in paths:
        full_path = REPO_ROOT / path
        if not full_path.is_file():
            continue
        try:
            yield path, read_text(full_path)
        except UnicodeDecodeError:
            continue


def check_cli_help() -> list[str]:
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, "-m", "asset_factory.main", "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        return [f"CLI help failed: {result.stderr.strip()}"]

    failures: list[str] = []
    help_text = result.stdout
    for command in EXPECTED_OWNER_PRICING_COMMANDS:
        if command not in help_text:
            failures.append(f"expected owner-pricing command missing from CLI help: {command}")
    if contains_forbidden_command(help_text):
        failures.append("bare owner-pricing final import command appears in CLI help")
    if PRODUCTION_ENABLE_FLAG in help_text:
        failures.append("production-enable flag appears in CLI help")
    return failures


def check_parser_registration() -> list[str]:
    main_path = REPO_ROOT / "src" / "asset_factory" / "main.py"
    main_source = read_text(main_path)
    failures: list[str] = []
    for command in EXPECTED_OWNER_PRICING_COMMANDS:
        if command not in main_source:
            failures.append(f"expected owner-pricing command missing from parser source: {command}")
    if FORBIDDEN_PARSER_RE.search(main_source):
        failures.append("bare owner-pricing final import command is registered in parser source")
    if PRODUCTION_ENABLE_FLAG in main_source:
        failures.append("production-enable flag appears in parser source")
    return failures


def check_production_flag_scope(tracked_files: list[str]) -> list[str]:
    failures: list[str] = []
    for path, text in iter_text_files(tracked_files):
        if PRODUCTION_ENABLE_FLAG not in text:
            continue
        if is_forbidden_flag_path(path):
            failures.append(f"production-enable flag appears outside approved planning docs: {path}")
    return failures


def check_tracked_owner_pricing_data(tracked_files: list[str]) -> list[str]:
    failures: list[str] = []
    for path in tracked_files:
        reason = real_owner_pricing_data_reason(path)
        if reason:
            failures.append(f"{reason}: {path}")
    return failures


def check_ignored_paths() -> list[str]:
    failures: list[str] = []
    for path in REQUIRED_IGNORED_PATHS:
        result = run_command(["git", "check-ignore", "-q", "--", path])
        if result.returncode != 0:
            failures.append(f"expected owner-pricing private/output path is not ignored: {path}")
    return failures


def check_safety_markers() -> list[str]:
    owner_pricing_source = read_text(REPO_ROOT / "src" / "asset_factory" / "owner_pricing.py")
    return [
        f"owner-pricing safety marker missing from source: {marker}"
        for marker in REQUIRED_SAFETY_MARKERS
        if marker not in owner_pricing_source
    ]


def check_ci_workflow_wiring() -> list[str]:
    workflow_path = REPO_ROOT / ".github" / "workflows" / "python-ci.yml"
    workflow = read_text(workflow_path)
    failures: list[str] = []
    if "test_owner_pricing.py" not in workflow:
        failures.append("python-ci workflow does not explicitly run owner-pricing unit tests")
    if "scripts/check_owner_pricing_safety.py" not in workflow:
        failures.append("python-ci workflow does not run the owner-pricing safety gate")
    return failures


def run_checks() -> list[str]:
    tracked_files = iter_tracked_files()
    candidate_files = iter_candidate_files()
    checks = (
        check_cli_help(),
        check_parser_registration(),
        check_production_flag_scope(candidate_files),
        check_tracked_owner_pricing_data(tracked_files),
        check_ignored_paths(),
        check_safety_markers(),
        check_ci_workflow_wiring(),
    )
    return [failure for check in checks for failure in check]


def main() -> int:
    failures = run_checks()
    if failures:
        print("Owner pricing CI safety gate failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Owner pricing CI safety gate passed.")
    print("Checked CLI boundaries, parser registration, ignored paths, tracked data, and markers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
