"""
PAA Service – Orchestrator kalkulasi Premium Allocation Approach.
"""
from __future__ import annotations

from datetime import datetime, timezone

from actuarial_engine.core.paa.calculator import PAACalculator
from actuarial_engine.audit.trace import AuditTrace
from actuarial_engine.models.schemas.paa_schemas import PAAInput, PAAOutput
from actuarial_engine.services.audit_service import AuditService


class PAAService:
    """Service layer untuk kalkulasi PAA."""

    def __init__(self, audit_service: AuditService = None) -> None:
        self._audit_svc = audit_service or AuditService()

    async def calculate(self, payload: PAAInput) -> PAAOutput:
        """Orchestrate kalkulasi PAA end-to-end."""

        calculator = PAACalculator(
            written_premium=payload.written_premium,
            coverage_start=payload.coverage_start,
            coverage_end=payload.coverage_end,
            reporting_date=payload.reporting_date,
            claims_incurred=payload.claims_incurred,
            outstanding_claims=payload.outstanding_claims,
            ibnr_ratio=payload.ibnr_ratio,
            acquisition_cost_ratio=payload.acquisition_cost_ratio,
            amortize_dac=payload.amortize_dac,
            discount_rate=payload.discount_rate,
        )
        result = calculator.calculate()

        trace = AuditTrace(
            calculation_type="PAA",
            assumption_version=payload.assumption_version,
        )
        trace.steps = result.intermediate_steps

        output_dict = {
            "lrc_net": result.lrc_net,
            "lic": result.lic,
            "total_liability": result.total_liability,
            "loss_ratio": result.loss_ratio,
        }

        self._audit_svc.save(
            trace=trace,
            contract_id=payload.contract_id,
            input_snapshot=payload.model_dump(mode="json"),
            output_snapshot=output_dict,
        )

        return PAAOutput(
            contract_id=payload.contract_id,
            lrc_gross=result.lrc_gross,
            dac=result.dac,
            lrc_net=result.lrc_net,
            outstanding_claims=result.outstanding_claims,
            ibnr=result.ibnr,
            lic=result.lic,
            total_liability=result.total_liability,
            earned_premium=result.earned_premium,
            unearned_premium=result.unearned_premium,
            loss_ratio=result.loss_ratio,
            trace_id=trace.trace_id,
            calculation_date=datetime.now(timezone.utc),
            assumption_version=payload.assumption_version,
        )
