"""
Export Endpoints – Download hasil kalkulasi sebagai Excel atau CSV.
"""
from __future__ import annotations

from datetime import datetime
from io import StringIO
import csv

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from io import BytesIO

from actuarial_engine.services.batch_service import get_batch
from actuarial_engine.core.excel.exporter import export_results
from actuarial_engine.api.v1.dependencies.auth import verify_api_key

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get("/excel/{batch_id}", summary="Export Hasil Kalkulasi ke Excel")
async def export_excel(
    batch_id: str,
    valuation_date: str = Query(None, description="Tanggal valuasi, format DD-MM-YYYY"),
) -> StreamingResponse:
    """
    Download hasil kalkulasi batch dalam format Excel (.xlsx).
    3 sheet: Ringkasan, Detail Per Polis, Sistem Pembukuan GMM.
    """
    results = get_batch(batch_id)
    if results is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch '{batch_id}' tidak ditemukan. Jalankan batch-calculate terlebih dahulu.",
        )

    val_date = valuation_date or datetime.now().strftime("%d-%m-%Y")
    excel_bytes = export_results(results, val_date)

    filename = f"PSAK117_Hasil_{batch_id[:8]}_{datetime.now().strftime('%Y%m%d')}.xlsx"

    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/csv/{batch_id}", summary="Export Hasil Kalkulasi ke CSV")
async def export_csv(batch_id: str) -> StreamingResponse:
    """
    Download hasil kalkulasi batch dalam format CSV.
    """
    results = get_batch(batch_id)
    if results is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch '{batch_id}' tidak ditemukan.",
        )

    buf = StringIO()
    if results:
        fieldnames = [k for k in results[0].keys() if k not in ("error",)]
        writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in results:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    filename = f"PSAK117_Hasil_{batch_id[:8]}_{datetime.now().strftime('%Y%m%d')}.csv"

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
