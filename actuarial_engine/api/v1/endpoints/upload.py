"""
Upload Endpoints – Menerima file Excel template PSAK 117

Endpoints:
  POST /upload/portfolio   – Upload 00-Templateupload.xlsx
  POST /upload/assumptions – Upload 01-templateassumption.xlsx
  POST /upload/tabphei     – Upload 02-templatetabphei.xlsx (yield curve)
  POST /upload/lapse       – Upload 03-templatelapse.xlsx
  POST /upload/batch-calculate – Proses semua yang sudah diupload
"""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from pydantic import BaseModel

from actuarial_engine.core.excel.parser import (
    parse_portfolio, parse_assumptions, parse_yield_curve, parse_lapse,
    PolicyRecord, AssumptionRow, YieldCurveRow, LapseRow,
)
from actuarial_engine.services.batch_service import BatchService
from actuarial_engine.services.audit_service import AuditService
from actuarial_engine.api.v1.dependencies.auth import verify_api_key

router = APIRouter(dependencies=[Depends(verify_api_key)])

# In-memory session store (per request tidak persistent – direset tiap upload baru)
_session: dict[str, Any] = {
    "policies": [],
    "assumptions": [],
    "yield_curve": [],
    "lapse": [],
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
    return {
        "policies": len(_session.get("policies", [])),
        "assumptions": len(_session.get("assumptions", [])),
        "yield_curve": len(_session.get("yield_curve", [])),
        "lapse": len(_session.get("lapse", [])),
    }
