"""
Risk Adjustment Calculator – PSAK 117 Par. 37

Teknik yang diimplementasikan:
1. Cost of Capital (CoC) – default, paling umum di industri Indonesia
2. Confidence Level / VaR – alternatif

CoC Method:
  RA = CoC_rate × Σ (Required_Capital(t) × DF(t))

dimana Required Capital diasumsikan proporsional terhadap PV arus kas
keluar yang tersisa (sebagai proxy risiko non-finansial).
"""
from __future__ import annotations

from actuarial_engine.core.cashflows.projector import CashFlowProjection


class RiskAdjustmentCalculator:
    """
    Menghitung Risk Adjustment menggunakan Cost of Capital method.

    Args:
        coc_rate: Cost of Capital rate tahunan (default 6% = 0.06, umum di IFRS 17)
        required_capital_ratio: Rasio Required Capital terhadap PV arus kas keluar
                                 (default 10%, sebagai proxy SCR sederhana)
        discount_rates: dict tenor → rate untuk mendiskon future CoC charges.
                        Jika None, gunakan flat 6%.
    """

    def __init__(
        self,
        coc_rate: float = 0.06,
        required_capital_ratio: float = 0.10,
        discount_rates: dict[int, float] | None = None,
    ) -> None:
        self._coc = coc_rate
        self._rc_ratio = required_capital_ratio
        self._disc_rates = discount_rates

    def _discount_factor(self, tenor: int) -> float:
        """Discount factor sederhana untuk CoC calculation."""
        if self._disc_rates and tenor in self._disc_rates:
            r = self._disc_rates[tenor]
        elif self._disc_rates:
            # Gunakan rate terakhir tersedia
            max_t = max(self._disc_rates.keys())
            r = self._disc_rates[max_t]
        else:
            r = self._coc  # flat curve = coc rate
        return 1.0 / ((1.0 + r) ** tenor)

    def calculate(self, projection: CashFlowProjection) -> float:
        """
        Hitung Risk Adjustment (RA).

        RA = Σ_t [ CoC_rate × RC(t) × DF(t) ]

        dimana RC(t) = Required Capital pada akhir tahun t
                     = RC_ratio × Σ_{s>t} PV(outflow_s)
        (Required capital mengecil seiring berkurangnya coverage period yang tersisa)

        Returns:
            float: Risk Adjustment dalam unit mata uang
        """
        outflows = projection.outflows
        n = len(outflows)

        if n == 0:
            return 0.0

        # PV outflows kumulatif dari belakang (remaining risk)
        pv_outflows = [
            cf * self._discount_factor(t + 1)
            for t, cf in enumerate(outflows)
        ]

        ra = 0.0
        for t in range(n):
            # RC(t) = rasio × total PV outflows yang tersisa setelah t
            remaining_pv = sum(pv_outflows[t:])
            rc_t = self._rc_ratio * remaining_pv
            # CoC charge tahun t, di-diskon ke t=0
            df = self._discount_factor(t + 1)
            ra += self._coc * rc_t * df

        return round(ra, 6)
