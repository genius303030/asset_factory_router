#!/usr/bin/env python3
"""Verify the static owner-pricing fake evidence packet."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKET_ROOT_REL = "examples/owner_pricing_fake_evidence_packet"
DEFAULT_PACKET_DIR = REPO_ROOT / PACKET_ROOT_REL
FAKE_ONLY_MARKER = "FAKE_ONLY"

REQUIRED_ARTIFACTS = (
    "README.md",
    "input/fake_owner_pricing_final_application_input.csv",
    "output/fake_owner_pricing_final_application_output.json",
    "audit/fake_owner_pricing_audit_log.json",
    "owner_report/fake_owner_pricing_owner_report.md",
    "rollback/fake_owner_pricing_rollback_plan.md",
    "checksums/SHA256SUMS.txt",
    "metrics/fake_owner_pricing_metrics_summary.json",
    "fixtures/fake_fixture_registry.json",
    "golden/fake_owner_pricing_golden_report.md",
)

CHECKSUM_ARTIFACTS = tuple(
    path for path in REQUIRED_ARTIFACTS if path != "checksums/SHA256SUMS.txt"
)

JSON_ARTIFACTS = (
    "output/fake_owner_pricing_final_application_output.json",
    "audit/fake_owner_pricing_audit_log.json",
    "metrics/fake_owner_pricing_metrics_summary.json",
    "fixtures/fake_fixture_registry.json",
)

REQUIRED_FAKE_IDENTIFIERS = (
    "FAKE_OWNER_ALPHA",
    "FAKE_JOB_001",
    "FAKE_MATERIAL_TEST_A",
    "FAKE_VENDOR_TEST",
)

FORBIDDEN_REAL_DATA_MARKERS = (
    "OWNER_PRICING_PRIVATE",
    "CUSTOMER_PRIVATE",
    "PRIVATE_CUSTOMER",
    "PRODUCTION_CUSTOMER",
    "PRODUCTION_OWNER",
)

IDENTIFIER_FIELDS = {"owner_id", "job_id", "material_id", "vendor_id"}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def artifact_path(packet_dir: Path, relative_path: str) -> Path:
    return packet_dir / relative_path


def manifest_path_to_packet_path(packet_dir: Path, manifest_path: str) -> Path:
    normalized = manifest_path.replace("\\", "/")
    prefix = PACKET_ROOT_REL + "/"
    if not normalized.startswith(prefix):
        raise ValueError(f"checksum path is outside fake packet: {manifest_path}")
    return packet_dir / normalized.removeprefix(prefix)


def load_json(path: Path, label: str, errors: list[str]) -> Any:
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        errors.append(f"{label}: invalid JSON: {exc}")
        return None


def require_false(data: dict[str, Any], path: tuple[str, ...], label: str, errors: list[str]) -> None:
    current: Any = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            errors.append(f"{label}: missing field {'.'.join(path)}")
            return
        current = current[key]
    if current is not False:
        errors.append(f"{label}: expected {'.'.join(path)} to be false")


def verify_required_files(packet_dir: Path) -> list[str]:
    errors: list[str] = []
    for relative_path in REQUIRED_ARTIFACTS:
        path = artifact_path(packet_dir, relative_path)
        if not path.is_file():
            errors.append(f"missing required artifact: {relative_path}")
    return errors


def verify_fake_only_markers(packet_dir: Path) -> list[str]:
    errors: list[str] = []
    for relative_path in REQUIRED_ARTIFACTS:
        path = artifact_path(packet_dir, relative_path)
        if not path.is_file():
            continue
        text = read_text(path)
        if FAKE_ONLY_MARKER not in text:
            errors.append(f"{relative_path}: missing {FAKE_ONLY_MARKER} marker")
        if b"\r\n" in path.read_bytes():
            errors.append(f"{relative_path}: CRLF line endings are not allowed")
    return errors


def verify_fake_identifiers(packet_dir: Path) -> list[str]:
    errors: list[str] = []
    combined_text_parts: list[str] = []
    for relative_path in REQUIRED_ARTIFACTS:
        path = artifact_path(packet_dir, relative_path)
        if path.is_file():
            combined_text_parts.append(read_text(path))

    combined_text = "\n".join(combined_text_parts)
    upper_text = combined_text.upper()
    for identifier in REQUIRED_FAKE_IDENTIFIERS:
        if identifier not in combined_text:
            errors.append(f"missing required fake identifier: {identifier}")
    for marker in FORBIDDEN_REAL_DATA_MARKERS:
        if marker in upper_text:
            errors.append(f"forbidden real/private data marker found: {marker}")

    csv_path = artifact_path(packet_dir, "input/fake_owner_pricing_final_application_input.csv")
    if csv_path.is_file():
        with csv_path.open(newline="", encoding="utf-8") as handle:
            for row_index, row in enumerate(csv.DictReader(handle), start=2):
                for field in IDENTIFIER_FIELDS:
                    value = row.get(field, "")
                    if not value.startswith("FAKE_"):
                        errors.append(f"input CSV line {row_index}: {field} is not fake")

    for relative_path in JSON_ARTIFACTS:
        path = artifact_path(packet_dir, relative_path)
        if not path.is_file():
            continue
        data = load_json(path, relative_path, errors)
        if data is not None:
            verify_json_identifier_values(data, relative_path, errors)

    return errors


def verify_json_identifier_values(data: Any, label: str, errors: list[str]) -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            if key in IDENTIFIER_FIELDS and isinstance(value, str) and not value.startswith("FAKE_"):
                errors.append(f"{label}: {key} is not fake")
            verify_json_identifier_values(value, label, errors)
    elif isinstance(data, list):
        for item in data:
            verify_json_identifier_values(item, label, errors)


def load_checksum_manifest(packet_dir: Path, errors: list[str]) -> dict[str, str]:
    checksum_path = artifact_path(packet_dir, "checksums/SHA256SUMS.txt")
    manifest: dict[str, str] = {}
    if not checksum_path.is_file():
        return manifest

    for line_number, line in enumerate(read_text(checksum_path).splitlines(), start=1):
        if not line or line.startswith("#"):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            errors.append(f"checksums/SHA256SUMS.txt:{line_number}: malformed checksum line")
            continue
        digest, manifest_path = parts
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            errors.append(f"checksums/SHA256SUMS.txt:{line_number}: invalid SHA-256 digest")
            continue
        manifest[manifest_path] = digest
    return manifest


def verify_checksums(packet_dir: Path) -> list[str]:
    errors: list[str] = []
    manifest = load_checksum_manifest(packet_dir, errors)
    expected_manifest_paths = {
        f"{PACKET_ROOT_REL}/{relative_path}" for relative_path in CHECKSUM_ARTIFACTS
    }

    if set(manifest) != expected_manifest_paths:
        missing = sorted(expected_manifest_paths - set(manifest))
        extra = sorted(set(manifest) - expected_manifest_paths)
        if missing:
            errors.append("checksums/SHA256SUMS.txt: missing entries: " + ", ".join(missing))
        if extra:
            errors.append("checksums/SHA256SUMS.txt: unexpected entries: " + ", ".join(extra))

    for manifest_relative_path, expected_digest in manifest.items():
        try:
            path = manifest_path_to_packet_path(packet_dir, manifest_relative_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not path.is_file():
            errors.append(f"checksum target is missing: {manifest_relative_path}")
            continue
        actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_digest != expected_digest:
            errors.append(
                f"checksum mismatch: {manifest_relative_path} "
                f"expected {expected_digest} got {actual_digest}"
            )

    return errors


def verify_structured_artifacts(packet_dir: Path) -> list[str]:
    errors: list[str] = []
    parsed: dict[str, Any] = {}
    for relative_path in JSON_ARTIFACTS:
        path = artifact_path(packet_dir, relative_path)
        if path.is_file():
            parsed[relative_path] = load_json(path, relative_path, errors)

    output = parsed.get("output/fake_owner_pricing_final_application_output.json")
    if isinstance(output, dict):
        require_false(output, ("final_application_behavior_added",), "output", errors)
        require_false(output, ("live_json_mutated",), "output", errors)
        require_false(output, ("sandbox_json_mutated",), "output", errors)
        require_false(output, ("production_write_performed",), "output", errors)

    audit = parsed.get("audit/fake_owner_pricing_audit_log.json")
    if isinstance(audit, dict):
        require_false(audit, ("final_application_behavior_added",), "audit", errors)
        require_false(audit, ("parser_registration_added",), "audit", errors)
        require_false(audit, ("safety_gate_changed",), "audit", errors)
        require_false(audit, ("live_json_mutated",), "audit", errors)
        require_false(audit, ("sandbox_json_mutated",), "audit", errors)

    metrics = parsed.get("metrics/fake_owner_pricing_metrics_summary.json")
    if isinstance(metrics, dict) and isinstance(metrics.get("change_flags"), dict):
        for key in (
            "src_changed",
            "workflow_changed",
            "production_behavior_changed",
            "safety_gate_changed",
            "live_json_mutated",
            "sandbox_json_mutated",
        ):
            require_false(metrics, ("change_flags", key), "metrics", errors)

    registry = parsed.get("fixtures/fake_fixture_registry.json")
    if isinstance(registry, dict) and isinstance(registry.get("review_boundary"), dict):
        for key in (
            "runtime_behavior_added",
            "parser_registration_added",
            "formal_cli_flags_added",
            "live_json_mutated",
            "sandbox_json_mutated",
            "real_data_allowed",
        ):
            require_false(registry, ("review_boundary", key), "fixture registry", errors)

    return errors


def verify_golden_report(packet_dir: Path) -> list[str]:
    errors: list[str] = []
    path = artifact_path(packet_dir, "golden/fake_owner_pricing_golden_report.md")
    if not path.is_file():
        return errors
    golden = read_text(path)
    if "G1-037-FAKE-EVIDENCE-PACKET-V1" not in golden:
        errors.append("golden report: missing deterministic golden ID")
    if "Fake output write count | 0" not in golden:
        errors.append("golden report: missing no-write summary")
    for pattern in (r"\b(now|today|generated at)\b", r"[A-Za-z]:\\", r"/home/runner/"):
        if re.search(pattern, golden, flags=re.IGNORECASE):
            errors.append(f"golden report: non-deterministic content matched {pattern}")
    return errors


def verify_packet(packet_dir: Path = DEFAULT_PACKET_DIR) -> list[str]:
    packet_dir = packet_dir.resolve()
    errors: list[str] = []
    if not packet_dir.is_dir():
        return [f"fake evidence packet directory is missing: {packet_dir}"]

    checks = (
        verify_required_files(packet_dir),
        verify_fake_only_markers(packet_dir),
        verify_fake_identifiers(packet_dir),
        verify_checksums(packet_dir),
        verify_structured_artifacts(packet_dir),
        verify_golden_report(packet_dir),
    )
    for check_errors in checks:
        errors.extend(check_errors)
    return errors


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--packet-dir",
        type=Path,
        default=DEFAULT_PACKET_DIR,
        help="fake evidence packet directory; defaults to examples/owner_pricing_fake_evidence_packet",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    errors = verify_packet(args.packet_dir)
    if errors:
        print("Owner pricing fake evidence packet verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Owner pricing fake evidence packet verification passed.")
    print(f"packet_dir: {args.packet_dir}")
    print(f"required_artifacts: {len(REQUIRED_ARTIFACTS)}")
    print(f"checksum_artifacts: {len(CHECKSUM_ARTIFACTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
