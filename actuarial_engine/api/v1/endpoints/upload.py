"""
Upload Endpoints – Menerima file Excel template PSAK 117

Endpoints:
  POST /upload/portfolio       – Upload 00-Templateupload.xlsx
  POST /upload/assumptions     – Upload 01-templateassumption.xlsx
  POST /upload/tabphei         – Upload 02-templatetabphei.xlsx (yield curve)
  POST /upload/lapse           – Upload 03-templatelapse.xlsx
  POST /upload/inforce         – Upload INFORCE 31 DESEMBER YYYY.xlsx
  POST /upload/assumptions-v2  – Upload ASUMSI 2020-2025.xlsx
  POST /upload/ojk-codes       – Upload SANDI LINI USAHA.xlsx
  POST /upload/batch-calculate – Proses semua yang sudah diupload
"""
from __future__ import annotations

import logging
from typing import Any
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from pydantic import BaseModel

from actuarial_engine.core.excel.parser import (
    parse_portfolio, parse_assumptions, parse_yield_curve, parse_lapse,
    PolicyRecord, AssumptionRow, YieldCurveRow, LapseRow,
)
from actuarial_engine.core.excel.inforce_parser import parse_inforce
from actuarial_engine.core.excel.inforce_converter import multi_inforce_to_policies
from actuarial_engine.core.excel.assumptions_v2_parser import parse_consolidated_assumptions
from actuarial_engine.core.excel.ojk_parser import parse_ojk_codes
from actuarial_engine.services.batch_service import BatchService
from actuarial_engine.services.audit_service import AuditService
from actuarial_engine.api.v1.dependencies.auth import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(verify_api_key)])

# In-memory session store
_session: dict[str, Any] = {
    "policies": [],
    "assumptions": [],
    "yield_curve": [],
    "lapse": [],
    # New data types
    "inforce": {},          # "YYYY-MM" -> ParsedInforce
    "assumptions_v2": None, # ConsolidatedAssumptions
    "ojk_codes": None,      # OJKCodeTable
}


class UploadResponse(BaseModel):
    success: bool
    filename: str
    rows_parsed: int
    errors: list[str] = []
    preview: list[dict] = []


class BatchCalcRequest(BaseModel):
    valuation_date: str | None = None


