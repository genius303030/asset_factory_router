import csv
import json
import os
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


def _format_decimal(value: Decimal) -> str:
    return format(value, "f")


def _generated_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _validate_sandbox_output_path(path: str, overwrite: bool = False) -> None:
    if not path or not path.strip():
        raise ValueError("sandbox apply plan output path is required")

    normalized_path = os.path.normpath(os.path.abspath(path))
    path_parts = {part.lower() for part in normalized_path.split(os.sep)}
    filename = os.path.basename(normalized_path).lower()

    if path_parts.intersection(LIVE_OUTPUT_PATH_PARTS) or filename in LIVE_OUTPUT_FILENAMES:
        raise ValueError(
            "sandbox apply plan output path appears to target live or production pricing data"
        )

    if os.path.exists(normalized_path) and not overwrite:
        raise FileExistsError(
            "refusing to overwrite existing sandbox apply plan output without --overwrite"
        )


def _read_optional_dry_run_report(path: Optional[str]) -> Optional[Dict[str, Any]]:
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
