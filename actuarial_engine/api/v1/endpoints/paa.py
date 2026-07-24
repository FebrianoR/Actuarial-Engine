"""
PAA API Endpoint – Premium Allocation Approach (PSAK 117 Par. 53-59)
"""
from fastapi import APIRouter, Depends

from actuarial_engine.models.schemas.paa_schemas import PAAInput, PAAOutput
from actuarial_engine.services.paa_service import PAAService
from actuarial_engine.services.audit_service import AuditService
from actuarial_engine.api.v1.dependencies.auth import verify_api_key

router = APIRouter(dependencies=[Depends(verify_api_key)])


def get_paa_service() -> PAAService:
    return PAAService(audit_service=AuditService())


@router.post("/calculate", response_model=PAAOutput, summary="Hitung Liabilitas PAA")
async def calculate_paa(
    payload: PAAInput,
    service: PAAService = Depends(get_paa_service),
) -> PAAOutput:
    """
    PAA digunakan untuk kontrak asuransi jangka pendek (≤ 1 tahun).
    Menghitung:
    - Liability for Remaining Coverage (LRC) = Unearned Premium − DAC
    - Liability for Incurred Claims (LIC) = Outstanding + IBNR
    - Total liabilitas = LRC + LIC
    """
    return await service.calculate(payload)
