#!/usr/bin/env python3
"""Validate and summarize the lightweight PR metrics baseline."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV_PATH = REPO_ROOT / "examples" / "metrics" / "owner_pricing_pr_metrics.csv"

EXPECTED_COLUMNS = (
    "pr_number",
    "task_id",
    "title",
    "branch",
    "workflow_category",
    "workflow_stage",
    "changed_files_count",
    "additions",
    "deletions",
    "changed_files",
    "unit_test_count",
    "owner_pricing_test_count",
    "ci_status",
    "safety_gate_status",
    "g2_review_status",
    "merge_status",
    "merge_commit",
    "docs_changed",
    "tests_changed",
    "src_changed",
    "workflow_changed",
    "examples_changed",
    "production_behavior_changed",
    "notes",
)

REQUIRED_PR_NUMBERS = {"13", "14", "15", "17", "18", "20", "21", "23"}
BOOLEAN_VALUES = {"yes", "no"}
COUNT_VALUES = {"unknown", "not_run"}
CI_STATUS_VALUES = {"pass", "fail", "pending", "unknown"}
SAFETY_GATE_STATUS_VALUES = {
    "pass",
    "passed",
    "passed_local",
    "fail",
    "failed",
    "not_applicable",
    "unknown",
}
G2_REVIEW_STATUS_VALUES = {"PASS", "REQUEST_CHANGES", "missing", "unknown"}
MERGE_STATUS_VALUES = {"merged", "open", "closed", "unknown"}


def load_metrics(path: Path = DEFAULT_CSV_PATH) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    if reader.fieldnames != list(EXPECTED_COLUMNS):
        expected = ", ".join(EXPECTED_COLUMNS)
        actual = ", ".join(reader.fieldnames or [])
        raise ValueError(f"unexpected metrics columns\nexpected: {expected}\nactual: {actual}")

    return rows


def is_non_negative_int(value: str) -> bool:
    return value.isdigit()


def is_count_value(value: str) -> bool:
    return value in COUNT_VALUES or is_non_negative_int(value)


def validate_rows(rows: Iterable[dict[str, str]]) -> list[str]:
    rows = list(rows)
    errors: list[str] = []

    seen_prs = {row.get("pr_number", "") for row in rows}
    missing_prs = sorted(REQUIRED_PR_NUMBERS - seen_prs, key=int)
    if missing_prs:
        errors.append(f"missing required PR rows: {', '.join(missing_prs)}")

    for index, row in enumerate(rows, start=2):
        pr_label = row.get("pr_number") or f"line {index}"
        for column in EXPECTED_COLUMNS:
            value = row.get(column, "")
            if column == "notes":
                continue
            if value == "":
                errors.append(f"PR {pr_label}: blank required column {column}")

        for column in ("changed_files_count", "additions", "deletions"):
            value = row.get(column, "")
            if not is_non_negative_int(value):
                errors.append(f"PR {pr_label}: {column} must be a non-negative integer")

        for column in ("unit_test_count", "owner_pricing_test_count"):
            value = row.get(column, "")
            if not is_count_value(value):
                errors.append(f"PR {pr_label}: {column} must be a count, unknown, or not_run")

        for column in (
            "docs_changed",
            "tests_changed",
            "src_changed",
            "workflow_changed",
            "examples_changed",
            "production_behavior_changed",
        ):
            value = row.get(column, "")
            if value not in BOOLEAN_VALUES:
                errors.append(f"PR {pr_label}: {column} must be yes or no")

        if row.get("ci_status") not in CI_STATUS_VALUES:
            errors.append(f"PR {pr_label}: invalid ci_status")
        if row.get("safety_gate_status") not in SAFETY_GATE_STATUS_VALUES:
            errors.append(f"PR {pr_label}: invalid safety_gate_status")
        if row.get("g2_review_status") not in G2_REVIEW_STATUS_VALUES:
            errors.append(f"PR {pr_label}: invalid g2_review_status")
        if row.get("merge_status") not in MERGE_STATUS_VALUES:
            errors.append(f"PR {pr_label}: invalid merge_status")
        if row.get("production_behavior_changed") != "no":
            errors.append(f"PR {pr_label}: production behavior change requires explicit G0 review")

    return errors


def summarize_rows(rows: Iterable[dict[str, str]]) -> str:
    rows = list(rows)
    ci_counts = Counter(row["ci_status"] for row in rows)
    category_counts = Counter(row["workflow_category"] for row in rows)
    production_changes = sum(
        1 for row in rows if row.get("production_behavior_changed") == "yes"
    )

    lines = [
        f"rows: {len(rows)}",
        "ci_status: "
        + ", ".join(f"{status}={count}" for status, count in sorted(ci_counts.items())),
        "workflow_category: "
        + ", ".join(
            f"{category}={count}" for category, count in sorted(category_counts.items())
        ),
        f"production_behavior_changed=yes: {production_changes}",
    ]
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV_PATH,
        help="metrics CSV path; defaults to examples/metrics/owner_pricing_pr_metrics.csv",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="validate the CSV schema and required baseline rows",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="print a short summary of the baseline",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    rows = load_metrics(args.csv)
    errors = validate_rows(rows)

    if args.validate or not args.summary:
        if errors:
            print("PR metrics baseline validation failed:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        print("PR metrics baseline validation passed.")

    if args.summary:
        print(summarize_rows(rows))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
