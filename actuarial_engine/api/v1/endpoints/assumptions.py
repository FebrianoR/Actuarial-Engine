"""
Assumptions Endpoint – CRUD untuk model asumsi aktuaria.
Asumsi disimpan di /data/assumptions/ sebagai JSON (versi-terkontrol).
"""
from fastapi import APIRouter, Depends, HTTPException, status

from actuarial_engine.models.assumptions.base_assumptions import AssumptionSet
from actuarial_engine.services.assumption_service import AssumptionService
from actuarial_engine.api.v1.dependencies.auth import verify_api_key

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get("/", response_model=list[AssumptionSet], summary="Daftar Semua Asumsi")
async def list_assumptions(service: AssumptionService = Depends()) -> list[AssumptionSet]:
    return await service.list_all()


@router.get("/{assumption_id}", response_model=AssumptionSet,  summary="Detail Asumsi")
async def get_assumption(assumption_id: str, service: AssumptionService = Depends()) -> AssumptionSet:
    result = await service.get_by_id(assumption_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asumsi tidak ditemukan")
    return result


@router.post("/", response_model=AssumptionSet, status_code=status.HTTP_201_CREATED, summary="Buat Asumsi Baru")
async def create_assumption(payload: AssumptionSet, service: AssumptionService = Depends()) -> AssumptionSet:
    return await service.create(payload)