@router.post("/portfolio", response_model=UploadResponse, summary="Upload Data Polis (00-Templateupload.xlsx)")
async def upload_portfolio(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload file 00-Templateupload.xlsx berisi data polis.
    Sheet yang dibaca: datapolis
    Kolom: policyno, cob, product, gwp, tsi, smethode (PAA/GMM), begindt, enddt
    """
    content = await file.read()
    policies, errors = parse_portfolio(content)

    if not policies and errors:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=errors)

    _session["policies"] = policies

    # Preview 5 baris pertama
    preview = [
        {
            "policyno": p.policyno, "cob": p.cob, "product": p.product,
            "gwp": p.gwp, "tsi": p.tsi, "smethode": p.smethode,
            "begindt": str(p.begindt), "enddt": str(p.enddt),
        }
        for p in policies[:5]
    ]

    return UploadResponse(
        success=True,
        filename=file.filename or "",
        rows_parsed=len(policies),
        errors=errors,
        preview=preview,
    )


@router.post("/assumptions", response_model=UploadResponse, summary="Upload Asumsi (01-templateassumption.xlsx)")
async def upload_assumptions(file: UploadFile = File(...)) -> UploadResponse:
    """Upload file 01-templateassumption.xlsx berisi asumsi aktuaria per COB."""
    content = await file.read()
    assumptions, errors = parse_assumptions(content)
    _session["assumptions"] = assumptions

    preview = [
        {"cob": a.cob, "syear": a.syear, "expclaim": a.expclaim,
         "expopex": a.expopex, "expriskadj": a.expriskadj}
        for a in assumptions[:5]
    ]

    return UploadResponse(
        success=True, filename=file.filename or "",
        rows_parsed=len(assumptions), errors=errors, preview=preview
    )


@router.post("/tabphei", response_model=UploadResponse, summary="Upload Yield Curve (02-templatetabphei.xlsx)")
async def upload_tabphei(file: UploadFile = File(...)) -> UploadResponse:
    """Upload file 02-templatetabphei.xlsx berisi data yield curve / suku bunga OJK."""
    content = await file.read()
    rows, errors = parse_yield_curve(content)
    _session["yield_curve"] = rows

    preview = [
        {"sdate": str(r.sdate), "srate": r.srate, "syear": r.syear}
        for r in rows[:5]
    ]

    return UploadResponse(
        success=True, filename=file.filename or "",
        rows_parsed=len(rows), errors=errors, preview=preview
    )


@router.post("/lapse", response_model=UploadResponse, summary="Upload Lapse Table (03-templatelapse.xlsx)")
async def upload_lapse(file: UploadFile = File(...)) -> UploadResponse:
    """Upload file 03-templatelapse.xlsx berisi tabel lapse per bulan per COB."""
    content = await file.read()
    rows, errors = parse_lapse(content)
    _session["lapse"] = rows

    preview = [
        {"cob": r.cob, "syear": r.syear, "smonth_th": r.smonth_th, "srate": r.srate}
        for r in rows[:5]
    ]

    return UploadResponse(
        success=True, filename=file.filename or "",
        rows_parsed=len(rows), errors=errors, preview=preview
    )


@router.post("/batch-calculate", summary="Proses Kalkulasi Batch Semua Polis")
async def batch_calculate(
    req: BatchCalcRequest = BatchCalcRequest(),
) -> dict:
    """
    Jalankan kalkulasi BBA/PAA/GMM untuk semua polis yang sudah diupload.
    Pastikan upload portfolio terlebih dahulu.
    """
    policies: list[PolicyRecord] = _session.get("policies", [])
    if not policies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Belum ada data polis. Upload portfolio terlebih dahulu.",
        )

    svc = BatchService(audit_service=AuditService())
    result = svc.run(
        policies=policies,
        assumptions=_session.get("assumptions", []),
        yield_curve=_session.get("yield_curve", []),
        lapse_rows=_session.get("lapse", []),
    )

    return result


@router.get("/session-status", summary="Status Data yang Sudah Diupload")
async def session_status() -> dict:
    """Lihat berapa banyak data yang sudah diupload per kategori."""
    # Inforce summary
    inforce_data = _session.get("inforce", {})
    inforce_summary = {}
    for period_key, parsed in inforce_data.items():
        inforce_summary[period_key] = {
            "year": parsed.year,
            "month": parsed.month,
            "records": len(parsed.records),
            "stoploss": len(parsed.stoploss),
        }

    # Assumptions v2 summary
    assumptions_v2 = _session.get("assumptions_v2")
    assumptions_v2_status = None
    if assumptions_v2:
        assumptions_v2_status = {
            "available_years": assumptions_v2.available_years,
            "loss_ratio_products": len(assumptions_v2.loss_ratio_by_product),
            "loss_ratio_cobs": len(assumptions_v2.loss_ratio_by_cob),
            "pad_tables": len(assumptions_v2.pad_tables),
            "iche_entries": len(assumptions_v2.iche),
            "discount_rate_years": len(assumptions_v2.discount_rates),
            "inflation_entries": len(assumptions_v2.inflation_monthly),
            "lapse_durations": len(assumptions_v2.lapse.ratios),
            "expense_years": len(assumptions_v2.expense.total_ratios),
        }

    # OJK codes
    ojk = _session.get("ojk_codes")

    return {
        "policies": len(_session.get("policies", [])),
        "assumptions": len(_session.get("assumptions", [])),
        "yield_curve": len(_session.get("yield_curve", [])),
        "lapse": len(_session.get("lapse", [])),
        "inforce": inforce_summary,
        "inforce_periods": len(inforce_data),
        "assumptions_v2": assumptions_v2_status,
        "ojk_codes": len(ojk.codes) if ojk else 0,
    }


# ──────────────────────────────────────────────
#  New endpoints for production data files
# ──────────────────────────────────────────────

@router.post("/inforce", response_model=UploadResponse,
             summary="Upload Inforce Data (INFORCE bulanan .xlsx/.xlsb)")
async def upload_inforce(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload file INFORCE bulanan atau tahunan.
    Mendukung format .xlsx dan .xlsb.
    Sheet yang dibaca: INSURANCE CONTRACT, STOPLOSS, Pivot
    File besar (~50-60MB, ~200K baris) – proses streaming.
    """
    content = await file.read()
    filename = file.filename or ""
    logger.info(f"Parsing inforce file: {filename} ({len(content)} bytes)")

    parsed = parse_inforce(content, filename=filename)

    if not parsed.records and parsed.errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=parsed.errors
        )

    # Store by "YYYY-MM" key for monthly support
    month_str = str(parsed.month).zfill(2) if parsed.month else "12"
    period_key = f"{parsed.year}-{month_str}"
    _session["inforce"][period_key] = parsed

    preview = [
        {
            "policyno": r.policyno, "cob": r.cob, "product": r.product,
            "gwp": r.gwp, "ngwp": r.ngwp, "tsi": r.tsi,
            "smethode": r.smethode, "begindt": str(r.begindt),
            "enddt": str(r.enddt), "ripremi": r.ripremi,
        }
        for r in parsed.records[:5]
    ]

    return UploadResponse(
        success=True,
        filename=filename,
        rows_parsed=len(parsed.records),
        errors=parsed.errors,
        preview=preview,
    )


