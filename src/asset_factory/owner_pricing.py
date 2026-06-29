import csv
import json
import os
from dataclasses import dataclass
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
