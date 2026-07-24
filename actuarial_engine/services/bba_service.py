"""
BBA Service – Orchestrator kalkulasi Building Block Approach.

Tanggung jawab:
1. Terima BBAInput
2. Bangun dependencies: CashFlowProjector, DiscountCurve, RACalc, CSMTracker
3. Jalankan BBACalculator.calculate() dengan AuditTrace
4. Simpan audit record
5. Kembalikan BBAOutput
"""
from __future__ import annotations

from datetime import datetime, timezone

from actuarial_engine.core.bba.calculator import BBACalculator
from actuarial_engine.core.cashflows.projector import CashFlowProjector
from actuarial_engine.core.discount.yield_curve import DiscountCurve
from actuarial_engine.core.risk_adjustment.calculator import RiskAdjustmentCalculator
from actuarial_engine.core.csm.tracker import CSMTracker
from actuarial_engine.audit.trace import AuditTrace
from actuarial_engine.models.schemas.bba_schemas import BBAInput, BBAOutput
from actuarial_engine.services.audit_service import AuditService


class BBAService:
    """Service layer untuk kalkulasi BBA."""

    def __init__(self, audit_service: AuditService = None) -> None:
        self._audit_svc = audit_service or AuditService()

    async def calculate(self, payload: BBAInput) -> BBAOutput:
        """Orchestrate kalkulasi BBA end-to-end."""

        # 1. Proyektor arus kas
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

        # 2. Yield curve: konversi key dari str ke int
        rates_int = {int(k): v for k, v in payload.discount_rates.items()}
        discount_curve = DiscountCurve(rates_int)

        # 3. Risk Adjustment
        ra_calc = RiskAdjustmentCalculator(
            coc_rate=payload.ra_coc_rate,
            required_capital_ratio=payload.ra_capital_ratio,
            discount_rates=rates_int,
        )

        # 4. CSM Tracker (coverage units = active polis, disederhanakan)
        csm_tracker = CSMTracker()

        # 5. Calculator + audit trace
        trace = AuditTrace(
            calculation_type="BBA",
            assumption_version=payload.assumption_version,
        )

        calculator = BBACalculator(
            cash_flow_projector=projection,
            discount_curve=discount_curve,
            ra_calculator=ra_calc,
            csm_tracker=csm_tracker,
        )
        result = calculator.calculate(audit_trace=trace)

        # 6. Simpan audit
        output_dict = {
            "pvfcf": result.pvfcf,
            "risk_adjustment": result.risk_adjustment,
            "csm": result.csm,
            "fulfilment_cash_flows": result.fulfilment_cash_flows,
            "insurance_contract_liability": result.insurance_contract_liability,
        }
        self._audit_svc.save(
            trace=trace,
            contract_id=payload.contract_id,
            input_snapshot=payload.model_dump(mode="json"),
            output_snapshot=output_dict,
        )

        # 7. Kembalikan output
        return BBAOutput(
            contract_id=payload.contract_id,
            pvfcf=result.pvfcf,
            risk_adjustment=result.risk_adjustment,
            csm=result.csm,
            fulfilment_cash_flows=result.fulfilment_cash_flows,
            insurance_contract_liability=result.insurance_contract_liability,
            is_onerous=(result.csm == 0.0 and result.fulfilment_cash_flows > 0),
            trace_id=trace.trace_id,
            calculation_date=datetime.now(timezone.utc),
            assumption_version=payload.assumption_version,
        )