@router.post("/assumptions-v2", response_model=UploadResponse,
             summary="Upload Asumsi Konsolidasi (ASUMSI 2020-2025.xlsx)")
async def upload_assumptions_v2(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload file ASUMSI 2020-2025 berisi asumsi konsolidasi.
    Sheet: Loss Ratio, PAD, ICHE, Bunga Diskonto, Inflasi, Lapse, Expense, Summary.
    """
    content = await file.read()
    assumptions, errors = parse_consolidated_assumptions(content)

    if not assumptions.loss_ratio_by_cob and errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=errors
        )

    _session["assumptions_v2"] = assumptions

    preview = [
        {
            "cob": lr.cob,
            "years": list(lr.ratios.keys()),
            "latest_ratio": lr.ratios.get(max(lr.ratios.keys())) if lr.ratios else None,
        }
        for lr in assumptions.loss_ratio_by_cob[:5]
    ]

    total_items = (
        len(assumptions.loss_ratio_by_product)
        + len(assumptions.loss_ratio_by_cob)
        + len(assumptions.iche)
        + len(assumptions.discount_rates)
        + len(assumptions.inflation_monthly)
        + len(assumptions.lapse.ratios)
    )

    return UploadResponse(
        success=True,
        filename=file.filename or "",
        rows_parsed=total_items,
        errors=errors,
        preview=preview,
    )


@router.post("/ojk-codes", response_model=UploadResponse,
             summary="Upload Kode OJK (SANDI LINI USAHA.xlsx)")
async def upload_ojk_codes(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload file SANDI LINI USAHA BERDASARKAN OJK APOLLO.
    Berisi mapping kode OJK (501-521) ke nama lini usaha.
    """
    content = await file.read()
    table, errors = parse_ojk_codes(content)

    if not table.codes and errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=errors
        )

    _session["ojk_codes"] = table

    preview = [
        {"sandi": c.sandi, "lini_usaha": c.lini_usaha}
        for c in table.codes[:10]
    ]

    return UploadResponse(
        success=True,
        filename=file.filename or "",
        rows_parsed=len(table.codes),
        errors=errors,
        preview=preview,
    )


# ──────────────────────────────────────────────
#  Batch calculate from inforce data
# ──────────────────────────────────────────────

@router.post("/batch-calculate-inforce",
             summary="Kalkulasi PAA/GMM dari Data Inforce")
async def batch_calculate_inforce(
    req: BatchCalcRequest = BatchCalcRequest(),
) -> dict:
    """
    Jalankan kalkulasi PAA/GMM menggunakan data inforce yang sudah diupload.
    Langkah:
      1. Konversi semua InforceRecord → PolicyRecord
      2. De-duplicate berdasarkan policyno (ambil terbaru)
      3. Jalankan BatchService.run() dengan asumsi yang tersedia
    """
    inforce_data = _session.get("inforce", {})
    if not inforce_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Belum ada data inforce. Upload file inforce terlebih dahulu.",
        )

    # Convert inforce → PolicyRecord
    policies, conversion_stats = multi_inforce_to_policies(inforce_data)

    if not policies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tidak ada polis aktif ditemukan dari data inforce.",
        )

    logger.info(f"Running batch calculation on {len(policies)} inforce policies")

    svc = BatchService(audit_service=AuditService())
    result = svc.run(
        policies=policies,
        assumptions=_session.get("assumptions", []),
        yield_curve=_session.get("yield_curve", []),
        lapse_rows=_session.get("lapse", []),
    )

    # Tambah conversion stats ke result
    result["inforce_conversion"] = conversion_stats

    return result

