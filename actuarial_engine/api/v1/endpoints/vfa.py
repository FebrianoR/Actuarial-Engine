"""
VFA API Endpoint – Variable Fee Approach (PSAK 117 Par. 45-46)
Untuk kontrak asuransi jiwa dengan fitur partisipasi (participating fund).
"""
from fastapi import APIRouter, Depends

from actuarial_engine.models.schemas.vfa_schemas import VFAInput, VFAOutput
from actuarial_engine.services.vfa_service import VFAService
from actuarial_engine.services.audit_service import AuditService
from actuarial_engine.api.v1.dependencies.auth import verify_api_key

router = APIRouter(dependencies=[Depends(verify_api_key)])


def get_vfa_service() -> VFAService:
    return VFAService(audit_service=AuditService())


@router.post("/calculate", response_model=VFAOutput, summary="Hitung Liabilitas VFA")
async def calculate_vfa(
    payload: VFAInput,
    service: VFAService = Depends(get_vfa_service),
) -> VFAOutput:
    """
    VFA menggantikan CSM dengan Variable Fee atas underlying items.
    Cocok untuk produk unit-link dan produk partisipasi lainnya.
    Menghitung:
    - Entity's share of underlying items fair value
    - Variable Fee = entity share − PVFCF
    - CSM = max(0, variable_fee − RA)
    """
    return await service.calculate(payload)
