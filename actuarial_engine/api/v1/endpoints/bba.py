"""
BBA API Endpoint – Building Block Approach (PSAK 117)
Layer tipis yang menerima request, mendelegasikan ke service layer.
"""
from fastapi import APIRouter, Depends

from actuarial_engine.models.schemas.bba_schemas import BBAInput, BBAOutput
from actuarial_engine.services.bba_service import BBAService
from actuarial_engine.services.audit_service import AuditService
from actuarial_engine.api.v1.dependencies.auth import verify_api_key

router = APIRouter(dependencies=[Depends(verify_api_key)])


def get_bba_service() -> BBAService:
    return BBAService(audit_service=AuditService())


@router.post("/calculate", response_model=BBAOutput, summary="Hitung Liabilitas BBA")
async def calculate_bba(
    payload: BBAInput,
    service: BBAService = Depends(get_bba_service),
) -> BBAOutput:
    """
    Menghitung komponen BBA (PSAK 117 Par. 32-44):
    - Present Value of Future Cash Flows (PVFCF)
    - Risk Adjustment (RA) – Cost of Capital method
    - Contractual Service Margin (CSM)
    - Fulfilment Cash Flows (FCF)
    - Insurance Contract Liability (ICL)

    Setiap kalkulasi menghasilkan audit trace yang dapat diambil
    melalui endpoint /audit/{trace_id}.
    """
    return await service.calculate(payload)
