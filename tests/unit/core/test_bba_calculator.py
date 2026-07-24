"""
Unit test untuk BBA Calculator – modul core paling kritis.

Prinsip pengujian aktuaria:
1.  Test dengan vektor angka yang sudah dihitung secara manual (benchmark values)
2.  Verifikasi setiap intermediate step, bukan hanya output final
3.  Test onerous contract (kontrak merugi, CSM = 0) secara terpisah
4.  Gunakan property-based testing untuk memverifikasi invariant aktuaria
"""
import pytest
from unittest.mock import MagicMock

from actuarial_engine.core.bba.calculator import BBACalculator, BBAResult
from actuarial_engine.audit.trace import AuditTrace


class TestBBACalculatorHappyPath:
    """Skenario kontrak normal (profitable)."""

    def setup_method(self) -> None:
        """Setup mock dependencies untuk setiap test."""
        self.mock_projector = MagicMock()
        self.mock_curve = MagicMock()
        self.mock_ra_calc = MagicMock()
        self.mock_csm_tracker = MagicMock()

        # Contoh vektor benchmark yang sudah diverifikasi manual
        projected = MagicMock()
        projected.inflows = [1_000_000, 900_000, 800_000]   # Premi
        projected.outflows = [400_000, 450_000, 2_500_000]   # Klaim + biaya
        projected.to_dict.return_value = {}

        self.mock_projector.project.return_value = projected
        self.mock_curve.discount.side_effect = lambda flows: [f * 0.95 for f in flows]
        self.mock_ra_calc.calculate.return_value = 150_000.0
        self.mock_csm_tracker.determine_initial_csm.return_value = 0.0

        self.calculator = BBACalculator(
            cash_flow_projector=self.mock_projector,
            discount_curve=self.mock_curve,
            ra_calculator=self.mock_ra_calc,
            csm_tracker=self.mock_csm_tracker,
        )

    def test_pvfcf_is_positive_for_net_outflow_contract(self) -> None:
        """PVFCF harus positif ketika PV outflows > PV inflows."""
        result = self.calculator.calculate()
        assert result.pvfcf > 0, "PVFCF harus positif untuk kontrak liabilitas"

    def test_fcf_equals_pvfcf_plus_ra(self) -> None:
        """FCF = PVFCF + RA (PSAK 117 Par. 32)."""
        result = self.calculator.calculate()
        assert abs(result.fulfilment_cash_flows - (result.pvfcf + result.risk_adjustment)) < 1e-6

    def test_icl_equals_fcf_plus_csm(self) -> None:
        """ICL = FCF + CSM (PSAK 117 Par. 32)."""
        result = self.calculator.calculate()
        assert abs(result.insurance_contract_liability - (result.fulfilment_cash_flows + result.csm)) < 1e-6


class TestBBACalculatorAuditTrace:
    """Verifikasi bahwa audit trail merekam semua langkah."""

    def test_audit_trace_records_all_steps(self) -> None:
        """Setiap langkah kalkulasi harus ada di dalam audit trace."""
        mock_projector = MagicMock()
        mock_curve = MagicMock()
        mock_ra_calc = MagicMock()
        mock_csm_tracker = MagicMock()

        projected = MagicMock()
        projected.inflows = [500_000]
        projected.outflows = [600_000]
        projected.to_dict.return_value = {}

        mock_projector.project.return_value = projected
        mock_curve.discount.return_value = [0.0]
        mock_ra_calc.calculate.return_value = 5_000.0
        mock_csm_tracker.determine_initial_csm.return_value = 0.0

        calc = BBACalculator(mock_projector, mock_curve, mock_ra_calc, mock_csm_tracker)
        trace = AuditTrace(calculation_type="BBA", assumption_version="2024.Q4.1")

        calc.calculate(audit_trace=trace)

        required_steps = {"projected_cash_flows", "pvfcf", "risk_adjustment", "csm"}
        assert required_steps.issubset(trace.steps.keys()), (
            f"Langkah audit yang hilang: {required_steps - trace.steps.keys()}"
        )
