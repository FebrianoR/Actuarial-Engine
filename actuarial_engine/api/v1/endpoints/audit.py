"""
Audit Endpoint – Membaca trail perhitungan untuk keperluan review SPA-04.
Setiap kalkulasi menghasilkan satu audit record yang berisi:
- Input lengkap
- Intermediate values (setiap langkah)
- Output final
- Timestamp dan versi asumsi yang digunakan
"""
from fastapi import APIRouter, Depends, Query
from actuarial_engine.models.schemas.audit_schemas import AuditRecord
from actuarial_engine.services.audit_service import AuditService
from actuarial_engine.api.v1.dependencies.auth import verify_api_key

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get("/", response_model=list[AuditRecord], summary="Daftar Audit Record")
async def list_audit_records(
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    service: AuditService = Depends(),
) -> list[AuditRecord]:
    return await service.list_records(limit=limit, offset=offset)


@router.get("/{record_id}", response_model=AuditRecord, summary="Detail Audit Record")
async def get_audit_record(record_id: str, service: AuditService = Depends()) -> AuditRecord:
    return await service.get_record(record_id)
