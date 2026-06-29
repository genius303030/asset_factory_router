import csv
import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple


REQUIRED_OWNER_PRICING_FIELDS = (
    "material_key",
    "material_name",
    "unit",
    "unit_price",
)

OWNER_PRICING_APPROVAL_PHRASE = "I_APPROVE_SANDBOX_PRICING_OUTPUT"


@dataclass
class OwnerPricingRow:
    row_number: int
    material_key: str
    material_name: str
    unit: str
    unit_price: Decimal


@dataclass
class CurrentPricingRow:
    material_key: str
    material_name: str
    unit: str
    unit_price: Decimal


@dataclass
class MissingFieldIssue:
    row_number: int
    material_key: str
    fields: List[str]


@dataclass
class PriceIssue:
    row_number: int
    material_key: str
    value: str
    issue: str


@dataclass
class DuplicateKeyIssue:
    material_key: str
    rows: List[int]


@dataclass
class PricingChange:
    material_key: str
    material_name: str
    unit: str
    new_price: Decimal
    current_price: Optional[Decimal] = None
    changed_fields: Optional[List[str]] = None


@dataclass
class OwnerPricingDryRunResult:
    source_csv: str
    current_pricing: Optional[str]
    rows_read: int
    valid_rows: int
    invalid_rows: int
    current_records_read: int
    missing_required_fields: List[MissingFieldIssue]
    price_format_issues: List[PriceIssue]
    duplicate_material_keys: List[DuplicateKeyIssue]
    would_be_added: List[PricingChange]
    would_be_updated: List[PricingChange]
    would_be_unchanged: List[PricingChange]


@dataclass
class OwnerPricingSandboxOutputResult:
    source_csv: str
    current_pricing: Optional[str]
    sandbox_output_path: str
    summary_report_path: Optional[str]
    summary_json_path: Optional[str]
    sandbox_apply_plan_path: Optional[str]
    generated_at: str
    rows_read: int
    valid_rows: int
    invalid_rows: int
    sandbox_materials_written: int
    added_materials: int
    updated_materials: int
    unchanged_materials: int
    duplicate_material_keys: int


@dataclass
class OwnerPricingApprovalRecordResult:
    sandbox_output_path: str
    approval_record_path: str
    markdown_summary_path: Optional[str]
    sandbox_output_sha256: str
    generated_at: str
    approved_by: str


@dataclass
class OwnerPricingPreflightResult:
    passed: bool
    report_path: str
    report_json_path: Optional[str]
    sandbox_output_sha256: Optional[str]
    approval_record_sha256: Optional[str]
    production_target_sha256: Optional[str]
    blockers: List[str]
    warnings: List[str]


@dataclass
class OwnerPricingFakeRehearsalResult:
    status: str
    report_path: str
    audit_log_path: str
    fake_production_output_path: str
    backup_output_path: str
    sandbox_output_sha256: Optional[str]
    approval_record_sha256: Optional[str]
    preflight_report_sha256: Optional[str]
    pre_import_production_sha256: Optional[str]
    backup_sha256: Optional[str]
    post_write_production_sha256: Optional[str]
    restored_production_sha256: Optional[str]
    blockers: List[str]
    warnings: List[str]


LIVE_OUTPUT_PATH_PARTS = {
    "config",
    "data",
    "live",
    "prod",
    "production",
    "src",
}

LIVE_OUTPUT_FILENAMES = {
    "current_pricing.csv",
    "current_pricing.json",
    "material_pricing.csv",
    "material_pricing.json",
    "owner_pricing.csv",
    "owner_pricing.json",
    "pricing.csv",
    "pricing.json",
}

FAKE_REHEARSAL_SAFE_PATH_PARTS = {
    "examples",
    "output",
    "outputs",
    "owner_pricing_private",
}


def dry_run_owner_pricing_import(
    csv_path: str,
    current_pricing_path: Optional[str] = None,
) -> OwnerPricingDryRunResult:
    raw_rows = _read_csv_rows(csv_path)
    parsed_rows: List[OwnerPricingRow] = []
    missing_required_fields: List[MissingFieldIssue] = []
    price_format_issues: List[PriceIssue] = []
    invalid_row_numbers = set()

    for row_number, row in raw_rows:
        cleaned = _clean_row(row)
        material_key = cleaned.get("material_key", "")
        missing_fields = [
            field for field in REQUIRED_OWNER_PRICING_FIELDS if not cleaned.get(field)
        ]

        if missing_fields:
            missing_required_fields.append(
                MissingFieldIssue(
                    row_number=row_number,
                    material_key=material_key,
                    fields=missing_fields,
                )
            )
            invalid_row_numbers.add(row_number)
            continue

        price, price_issue = _parse_price(cleaned["unit_price"])
        if price_issue:
            price_format_issues.append(
                PriceIssue(
                    row_number=row_number,
                    material_key=material_key,
                    value=cleaned["unit_price"],
                    issue=price_issue,
                )
            )
            invalid_row_numbers.add(row_number)
            continue

        parsed_rows.append(
            OwnerPricingRow(
                row_number=row_number,
                material_key=material_key,
                material_name=cleaned["material_name"],
                unit=cleaned["unit"],
                unit_price=price,
            )
        )

    duplicate_material_keys = _find_duplicate_keys(parsed_rows)
    duplicate_rows = {
        row_number
        for issue in duplicate_material_keys
        for row_number in issue.rows
    }
    invalid_row_numbers.update(duplicate_rows)

    valid_rows = [
        row for row in parsed_rows if row.row_number not in invalid_row_numbers
    ]
    current_pricing = _load_current_pricing(current_pricing_path)
    would_be_added, would_be_updated, would_be_unchanged = _compare_rows(
        valid_rows,
        current_pricing,
    )

    return OwnerPricingDryRunResult(
        source_csv=csv_path,
        current_pricing=current_pricing_path,
        rows_read=len(raw_rows),
        valid_rows=len(valid_rows),
        invalid_rows=len(invalid_row_numbers),
        current_records_read=len(current_pricing),
        missing_required_fields=missing_required_fields,
        price_format_issues=price_format_issues,
        duplicate_material_keys=duplicate_material_keys,
        would_be_added=would_be_added,
        would_be_updated=would_be_updated,
        would_be_unchanged=would_be_unchanged,
    )


