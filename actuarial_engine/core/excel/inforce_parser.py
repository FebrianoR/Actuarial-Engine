"""
Inforce Parser – Membaca file INFORCE 31 DESEMBER YYYY.

File Excel berisi 3 sheet:
  - INSURANCE CONTRACT: data polis (200K+ baris)
  - STOPLOSS: data stoploss/kredit (kecil)
  - Pivot: ringkasan per produk

Mendukung format .xlsx (openpyxl) dan .xlsb (pyxlsb).
Menggunakan read_only=True + streaming untuk efisiensi memori.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any
import io
import logging
import os
import re

import openpyxl

from actuarial_engine.models.inforce import (
    InforceRecord, StoplossRecord, InforceSummary, ParsedInforce,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  Indonesian month mapping
# ──────────────────────────────────────────────

BULAN_MAP: dict[str, int] = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4,
    "mei": 5, "juni": 6, "juli": 7, "agustus": 8,
    "september": 9, "oktober": 10, "november": 11, "desember": 12,
    # Abbreviations that appear in filenames
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "agu": 8, "ags": 8, "aug": 8,
    "sep": 9, "okt": 10, "nov": 11, "des": 12,
}

# ──────────────────────────────────────────────
#  Utility helpers
# ──────────────────────────────────────────────

def _to_date(val: Any) -> date | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, (int, float)):
        # pyxlsb returns dates as serial numbers (days since 1899-12-30)
        try:
            serial = int(val)
            if 1 < serial < 200000:  # reasonable date range
                from datetime import timedelta
                base = date(1899, 12, 30)
                return base + timedelta(days=serial)
        except (ValueError, OverflowError):
            pass
        return None
    if isinstance(val, str):
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(val.strip(), fmt).date()
            except ValueError:
                continue
    return None


def _to_float(val: Any) -> float:
    try:
        return float(val or 0)
    except (TypeError, ValueError):
        return 0.0


def _to_str(val: Any) -> str:
    if val is None:
        return ""
    return str(val).strip()


def _detect_month_year(filename: str) -> tuple[int, int]:
    """
    Detect month and year from filename.
    e.g. '02. INFORCE 31 JANUARI 2024 - KIRIM.xlsx' → (1, 2024)
         '22. INFORCE 30 SEP 2025- KIRIM.xlsx' → (9, 2025)
    """
    fn_lower = filename.lower()

    # Detect year: find 4-digit year
    year_match = re.search(r"(\d{4})", fn_lower)
    year = int(year_match.group(1)) if year_match else 0

    # Detect month from Indonesian month name
    month = 0
    for bulan, num in BULAN_MAP.items():
        if bulan in fn_lower:
            month = num
            break

    return month, year


def _is_xlsb(filename: str) -> bool:
    """Check if the file is Excel Binary format (.xlsb)."""
    return filename.lower().endswith(".xlsb")


# ──────────────────────────────────────────────
#  Column mapping
# ──────────────────────────────────────────────

INFORCE_COLUMNS = [
    "sguser", "id", "batchnr", "cob", "product", "sob", "mkt", "uw",
    "policyno", "begindt", "enddt", "begindtlt", "valdate", "stspolis",
    "aktif", "tsi", "gwp", "discount", "outgo", "ngwp",
    "ripremi", "ricom", "ripreminett", "grace", "smethode",
]


# ──────────────────────────────────────────────
#  .xlsb reader adapter (pyxlsb)
#  Provides a unified row iteration interface.
# ──────────────────────────────────────────────

def _xlsb_sheet_rows(wb_xlsb, sheet_name: str) -> list[tuple]:
    """Read all rows from an xlsb sheet as tuples of values."""
    rows: list[tuple] = []
    with wb_xlsb.get_sheet(sheet_name) as sheet:
        for row in sheet.rows():
            rows.append(tuple(cell.v for cell in row))
    return rows


def _find_header_in_rows(
    rows: list[tuple], max_scan: int = 10,
) -> tuple[int, list[str]]:
    """Scan rows to find the header row containing 'policyno'."""
    for i, row in enumerate(rows[:max_scan]):
        row_lower = [_to_str(v).lower() for v in row]
        if "policyno" in row_lower:
            return i, row_lower  # 0-indexed here
    return 0, []


def _find_header_row(ws, max_scan: int = 10) -> tuple[int, list[str]]:
    """Scan rows to find the header row containing 'policyno'. For openpyxl."""
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=max_scan, values_only=True)):
        row_lower = [_to_str(v).lower() for v in row]
        if "policyno" in row_lower:
            return i + 1, row_lower  # 1-indexed row number
    return 1, []  # default to row 1


def _build_col_map(headers: list[str]) -> dict[str, int]:
    """Build column index mapping from header list."""
    col_map: dict[str, int] = {}
    for col in INFORCE_COLUMNS:
        if col in headers:
            col_map[col] = headers.index(col)
    return col_map


def _row_getter(col_map: dict[str, int]):
    """Return a function that gets a value from a row tuple by column name."""
    def get(row: tuple, col: str) -> Any:
        idx = col_map.get(col)
        if idx is not None and idx < len(row):
            return row[idx]
        return None
    return get


def _row_to_inforce_record(row: tuple, get) -> InforceRecord | None:
    """Convert a row tuple to InforceRecord. Returns None if no policyno."""
    policyno = get(row, "policyno")
    if not policyno:
        return None

    return InforceRecord(
        sguser=_to_str(get(row, "sguser")),
        id=_to_str(get(row, "id")),
        batchnr=_to_str(get(row, "batchnr")),
        cob=_to_str(get(row, "cob")),
        product=_to_str(get(row, "product")),
        sob=_to_str(get(row, "sob")),
        mkt=_to_str(get(row, "mkt")),
        uw=_to_str(get(row, "uw")),
        policyno=_to_str(policyno),
        begindt=_to_date(get(row, "begindt")),
        enddt=_to_date(get(row, "enddt")),
        begindtlt=_to_date(get(row, "begindtlt")),
        valdate=_to_date(get(row, "valdate")),
        stspolis=_to_str(get(row, "stspolis")) or "INFORCE",
        aktif=_to_str(get(row, "aktif")) or "AKTIF",
        tsi=_to_float(get(row, "tsi")),
        gwp=_to_float(get(row, "gwp")),
        discount=_to_float(get(row, "discount")),
        outgo=_to_float(get(row, "outgo")),
        ngwp=_to_float(get(row, "ngwp")),
        ripremi=_to_float(get(row, "ripremi")),
        ricom=_to_float(get(row, "ricom")),
        ripreminett=_to_float(get(row, "ripreminett")),
        grace=_to_str(get(row, "grace")),
        smethode=_to_str(get(row, "smethode")).upper() or "PAA",
    )


def _row_to_stoploss_record(row: tuple, get) -> StoplossRecord | None:
    """Convert a row tuple to StoplossRecord. Returns None if no policyno."""
    policyno = get(row, "policyno")
    if not policyno:
        return None

    return StoplossRecord(
        sguser=_to_str(get(row, "sguser")),
        id=_to_str(get(row, "id")),
        batchnr=_to_str(get(row, "batchnr")),
        cob=_to_str(get(row, "cob")),
        product=_to_str(get(row, "product")),
        sob=_to_str(get(row, "sob")),
        mkt=_to_str(get(row, "mkt")),
        uw=_to_str(get(row, "uw")),
        policyno=_to_str(policyno),
        begindt=_to_date(get(row, "begindt")),
        enddt=_to_date(get(row, "enddt")),
        begindtlt=_to_date(get(row, "begindtlt")),
        valdate=_to_date(get(row, "valdate")),
        stspolis=_to_str(get(row, "stspolis")) or "INFORCE",
        aktif=_to_str(get(row, "aktif")) or "AKTIF",
        tsi=_to_float(get(row, "tsi")),
        gwp=_to_float(get(row, "gwp")),
        discount=_to_float(get(row, "discount")),
        outgo=_to_float(get(row, "outgo")),
        ngwp=_to_float(get(row, "ngwp")),
        ripremi=_to_float(get(row, "ripremi")),
        ricom=_to_float(get(row, "ricom")),
        ripreminett=_to_float(get(row, "ripreminett")),
        grace=_to_str(get(row, "grace")),
        smethode=_to_str(get(row, "smethode")),
    )


# ──────────────────────────────────────────────
#  Parse INSURANCE CONTRACT sheet
# ──────────────────────────────────────────────

def _parse_insurance_contract_xlsx(
    wb: openpyxl.Workbook,
    sheet_name: str,
) -> tuple[list[InforceRecord], list[str]]:
    """Parse the main INSURANCE CONTRACT sheet (.xlsx)."""
    records: list[InforceRecord] = []
    errors: list[str] = []

    ws = wb[sheet_name]
    header_row_num, headers = _find_header_row(ws)

    if not headers or "policyno" not in headers:
        errors.append(f"Header 'policyno' tidak ditemukan di sheet '{sheet_name}'")
        return records, errors

    col_map = _build_col_map(headers)
    get = _row_getter(col_map)

    count = 0
    for row in ws.iter_rows(min_row=header_row_num + 1, values_only=True):
        if not any(row):
            continue
        rec = _row_to_inforce_record(row, get)
        if rec:
            records.append(rec)
            count += 1
            if count % 50000 == 0:
                logger.info(f"Parsed {count} inforce records...")

    logger.info(f"Total inforce records parsed: {count}")
    return records, errors


def _parse_insurance_contract_xlsb(
    all_rows: list[tuple],
) -> tuple[list[InforceRecord], list[str]]:
    """Parse the main INSURANCE CONTRACT sheet (.xlsb)."""
    records: list[InforceRecord] = []
    errors: list[str] = []

    header_idx, headers = _find_header_in_rows(all_rows)

    if not headers or "policyno" not in headers:
        errors.append("Header 'policyno' tidak ditemukan di sheet INSURANCE CONTRACT (.xlsb)")
        return records, errors

    col_map = _build_col_map(headers)
    get = _row_getter(col_map)

    count = 0
    for row in all_rows[header_idx + 1:]:
        if not any(row):
            continue
        rec = _row_to_inforce_record(row, get)
        if rec:
            records.append(rec)
            count += 1
            if count % 50000 == 0:
                logger.info(f"Parsed {count} inforce records (.xlsb)...")

    logger.info(f"Total inforce records parsed (.xlsb): {count}")
    return records, errors


# ──────────────────────────────────────────────
#  Parse STOPLOSS sheet
# ──────────────────────────────────────────────

def _parse_stoploss_xlsx(
    wb: openpyxl.Workbook,
    sheet_name: str,
) -> tuple[list[StoplossRecord], list[str]]:
    """Parse the STOPLOSS sheet (.xlsx)."""
    records: list[StoplossRecord] = []
    errors: list[str] = []

    ws = wb[sheet_name]
    header_row_num, headers = _find_header_row(ws)

    if not headers or "policyno" not in headers:
        errors.append(f"Header 'policyno' tidak ditemukan di sheet '{sheet_name}'")
        return records, errors

    col_map = _build_col_map(headers)
    get = _row_getter(col_map)

    for row in ws.iter_rows(min_row=header_row_num + 1, values_only=True):
        if not any(row):
            continue
        rec = _row_to_stoploss_record(row, get)
        if rec:
            records.append(rec)

    logger.info(f"Total stoploss records parsed: {len(records)}")
    return records, errors


def _parse_stoploss_xlsb(
    all_rows: list[tuple],
) -> tuple[list[StoplossRecord], list[str]]:
    """Parse the STOPLOSS sheet (.xlsb)."""
    records: list[StoplossRecord] = []
    errors: list[str] = []

    header_idx, headers = _find_header_in_rows(all_rows)

    if not headers or "policyno" not in headers:
        errors.append("Header 'policyno' tidak ditemukan di sheet STOPLOSS (.xlsb)")
        return records, errors

    col_map = _build_col_map(headers)
    get = _row_getter(col_map)

    for row in all_rows[header_idx + 1:]:
        if not any(row):
            continue
        rec = _row_to_stoploss_record(row, get)
        if rec:
            records.append(rec)

    logger.info(f"Total stoploss records parsed (.xlsb): {len(records)}")
    return records, errors


# ──────────────────────────────────────────────
#  Parse Pivot sheet (summary)
# ──────────────────────────────────────────────

def _parse_pivot_from_rows(rows: list[tuple]) -> InforceSummary | None:
    """Parse the Pivot summary from a list of row tuples."""
    try:
        summary = InforceSummary()

        for i, row in enumerate(rows):
            row_str = [_to_str(v).lower() for v in row]

            if "row labels" in row_str and "count of product" in row_str:
                rl_idx = row_str.index("row labels")
                cnt_idx = row_str.index("count of product")
                gwp_idx = next((j for j, v in enumerate(row_str) if "sum of gwp" in v), None)
                ngwp_idx = next((j for j, v in enumerate(row_str) if "sum of ngwp" in v), None)
                tsi_idx = next((j for j, v in enumerate(row_str) if "sum of tsi" in v), None)

                for data_row in rows[i + 1:]:
                    label = _to_str(data_row[rl_idx]) if rl_idx < len(data_row) else ""
                    if not label or label.lower() == "grand total":
                        if label.lower() == "grand total":
                            summary.total_policies = int(_to_float(data_row[cnt_idx])) if cnt_idx is not None and cnt_idx < len(data_row) else 0
                            summary.total_gwp = _to_float(data_row[gwp_idx]) if gwp_idx is not None and gwp_idx < len(data_row) else 0
                            summary.total_ngwp = _to_float(data_row[ngwp_idx]) if ngwp_idx is not None and ngwp_idx < len(data_row) else 0
                            summary.total_tsi = _to_float(data_row[tsi_idx]) if tsi_idx is not None and tsi_idx < len(data_row) else 0
                        continue

                    summary.by_product[label] = {
                        "count": int(_to_float(data_row[cnt_idx])) if cnt_idx is not None and cnt_idx < len(data_row) else 0,
                        "gwp": _to_float(data_row[gwp_idx]) if gwp_idx is not None and gwp_idx < len(data_row) else 0,
                        "ngwp": _to_float(data_row[ngwp_idx]) if ngwp_idx is not None and ngwp_idx < len(data_row) else 0,
                        "tsi": _to_float(data_row[tsi_idx]) if tsi_idx is not None and tsi_idx < len(data_row) else 0,
                    }

        return summary
    except Exception as e:
        logger.warning(f"Error parsing Pivot sheet: {e}")
        return None


def _parse_pivot(
    wb: openpyxl.Workbook,
    sheet_name: str,
) -> InforceSummary | None:
    """Parse the Pivot summary sheet (.xlsx)."""
    try:
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        return _parse_pivot_from_rows(rows)
    except Exception as e:
        logger.warning(f"Error parsing Pivot sheet: {e}")
        return None


# ──────────────────────────────────────────────
#  Find sheet name helpers
# ──────────────────────────────────────────────

def _find_ic_sheet(sheet_names: list[str]) -> str | None:
    """Find the INSURANCE CONTRACT sheet by name pattern."""
    lower_map = {s.lower(): s for s in sheet_names}
    for key, name in lower_map.items():
        if "insurance" in key or "contract" in key:
            return name
    # Fallback to first sheet
    return sheet_names[0] if sheet_names else None


def _find_sheet(sheet_names: list[str], target: str) -> str | None:
    """Find a sheet by lowercase target name."""
    lower_map = {s.lower(): s for s in sheet_names}
    return lower_map.get(target)


# ──────────────────────────────────────────────
#  Main entry point — .xlsx
# ──────────────────────────────────────────────

def _parse_inforce_xlsx(file_bytes: bytes, filename: str) -> ParsedInforce:
    """Parse .xlsx inforce file using openpyxl."""
    month, year = _detect_month_year(filename)
    result = ParsedInforce(year=year, month=month)

    try:
        wb = openpyxl.load_workbook(
            io.BytesIO(file_bytes),
            read_only=True,
            data_only=True,
        )

        logger.info(f"Sheets found: {wb.sheetnames}")

        # 1. Parse INSURANCE CONTRACT
        ic_sheet = _find_ic_sheet(wb.sheetnames)
        if ic_sheet:
            records, errs = _parse_insurance_contract_xlsx(wb, ic_sheet)
            result.records = records
            result.errors.extend(errs)

        # Detect year from valdate if not found in filename
        if result.year == 0 and result.records:
            if result.records[0].valdate:
                result.year = result.records[0].valdate.year

        # 2. Parse STOPLOSS
        sl_sheet = _find_sheet(wb.sheetnames, "stoploss")
        if sl_sheet:
            stoploss, sl_errs = _parse_stoploss_xlsx(wb, sl_sheet)
            result.stoploss = stoploss
            result.errors.extend(sl_errs)

        # 3. Parse Pivot
        pv_sheet = _find_sheet(wb.sheetnames, "pivot")
        if pv_sheet:
            result.summary = _parse_pivot(wb, pv_sheet)
            if result.summary:
                result.summary.year = result.year

        wb.close()

    except Exception as e:
        result.errors.append(f"Error parsing inforce file (.xlsx): {e}")
        logger.exception(f"Error parsing inforce (.xlsx): {e}")

    return result


# ──────────────────────────────────────────────
#  Main entry point — .xlsb
# ──────────────────────────────────────────────

def _parse_inforce_xlsb(file_bytes: bytes, filename: str) -> ParsedInforce:
    """Parse .xlsb inforce file using pyxlsb."""
    from pyxlsb import open_workbook

    month, year = _detect_month_year(filename)
    result = ParsedInforce(year=year, month=month)

    try:
        wb = open_workbook(io.BytesIO(file_bytes))
        sheet_names = wb.sheets
        logger.info(f"Sheets found (.xlsb): {sheet_names}")

        # 1. Parse INSURANCE CONTRACT
        ic_sheet = _find_ic_sheet(sheet_names)
        if ic_sheet:
            all_rows = _xlsb_sheet_rows(wb, ic_sheet)
            records, errs = _parse_insurance_contract_xlsb(all_rows)
            result.records = records
            result.errors.extend(errs)

        # Detect year from valdate if not found in filename
        if result.year == 0 and result.records:
            if result.records[0].valdate:
                result.year = result.records[0].valdate.year

        # 2. Parse STOPLOSS
        sl_sheet = _find_sheet(sheet_names, "stoploss")
        if not sl_sheet:
            sl_sheet = _find_sheet(sheet_names, "STOPLOSS")
        if sl_sheet:
            sl_rows = _xlsb_sheet_rows(wb, sl_sheet)
            stoploss, sl_errs = _parse_stoploss_xlsb(sl_rows)
            result.stoploss = stoploss
            result.errors.extend(sl_errs)

        # 3. Parse Pivot
        pv_sheet = _find_sheet(sheet_names, "pivot")
        if not pv_sheet:
            pv_sheet = _find_sheet(sheet_names, "Pivot")
        if pv_sheet:
            pv_rows = _xlsb_sheet_rows(wb, pv_sheet)
            result.summary = _parse_pivot_from_rows(pv_rows)
            if result.summary:
                result.summary.year = result.year

        wb.close()

    except Exception as e:
        result.errors.append(f"Error parsing inforce file (.xlsb): {e}")
        logger.exception(f"Error parsing inforce (.xlsb): {e}")

    return result


# ──────────────────────────────────────────────
#  Public API — auto-detect format
# ──────────────────────────────────────────────

def parse_inforce(
    file_bytes: bytes,
    filename: str = "",
) -> ParsedInforce:
    """
    Parse file INFORCE (monthly or year-end).

    Supports both .xlsx and .xlsb formats.
    Detects month and year from filename automatically.

    Args:
        file_bytes: Isi file Excel sebagai bytes.
        filename: Nama file (opsional, untuk deteksi bulan & tahun).

    Returns:
        ParsedInforce object dengan records, stoploss, summary, dan errors.
    """
    logger.info(f"Parsing inforce: {filename} ({len(file_bytes)} bytes)")

    if _is_xlsb(filename):
        return _parse_inforce_xlsb(file_bytes, filename)
    else:
        return _parse_inforce_xlsx(file_bytes, filename)


def parse_inforce_from_path(file_path: str) -> ParsedInforce:
    """Convenience: parse from file path instead of bytes."""
    with open(file_path, "rb") as f:
        return parse_inforce(f.read(), filename=os.path.basename(file_path))
