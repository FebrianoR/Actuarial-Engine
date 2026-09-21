"""
Consolidated Assumptions Parser (v2) – Membaca file ASUMSI 2020-2025.

File ini berisi 7 sheet:
  1. Loss Rasio Per Produk – loss ratio per produk per tahun
  2. Loss Rasio Per COB   – aggregat loss ratio per COB
  3. PAD                  – Provision for Adverse Deviation (CL 75% & 95%)
  4. ICHE                 – Insurance Contract Hedging Effectiveness
  5. Bunga Diskonto       – Gov bond yield curves per tahun
  6. Inflasi              – Data inflasi bulanan + rata-rata 3 tahun
  7. Lapse Rasio          – Lapse rate per durasi per tahun
  8. Expense Rasio        – Rasio biaya operasional
  + SUMMARY              – Ringkasan per COB per tahun
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
import io
import logging
import re

import openpyxl

from actuarial_engine.models.assumptions_v2 import (
    LossRatioProduct,
    LossRatioCOB,
    PADEntry,
    PADTable,
    ICHEEntry,
    DiscountRateYear,
    InflationEntry,
    InflationAverage,
    LapseRatioTable,
    ExpenseDetail,
    ExpenseRatio,
    SummaryRow,
    SummaryYear,
    ConsolidatedAssumptions,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────

def _to_float(val: Any) -> float:
    try:
        return float(val or 0)
    except (TypeError, ValueError):
        return 0.0


def _to_str(val: Any) -> str:
    if val is None:
        return ""
    return str(val).strip()


def _extract_years_from_header(row: tuple, start_col: int = 0) -> list[int]:
    """Ekstrak tahun-tahun dari baris header."""
    years = []
    for val in row[start_col:]:
        try:
            y = int(float(str(val)))
            if 2000 <= y <= 2100:
                years.append(y)
        except (TypeError, ValueError):
            continue
    return years


def _find_sheet(wb: openpyxl.Workbook, *keywords: str) -> str | None:
    """Cari sheet name yang mengandung salah satu keyword (case-insensitive)."""
    for name in wb.sheetnames:
        nl = name.lower()
        for kw in keywords:
            if kw.lower() in nl:
                return name
    return None


# ──────────────────────────────────────────────
#  1. Loss Ratio Per Produk
# ──────────────────────────────────────────────

def _parse_loss_ratio_per_product(ws) -> list[LossRatioProduct]:
    """Parse sheet 'Loss Rasio Per Produk'."""
    rows = list(ws.iter_rows(values_only=True))
    results: list[LossRatioProduct] = []

    # Find header row with COB | BUSINESS CODE | BUSINESS NAME | years...
    header_idx = None
    years: list[int] = []
    year_cols: list[int] = []

    for i, row in enumerate(rows):
        row_str = [_to_str(v).lower() for v in row]
        if "cob" in row_str and ("business code" in row_str or "business name" in row_str):
            header_idx = i
            # Extract year columns
            for j, val in enumerate(row):
                try:
                    y = int(float(str(val)))
                    if 2000 <= y <= 2100:
                        years.append(y)
                        year_cols.append(j)
                except (TypeError, ValueError):
                    continue
            break

    if header_idx is None:
        return results

    headers = [_to_str(v).lower() for v in rows[header_idx]]
    cob_idx = headers.index("cob") if "cob" in headers else 0
    code_idx = next((j for j, h in enumerate(headers) if "business code" in h), 1)
    name_idx = next((j for j, h in enumerate(headers) if "business name" in h), 2)

    for row in rows[header_idx + 1:]:
        cob = _to_str(row[cob_idx]) if cob_idx < len(row) else ""
        if not cob:
            continue

        ratios = {}
        for y, col_idx in zip(years, year_cols):
            if col_idx < len(row):
                ratios[y] = _to_float(row[col_idx])

        results.append(LossRatioProduct(
            cob=cob,
            business_code=_to_str(row[code_idx]) if code_idx < len(row) else "",
            business_name=_to_str(row[name_idx]) if name_idx < len(row) else "",
            ratios=ratios,
        ))

    return results


# ──────────────────────────────────────────────
#  2. Loss Ratio Per COB
# ──────────────────────────────────────────────

def _parse_loss_ratio_per_cob(ws) -> list[LossRatioCOB]:
    """Parse sheet 'Loss Rasio Per COB'."""
    rows = list(ws.iter_rows(values_only=True))
    results: list[LossRatioCOB] = []

    # Find header with COB + year columns
    header_idx = None
    years: list[int] = []
    year_cols: list[int] = []
    cob_col = 1  # default

    for i, row in enumerate(rows):
        row_str = [_to_str(v).lower() for v in row]
        if "cob" in row_str:
            header_idx = i
            cob_col = row_str.index("cob")
            for j, val in enumerate(row):
                try:
                    y = int(float(str(val)))
                    if 2000 <= y <= 2100:
                        years.append(y)
                        year_cols.append(j)
                except (TypeError, ValueError):
                    continue
            break

    if header_idx is None:
        return results

    for row in rows[header_idx + 1:]:
        cob = _to_str(row[cob_col]) if cob_col < len(row) else ""
        if not cob:
            continue

        ratios = {}
        for y, col_idx in zip(years, year_cols):
            val = row[col_idx] if col_idx < len(row) else None
            if val is not None and val != "":
                ratios[y] = _to_float(val)

        results.append(LossRatioCOB(cob=cob, ratios=ratios))

    return results


# ──────────────────────────────────────────────
#  3. PAD (Provision for Adverse Deviation)
# ──────────────────────────────────────────────

def _parse_pad_section(
    rows: list[tuple],
    start_idx: int,
    years: list[int],
    year_offsets: list[int],
) -> list[PADEntry]:
    """Parse one section of PAD (Gross/Reas/Net)."""
    entries: list[PADEntry] = []
    cob_offset = year_offsets[0] - 1 if year_offsets else 1

    for row in rows[start_idx:]:
        cob = _to_str(row[cob_offset]) if cob_offset < len(row) else ""
        if not cob or cob.lower() == "cob":
            continue
        if cob.lower().startswith("pad"):
            break  # hit next section

        ratios = {}
        for y, col_idx in zip(years, year_offsets):
            val = row[col_idx] if col_idx < len(row) else None
            if val is not None and val != "":
                ratios[y] = _to_float(val)

        entries.append(PADEntry(cob=cob, ratios=ratios))

    return entries


def _parse_pad(ws) -> list[PADTable]:
    """Parse sheet 'PAD'."""
    rows = list(ws.iter_rows(values_only=True))
    tables: list[PADTable] = []

    i = 0
    while i < len(rows):
        row_str = [_to_str(v).lower() for v in rows[i]]
        full_text = " ".join(row_str)

        # Detect PAD section headers like "PAD Gross CL 75%"
        cl_match = re.search(r"cl\s*(\d+)%", full_text)
        if not cl_match:
            i += 1
            continue

        cl = f"{cl_match.group(1)}%"

        # Find COB header row (next row after section header)
        header_row_idx = i + 1
        if header_row_idx >= len(rows):
            break

        header = [_to_str(v).lower() for v in rows[header_row_idx]]

        # Find 3 groups: Gross, Reas, Net
        # Each group has: COB + year columns
        # Detect by finding "cob" columns and their year ranges
        cob_positions = [j for j, h in enumerate(header) if h == "cob"]

        if len(cob_positions) < 3:
            i += 1
            continue

        # Extract years for each group
        groups: list[tuple[list[int], list[int]]] = []
        for g, cob_pos in enumerate(cob_positions):
            # Year columns are after cob_pos until next empty or next "cob"
            end = cob_positions[g + 1] if g + 1 < len(cob_positions) else len(header)
            year_cols = []
            year_vals = []
            for j in range(cob_pos + 1, end):
                val = rows[header_row_idx][j]
                try:
                    y = int(float(str(val)))
                    if 2000 <= y <= 2100:
                        year_vals.append(y)
                        year_cols.append(j)
                except (TypeError, ValueError):
                    continue
            groups.append((year_vals, year_cols))

        data_start = header_row_idx + 1

        pad_table = PADTable(confidence_level=cl)
        if len(groups) >= 1:
            pad_table.gross = _parse_pad_section(rows, data_start, groups[0][0], groups[0][1])
        if len(groups) >= 2:
            pad_table.reinsurance = _parse_pad_section(rows, data_start, groups[1][0], groups[1][1])
        if len(groups) >= 3:
            pad_table.net = _parse_pad_section(rows, data_start, groups[2][0], groups[2][1])

        tables.append(pad_table)

        # Skip to next section
        i = data_start + max(len(pad_table.gross), 1) + 1

    return tables


# ──────────────────────────────────────────────
#  4. ICHE
# ──────────────────────────────────────────────

def _parse_iche(ws) -> list[ICHEEntry]:
    """Parse sheet 'ICHE'."""
    rows = list(ws.iter_rows(values_only=True))
    results: list[ICHEEntry] = []

    # Find header row with COB + years
    header_idx = None
    years: list[int] = []
    year_cols: list[int] = []
    cob_col = 1

    for i, row in enumerate(rows):
        row_str = [_to_str(v).lower() for v in row]
        if "cob" in row_str:
            header_idx = i
            cob_col = row_str.index("cob")
            for j, val in enumerate(row):
                try:
                    y = int(float(str(val)))
                    if 2000 <= y <= 2100:
                        years.append(y)
                        year_cols.append(j)
                except (TypeError, ValueError):
                    continue
            break

    if header_idx is None:
        return results

    for row in rows[header_idx + 1:]:
        cob = _to_str(row[cob_col]) if cob_col < len(row) else ""
        if not cob:
            continue

        ratios = {}
        for y, col_idx in zip(years, year_cols):
            val = row[col_idx] if col_idx < len(row) else None
            if val is not None:
                ratios[y] = _to_float(val)

        results.append(ICHEEntry(cob=cob, ratios=ratios))

    return results


# ──────────────────────────────────────────────
#  5. Bunga Diskonto (Discount Rates)
# ──────────────────────────────────────────────

def _parse_discount_rates(ws) -> list[DiscountRateYear]:
    """Parse sheet 'Bunga Diskonto'."""
    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 3:
        return []

    results: list[DiscountRateYear] = []

    # Row 1 has year group headers
    # Row 2 has Term + monthly date columns + SAK + SAP
    # Rows 3+ have data per term

    header1 = rows[0]  # Year group labels
    header2 = rows[1]  # Term / date columns

    # Identify year groups by scanning header1 for year labels
    year_groups: list[dict[str, Any]] = []
    current_group: dict[str, Any] | None = None

    for j, val in enumerate(header1):
        val_str = _to_str(val)
        if val_str and ("gov bond" in val_str.lower() or "des" in val_str.lower()
                        or "bond yield" in val_str.lower()):
            # Extract year from label
            year_match = re.search(r"(\d{4})", val_str)
            if year_match:
                if current_group:
                    current_group["end_col"] = j - 1
                    year_groups.append(current_group)
                current_group = {
                    "year": int(year_match.group(1)),
                    "label": val_str,
                    "start_col": j,
                    "end_col": None,
                }

    if current_group:
        current_group["end_col"] = len(header2) - 1
        year_groups.append(current_group)

    # For each year group, parse the data
    for group in year_groups:
        dr_year = DiscountRateYear(
            year=group["year"],
            label=group["label"],
        )

        start = group["start_col"]
        end = group["end_col"] if group["end_col"] else len(header2) - 1

        # Find Term column and date/SAK/SAP columns within this group
        term_col = None
        date_cols: list[tuple[int, str]] = []  # (col_idx, column_label)

        for j in range(start, min(end + 1, len(header2))):
            h2_val = _to_str(header2[j]).lower()
            if h2_val == "term":
                term_col = j
            elif h2_val in ("sak", "sap"):
                date_cols.append((j, h2_val.upper()))
            elif header2[j] is not None:
                # Try to parse as date or use as label
                date_str = _to_str(header2[j])
                date_cols.append((j, date_str))

        if term_col is None:
            continue

        # Parse data rows
        for row in rows[2:]:
            if not row or term_col >= len(row):
                continue
            term_val = row[term_col]
            if term_val is None:
                continue
            try:
                term = int(float(str(term_val)))
            except (TypeError, ValueError):
                continue

            term_data: dict[str, float] = {}
            for col_idx, col_label in date_cols:
                if col_idx < len(row) and row[col_idx] is not None:
                    term_data[col_label] = _to_float(row[col_idx])

            dr_year.terms[term] = term_data

        results.append(dr_year)

    return results


# ──────────────────────────────────────────────
#  6. Inflasi
# ──────────────────────────────────────────────

def _parse_inflation(ws) -> tuple[list[InflationEntry], list[InflationAverage]]:
    """Parse sheet 'Inflasi'."""
    rows = list(ws.iter_rows(values_only=True))
    monthly: list[InflationEntry] = []
    averages: list[InflationAverage] = []

    # Find header row
    header_idx = None
    bulan_col = 0
    tahun_col = 1
    inflasi_col = 2
    valuasi_col = None
    avg_col = None

    for i, row in enumerate(rows):
        row_str = [_to_str(v).lower() for v in row]
        if "bulan" in row_str or "inflasi" in row_str:
            header_idx = i
            if "bulan" in row_str:
                bulan_col = row_str.index("bulan")
            if "tahun" in row_str:
                tahun_col = row_str.index("tahun")
            if "inflasi" in row_str:
                inflasi_col = row_str.index("inflasi")
            # Look for valuasi and average columns
            for j, v in enumerate(row_str):
                if "valuasi" in v:
                    valuasi_col = j
                if "rata" in v or "average" in v:
                    avg_col = j
            break

    if header_idx is None:
        return monthly, averages

    for row in rows[header_idx + 1:]:
        # Monthly inflation
        bulan = _to_str(row[bulan_col]) if bulan_col < len(row) else ""
        tahun_val = row[tahun_col] if tahun_col < len(row) else None
        inflasi_val = row[inflasi_col] if inflasi_col < len(row) else None

        if bulan and tahun_val is not None:
            try:
                tahun = int(float(str(tahun_val)))
                monthly.append(InflationEntry(
                    month=bulan,
                    year=tahun,
                    rate=_to_float(inflasi_val),
                ))
            except (TypeError, ValueError):
                pass

        # 3-year averages
        if valuasi_col is not None and avg_col is not None:
            val_str = _to_str(row[valuasi_col]) if valuasi_col < len(row) else ""
            avg_val = row[avg_col] if avg_col < len(row) else None
            if val_str and avg_val is not None:
                averages.append(InflationAverage(
                    valuation_date=val_str,
                    average_3yr=_to_float(avg_val),
                ))

    return monthly, averages


# ──────────────────────────────────────────────
#  7. Lapse Rasio
# ──────────────────────────────────────────────

def _parse_lapse_ratio(ws) -> LapseRatioTable:
    """Parse sheet 'Lapse Rasio'."""
    rows = list(ws.iter_rows(values_only=True))
    table = LapseRatioTable()

    # Find header with Year + year columns
    header_idx = None
    years: list[int] = []
    year_cols: list[int] = []
    year_col_header = 1  # column with duration "Year" label

    for i, row in enumerate(rows):
        row_str = [_to_str(v).lower() for v in row]
        if "year" in row_str:
            header_idx = i
            year_col_header = row_str.index("year")
            for j, val in enumerate(row):
                try:
                    y = int(float(str(val)))
                    if 2000 <= y <= 2100:
                        years.append(y)
                        year_cols.append(j)
                except (TypeError, ValueError):
                    continue
            break

    if header_idx is None:
        return table

    for row in rows[header_idx + 1:]:
        duration_val = row[year_col_header] if year_col_header < len(row) else None
        if duration_val is None:
            continue
        try:
            duration = int(float(str(duration_val)))
        except (TypeError, ValueError):
            continue

        year_map: dict[int, float] = {}
        for y, col_idx in zip(years, year_cols):
            val = row[col_idx] if col_idx < len(row) else None
            if val is not None:
                year_map[y] = _to_float(val)

        table.ratios[duration] = year_map

    return table


# ──────────────────────────────────────────────
#  8. Expense Rasio
# ──────────────────────────────────────────────

def _parse_expense_ratio(ws) -> ExpenseRatio:
    """Parse sheet 'Expense Rasio'."""
    rows = list(ws.iter_rows(values_only=True))
    result = ExpenseRatio()

    # Find year columns from header
    header_idx = None
    years: list[int] = []
    year_cols: list[int] = []

    for i, row in enumerate(rows):
        yr_found = _extract_years_from_header(row)
        if len(yr_found) >= 2:
            header_idx = i
            for j, val in enumerate(row):
                try:
                    y = int(float(str(val)))
                    if 2000 <= y <= 2100:
                        years.append(y)
                        year_cols.append(j)
                except (TypeError, ValueError):
                    continue
            break

    if header_idx is None:
        return result

    # Parse rows: look for key categories
    is_ratio_section = False

    for row in rows[header_idx + 1:]:
        # Identify category from columns (col 1 or col 2)
        col1 = _to_str(row[1]) if len(row) > 1 else ""
        col2 = _to_str(row[2]) if len(row) > 2 else ""
        label = col2 if col2 else col1

        if not label:
            continue

        # Extract values per year
        amounts: dict[int, float] = {}
        for y, col_idx in zip(years, year_cols):
            val = row[col_idx] if col_idx < len(row) else None
            if val is not None and val != "":
                amounts[y] = _to_float(val)

        # Detect ratio section ("Rasio Biaya" row contains the totals)
        if "rasio biaya" in label.lower() or ("rasio" in col1.lower() and not is_ratio_section):
            is_ratio_section = True
            if amounts:
                result.total_ratios = amounts
            continue

        if not amounts:
            continue

        if is_ratio_section:
            result.sub_ratios.append(ExpenseDetail(
                category=label,
                amounts=amounts,
            ))
        else:
            if "premi bruto" in label.lower():
                result.gross_premium = amounts
            elif "beban usaha" in label.lower() and not col2:
                result.total_operating_expense = amounts
            else:
                result.details.append(ExpenseDetail(
                    category=label,
                    amounts=amounts,
                ))

    return result


# ──────────────────────────────────────────────
#  SUMMARY sheet
# ──────────────────────────────────────────────

def _parse_summary(ws) -> list[SummaryYear]:
    """Parse sheet 'SUMMARY'."""
    rows = list(ws.iter_rows(values_only=True))
    results: list[SummaryYear] = []

    i = 0
    while i < len(rows):
        row = rows[i]
        # Look for year markers (standalone year in a cell)
        for j, val in enumerate(row):
            try:
                y = int(float(str(val)))
                if 2000 <= y <= 2100:
                    # Next row should be header: COB | LOSS RASIO | PAD | EXPENSE | TOTAL
                    if i + 1 < len(rows):
                        header = [_to_str(v).lower() for v in rows[i + 1]]
                        if "cob" in header:
                            cob_col = header.index("cob")
                            lr_col = next((k for k, h in enumerate(header) if "loss" in h), None)
                            pad_col = next((k for k, h in enumerate(header) if "pad" in h), None)
                            exp_col = next((k for k, h in enumerate(header) if "expense" in h), None)
                            tot_col = next((k for k, h in enumerate(header) if "total" in h), None)

                            sy = SummaryYear(year=y)
                            for data_row in rows[i + 2:]:
                                cob = _to_str(data_row[cob_col]) if cob_col < len(data_row) else ""
                                if not cob:
                                    break
                                sy.rows.append(SummaryRow(
                                    cob=cob,
                                    loss_ratio=_to_float(data_row[lr_col]) if lr_col is not None and lr_col < len(data_row) else 0,
                                    pad=_to_float(data_row[pad_col]) if pad_col is not None and pad_col < len(data_row) else 0,
                                    expense=_to_float(data_row[exp_col]) if exp_col is not None and exp_col < len(data_row) else 0,
                                    total=_to_float(data_row[tot_col]) if tot_col is not None and tot_col < len(data_row) else 0,
                                ))
                            results.append(sy)
                    break
            except (TypeError, ValueError):
                continue
        i += 1

    return results


# ──────────────────────────────────────────────
#  Main entry point
# ──────────────────────────────────────────────

def parse_consolidated_assumptions(
    file_bytes: bytes,
) -> tuple[ConsolidatedAssumptions, list[str]]:
    """
    Parse file ASUMSI 2020-2025.

    Returns:
        Tuple of (ConsolidatedAssumptions, errors list).
    """
    result = ConsolidatedAssumptions()
    errors: list[str] = []

    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        logger.info(f"ASUMSI sheets: {wb.sheetnames}")

        # 1. Loss Ratio Per Produk
        sheet = _find_sheet(wb, "loss rasio per produk", "loss ratio per produk")
        if sheet:
            result.loss_ratio_by_product = _parse_loss_ratio_per_product(wb[sheet])
            logger.info(f"Parsed {len(result.loss_ratio_by_product)} loss ratio products")

        # 2. Loss Ratio Per COB
        sheet = _find_sheet(wb, "loss rasio per cob", "loss ratio per cob")
        if sheet:
            result.loss_ratio_by_cob = _parse_loss_ratio_per_cob(wb[sheet])
            logger.info(f"Parsed {len(result.loss_ratio_by_cob)} loss ratio COBs")

        # 3. PAD
        sheet = _find_sheet(wb, "pad")
        if sheet:
            result.pad_tables = _parse_pad(wb[sheet])
            logger.info(f"Parsed {len(result.pad_tables)} PAD tables")

        # 4. ICHE
        sheet = _find_sheet(wb, "iche")
        if sheet:
            result.iche = _parse_iche(wb[sheet])
            logger.info(f"Parsed {len(result.iche)} ICHE entries")

        # 5. Bunga Diskonto
        sheet = _find_sheet(wb, "bunga diskonto", "discount")
        if sheet:
            result.discount_rates = _parse_discount_rates(wb[sheet])
            logger.info(f"Parsed {len(result.discount_rates)} discount rate years")

        # 6. Inflasi
        sheet = _find_sheet(wb, "inflasi", "inflation")
        if sheet:
            monthly, averages = _parse_inflation(wb[sheet])
            result.inflation_monthly = monthly
            result.inflation_averages = averages
            logger.info(f"Parsed {len(monthly)} inflation entries, {len(averages)} averages")

        # 7. Lapse Rasio
        sheet = _find_sheet(wb, "lapse")
        if sheet:
            result.lapse = _parse_lapse_ratio(wb[sheet])
            logger.info(f"Parsed lapse ratios for {len(result.lapse.ratios)} durations")

        # 8. Expense Rasio
        sheet = _find_sheet(wb, "expense")
        if sheet:
            result.expense = _parse_expense_ratio(wb[sheet])
            logger.info(f"Parsed expense ratios for {len(result.expense.total_ratios)} years")

        # SUMMARY
        sheet = _find_sheet(wb, "summary")
        if sheet:
            result.summary = _parse_summary(wb[sheet])
            logger.info(f"Parsed {len(result.summary)} summary years")

        wb.close()

    except Exception as e:
        errors.append(f"Error parsing consolidated assumptions: {e}")
        logger.exception(f"Error parsing assumptions: {e}")

    result.errors = errors
    return result, errors


def parse_consolidated_assumptions_from_path(
    file_path: str,
) -> tuple[ConsolidatedAssumptions, list[str]]:
    """Convenience: parse from file path."""
    with open(file_path, "rb") as f:
        return parse_consolidated_assumptions(f.read())