def write_preview_report(result: OwnerPricingDryRunResult, report_path: str) -> None:
    report = build_preview_report(result)
    report_dir = os.path.dirname(os.path.abspath(report_path))
    os.makedirs(report_dir, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as file:
        file.write(report)


def write_sandbox_apply_plan(
    csv_path: str,
    plan_path: str,
    current_pricing_path: Optional[str] = None,
    dry_run_report_path: Optional[str] = None,
    plan_json_path: Optional[str] = None,
    overwrite: bool = False,
) -> OwnerPricingDryRunResult:
    _validate_sandbox_output_path(plan_path, overwrite=overwrite)
    if plan_json_path:
        _validate_sandbox_output_path(plan_json_path, overwrite=overwrite)
        if os.path.abspath(plan_json_path) == os.path.abspath(plan_path):
            raise ValueError("plan JSON output path must be different from markdown plan path")

    dry_run_report_info = _read_optional_dry_run_report(dry_run_report_path)
    result = dry_run_owner_pricing_import(csv_path, current_pricing_path)
    generated_at = _generated_timestamp()
    markdown = build_sandbox_apply_plan(
        result,
        plan_path=plan_path,
        dry_run_report_info=dry_run_report_info,
        plan_json_path=plan_json_path,
        generated_at=generated_at,
    )

    plan_dir = os.path.dirname(os.path.abspath(plan_path))
    os.makedirs(plan_dir, exist_ok=True)
    with open(plan_path, "w", encoding="utf-8") as file:
        file.write(markdown)

    if plan_json_path:
        plan_json = build_sandbox_apply_plan_json(
            result,
            plan_path=plan_path,
            dry_run_report_info=dry_run_report_info,
            plan_json_path=plan_json_path,
            generated_at=generated_at,
        )
        json_dir = os.path.dirname(os.path.abspath(plan_json_path))
        os.makedirs(json_dir, exist_ok=True)
        with open(plan_json_path, "w", encoding="utf-8") as file:
            json.dump(plan_json, file, indent=2, ensure_ascii=False)
            file.write("\n")

    return result


def write_sandbox_apply_output(
    csv_path: str,
    sandbox_output_path: str,
    current_pricing_path: Optional[str] = None,
    sandbox_apply_plan_path: Optional[str] = None,
    summary_report_path: Optional[str] = None,
    summary_json_path: Optional[str] = None,
    overwrite: bool = False,
) -> OwnerPricingSandboxOutputResult:
    _validate_sandbox_output_path(
        sandbox_output_path,
        overwrite=overwrite,
        output_kind="sandbox pricing output",
    )
    if summary_report_path:
        _validate_sandbox_output_path(
            summary_report_path,
            overwrite=overwrite,
            output_kind="sandbox summary report",
        )
    if summary_json_path:
        _validate_sandbox_output_path(
            summary_json_path,
            overwrite=overwrite,
            output_kind="sandbox JSON summary",
        )

    _validate_distinct_output_paths(
        [
            ("sandbox pricing output", sandbox_output_path),
            ("sandbox summary report", summary_report_path),
            ("sandbox JSON summary", summary_json_path),
        ]
    )

    sandbox_apply_plan_info = _read_optional_sandbox_apply_plan(sandbox_apply_plan_path)
    result = dry_run_owner_pricing_import(csv_path, current_pricing_path)
    current_pricing = _load_current_pricing(current_pricing_path)
    generated_at = _generated_timestamp()
    sandbox_output = build_sandbox_apply_output_json(
        result,
        current_pricing=current_pricing,
        sandbox_output_path=sandbox_output_path,
        sandbox_apply_plan_info=sandbox_apply_plan_info,
        generated_at=generated_at,
    )

    _write_json_file(sandbox_output_path, sandbox_output)

    if summary_report_path:
        summary_report = build_sandbox_apply_output_report(
            result,
            sandbox_output=sandbox_output,
            summary_report_path=summary_report_path,
        )
        _write_text_file(summary_report_path, summary_report)

    if summary_json_path:
        summary_json = build_sandbox_apply_output_summary_json(
            sandbox_output,
            summary_json_path=summary_json_path,
        )
        _write_json_file(summary_json_path, summary_json)

    summary = sandbox_output["summary"]
    return OwnerPricingSandboxOutputResult(
        source_csv=csv_path,
        current_pricing=current_pricing_path,
        sandbox_output_path=sandbox_output_path,
        summary_report_path=summary_report_path,
        summary_json_path=summary_json_path,
        sandbox_apply_plan_path=sandbox_apply_plan_path,
        generated_at=generated_at,
        rows_read=result.rows_read,
        valid_rows=result.valid_rows,
        invalid_rows=result.invalid_rows,
        sandbox_materials_written=summary["sandbox_materials_written"],
        added_materials=summary["added_materials"],
        updated_materials=summary["updated_materials"],
        unchanged_materials=summary["unchanged_materials"],
        duplicate_material_keys=len(result.duplicate_material_keys),
    )


def write_owner_pricing_approval_record(
    sandbox_output_path: str,
    approval_record_path: str,
    owner_approval: str,
    sandbox_apply_plan_path: Optional[str] = None,
    dry_run_report_path: Optional[str] = None,
    markdown_summary_path: Optional[str] = None,
    approved_by: str = "local owner / manual owner",
    overwrite: bool = False,
) -> OwnerPricingApprovalRecordResult:
    sandbox_output, sandbox_output_sha256 = _load_validated_sandbox_output(
        sandbox_output_path
    )
    _validate_owner_approval_phrase(owner_approval)
    _validate_sandbox_output_path(
        approval_record_path,
        overwrite=overwrite,
        output_kind="owner pricing approval record",
    )
    if markdown_summary_path:
        _validate_sandbox_output_path(
            markdown_summary_path,
            overwrite=overwrite,
            output_kind="owner pricing approval markdown summary",
        )

    _validate_distinct_output_paths(
        [
            ("owner pricing approval record", approval_record_path),
            ("owner pricing approval markdown summary", markdown_summary_path),
        ]
    )

    sandbox_apply_plan_info = _read_optional_sandbox_apply_plan(sandbox_apply_plan_path)
    dry_run_report_info = _read_optional_dry_run_report(dry_run_report_path)
    generated_at = _generated_timestamp()
    approval_record = build_owner_pricing_approval_record_json(
        sandbox_output=sandbox_output,
        sandbox_output_path=sandbox_output_path,
        sandbox_output_sha256=sandbox_output_sha256,
        owner_approval=owner_approval,
        approved_by=approved_by,
        sandbox_apply_plan_info=sandbox_apply_plan_info,
        dry_run_report_info=dry_run_report_info,
        generated_at=generated_at,
    )

    _write_json_file(approval_record_path, approval_record)

    if markdown_summary_path:
        markdown = build_owner_pricing_approval_record_markdown(
            approval_record,
            markdown_summary_path=markdown_summary_path,
        )
        _write_text_file(markdown_summary_path, markdown)

    return OwnerPricingApprovalRecordResult(
        sandbox_output_path=sandbox_output_path,
        approval_record_path=approval_record_path,
        markdown_summary_path=markdown_summary_path,
        sandbox_output_sha256=sandbox_output_sha256,
        generated_at=generated_at,
        approved_by=approved_by,
    )


def write_owner_pricing_final_import_preflight(
    sandbox_output_path: str,
    approval_record_path: str,
    production_target_path: str,
    backup_output_path: str,
    report_path: str,
    report_json_path: Optional[str] = None,
    overwrite: bool = False,
) -> OwnerPricingPreflightResult:
    _validate_sandbox_output_path(
        report_path,
        overwrite=overwrite,
        output_kind="owner pricing preflight report",
    )
    if report_json_path:
        _validate_sandbox_output_path(
            report_json_path,
            overwrite=overwrite,
            output_kind="owner pricing preflight JSON report",
        )
    _validate_distinct_output_paths(
        [
            ("sandbox output", sandbox_output_path),
            ("approval record", approval_record_path),
            ("production target", production_target_path),
            ("expected backup output", backup_output_path),
            ("owner pricing preflight report", report_path),
            ("owner pricing preflight JSON report", report_json_path),
        ]
    )
    _validate_readonly_pricing_path(
        production_target_path,
        path_kind="production target",
        must_exist=True,
    )
    _validate_backup_output_path(backup_output_path)

    sandbox_output, sandbox_output_sha256 = _load_validated_sandbox_output(
        sandbox_output_path
    )
    approval_record, approval_record_sha256 = _load_json_file_with_sha256(
        approval_record_path,
        input_kind="approval record",
    )
    production_target_sha256 = _file_sha256(production_target_path)
    production_records = _load_current_pricing(production_target_path)

    generated_at = _generated_timestamp()
    validation_results, blockers, warnings = _build_preflight_validations(
        sandbox_output=sandbox_output,
        sandbox_output_path=sandbox_output_path,
        sandbox_output_sha256=sandbox_output_sha256,
        approval_record=approval_record,
        approval_record_path=approval_record_path,
        production_target_path=production_target_path,
        production_records=production_records,
        backup_output_path=backup_output_path,
    )
    passed = not blockers
    preflight = build_owner_pricing_preflight_json(
        passed=passed,
        generated_at=generated_at,
        sandbox_output_path=sandbox_output_path,
        sandbox_output_sha256=sandbox_output_sha256,
        approval_record_path=approval_record_path,
        approval_record_sha256=approval_record_sha256,
        production_target_path=production_target_path,
        production_target_sha256=production_target_sha256,
        production_records_read=len(production_records),
        backup_output_path=backup_output_path,
        report_path=report_path,
        report_json_path=report_json_path,
        validation_results=validation_results,
        blockers=blockers,
        warnings=warnings,
    )

    _write_text_file(report_path, build_owner_pricing_preflight_report(preflight))
    if report_json_path:
        _write_json_file(report_json_path, preflight)

    result = OwnerPricingPreflightResult(
        passed=passed,
        report_path=report_path,
        report_json_path=report_json_path,
        sandbox_output_sha256=sandbox_output_sha256,
        approval_record_sha256=approval_record_sha256,
        production_target_sha256=production_target_sha256,
        blockers=blockers,
        warnings=warnings,
    )

    if not passed:
        raise ValueError("owner pricing final import preflight failed")

    return result


def run_owner_pricing_final_import_fake_rehearsal(
    sandbox_output_path: str,
    approval_record_path: str,
    preflight_report_path: str,
    fake_production_target_path: str,
    fake_production_output_path: str,
    backup_output_path: str,
    audit_log_path: str,
    report_path: str,
    overwrite: bool = False,
    simulate_post_write_validation_failure: bool = False,
    simulate_rollback_verification_failure: bool = False,
) -> OwnerPricingFakeRehearsalResult:
    _validate_fake_rehearsal_input_path(
        sandbox_output_path,
        path_kind="sandbox output",
        allowed_extensions={".json"},
    )
    _validate_fake_rehearsal_input_path(
        approval_record_path,
        path_kind="approval record",
        allowed_extensions={".json"},
    )
    _validate_fake_rehearsal_input_path(
        preflight_report_path,
        path_kind="preflight report",
        allowed_extensions={".json"},
    )
    _validate_fake_rehearsal_input_path(
        fake_production_target_path,
        path_kind="fake production target",
        allowed_extensions={".csv", ".json"},
    )
    _validate_fake_rehearsal_write_path(
        fake_production_output_path,
        path_kind="fake production output",
        allowed_extensions={".csv", ".json"},
        overwrite=overwrite,
    )
    _validate_fake_rehearsal_write_path(
        backup_output_path,
        path_kind="fake backup output",
        allowed_extensions={".csv", ".json"},
        overwrite=False,
    )
    _validate_fake_rehearsal_write_path(
        audit_log_path,
        path_kind="fake rehearsal audit log",
        allowed_extensions={".json"},
        overwrite=overwrite,
    )
    _validate_fake_rehearsal_write_path(
        report_path,
        path_kind="fake rehearsal report",
        allowed_extensions={".md"},
        overwrite=overwrite,
    )
    _validate_distinct_output_paths(
        [
            ("sandbox output", sandbox_output_path),
            ("approval record", approval_record_path),
            ("preflight report", preflight_report_path),
            ("fake production target", fake_production_target_path),
            ("fake production output", fake_production_output_path),
            ("fake backup output", backup_output_path),
            ("fake rehearsal audit log", audit_log_path),
            ("fake rehearsal report", report_path),
        ]
    )

    sandbox_output, sandbox_output_sha256 = _load_validated_sandbox_output(
        sandbox_output_path
    )
    approval_record, approval_record_sha256 = _load_json_file_with_sha256(
        approval_record_path,
        input_kind="approval record",
    )
    preflight_report, preflight_report_sha256 = _load_json_file_with_sha256(
        preflight_report_path,
        input_kind="preflight report",
    )
    pre_import_production_sha256 = _file_sha256(fake_production_target_path)
    pre_import_records = _load_current_pricing(fake_production_target_path)

    audit = build_owner_pricing_fake_rehearsal_audit(
        generated_at=_generated_timestamp(),
        sandbox_output_path=sandbox_output_path,
        approval_record_path=approval_record_path,
        preflight_report_path=preflight_report_path,
        fake_production_target_path=fake_production_target_path,
        fake_production_output_path=fake_production_output_path,
        backup_output_path=backup_output_path,
        audit_log_path=audit_log_path,
        report_path=report_path,
        sandbox_output_sha256=sandbox_output_sha256,
        approval_record_sha256=approval_record_sha256,
        preflight_report_sha256=preflight_report_sha256,
        pre_import_production_sha256=pre_import_production_sha256,
    )
    _append_fake_rehearsal_state(audit, "started", "fake rehearsal started")
    _write_json_file(audit_log_path, audit)

    validation_results, blockers, warnings = _build_fake_rehearsal_packet_validations(
        sandbox_output=sandbox_output,
        sandbox_output_path=sandbox_output_path,
        sandbox_output_sha256=sandbox_output_sha256,
        approval_record=approval_record,
        approval_record_path=approval_record_path,
        approval_record_sha256=approval_record_sha256,
        preflight_report=preflight_report,
        preflight_report_path=preflight_report_path,
        fake_production_target_path=fake_production_target_path,
        pre_import_production_sha256=pre_import_production_sha256,
        backup_output_path=backup_output_path,
    )
    audit["validation_results"] = validation_results
    audit["warnings"] = warnings
    if blockers:
        _finalize_fake_rehearsal(
            audit=audit,
            audit_log_path=audit_log_path,
            report_path=report_path,
            status="aborted",
            blockers=blockers,
            detail="input packet failed fake rehearsal validation",
        )
        raise ValueError("owner pricing final import fake rehearsal failed")

    try:
        backup_dir = os.path.dirname(os.path.abspath(backup_output_path))
        os.makedirs(backup_dir, exist_ok=True)
        shutil.copyfile(fake_production_target_path, backup_output_path)
    except OSError as exc:
        blockers = [f"fake backup write failed: {exc}"]
        _finalize_fake_rehearsal(
            audit=audit,
            audit_log_path=audit_log_path,
            report_path=report_path,
            status="failed_before_write",
            blockers=blockers,
            detail="fake backup could not be written",
        )
        raise ValueError("owner pricing final import fake rehearsal failed") from exc

    backup_sha256 = _file_sha256(backup_output_path)
    audit["checksums"]["backup_sha256"] = backup_sha256
    audit["safety_flags"]["backup_written"] = True
    audit["safety_flags"]["backup_written_to_fake_path"] = True
    if backup_sha256 != pre_import_production_sha256:
        blockers = ["fake backup checksum does not match pre-import fake production checksum"]
        _finalize_fake_rehearsal(
            audit=audit,
            audit_log_path=audit_log_path,
            report_path=report_path,
            status="failed_before_write",
            blockers=blockers,
            detail="fake backup checksum verification failed",
        )
        raise ValueError("owner pricing final import fake rehearsal failed")

    _append_fake_rehearsal_state(
        audit,
        "backup_verified",
        "fake backup checksum matched pre-import fake production checksum",
    )
    _write_json_file(audit_log_path, audit)

    fake_materials = _sandbox_materials_for_fake_rehearsal(sandbox_output)
    if simulate_post_write_validation_failure and fake_materials:
        fake_materials = [*fake_materials, dict(fake_materials[0])]
    _write_fake_pricing_output(fake_production_output_path, fake_materials)
    audit["safety_flags"]["fake_production_write_performed"] = True
    audit["safety_flags"]["production_write_performed"] = False
    post_write_sha256 = _file_sha256(fake_production_output_path)
    audit["checksums"]["post_write_fake_production_sha256"] = post_write_sha256
    _append_fake_rehearsal_state(
        audit,
        "fake_write_completed",
        "fake production output path was written",
    )

    post_results, post_blockers = _validate_fake_rehearsal_written_output(
        output_path=fake_production_output_path,
        expected_materials=fake_materials,
        skipped_rows=sandbox_output.get("skipped_rows", []),
        validation_label="post-write fake production output",
    )
    audit["post_write_validation_results"] = post_results
    if post_blockers:
        audit["post_write_blockers"] = post_blockers
        _append_fake_rehearsal_state(
            audit,
            "rollback_required",
            "post-write fake validation failed; rollback required",
        )
    else:
        _append_fake_rehearsal_state(
            audit,
            "passed",
            "fake write and post-write validation passed",
        )
    _write_json_file(audit_log_path, audit)

    restored_sha256 = None
    rollback_blockers: List[str] = []
    try:
        shutil.copyfile(backup_output_path, fake_production_output_path)
        if simulate_rollback_verification_failure:
            with open(fake_production_output_path, "a", encoding="utf-8") as file:
                file.write("corrupted_fake_restore,Corrupted Fake Restore,kg,1.00\n")
        restored_sha256 = _file_sha256(fake_production_output_path)
        audit["checksums"]["restored_fake_production_sha256"] = restored_sha256
        restore_results, restore_blockers = _validate_fake_rehearsal_restored_output(
            output_path=fake_production_output_path,
            expected_records=pre_import_records,
        )
        audit["restore_validation_results"] = restore_results
        if restored_sha256 != backup_sha256:
            restore_blockers.append("restored fake production checksum does not match fake backup checksum")
        rollback_blockers.extend(restore_blockers)
    except OSError as exc:
        rollback_blockers.append(f"fake rollback restore failed: {exc}")

    if rollback_blockers:
        _finalize_fake_rehearsal(
            audit=audit,
            audit_log_path=audit_log_path,
            report_path=report_path,
            status="rollback_failed",
            blockers=rollback_blockers,
            detail="fake rollback verification failed",
        )
        raise ValueError("owner pricing final import fake rehearsal rollback failed")

    _finalize_fake_rehearsal(
        audit=audit,
        audit_log_path=audit_log_path,
        report_path=report_path,
        status="rollback_passed",
        blockers=[],
        detail="fake rollback restored and verified the fake output path",
    )

    return OwnerPricingFakeRehearsalResult(
        status=audit["status"],
        report_path=report_path,
        audit_log_path=audit_log_path,
        fake_production_output_path=fake_production_output_path,
        backup_output_path=backup_output_path,
        sandbox_output_sha256=sandbox_output_sha256,
        approval_record_sha256=approval_record_sha256,
        preflight_report_sha256=preflight_report_sha256,
        pre_import_production_sha256=pre_import_production_sha256,
        backup_sha256=backup_sha256,
        post_write_production_sha256=post_write_sha256,
        restored_production_sha256=restored_sha256,
        blockers=audit["blockers"],
        warnings=audit["warnings"],
    )


def build_preview_report(result: OwnerPricingDryRunResult) -> str:
    lines = [
        "# Owner Pricing Import Dry-run Preview",
        "",
        "Dry-run only. No live JSON or production pricing data was mutated.",
        "",
        "## Input",
        "",
        f"- Owner pricing CSV: `{result.source_csv}`",
        f"- Current pricing snapshot: `{result.current_pricing or 'not provided'}`",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| CSV rows read | {result.rows_read} |",
        f"| Valid rows | {result.valid_rows} |",
        f"| Invalid rows | {result.invalid_rows} |",
        f"| Current pricing records read | {result.current_records_read} |",
        f"| Duplicate material keys | {len(result.duplicate_material_keys)} |",
        f"| Missing required field rows | {len(result.missing_required_fields)} |",
        f"| Price format issue rows | {len(result.price_format_issues)} |",
        f"| Materials that would be added | {len(result.would_be_added)} |",
        f"| Materials that would be updated | {len(result.would_be_updated)} |",
        f"| Materials that would be unchanged | {len(result.would_be_unchanged)} |",
        "",
        _duplicate_section(result.duplicate_material_keys),
        _missing_fields_section(result.missing_required_fields),
        _price_issues_section(result.price_format_issues),
        _pricing_change_section("Materials That Would Be Added", result.would_be_added),
        _pricing_change_section("Materials That Would Be Updated", result.would_be_updated),
        _pricing_change_section("Materials That Would Be Unchanged", result.would_be_unchanged),
        "## Safety Notes",
        "",
        "- This command writes only this preview report.",
        "- This command does not import rows into live JSON.",
        "- This command does not modify production pricing data.",
        "- Keep real owner pricing CSV files outside Git-tracked sample paths.",
        "",
    ]
    return "\n".join(lines)


def build_sandbox_apply_plan(
    result: OwnerPricingDryRunResult,
    plan_path: str,
    dry_run_report_info: Optional[Dict[str, Any]] = None,
    plan_json_path: Optional[str] = None,
    generated_at: Optional[str] = None,
) -> str:
    generated_at = generated_at or _generated_timestamp()
    warnings = _sandbox_warnings(result)
    skipped_rows = _skipped_rows(result)
    checklist = _confirmation_checklist()

    lines = [
        "# Owner Pricing Sandbox Apply Plan",
        "",
        "Sandbox plan only. This file is not an import result and does not mutate live pricing data.",
        "",
        "## Plan Metadata",
        "",
        f"- Generated at: `{generated_at}`",
        f"- Source CSV path: `{result.source_csv}`",
        f"- Baseline pricing path: `{result.current_pricing or 'not provided'}`",
        f"- Dry-run report reference: `{_dry_run_report_label(dry_run_report_info)}`",
        f"- Markdown sandbox output target: `{plan_path}`",
        f"- JSON sandbox output target: `{plan_json_path or 'not requested'}`",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Total rows read | {result.rows_read} |",
        f"| Valid rows | {result.valid_rows} |",
        f"| Invalid rows | {result.invalid_rows} |",
        f"| Duplicate keys | {len(result.duplicate_material_keys)} |",
        f"| Add candidates | {len(result.would_be_added)} |",
        f"| Update candidates | {len(result.would_be_updated)} |",
        f"| Unchanged rows | {len(result.would_be_unchanged)} |",
        f"| Skipped rows | {len(skipped_rows)} |",
        "",
        "## Warnings",
        "",
        *_bullet_lines(warnings),
        "",
        _duplicate_section(result.duplicate_material_keys),
        _pricing_change_section("Add Candidates", result.would_be_added),
        _pricing_change_section("Update Candidates", result.would_be_updated),
        _pricing_change_section("Unchanged Rows", result.would_be_unchanged),
        _skipped_rows_section(skipped_rows),
        "## Confirmation Checklist Before Any Future Apply",
        "",
        *_checklist_lines(checklist),
        "",
        "## Sandbox Boundaries",
        "",
        "- This plan does not import owner pricing into live JSON.",
        "- This plan does not update production pricing data.",
        "- This plan is intended for owner/G2 review before any future apply command exists.",
        "- Any future apply must use a separate reviewed command and an explicit sandbox output path.",
        "",
    ]
    return "\n".join(lines)


def build_sandbox_apply_plan_json(
    result: OwnerPricingDryRunResult,
    plan_path: str,
    dry_run_report_info: Optional[Dict[str, Any]] = None,
    plan_json_path: Optional[str] = None,
    generated_at: Optional[str] = None,
) -> Dict[str, Any]:
    generated_at = generated_at or _generated_timestamp()
    skipped_rows = _skipped_rows(result)

    return {
        "plan_type": "owner_pricing_sandbox_apply_plan",
        "dry_run_only": True,
        "generated_at": generated_at,
        "source_csv_path": result.source_csv,
        "baseline_pricing_path": result.current_pricing,
        "dry_run_report": dry_run_report_info,
        "sandbox_output_target": {
            "markdown": plan_path,
            "json": plan_json_path,
        },
        "summary": {
            "total_rows_read": result.rows_read,
            "valid_rows": result.valid_rows,
            "invalid_rows": result.invalid_rows,
            "duplicate_keys": len(result.duplicate_material_keys),
            "add_candidates": len(result.would_be_added),
            "update_candidates": len(result.would_be_updated),
            "unchanged_rows": len(result.would_be_unchanged),
            "skipped_rows": len(skipped_rows),
        },
        "warnings": _sandbox_warnings(result),
        "duplicate_material_keys": [
            {
                "material_key": issue.material_key,
                "rows": issue.rows,
            }
            for issue in result.duplicate_material_keys
        ],
        "add_candidates": [_change_to_dict(change) for change in result.would_be_added],
        "update_candidates": [_change_to_dict(change) for change in result.would_be_updated],
        "unchanged_rows": [_change_to_dict(change) for change in result.would_be_unchanged],
        "skipped_rows": skipped_rows,
        "confirmation_checklist": _confirmation_checklist(),
        "sandbox_boundaries": [
            "No live JSON mutation.",
            "No production pricing mutation.",
            "No import/apply command is executed by this plan.",
        ],
    }


def build_sandbox_apply_output_json(
    result: OwnerPricingDryRunResult,
    current_pricing: Dict[str, CurrentPricingRow],
    sandbox_output_path: str,
    sandbox_apply_plan_info: Optional[Dict[str, Any]] = None,
    generated_at: Optional[str] = None,
) -> Dict[str, Any]:
    generated_at = generated_at or _generated_timestamp()
    sandbox_materials, retained_baseline_materials = _build_sandbox_materials(
        current_pricing,
        result.would_be_added,
        result.would_be_updated,
        result.would_be_unchanged,
    )
    skipped_rows = _skipped_rows(result)

    return {
        "output_type": "owner_pricing_sandbox_apply_output",
        "sandbox_only": True,
        "sandbox_notice": (
            "Sandbox output only. This file is not production pricing data and "
            "final import remains disabled."
        ),
        "generated_at": generated_at,
        "source_csv_path": result.source_csv,
        "baseline_pricing_path": result.current_pricing,
        "sandbox_apply_plan": sandbox_apply_plan_info,
        "sandbox_pricing_output_path": sandbox_output_path,
        "live_json_mutated": False,
        "production_pricing_mutated": False,
        "final_import_enabled": False,
        "summary": {
            "total_rows_read": result.rows_read,
            "valid_rows_applied": result.valid_rows,
            "invalid_rows_skipped": result.invalid_rows,
            "duplicate_keys": len(result.duplicate_material_keys),
            "added_materials": len(result.would_be_added),
            "updated_materials": len(result.would_be_updated),
            "unchanged_materials": len(result.would_be_unchanged),
            "retained_baseline_materials": len(retained_baseline_materials),
            "skipped_rows": len(skipped_rows),
            "sandbox_materials_written": len(sandbox_materials),
        },
        "warnings": _sandbox_output_warnings(result),
        "materials": sandbox_materials,
        "added_materials": [_change_to_dict(change) for change in result.would_be_added],
        "updated_materials": [_change_to_dict(change) for change in result.would_be_updated],
        "unchanged_materials": [_change_to_dict(change) for change in result.would_be_unchanged],
        "retained_baseline_materials": retained_baseline_materials,
        "skipped_rows": skipped_rows,
        "duplicate_material_keys": [
            {
                "material_key": issue.material_key,
                "rows": issue.rows,
            }
            for issue in result.duplicate_material_keys
        ],
        "sandbox_boundaries": [
            "No live JSON mutation.",
            "No production pricing mutation.",
            "Invalid rows are skipped.",
            "Duplicate material keys are skipped until owner/G2 review resolves them.",
            "Final import remains disabled.",
        ],
    }


def build_sandbox_apply_output_report(
    result: OwnerPricingDryRunResult,
    sandbox_output: Dict[str, Any],
    summary_report_path: str,
) -> str:
    summary = sandbox_output["summary"]

    lines = [
        "# Owner Pricing Sandbox Apply Output Summary",
        "",
        "Sandbox output only. This report is not production pricing data and final import remains disabled.",
        "",
        "## Output Metadata",
        "",
        f"- Generated at: `{sandbox_output['generated_at']}`",
        f"- Source CSV path: `{sandbox_output['source_csv_path']}`",
        f"- Baseline pricing path: `{sandbox_output['baseline_pricing_path'] or 'not provided'}`",
        f"- Sandbox apply plan reference: `{_sandbox_apply_plan_label(sandbox_output['sandbox_apply_plan'])}`",
        f"- Sandbox pricing output path: `{sandbox_output['sandbox_pricing_output_path']}`",
        f"- Summary report path: `{summary_report_path}`",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Total rows read | {summary['total_rows_read']} |",
        f"| Valid rows applied | {summary['valid_rows_applied']} |",
        f"| Invalid rows skipped | {summary['invalid_rows_skipped']} |",
        f"| Duplicate keys | {summary['duplicate_keys']} |",
        f"| Added materials | {summary['added_materials']} |",
        f"| Updated materials | {summary['updated_materials']} |",
        f"| Unchanged materials | {summary['unchanged_materials']} |",
        f"| Retained baseline materials | {summary['retained_baseline_materials']} |",
        f"| Skipped rows | {summary['skipped_rows']} |",
        f"| Sandbox materials written | {summary['sandbox_materials_written']} |",
        "",
        "## Warnings",
        "",
        *_bullet_lines(sandbox_output["warnings"]),
        "",
        _duplicate_section(result.duplicate_material_keys),
        _pricing_change_section("Added Materials", result.would_be_added),
        _pricing_change_section("Updated Materials", result.would_be_updated),
        _pricing_change_section("Unchanged Materials", result.would_be_unchanged),
        _retained_baseline_section(sandbox_output["retained_baseline_materials"]),
        _skipped_rows_section(sandbox_output["skipped_rows"]),
        "## Sandbox Boundaries",
        "",
        "- This output does not import owner pricing into live JSON.",
        "- This output does not update production pricing data.",
        "- Invalid rows and duplicate material keys are not applied into the sandbox output.",
        "- Owner approval and final import remain disabled until a separate G0-approved task exists.",
        "",
    ]
    return "\n".join(lines)


def build_sandbox_apply_output_summary_json(
    sandbox_output: Dict[str, Any],
    summary_json_path: str,
) -> Dict[str, Any]:
    return {
        "summary_type": "owner_pricing_sandbox_apply_output_summary",
        "sandbox_only": True,
        "generated_at": sandbox_output["generated_at"],
        "source_csv_path": sandbox_output["source_csv_path"],
        "baseline_pricing_path": sandbox_output["baseline_pricing_path"],
        "sandbox_apply_plan": sandbox_output["sandbox_apply_plan"],
        "sandbox_pricing_output_path": sandbox_output["sandbox_pricing_output_path"],
        "summary_json_path": summary_json_path,
        "summary": sandbox_output["summary"],
        "warnings": sandbox_output["warnings"],
        "duplicate_material_keys": sandbox_output["duplicate_material_keys"],
        "skipped_rows": sandbox_output["skipped_rows"],
        "sandbox_boundaries": sandbox_output["sandbox_boundaries"],
    }


def build_owner_pricing_approval_record_json(
    sandbox_output: Dict[str, Any],
    sandbox_output_path: str,
    sandbox_output_sha256: str,
    owner_approval: str,
    approved_by: str,
    sandbox_apply_plan_info: Optional[Dict[str, Any]] = None,
    dry_run_report_info: Optional[Dict[str, Any]] = None,
    generated_at: Optional[str] = None,
) -> Dict[str, Any]:
    generated_at = generated_at or _generated_timestamp()

    return {
        "approval_type": "owner_pricing_sandbox_output_approval",
        "sandbox_only": True,
        "approval_notice": (
            "Manual owner approval record only. This does not enable final import "
            "and does not mutate live or production pricing data."
        ),
        "generated_at": generated_at,
        "approved_by": approved_by or "local owner / manual owner",
        "approval_phrase_used": owner_approval,
        "expected_approval_phrase": OWNER_PRICING_APPROVAL_PHRASE,
        "sandbox_output": {
            "path": sandbox_output_path,
            "sha256": sandbox_output_sha256,
            "output_type": sandbox_output.get("output_type"),
            "generated_at": sandbox_output.get("generated_at"),
            "source_csv_path": sandbox_output.get("source_csv_path"),
            "baseline_pricing_path": sandbox_output.get("baseline_pricing_path"),
            "summary": sandbox_output.get("summary", {}),
        },
        "sandbox_apply_plan": sandbox_apply_plan_info,
        "dry_run_report": dry_run_report_info,
        "final_import_enabled": False,
        "live_json_mutated": False,
        "production_pricing_mutated": False,
        "warnings": [
            "This approval record is file-based and traceable, but it is not a production import.",
            "Final import remains disabled until a separate G0-approved task exists.",
            "Keep real owner pricing CSV and local approval records outside Git-tracked paths.",
        ],
        "checklist": _approval_checklist(),
    }


def build_owner_pricing_approval_record_markdown(
    approval_record: Dict[str, Any],
    markdown_summary_path: str,
) -> str:
    sandbox_output = approval_record["sandbox_output"]
    summary = sandbox_output.get("summary", {})

    lines = [
        "# Owner Pricing Approval Record Summary",
        "",
        "Manual owner approval record only. This does not enable final import or mutate production pricing data.",
        "",
        "## Approval Metadata",
        "",
        f"- Generated at: `{approval_record['generated_at']}`",
        f"- Approved by: `{approval_record['approved_by']}`",
        f"- Approval phrase used: `{approval_record['approval_phrase_used']}`",
        f"- Sandbox output path: `{sandbox_output['path']}`",
        f"- Sandbox output SHA-256: `{sandbox_output['sha256']}`",
        f"- Sandbox apply plan: `{_sandbox_apply_plan_label(approval_record['sandbox_apply_plan'])}`",
        f"- Dry-run report: `{_dry_run_report_label(approval_record['dry_run_report'])}`",
        f"- Markdown summary path: `{markdown_summary_path}`",
        "",
        "## Sandbox Output Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Added materials | {summary.get('added_materials', 0)} |",
        f"| Updated materials | {summary.get('updated_materials', 0)} |",
        f"| Unchanged materials | {summary.get('unchanged_materials', 0)} |",
        f"| Invalid rows skipped | {summary.get('invalid_rows_skipped', 0)} |",
        f"| Duplicate keys | {summary.get('duplicate_keys', 0)} |",
        f"| Sandbox materials written | {summary.get('sandbox_materials_written', 0)} |",
        "",
        "## Warnings",
        "",
        *_bullet_lines(approval_record["warnings"]),
        "",
        "## Checklist",
        "",
        *_checklist_lines(approval_record["checklist"]),
        "",
        "## Safety Boundaries",
        "",
        "- final_import_enabled: false",
        "- live_json_mutated: false",
        "- production_pricing_mutated: false",
        "",
    ]
    return "\n".join(lines)


def build_owner_pricing_preflight_json(
    passed: bool,
    generated_at: str,
    sandbox_output_path: str,
    sandbox_output_sha256: str,
    approval_record_path: str,
    approval_record_sha256: str,
    production_target_path: str,
    production_target_sha256: str,
    production_records_read: int,
    backup_output_path: str,
    report_path: str,
    report_json_path: Optional[str],
    validation_results: List[Dict[str, Any]],
    blockers: List[str],
    warnings: List[str],
) -> Dict[str, Any]:
    return {
        "preflight_type": "owner_pricing_final_import_preflight",
        "status": "PASS" if passed else "FAIL",
        "generated_at": generated_at,
        "checked_paths": {
            "sandbox_output": sandbox_output_path,
            "approval_record": approval_record_path,
            "production_target": production_target_path,
            "backup_output": backup_output_path,
            "report": report_path,
            "report_json": report_json_path,
        },
        "checksums": {
            "sandbox_output_sha256": sandbox_output_sha256,
            "approval_record_sha256": approval_record_sha256,
            "production_target_sha256": production_target_sha256,
        },
        "production_records_read": production_records_read,
        "expected_backup_path": backup_output_path,
        "validation_results": validation_results,
        "blockers": blockers,
        "warnings": warnings,
        "final_import_command_invoked": False,
        "production_write_performed": False,
        "live_json_mutated": False,
        "production_pricing_mutated": False,
        "backup_written": False,
        "next_safe_step": (
            "Proceed to G2/G0 review of this preflight report; final import remains disabled."
            if passed
            else "Resolve blockers and rerun preflight; do not run final import."
        ),
    }


def build_owner_pricing_preflight_report(preflight: Dict[str, Any]) -> str:
    lines = [
        "# Owner Pricing Final Import Preflight Report",
        "",
        "Preflight report only. No production write was performed.",
        "",
        "## Status",
        "",
        f"- Result: `{preflight['status']}`",
        f"- Generated at: `{preflight['generated_at']}`",
        f"- Next safe step: {preflight['next_safe_step']}",
        "",
        "## Checked Paths",
        "",
        f"- Sandbox output: `{preflight['checked_paths']['sandbox_output']}`",
        f"- Approval record: `{preflight['checked_paths']['approval_record']}`",
        f"- Production target: `{preflight['checked_paths']['production_target']}`",
        f"- Expected backup path: `{preflight['checked_paths']['backup_output']}`",
        f"- Markdown report: `{preflight['checked_paths']['report']}`",
        f"- JSON report: `{preflight['checked_paths']['report_json'] or 'not requested'}`",
        "",
        "## Checksums",
        "",
        f"- Sandbox output SHA-256: `{preflight['checksums']['sandbox_output_sha256']}`",
        f"- Approval record SHA-256: `{preflight['checksums']['approval_record_sha256']}`",
        f"- Production target SHA-256: `{preflight['checksums']['production_target_sha256']}`",
        "",
        "## Validation Results",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for item in preflight["validation_results"]:
        lines.append(
            f"| {item['check']} | {item['status']} | {item['detail']} |"
        )

    lines.extend(
        [
            "",
            "## Blockers",
            "",
            *_bullet_lines(preflight["blockers"]),
            "",
            "## Warnings",
            "",
            *_bullet_lines(preflight["warnings"]),
            "",
            "## Safety Statement",
            "",
            "- No final import command was invoked.",
            "- No production write was performed.",
            "- No live JSON was mutated.",
            "- No production pricing data was mutated.",
            "- Backup path was validated only; backup was not written.",
            "",
        ]
    )
    return "\n".join(lines)


def build_owner_pricing_fake_rehearsal_audit(
    generated_at: str,
    sandbox_output_path: str,
    approval_record_path: str,
    preflight_report_path: str,
    fake_production_target_path: str,
    fake_production_output_path: str,
    backup_output_path: str,
    audit_log_path: str,
    report_path: str,
    sandbox_output_sha256: str,
    approval_record_sha256: str,
    preflight_report_sha256: str,
    pre_import_production_sha256: str,
) -> Dict[str, Any]:
    return {
        "audit_type": "owner_pricing_final_import_fake_rehearsal",
        "schema_version": 1,
        "fake_fixture_only": True,
        "status": "started",
        "generated_at": generated_at,
        "command": {
            "name": "asset-factory owner-pricing-final-import-fake-rehearsal",
            "reserved_production_command": "asset-factory owner-pricing-final-import",
            "production_command_invoked": False,
        },
        "paths": {
            "sandbox_output": sandbox_output_path,
            "approval_record": approval_record_path,
            "preflight_report": preflight_report_path,
            "fake_production_target": fake_production_target_path,
            "fake_production_output": fake_production_output_path,
            "backup_output": backup_output_path,
            "audit_log": audit_log_path,
            "report": report_path,
        },
        "checksums": {
            "sandbox_output_sha256": sandbox_output_sha256,
            "approval_record_sha256": approval_record_sha256,
            "preflight_report_sha256": preflight_report_sha256,
            "pre_import_fake_production_sha256": pre_import_production_sha256,
            "backup_sha256": None,
            "post_write_fake_production_sha256": None,
            "restored_fake_production_sha256": None,
        },
        "validation_results": [],
        "post_write_validation_results": [],
        "restore_validation_results": [],
        "state_history": [],
        "safety_flags": {
            "production_write_performed": False,
            "fake_production_write_performed": False,
            "backup_written": False,
            "backup_written_to_fake_path": False,
            "live_json_mutated": False,
            "production_pricing_mutated": False,
        },
        "rollback": {
            "required": False,
            "executed": False,
            "restore_verified": False,
        },
        "blockers": [],
        "warnings": [],
        "next_safe_step": "Review fake rehearsal evidence; real final import remains blocked.",
    }


def build_owner_pricing_fake_rehearsal_report(audit: Dict[str, Any]) -> str:
    lines = [
        "# Owner Pricing Final Import Fake Rehearsal Report",
        "",
        "Fake-fixture-only rehearsal. No real production import command was invoked.",
        "",
        "## Status",
        "",
        f"- Result: `{audit['status']}`",
        f"- Generated at: `{audit['generated_at']}`",
        f"- Next safe step: {audit['next_safe_step']}",
        "",
        "## Safety Statement",
        "",
        "- No `asset-factory owner-pricing-final-import` command was added or invoked.",
        "- No real production write was performed.",
        "- No live JSON was mutated.",
        "- No production pricing data was mutated.",
        "- Backup writing is limited to the explicit fake backup path.",
        "",
        "## Paths",
        "",
        f"- Sandbox output: `{audit['paths']['sandbox_output']}`",
        f"- Approval record: `{audit['paths']['approval_record']}`",
        f"- Preflight report: `{audit['paths']['preflight_report']}`",
        f"- Fake production target: `{audit['paths']['fake_production_target']}`",
        f"- Fake production output: `{audit['paths']['fake_production_output']}`",
        f"- Fake backup output: `{audit['paths']['backup_output']}`",
        f"- Audit log: `{audit['paths']['audit_log']}`",
        "",
        "## Checksums",
        "",
        f"- Sandbox output SHA-256: `{audit['checksums']['sandbox_output_sha256']}`",
        f"- Approval record SHA-256: `{audit['checksums']['approval_record_sha256']}`",
        f"- Preflight report SHA-256: `{audit['checksums']['preflight_report_sha256']}`",
        f"- Pre-import fake production SHA-256: `{audit['checksums']['pre_import_fake_production_sha256']}`",
        f"- Fake backup SHA-256: `{audit['checksums']['backup_sha256']}`",
        f"- Post-write fake production SHA-256: `{audit['checksums']['post_write_fake_production_sha256']}`",
        f"- Restored fake production SHA-256: `{audit['checksums']['restored_fake_production_sha256']}`",
        "",
        "## State History",
        "",
        "| Status | Detail |",
        "| --- | --- |",
    ]
    for item in audit["state_history"]:
        lines.append(f"| {item['status']} | {item['detail']} |")

    lines.extend(
        [
            "",
            "## Input Validation",
            "",
            "| Check | Status | Detail |",
            "| --- | --- | --- |",
        ]
    )
    for item in audit["validation_results"]:
        lines.append(f"| {item['check']} | {item['status']} | {item['detail']} |")

    lines.extend(
        [
            "",
            "## Post-write Validation",
            "",
            "| Check | Status | Detail |",
            "| --- | --- | --- |",
        ]
    )
    for item in audit["post_write_validation_results"]:
        lines.append(f"| {item['check']} | {item['status']} | {item['detail']} |")

    lines.extend(
        [
            "",
            "## Restore Validation",
            "",
            "| Check | Status | Detail |",
            "| --- | --- | --- |",
        ]
    )
    for item in audit["restore_validation_results"]:
        lines.append(f"| {item['check']} | {item['status']} | {item['detail']} |")

    lines.extend(
        [
            "",
            "## Blockers",
            "",
            *_bullet_lines(audit["blockers"]),
            "",
            "## Warnings",
            "",
            *_bullet_lines(audit["warnings"]),
            "",
        ]
    )
    return "\n".join(lines)


def _read_csv_rows(csv_path: str) -> List[Tuple[int, Dict[str, str]]]:
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return [(row_number, row) for row_number, row in enumerate(reader, start=2)]


def _clean_row(row: Dict[str, Any]) -> Dict[str, str]:
    return {
        str(key).strip(): "" if value is None else str(value).strip()
        for key, value in row.items()
        if key is not None
    }


def _normalize_key(material_key: str) -> str:
    return material_key.strip().lower()


def _parse_price(value: str) -> Tuple[Optional[Decimal], Optional[str]]:
    cleaned = value.strip()
    if not cleaned:
        return None, "blank unit_price"

    try:
        price = Decimal(cleaned)
    except InvalidOperation:
        return None, "unit_price must be a plain decimal number"

    if not price.is_finite():
        return None, "unit_price must be finite"

    if price < Decimal("0"):
        return None, "unit_price must not be negative"

    return price, None


def _find_duplicate_keys(rows: List[OwnerPricingRow]) -> List[DuplicateKeyIssue]:
    rows_by_key: Dict[str, List[int]] = {}
    display_key_by_normalized_key: Dict[str, str] = {}
    for row in rows:
        normalized_key = _normalize_key(row.material_key)
        rows_by_key.setdefault(normalized_key, []).append(row.row_number)
        display_key_by_normalized_key.setdefault(normalized_key, row.material_key)

    duplicate_issues = []
    for normalized_key, row_numbers in rows_by_key.items():
        if len(row_numbers) > 1:
            duplicate_issues.append(
                DuplicateKeyIssue(
                    material_key=display_key_by_normalized_key[normalized_key],
                    rows=row_numbers,
                )
            )

    return sorted(duplicate_issues, key=lambda issue: issue.material_key)


def _load_current_pricing(
    current_pricing_path: Optional[str],
) -> Dict[str, CurrentPricingRow]:
    if not current_pricing_path:
        return {}

    extension = os.path.splitext(current_pricing_path)[1].lower()
    if extension == ".csv":
        return _load_current_pricing_csv(current_pricing_path)
    if extension == ".json":
        return _load_current_pricing_json(current_pricing_path)

    raise ValueError("current pricing snapshot must be a CSV or JSON file")


def _load_current_pricing_csv(current_pricing_path: str) -> Dict[str, CurrentPricingRow]:
    records: Dict[str, CurrentPricingRow] = {}
    with open(current_pricing_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            cleaned = _clean_row(row)
            record = _current_record_from_mapping(cleaned)
            if record:
                records[_normalize_key(record.material_key)] = record
    return records


def _load_current_pricing_json(current_pricing_path: str) -> Dict[str, CurrentPricingRow]:
    with open(current_pricing_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    records: Dict[str, CurrentPricingRow] = {}
    for material_key, item in _iter_json_materials(data):
        if not isinstance(item, dict):
            continue
        cleaned = _clean_row(item)
        if material_key and not cleaned.get("material_key"):
            cleaned["material_key"] = material_key
        record = _current_record_from_mapping(cleaned)
        if record:
            records[_normalize_key(record.material_key)] = record
    return records


def _iter_json_materials(data: Any):
    if isinstance(data, list):
        for item in data:
            yield None, item
    elif isinstance(data, dict) and isinstance(data.get("materials"), list):
        for item in data["materials"]:
            yield None, item
    elif isinstance(data, dict):
        for material_key, item in data.items():
            yield material_key, item


def _current_record_from_mapping(data: Dict[str, str]) -> Optional[CurrentPricingRow]:
    material_key = data.get("material_key", "")
    price_value = data.get("unit_price", data.get("price", ""))
    price, price_issue = _parse_price(price_value)
    if not material_key or price_issue:
        return None

    return CurrentPricingRow(
        material_key=material_key,
        material_name=data.get("material_name", ""),
        unit=data.get("unit", ""),
        unit_price=price,
    )


def _compare_rows(
    rows: List[OwnerPricingRow],
    current_pricing: Dict[str, CurrentPricingRow],
) -> Tuple[List[PricingChange], List[PricingChange], List[PricingChange]]:
    would_be_added: List[PricingChange] = []
    would_be_updated: List[PricingChange] = []
    would_be_unchanged: List[PricingChange] = []

    for row in rows:
        current = current_pricing.get(_normalize_key(row.material_key))
        if current is None:
            would_be_added.append(
                PricingChange(
                    material_key=row.material_key,
                    material_name=row.material_name,
                    unit=row.unit,
                    new_price=row.unit_price,
                )
            )
            continue

        changed_fields = _changed_fields(row, current)
        change = PricingChange(
            material_key=row.material_key,
            material_name=row.material_name,
            unit=row.unit,
            new_price=row.unit_price,
            current_price=current.unit_price,
            changed_fields=changed_fields,
        )
        if changed_fields:
            would_be_updated.append(change)
        else:
            would_be_unchanged.append(change)

    return (
        sorted(would_be_added, key=lambda item: item.material_key),
        sorted(would_be_updated, key=lambda item: item.material_key),
        sorted(would_be_unchanged, key=lambda item: item.material_key),
    )


def _changed_fields(row: OwnerPricingRow, current: CurrentPricingRow) -> List[str]:
    changed_fields = []
    if row.material_name != current.material_name:
        changed_fields.append("material_name")
    if row.unit != current.unit:
        changed_fields.append("unit")
    if row.unit_price != current.unit_price:
        changed_fields.append("unit_price")
    return changed_fields


def _duplicate_section(issues: List[DuplicateKeyIssue]) -> str:
    lines = [
        "## Duplicate Material Keys",
        "",
    ]
    if not issues:
        lines.extend(["None.", ""])
        return "\n".join(lines)

    lines.extend(["| Material key | CSV rows |", "| --- | --- |"])
    for issue in issues:
        lines.append(f"| `{issue.material_key}` | {', '.join(map(str, issue.rows))} |")
    lines.append("")
    return "\n".join(lines)


def _missing_fields_section(issues: List[MissingFieldIssue]) -> str:
    lines = [
        "## Missing Required Fields",
        "",
    ]
    if not issues:
        lines.extend(["None.", ""])
        return "\n".join(lines)

    lines.extend(["| CSV row | Material key | Missing fields |", "| ---: | --- | --- |"])
    for issue in issues:
        lines.append(
            f"| {issue.row_number} | `{issue.material_key or '(blank)'}` | "
            f"{', '.join(issue.fields)} |"
        )
    lines.append("")
    return "\n".join(lines)


def _price_issues_section(issues: List[PriceIssue]) -> str:
    lines = [
        "## Price Format Issues",
        "",
    ]
    if not issues:
        lines.extend(["None.", ""])
        return "\n".join(lines)

    lines.extend(["| CSV row | Material key | Value | Issue |", "| ---: | --- | --- | --- |"])
    for issue in issues:
        lines.append(
            f"| {issue.row_number} | `{issue.material_key or '(blank)'}` | "
            f"`{issue.value}` | {issue.issue} |"
        )
    lines.append("")
    return "\n".join(lines)


def _pricing_change_section(title: str, changes: List[PricingChange]) -> str:
    lines = [
        f"## {title}",
        "",
    ]
    if not changes:
        lines.extend(["None.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "| Material key | Material name | Unit | Current price | New price | Changed fields |",
            "| --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    for change in changes:
        current_price = (
            _format_decimal(change.current_price)
            if change.current_price is not None
            else "-"
        )
        changed_fields = ", ".join(change.changed_fields or [])
        lines.append(
            f"| `{change.material_key}` | {change.material_name} | {change.unit} | "
            f"{current_price} | {_format_decimal(change.new_price)} | {changed_fields or '-'} |"
        )
    lines.append("")
    return "\n".join(lines)


def _retained_baseline_section(materials: List[Dict[str, Any]]) -> str:
    lines = [
        "## Retained Baseline Materials",
        "",
    ]
    if not materials:
        lines.extend(["None.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "| Material key | Material name | Unit | Unit price |",
            "| --- | --- | --- | ---: |",
        ]
    )
    for material in materials:
        lines.append(
            f"| `{material['material_key']}` | {material['material_name']} | "
            f"{material['unit']} | {material['unit_price']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _build_sandbox_materials(
    current_pricing: Dict[str, CurrentPricingRow],
    added: List[PricingChange],
    updated: List[PricingChange],
    unchanged: List[PricingChange],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    materials_by_key = {
        normalized_key: _current_row_to_material(record)
        for normalized_key, record in current_pricing.items()
    }

    for change in added:
        materials_by_key[_normalize_key(change.material_key)] = _change_to_material(
            change,
            sandbox_status="added",
        )

    for change in updated:
        materials_by_key[_normalize_key(change.material_key)] = _change_to_material(
            change,
            sandbox_status="updated",
        )

    for change in unchanged:
        materials_by_key[_normalize_key(change.material_key)] = _change_to_material(
            change,
            sandbox_status="unchanged",
        )

    materials = sorted(
        materials_by_key.values(),
        key=lambda item: item["material_key"],
    )
    retained_baseline_materials = [
        material
        for material in materials
        if material["sandbox_status"] == "baseline_retained"
    ]
    return materials, retained_baseline_materials


def _current_row_to_material(record: CurrentPricingRow) -> Dict[str, Any]:
    return {
        "material_key": record.material_key,
        "material_name": record.material_name,
        "unit": record.unit,
        "unit_price": _format_decimal(record.unit_price),
        "sandbox_status": "baseline_retained",
        "changed_fields": [],
    }


def _change_to_material(change: PricingChange, sandbox_status: str) -> Dict[str, Any]:
    return {
        "material_key": change.material_key,
        "material_name": change.material_name,
        "unit": change.unit,
        "unit_price": _format_decimal(change.new_price),
        "sandbox_status": sandbox_status,
        "changed_fields": change.changed_fields or [],
    }


def _format_decimal(value: Decimal) -> str:
    return format(value, "f")


def _generated_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _validate_sandbox_output_path(
    path: str,
    overwrite: bool = False,
    output_kind: str = "sandbox apply plan output",
) -> None:
    if not path or not path.strip():
        raise ValueError(f"{output_kind} path is required")

    normalized_path = os.path.normpath(os.path.abspath(path))
    path_parts = {part.lower() for part in normalized_path.split(os.sep)}
    filename = os.path.basename(normalized_path).lower()

    if path_parts.intersection(LIVE_OUTPUT_PATH_PARTS) or filename in LIVE_OUTPUT_FILENAMES:
        raise ValueError(
            f"{output_kind} path appears to target live or production pricing data"
        )

    if os.path.exists(normalized_path) and not overwrite:
        raise FileExistsError(
            f"refusing to overwrite existing {output_kind} without --overwrite"
        )


def _validate_distinct_output_paths(paths: List[Tuple[str, Optional[str]]]) -> None:
    seen_paths: Dict[str, str] = {}
    for output_kind, path in paths:
        if not path:
            continue
        normalized_path = os.path.normcase(os.path.normpath(os.path.abspath(path)))
        if normalized_path in seen_paths:
            raise ValueError(
                f"{output_kind} path must be different from {seen_paths[normalized_path]}"
            )
        seen_paths[normalized_path] = output_kind


def _validate_readonly_pricing_path(
    path: str,
    path_kind: str,
    must_exist: bool,
) -> None:
    if not path or not path.strip():
        raise ValueError(f"{path_kind} path is required")

    normalized_path = os.path.normpath(os.path.abspath(path))
    path_parts = {part.lower() for part in normalized_path.split(os.sep)}
    if path_parts.intersection(LIVE_OUTPUT_PATH_PARTS):
        raise ValueError(f"{path_kind} path appears unsafe")

    extension = os.path.splitext(normalized_path)[1].lower()
    if extension not in {".csv", ".json"}:
        raise ValueError(f"{path_kind} must be a CSV or JSON file")

    if must_exist and not os.path.exists(normalized_path):
        raise FileNotFoundError(f"{path_kind} file does not exist")


def _validate_backup_output_path(path: str) -> None:
    _validate_sandbox_output_path(
        path,
        overwrite=False,
        output_kind="backup output",
    )


def _load_json_file_with_sha256(
    path: str,
    input_kind: str,
) -> Tuple[Dict[str, Any], str]:
    if not path or not path.strip():
        raise ValueError(f"{input_kind} path is required")
    normalized_path = os.path.normpath(os.path.abspath(path))
    if not os.path.exists(normalized_path):
        raise FileNotFoundError(f"{input_kind} file does not exist")
    if os.path.splitext(normalized_path)[1].lower() != ".json":
        raise ValueError(f"{input_kind} must be JSON")

    with open(normalized_path, "rb") as file:
        raw_content = file.read()

    try:
        data = json.loads(raw_content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{input_kind} must be JSON") from exc

    if not isinstance(data, dict):
        raise ValueError(f"{input_kind} JSON must be an object")

    return data, hashlib.sha256(raw_content).hexdigest()


def _file_sha256(path: str) -> str:
    with open(path, "rb") as file:
        return hashlib.sha256(file.read()).hexdigest()


def _build_preflight_validations(
    sandbox_output: Dict[str, Any],
    sandbox_output_path: str,
    sandbox_output_sha256: str,
    approval_record: Dict[str, Any],
    approval_record_path: str,
    production_target_path: str,
    production_records: Dict[str, CurrentPricingRow],
    backup_output_path: str,
) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    validation_results: List[Dict[str, Any]] = []
    blockers: List[str] = []
    warnings: List[str] = []

    _add_preflight_check(
        validation_results,
        blockers,
        "sandbox output is sandbox-only",
        sandbox_output.get("sandbox_only") is True,
        "sandbox_only is true",
        "sandbox output must declare sandbox_only true",
    )
    _add_preflight_check(
        validation_results,
        blockers,
        "final import remains disabled in sandbox output",
        sandbox_output.get("final_import_enabled") is False,
        "final_import_enabled is false",
        "sandbox output must declare final_import_enabled false",
    )
    _add_preflight_check(
        validation_results,
        blockers,
        "live JSON mutation flag remains false",
        sandbox_output.get("live_json_mutated") is False,
        "live_json_mutated is false",
        "sandbox output must declare live_json_mutated false",
    )
    _add_preflight_check(
        validation_results,
        blockers,
        "production pricing mutation flag remains false",
        sandbox_output.get("production_pricing_mutated") is False,
        "production_pricing_mutated is false",
        "sandbox output must declare production_pricing_mutated false",
    )

    approval_sandbox = approval_record.get("sandbox_output", {})
    approval_sha = approval_sandbox.get("sha256")
    _add_preflight_check(
        validation_results,
        blockers,
        "approval checksum matches sandbox output",
        approval_sha == sandbox_output_sha256,
        "approval checksum matches sandbox output bytes",
        "approval checksum does not match sandbox output bytes",
    )
    _add_preflight_check(
        validation_results,
        blockers,
        "approval record references intended sandbox output",
        _paths_match(approval_sandbox.get("path"), sandbox_output_path),
        "approval record references the intended sandbox output",
        "approval record does not reference the intended sandbox output",
    )
    _add_preflight_check(
        validation_results,
        blockers,
        "approval record final import flag remains false",
        approval_record.get("final_import_enabled") is False,
        "approval record final_import_enabled is false",
        "approval record must declare final_import_enabled false",
    )
    _add_preflight_check(
        validation_results,
        blockers,
        "approval record live JSON mutation flag remains false",
        approval_record.get("live_json_mutated") is False,
        "approval record live_json_mutated is false",
        "approval record must declare live_json_mutated false",
    )
    _add_preflight_check(
        validation_results,
        blockers,
        "approval record production pricing mutation flag remains false",
        approval_record.get("production_pricing_mutated") is False,
        "approval record production_pricing_mutated is false",
        "approval record must declare production_pricing_mutated false",
    )

    materials = sandbox_output.get("materials", [])
    material_keys = _material_keys(materials)
    duplicate_keys = sorted(
        key
        for key, count in _count_items(_normalize_key(key) for key in material_keys).items()
        if count > 1
    )
    _add_preflight_check(
        validation_results,
        blockers,
        "sandbox material keys are unique",
        not duplicate_keys,
        "sandbox material keys are unique",
        f"duplicate sandbox material keys: {', '.join(duplicate_keys)}",
    )

    skipped_material_keys = {
        _normalize_key(str(row.get("material_key", "")))
        for row in sandbox_output.get("skipped_rows", [])
        if row.get("material_key")
    }
    material_key_set = {_normalize_key(key) for key in material_keys}
    skipped_present = sorted(skipped_material_keys.intersection(material_key_set))
    _add_preflight_check(
        validation_results,
        blockers,
        "skipped invalid rows are not present in sandbox materials",
        not skipped_present,
        "skipped invalid rows are not present in materials",
        f"skipped invalid material keys appear in materials: {', '.join(skipped_present)}",
    )

    summary = sandbox_output.get("summary", {})
    status_counts = _sandbox_material_status_counts(materials)
    expected_counts = {
        "added_materials": status_counts.get("added", 0),
        "updated_materials": status_counts.get("updated", 0),
        "unchanged_materials": status_counts.get("unchanged", 0),
        "retained_baseline_materials": status_counts.get("baseline_retained", 0),
        "sandbox_materials_written": len(materials),
        "skipped_rows": len(sandbox_output.get("skipped_rows", [])),
    }
    mismatched_counts = [
        f"{field}: summary={summary.get(field)} actual={actual_count}"
        for field, actual_count in expected_counts.items()
        if summary.get(field) != actual_count
    ]
    _add_preflight_check(
        validation_results,
        blockers,
        "sandbox summary counts match materials",
        not mismatched_counts,
        "sandbox summary counts match material lists",
        "; ".join(mismatched_counts),
    )

    _add_preflight_check(
        validation_results,
        blockers,
        "production target was inspected read-only",
        True,
        f"read {len(production_records)} comparable production records",
        "",
    )
    _add_preflight_check(
        validation_results,
        blockers,
        "backup output path is available and not written",
        not os.path.exists(os.path.abspath(backup_output_path)),
        "backup path is available; no backup was written",
        "backup output path already exists",
    )
    _add_preflight_check(
        validation_results,
        blockers,
        "no final import command invoked",
        True,
        "preflight checker does not invoke final import",
        "",
    )
    _add_preflight_check(
        validation_results,
        blockers,
        "no production write occurred",
        True,
        "production target was read only",
        "",
    )

    if not production_records:
        warnings.append("Production target was readable but no comparable pricing records were parsed.")
    if approval_record.get("approval_type") != "owner_pricing_sandbox_output_approval":
        warnings.append("Approval record type is not the expected owner pricing sandbox approval type.")
    if approval_record_path and not approval_record.get("approved_by"):
        warnings.append("Approval record has no approved_by value.")

    return validation_results, blockers, warnings


def _add_preflight_check(
    validation_results: List[Dict[str, Any]],
    blockers: List[str],
    check: str,
    passed: bool,
    pass_detail: str,
    fail_detail: str,
) -> None:
    validation_results.append(
        {
            "check": check,
            "status": "PASS" if passed else "FAIL",
            "detail": pass_detail if passed else fail_detail,
        }
    )
    if not passed:
        blockers.append(fail_detail)


def _material_keys(materials: Any) -> List[str]:
    if not isinstance(materials, list):
        return []
    return [
        str(material.get("material_key", ""))
        for material in materials
        if isinstance(material, dict) and material.get("material_key")
    ]


def _sandbox_material_status_counts(materials: Any) -> Dict[str, int]:
    if not isinstance(materials, list):
        return {}
    return _count_items(
        str(material.get("sandbox_status", ""))
        for material in materials
        if isinstance(material, dict)
    )


def _count_items(items) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts


def _normalize_reference_path(path: str) -> str:
    native_path = path.replace("\\", os.sep).replace("/", os.sep)
    return os.path.normcase(os.path.normpath(os.path.abspath(native_path)))


def _paths_match(left: Optional[str], right: str) -> bool:
    if not left or not right:
        return False
    return _normalize_reference_path(left) == _normalize_reference_path(right)


def _validate_fake_rehearsal_input_path(
    path: str,
    path_kind: str,
    allowed_extensions: set,
) -> None:
    _validate_fake_rehearsal_path_shape(path, path_kind, allowed_extensions)
    normalized_path = os.path.normpath(os.path.abspath(path))
    if not os.path.exists(normalized_path):
        raise FileNotFoundError(f"{path_kind} file does not exist")


def _validate_fake_rehearsal_write_path(
    path: str,
    path_kind: str,
    allowed_extensions: set,
    overwrite: bool,
) -> None:
    _validate_fake_rehearsal_path_shape(path, path_kind, allowed_extensions)
    normalized_path = os.path.normpath(os.path.abspath(path))
    if os.path.exists(normalized_path) and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing {path_kind}")


def _validate_fake_rehearsal_path_shape(
    path: str,
    path_kind: str,
    allowed_extensions: set,
) -> None:
    if not path or not path.strip():
        raise ValueError(f"{path_kind} path is required")
    normalized_path = os.path.normpath(os.path.abspath(path))
    path_parts = {part.lower() for part in normalized_path.split(os.sep)}
    filename = os.path.basename(normalized_path).lower()
    if path_parts.intersection(LIVE_OUTPUT_PATH_PARTS) or filename in LIVE_OUTPUT_FILENAMES:
        raise ValueError(f"{path_kind} path appears unsafe")
    if not _path_has_fake_rehearsal_marker(normalized_path):
        raise ValueError(f"{path_kind} path must be a fake fixture or local output path")
    extension = os.path.splitext(normalized_path)[1].lower()
    if extension not in allowed_extensions:
        expected = ", ".join(sorted(allowed_extensions))
        raise ValueError(f"{path_kind} must use one of these extensions: {expected}")


def _path_has_fake_rehearsal_marker(path: str) -> bool:
    parts = [part.lower() for part in os.path.normpath(path).split(os.sep)]
    filename = os.path.basename(path).lower()
    if "fake" in filename:
        return True
    if any("fake" in part for part in parts):
        return True
    return bool(set(parts).intersection(FAKE_REHEARSAL_SAFE_PATH_PARTS))


def _build_fake_rehearsal_packet_validations(
    sandbox_output: Dict[str, Any],
    sandbox_output_path: str,
    sandbox_output_sha256: str,
    approval_record: Dict[str, Any],
    approval_record_path: str,
    approval_record_sha256: str,
    preflight_report: Dict[str, Any],
    preflight_report_path: str,
    fake_production_target_path: str,
    pre_import_production_sha256: str,
    backup_output_path: str,
) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    validation_results: List[Dict[str, Any]] = []
    blockers: List[str] = []
    warnings: List[str] = []

    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "sandbox output remains sandbox-only",
        sandbox_output.get("sandbox_only") is True,
        "sandbox_only is true",
        "sandbox output must declare sandbox_only true",
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "sandbox output final import remains disabled",
        sandbox_output.get("final_import_enabled") is False,
        "final_import_enabled is false",
        "sandbox output must declare final_import_enabled false",
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "sandbox output live JSON mutation flag remains false",
        sandbox_output.get("live_json_mutated") is False,
        "live_json_mutated is false",
        "sandbox output must declare live_json_mutated false",
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "sandbox output production mutation flag remains false",
        sandbox_output.get("production_pricing_mutated") is False,
        "production_pricing_mutated is false",
        "sandbox output must declare production_pricing_mutated false",
    )

    approval_sandbox = approval_record.get("sandbox_output", {})
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "approval record type is owner sandbox approval",
        approval_record.get("approval_type") == "owner_pricing_sandbox_output_approval",
        "approval record type is expected",
        "approval record type is not owner_pricing_sandbox_output_approval",
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "approval checksum matches sandbox output",
        approval_sandbox.get("sha256") == sandbox_output_sha256,
        "approval checksum matches sandbox output bytes",
        "approval checksum does not match sandbox output bytes",
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "approval record references intended sandbox output",
        _paths_match(approval_sandbox.get("path"), sandbox_output_path),
        "approval record references intended sandbox output",
        "approval record does not reference intended sandbox output",
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "approval record final import flag remains false",
        approval_record.get("final_import_enabled") is False,
        "approval final_import_enabled is false",
        "approval record must declare final_import_enabled false",
    )

    preflight_paths = preflight_report.get("checked_paths", {})
    preflight_checksums = preflight_report.get("checksums", {})
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "preflight report type is expected",
        preflight_report.get("preflight_type") == "owner_pricing_final_import_preflight",
        "preflight type is expected",
        "preflight report type is not owner_pricing_final_import_preflight",
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "preflight status is PASS",
        preflight_report.get("status") == "PASS",
        "preflight status is PASS",
        "preflight status is not PASS",
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "preflight references sandbox output",
        _paths_match(preflight_paths.get("sandbox_output"), sandbox_output_path),
        "preflight references intended sandbox output",
        "preflight does not reference intended sandbox output",
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "preflight references approval record",
        _paths_match(preflight_paths.get("approval_record"), approval_record_path),
        "preflight references intended approval record",
        "preflight does not reference intended approval record",
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "preflight references fake production target",
        _paths_match(preflight_paths.get("production_target"), fake_production_target_path),
        "preflight references intended fake production target",
        "preflight does not reference intended fake production target",
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "preflight references fake backup output",
        _paths_match(preflight_paths.get("backup_output"), backup_output_path),
        "preflight references intended fake backup output",
        "preflight does not reference intended fake backup output",
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "preflight sandbox checksum matches",
        preflight_checksums.get("sandbox_output_sha256") == sandbox_output_sha256,
        "preflight sandbox checksum matches",
        "preflight sandbox checksum does not match sandbox output bytes",
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "preflight approval checksum matches",
        preflight_checksums.get("approval_record_sha256") == approval_record_sha256,
        "preflight approval checksum matches",
        "preflight approval checksum does not match approval record bytes",
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "preflight production target checksum matches fake target",
        preflight_checksums.get("production_target_sha256") == pre_import_production_sha256,
        "preflight fake production checksum matches",
        "preflight production target checksum does not match fake target bytes",
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "preflight reports no production write",
        preflight_report.get("production_write_performed") is False,
        "preflight production_write_performed is false",
        "preflight must report production_write_performed false",
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "preflight reports no backup written",
        preflight_report.get("backup_written") is False,
        "preflight backup_written is false",
        "preflight must report backup_written false",
    )

    material_results, material_blockers = _validate_fake_rehearsal_material_packet(
        sandbox_output
    )
    validation_results.extend(material_results)
    blockers.extend(material_blockers)

    if preflight_report_path and preflight_report.get("status") == "PASS":
        warnings.extend(preflight_report.get("warnings", []))

    return validation_results, blockers, warnings


def _validate_fake_rehearsal_material_packet(
    sandbox_output: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    validation_results: List[Dict[str, Any]] = []
    blockers: List[str] = []
    materials = sandbox_output.get("materials", [])
    material_keys = _material_keys(materials)
    duplicate_keys = sorted(
        key
        for key, count in _count_items(_normalize_key(key) for key in material_keys).items()
        if count > 1
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "sandbox material keys are unique",
        not duplicate_keys,
        "sandbox material keys are unique",
        f"duplicate sandbox material keys: {', '.join(duplicate_keys)}",
    )

    skipped_material_keys = {
        _normalize_key(str(row.get("material_key", "")))
        for row in sandbox_output.get("skipped_rows", [])
        if row.get("material_key")
    }
    material_key_set = {_normalize_key(key) for key in material_keys}
    skipped_present = sorted(skipped_material_keys.intersection(material_key_set))
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "skipped invalid rows are absent from sandbox materials",
        not skipped_present,
        "skipped invalid rows are absent from materials",
        f"skipped invalid material keys appear in materials: {', '.join(skipped_present)}",
    )

    summary = sandbox_output.get("summary", {})
    status_counts = _sandbox_material_status_counts(materials)
    expected_counts = {
        "added_materials": status_counts.get("added", 0),
        "updated_materials": status_counts.get("updated", 0),
        "unchanged_materials": status_counts.get("unchanged", 0),
        "retained_baseline_materials": status_counts.get("baseline_retained", 0),
        "sandbox_materials_written": len(materials),
        "skipped_rows": len(sandbox_output.get("skipped_rows", [])),
    }
    mismatched_counts = [
        f"{field}: summary={summary.get(field)} actual={actual_count}"
        for field, actual_count in expected_counts.items()
        if summary.get(field) != actual_count
    ]
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        "sandbox summary counts match materials",
        not mismatched_counts,
        "sandbox summary counts match material lists",
        "; ".join(mismatched_counts),
    )
    return validation_results, blockers


def _add_fake_rehearsal_check(
    validation_results: List[Dict[str, Any]],
    blockers: List[str],
    check: str,
    passed: bool,
    pass_detail: str,
    fail_detail: str,
) -> None:
    validation_results.append(
        {
            "check": check,
            "status": "PASS" if passed else "FAIL",
            "detail": pass_detail if passed else fail_detail,
        }
    )
    if not passed:
        blockers.append(fail_detail)


def _append_fake_rehearsal_state(
    audit: Dict[str, Any],
    status: str,
    detail: str,
) -> None:
    audit["state_history"].append(
        {
            "status": status,
            "at": _generated_timestamp(),
            "detail": detail,
        }
    )
    if status == "rollback_required":
        audit["rollback"]["required"] = True
    if status in {"rollback_passed", "rollback_failed"}:
        audit["rollback"]["executed"] = True
    if status == "rollback_passed":
        audit["rollback"]["restore_verified"] = True


def _finalize_fake_rehearsal(
    audit: Dict[str, Any],
    audit_log_path: str,
    report_path: str,
    status: str,
    blockers: List[str],
    detail: str,
) -> None:
    audit["status"] = status
    audit["blockers"] = blockers
    _append_fake_rehearsal_state(audit, status, detail)
    _write_json_file(audit_log_path, audit)
    _write_text_file(report_path, build_owner_pricing_fake_rehearsal_report(audit))


def _sandbox_materials_for_fake_rehearsal(
    sandbox_output: Dict[str, Any],
) -> List[Dict[str, str]]:
    materials: List[Dict[str, str]] = []
    for material in sandbox_output.get("materials", []):
        if not isinstance(material, dict):
            continue
        materials.append(
            {
                "material_key": str(material.get("material_key", "")),
                "material_name": str(material.get("material_name", "")),
                "unit": str(material.get("unit", "")),
                "unit_price": str(material.get("unit_price", "")),
            }
        )
    return materials


def _write_fake_pricing_output(path: str, materials: List[Dict[str, str]]) -> None:
    output_dir = os.path.dirname(os.path.abspath(path))
    os.makedirs(output_dir, exist_ok=True)
    extension = os.path.splitext(path)[1].lower()
    if extension == ".csv":
        with open(path, "w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(REQUIRED_OWNER_PRICING_FIELDS))
            writer.writeheader()
            for material in materials:
                writer.writerow({field: material.get(field, "") for field in REQUIRED_OWNER_PRICING_FIELDS})
        return
    if extension == ".json":
        _write_json_file(path, {"materials": materials})
        return
    raise ValueError("fake production output must be CSV or JSON")


def _validate_fake_rehearsal_written_output(
    output_path: str,
    expected_materials: List[Dict[str, str]],
    skipped_rows: List[Dict[str, Any]],
    validation_label: str,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    rows = _read_pricing_rows_for_fake_validation(output_path)
    expected_keys = {
        _normalize_key(str(material.get("material_key", "")))
        for material in expected_materials
        if material.get("material_key")
    }
    skipped_keys = {
        _normalize_key(str(row.get("material_key", "")))
        for row in skipped_rows
        if row.get("material_key")
    }
    return _validate_fake_rehearsal_rows(
        rows=rows,
        expected_count=len(expected_materials),
        expected_keys=expected_keys,
        skipped_keys=skipped_keys,
        validation_label=validation_label,
    )


def _validate_fake_rehearsal_restored_output(
    output_path: str,
    expected_records: Dict[str, CurrentPricingRow],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    rows = _read_pricing_rows_for_fake_validation(output_path)
    expected_keys = set(expected_records.keys())
    return _validate_fake_rehearsal_rows(
        rows=rows,
        expected_count=len(expected_records),
        expected_keys=expected_keys,
        skipped_keys=set(),
        validation_label="restored fake production output",
    )


def _validate_fake_rehearsal_rows(
    rows: List[Dict[str, str]],
    expected_count: int,
    expected_keys: set,
    skipped_keys: set,
    validation_label: str,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    validation_results: List[Dict[str, Any]] = []
    blockers: List[str] = []
    row_keys = [
        _normalize_key(str(row.get("material_key", "")))
        for row in rows
        if row.get("material_key")
    ]
    row_key_set = set(row_keys)
    duplicate_keys = sorted(
        key for key, count in _count_items(row_keys).items() if count > 1
    )
    invalid_rows = [
        row.get("material_key", "")
        for row in rows
        if _current_record_from_mapping(row) is None
    ]
    skipped_present = sorted(row_key_set.intersection(skipped_keys))

    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        f"{validation_label} material count matches",
        len(rows) == expected_count,
        f"material count is {expected_count}",
        f"material count mismatch: expected={expected_count} actual={len(rows)}",
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        f"{validation_label} material keys match",
        row_key_set == expected_keys,
        "material keys match expected set",
        "material keys do not match expected set",
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        f"{validation_label} material keys are unique",
        not duplicate_keys,
        "material keys are unique",
        f"duplicate material keys: {', '.join(duplicate_keys)}",
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        f"{validation_label} has no skipped invalid rows",
        not skipped_present,
        "skipped invalid rows are absent",
        f"skipped invalid material keys appear in output: {', '.join(skipped_present)}",
    )
    _add_fake_rehearsal_check(
        validation_results,
        blockers,
        f"{validation_label} schema is valid",
        not invalid_rows,
        "schema is valid",
        f"invalid material rows: {', '.join(invalid_rows)}",
    )
    return validation_results, blockers


def _read_pricing_rows_for_fake_validation(path: str) -> List[Dict[str, str]]:
    extension = os.path.splitext(path)[1].lower()
    if extension == ".csv":
        with open(path, "r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            return [_clean_row(row) for row in reader]
    if extension == ".json":
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        rows: List[Dict[str, str]] = []
        for material_key, item in _iter_json_materials(data):
            if not isinstance(item, dict):
                continue
            cleaned = _clean_row(item)
            if material_key and not cleaned.get("material_key"):
                cleaned["material_key"] = material_key
            rows.append(cleaned)
        return rows
    raise ValueError("fake pricing validation input must be CSV or JSON")


def _load_validated_sandbox_output(sandbox_output_path: str) -> Tuple[Dict[str, Any], str]:
    if not sandbox_output_path or not sandbox_output_path.strip():
        raise ValueError("sandbox output path is required")

    normalized_path = os.path.normpath(os.path.abspath(sandbox_output_path))
    if not os.path.exists(normalized_path):
        raise FileNotFoundError("sandbox output file does not exist")

    if os.path.splitext(normalized_path)[1].lower() != ".json":
        raise ValueError("sandbox output must be JSON")

    with open(normalized_path, "rb") as file:
        raw_content = file.read()

    try:
        sandbox_output = json.loads(raw_content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("sandbox output must be JSON") from exc

    if not isinstance(sandbox_output, dict):
        raise ValueError("sandbox output JSON must be an object")
    if sandbox_output.get("sandbox_only") is not True:
        raise ValueError("sandbox output must declare sandbox_only true")
    if sandbox_output.get("final_import_enabled") is True:
        raise ValueError("sandbox output must not enable final import")
    if sandbox_output.get("live_json_mutated") is True:
        raise ValueError("sandbox output must not declare live JSON mutation")
    if sandbox_output.get("production_pricing_mutated") is True:
        raise ValueError("sandbox output must not declare production pricing mutation")

    return sandbox_output, hashlib.sha256(raw_content).hexdigest()


def _validate_owner_approval_phrase(owner_approval: str) -> None:
    if not owner_approval or not owner_approval.strip():
        raise ValueError("owner approval phrase is required")
    if owner_approval.strip() != OWNER_PRICING_APPROVAL_PHRASE:
        raise ValueError("owner approval phrase is incorrect")


def _read_optional_dry_run_report(path: Optional[str]) -> Optional[Dict[str, Any]]:
    if not path:
        return None

    with open(path, "r", encoding="utf-8") as file:
        content = file.read()

    return {
        "path": path,
        "bytes_read": len(content.encode("utf-8")),
    }


def _read_optional_sandbox_apply_plan(path: Optional[str]) -> Optional[Dict[str, Any]]:
    if not path:
        return None

    with open(path, "r", encoding="utf-8") as file:
        content = file.read()

    return {
        "path": path,
        "bytes_read": len(content.encode("utf-8")),
    }


def _dry_run_report_label(info: Optional[Dict[str, Any]]) -> str:
    if not info:
        return "not provided"
    return f"{info['path']} ({info['bytes_read']} bytes read)"


def _sandbox_apply_plan_label(info: Optional[Dict[str, Any]]) -> str:
    if not info:
        return "not provided"
    return f"{info['path']} ({info['bytes_read']} bytes read)"


def _sandbox_warnings(result: OwnerPricingDryRunResult) -> List[str]:
    warnings = [
        "Sandbox plan only; live import remains disabled.",
    ]
    if result.invalid_rows:
        warnings.append("Invalid rows exist; future apply is not recommended until they are fixed.")
    if result.duplicate_material_keys:
        warnings.append("Duplicate material keys exist; owner/G2 review is required.")
    if not result.current_pricing:
        warnings.append("No baseline pricing snapshot was provided; all valid rows are treated as add candidates.")
    if result.current_pricing and result.current_records_read == 0:
        warnings.append("Baseline pricing snapshot was provided but no comparable records were read.")
    return warnings


def _sandbox_output_warnings(result: OwnerPricingDryRunResult) -> List[str]:
    warnings = [
        "Sandbox output only; final import remains disabled.",
    ]
    if result.invalid_rows:
        warnings.append("Invalid rows were skipped and were not applied into sandbox output.")
    if result.duplicate_material_keys:
        warnings.append("Duplicate material keys were skipped and require owner/G2 review.")
    if not result.current_pricing:
        warnings.append("No baseline pricing snapshot was provided; all valid rows are written as added materials.")
    if result.current_pricing and result.current_records_read == 0:
        warnings.append("Baseline pricing snapshot was provided but no comparable records were read.")
    return warnings


def _skipped_rows(result: OwnerPricingDryRunResult) -> List[Dict[str, Any]]:
    skipped_by_row: Dict[int, Dict[str, Any]] = {}

    for issue in result.missing_required_fields:
        skipped_by_row[issue.row_number] = {
            "row_number": issue.row_number,
            "material_key": issue.material_key,
            "reason": f"missing required fields: {', '.join(issue.fields)}",
        }

    for issue in result.price_format_issues:
        skipped_by_row[issue.row_number] = {
            "row_number": issue.row_number,
            "material_key": issue.material_key,
            "reason": f"price format issue: {issue.issue}",
        }

    for issue in result.duplicate_material_keys:
        for row_number in issue.rows:
            skipped_by_row[row_number] = {
                "row_number": row_number,
                "material_key": issue.material_key,
                "reason": "duplicate material_key requires manual review",
            }

    return [
        skipped_by_row[row_number]
        for row_number in sorted(skipped_by_row)
    ]


def _skipped_rows_section(skipped_rows: List[Dict[str, Any]]) -> str:
    lines = [
        "## Skipped Rows",
        "",
    ]
    if not skipped_rows:
        lines.extend(["None.", ""])
        return "\n".join(lines)

    lines.extend(["| CSV row | Material key | Reason |", "| ---: | --- | --- |"])
    for row in skipped_rows:
        lines.append(
            f"| {row['row_number']} | `{row['material_key'] or '(blank)'}` | {row['reason']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _bullet_lines(items: List[str]) -> List[str]:
    if not items:
        return ["- None."]
    return [f"- {item}" for item in items]


def _confirmation_checklist() -> List[str]:
    return [
        "Owner confirms the source CSV is the intended file.",
        "Owner confirms no real pricing sample is committed to the repository.",
        "G2 reviews invalid rows, duplicate keys, and skipped rows.",
        "G2 confirms add/update/unchanged candidates match the dry-run report.",
        "A future apply command, if approved, writes to sandbox output only.",
        "Rollback approach is documented before any production import is considered.",
    ]


def _approval_checklist() -> List[str]:
    return [
        "Owner reviewed the sandbox output JSON.",
        "Owner confirmed the sandbox output checksum is attached to this record.",
        "Owner reviewed the dry-run report, when provided.",
        "Owner reviewed the sandbox apply plan, when provided.",
        "Owner confirmed this approval does not enable production import.",
        "Owner confirmed no live JSON or production pricing data was mutated.",
        "G2 should review this approval record before any future final import task.",
    ]


def _checklist_lines(items: List[str]) -> List[str]:
    return [f"- [ ] {item}" for item in items]


def _change_to_dict(change: PricingChange) -> Dict[str, Any]:
    return {
        "material_key": change.material_key,
        "material_name": change.material_name,
        "unit": change.unit,
        "current_price": (
            _format_decimal(change.current_price)
            if change.current_price is not None
            else None
        ),
        "new_price": _format_decimal(change.new_price),
        "changed_fields": change.changed_fields or [],
    }


def _write_text_file(path: str, content: str) -> None:
    output_dir = os.path.dirname(os.path.abspath(path))
    os.makedirs(output_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        file.write(content)


def _write_json_file(path: str, content: Dict[str, Any]) -> None:
    output_dir = os.path.dirname(os.path.abspath(path))
    os.makedirs(output_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(content, file, indent=2, ensure_ascii=False)
        file.write("\n")
