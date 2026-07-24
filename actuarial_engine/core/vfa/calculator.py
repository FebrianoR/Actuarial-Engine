"""
VFA Calculator – Variable Fee Approach (PSAK 117 Par. 45-46)

Untuk kontrak asuransi jiwa dengan fitur partisipasi langsung
(direct participating contracts), dimana:
- Insurer menanggung underlying items (investasi) atas nama pemegang polis
- Pemegang polis berhak atas porsi yang substansial dari fair value underlying items
- Insurer mendapatkan variable fee = share underlying items − PVFCF

Kunci VFA vs BBA:
- CSM di-update setiap period untuk perubahan variable fee (bukan dikunci)
- CSM absorbs changes in variable fee (entity's share of underlying items)
- PVFCF diitung sama seperti BBA, RA sama
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from actuarial_engine.core.cashflows.projector import CashFlowProjection
from actuarial_engine.core.discount.yield_curve import DiscountCurve
from actuarial_engine.core.risk_adjustment.calculator import RiskAdjustmentCalculator
from actuarial_engine.audit.trace import AuditTrace


@dataclass
class VFAResult:
    """Hasil perhitungan VFA."""
    pvfcf: float                       # Present Value of Future Cash Flows
    risk_adjustment: float             # RA
    fulfilment_cash_flows: float       # FCF = PVFCF + RA
    underlying_items_fair_value: float # Fair value underlying items
    entity_share: float                # Entity's share (%)
    entity_share_value: float          # = FV × share%
    variable_fee: float                # Variable fee = entity_share_value − PVFCF
    csm: float                         # CSM = max(0, variable_fee − RA)
    insurance_contract_liability: float # ICL = FCF + CSM
    intermediate_steps: dict = field(default_factory=dict)


class VFACalculator:
    """
    Implementasi VFA sesuai PSAK 117 Par. 45-46.

    Args:
        cash_flow_projector: projeksi arus kas
        discount_curve: yield curve untuk mendiskon
        ra_calculator: risk adjustment calculator
        underlying_items_fair_value: fair value total underlying items
        entity_share_pct: porsi entitas atas underlying items (0-1)
    """

    def __init__(
        self,
        cash_flow_projector: CashFlowProjection,
        discount_curve: DiscountCurve,
        ra_calculator: RiskAdjustmentCalculator,
        underlying_items_fair_value: float,
        entity_share_pct: float,
    ) -> None:
        self._projection = cash_flow_projector
        self._curve = discount_curve
        self._ra_calc = ra_calculator
        self._fv = underlying_items_fair_value
        self._share_pct = entity_share_pct

    def calculate(self, audit_trace: AuditTrace | None = None) -> VFAResult:
        """Hitung komponen VFA."""
        # Langkah 1: PVFCF (sama seperti BBA)
        pv_inflows = self._curve.discount(self._projection.inflows)
        pv_outflows = self._curve.discount(self._projection.outflows)
        pvfcf = float(np.sum(pv_outflows) - np.sum(pv_inflows))

        if audit_trace:
            audit_trace.record("pvfcf_vfa", pvfcf)

        # Langkah 2: RA
        ra = self._ra_calc.calculate(self._projection)
        if audit_trace:
            audit_trace.record("risk_adjustment_vfa", ra)

        # Langkah 3: FCF = PVFCF + RA
        fcf = pvfcf + ra

        # Langkah 4: Entity's share of underlying items
        entity_share_value = self._fv * self._share_pct
        if audit_trace:
            audit_trace.record("entity_share_value", entity_share_value)

        # Langkah 5: Variable Fee = entity's share − PVFCF (Par. 45b)
        variable_fee = entity_share_value - pvfcf

        # Langkah 6: CSM = max(0, variable_fee - RA)
        csm = max(0.0, variable_fee - ra)
        if audit_trace:
            audit_trace.record("csm_vfa", csm)

        # Langkah 7: ICL = FCF + CSM
        icl = fcf + csm

        return VFAResult(
            pvfcf=round(pvfcf, 6),
            risk_adjustment=round(ra, 6),
            fulfilment_cash_flows=round(fcf, 6),
            underlying_items_fair_value=round(self._fv, 6),
            entity_share=self._share_pct,
            entity_share_value=round(entity_share_value, 6),
            variable_fee=round(variable_fee, 6),
            csm=round(csm, 6),
            insurance_contract_liability=round(icl, 6),
            intermediate_steps=audit_trace.steps if audit_trace else {},
        )
