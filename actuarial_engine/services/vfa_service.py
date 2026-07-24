"""
VFA Service – Orchestrator kalkulasi Variable Fee Approach.
"""
from __future__ import annotations

from datetime import datetime, timezone

from actuarial_engine.core.cashflows.projector import CashFlowProjector
from actuarial_engine.core.discount.yield_curve import DiscountCurve
from actuarial_engine.core.risk_adjustment.calculator import RiskAdjustmentCalculator
from actuarial_engine.core.vfa.calculator import VFACalculator
from actuarial_engine.audit.trace import AuditTrace
from actuarial_engine.models.schemas.vfa_schemas import VFAInput, VFAOutput
from actuarial_engine.services.audit_service import AuditService


class VFAService:
    """Service layer untuk kalkulasi VFA."""

    def __init__(self, audit_service: AuditService = None) -> None:
        self._audit_svc = audit_service or AuditService()

    async def calculate(self, payload: VFAInput) -> VFAOutput:
        """Orchestrate kalkulasi VFA end-to-end."""

        # Proyektor arus kas
        projector = CashFlowProjector(
            gross_premium=payload.gross_premium,
            sum_assured=payload.sum_assured,
            coverage_years=payload.coverage_years,
            mortality_rates=payload.mortality_rates,
            lapse_rates=payload.lapse_rates,
            expense_ratio=payload.expense_ratio,
            maintenance_per_year=payload.maintenance_per_year,
            inflation_rate=payload.inflation_rate,
        )
        projection = projector.project()

        rates_int = {int(k): v for k, v in payload.discount_rates.items()}
        discount_curve = DiscountCurve(rates_int)

        ra_calc = RiskAdjustmentCalculator(
            coc_rate=payload.ra_coc_rate,
            required_capital_ratio=payload.ra_capital_ratio,
            discount_rates=rates_int,
        )

        trace = AuditTrace(
            calculation_type="VFA",
            assumption_version=payload.assumption_version,
        )

        calculator = VFACalculator(
            cash_flow_projector=projection,
            discount_curve=discount_curve,
            ra_calculator=ra_calc,
            underlying_items_fair_value=payload.underlying_items_fair_value,
            entity_share_pct=payload.entity_share_pct,
        )
        result = calculator.calculate(audit_trace=trace)

        output_dict = {
            "variable_fee": result.variable_fee,
            "csm": result.csm,
            "insurance_contract_liability": result.insurance_contract_liability,
        }

        self._audit_svc.save(
            trace=trace,
            contract_id=payload.contract_id,
            input_snapshot=payload.model_dump(mode="json"),
            output_snapshot=output_dict,
        )

        return VFAOutput(
            contract_id=payload.contract_id,
            pvfcf=result.pvfcf,
            risk_adjustment=result.risk_adjustment,
            fulfilment_cash_flows=result.fulfilment_cash_flows,
            underlying_items_fair_value=result.underlying_items_fair_value,
            entity_share=result.entity_share,
            entity_share_value=result.entity_share_value,
            variable_fee=result.variable_fee,
            csm=result.csm,
            insurance_contract_liability=result.insurance_contract_liability,
            trace_id=trace.trace_id,
            calculation_date=datetime.now(timezone.utc),
            assumption_version=payload.assumption_version,
        )
