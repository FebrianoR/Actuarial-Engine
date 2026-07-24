"""
Core BBA Calculator – Building Block Approach (PSAK 117)

Modul ini TIDAK mengetahui keberadaan FastAPI, database, atau HTTP.
Menerima data domain murni, mengembalikan data domain murni.
Dapat diuji secara independen tanpa menjalankan server.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np

from actuarial_engine.core.cashflows.projector import CashFlowProjection
from actuarial_engine.core.discount.yield_curve import DiscountCurve
from actuarial_engine.core.risk_adjustment.calculator import RiskAdjustmentCalculator
from actuarial_engine.core.csm.tracker import CSMTracker
from actuarial_engine.audit.trace import AuditTrace


@dataclass
class BBAResult:
    """Hasil perhitungan BBA yang deterministik dan dapat di-audit."""
    pvfcf: float                        # Present Value of Future Cash Flows
    risk_adjustment: float              # Risk Adjustment (RA)
    csm: float                          # Contractual Service Margin
    fulfilment_cash_flows: float        # FCF = PVFCF + RA
    insurance_contract_liability: float # ICL = FCF + CSM
    intermediate_steps: dict = field(default_factory=dict)  # Untuk audit trail


class BBACalculator:
    """
    Implementasi perhitungan BBA sesuai PSAK 117 Paragraf 32-44.

    Menerima CashFlowProjection (hasil project()) secara langsung
    agar dapat diuji tanpa perlu melalui CashFlowProjector.

    Alur:
        1. Arus kas sudah diproyeksikan (CashFlowProjection diberikan langsung)
        2. Diskon ke nilai kini menggunakan yield curve sesuai PSAK 117 Par. 36
        3. Hitung Risk Adjustment dengan teknik yang dipilih (Par. 37)
        4. Tentukan CSM pada pengakuan awal dan amortisasinya (Par. 38-39)
    """

    def __init__(
        self,
        cash_flow_projector: CashFlowProjection,
        discount_curve: DiscountCurve,
        ra_calculator: RiskAdjustmentCalculator,
        csm_tracker: CSMTracker,
    ) -> None:
        # Nama parameter dipertahankan untuk backward-compat dengan test
        self._projection = cash_flow_projector
        self._curve = discount_curve
        self._ra_calc = ra_calculator
        self._csm_tracker = csm_tracker

    def calculate(self, audit_trace: AuditTrace | None = None) -> BBAResult:
        """
        Hitung liabilitas BBA.

        Args:
            audit_trace: Objek logging untuk mencatat setiap langkah kalkulasi.
                         Jika None, perhitungan tetap berjalan tanpa logging.

        Returns:
            BBAResult: Semua komponen liabilitas beserta intermediate values.
        """
        # Langkah 1: Gunakan proyeksi yang sudah diberikan
        projected_cfs = self._projection
        if audit_trace:
            audit_trace.record("projected_cash_flows", projected_cfs.to_dict())

        # Langkah 2: Hitung Present Value
        pv_inflows = self._curve.discount(projected_cfs.inflows)
        pv_outflows = self._curve.discount(projected_cfs.outflows)
        pvfcf = float(np.sum(pv_outflows) - np.sum(pv_inflows))
        if audit_trace:
            audit_trace.record("pvfcf", pvfcf)

        # Langkah 3: Hitung Risk Adjustment
        ra = self._ra_calc.calculate(projected_cfs)
        if audit_trace:
            audit_trace.record("risk_adjustment", ra)

        # Langkah 4: Fulfilment Cash Flows
        fcf = pvfcf + ra

        # Langkah 5: CSM (nol jika kontrak merugi / onerous)
        csm = self._csm_tracker.determine_initial_csm(fcf)
        if audit_trace:
            audit_trace.record("csm", csm)

        icl = fcf + csm

        return BBAResult(
            pvfcf=pvfcf,
            risk_adjustment=ra,
            csm=csm,
            fulfilment_cash_flows=fcf,
            insurance_contract_liability=icl,
            intermediate_steps=audit_trace.steps if audit_trace else {},
        )
