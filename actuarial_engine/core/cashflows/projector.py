"""
Cash Flow Projector – PSAK 117

Memproyeksikan arus kas masa depan (premi, klaim, biaya, surrender)
sepanjang horizon pertanggungan. Modul ini murni domain logic,
tidak bergantung pada FastAPI/database.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass
class CashFlowProjection:
    """
    Hasil proyeksi arus kas per periode (tahun).

    inflows  : premi yang diharapkan masuk (gross premium)
    outflows : klaim + biaya + pembayaran surrender yang diharapkan keluar
    periods  : label periode (mis: [1, 2, 3, ...])
    """
    inflows: list[float]
    outflows: list[float]
    periods: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        if len(self.inflows) != len(self.outflows):
            raise ValueError(
                f"Panjang inflows ({len(self.inflows)}) "
                f"harus sama dengan outflows ({len(self.outflows)})"
            )
        if not self.periods:
            self.periods = list(range(1, len(self.inflows) + 1))

    def net_cash_flows(self) -> list[float]:
        """Net cash flow = outflows - inflows (positif = liabilitas neto)."""
        return [o - i for i, o in zip(self.inflows, self.outflows)]

    def to_dict(self) -> dict:
        return {
            "periods": self.periods,
            "inflows": self.inflows,
            "outflows": self.outflows,
            "net_cash_flows": self.net_cash_flows(),
        }


class CashFlowProjector:
    """
    Proyektor arus kas berbasis asumsi aktuaria.

    Input asumsi:
      - gross_premium        : premi bruto per tahun (konstan atau array)
      - sum_assured          : uang pertanggungan
      - coverage_years       : lama pertanggungan (tahun)
      - mortality_rates      : qx per tahun (list panjang coverage_years)
      - lapse_rates          : lapse rate per tahun
      - expense_ratio        : rasio biaya terhadap premi (awal tahun)
      - maintenance_per_year : biaya pemeliharaan tetap per tahun
      - inflation_rate        : inflasi biaya per tahun
    """

    def __init__(
        self,
        gross_premium: float | Sequence[float],
        sum_assured: float,
        coverage_years: int,
        mortality_rates: Sequence[float],
        lapse_rates: Sequence[float],
        expense_ratio: float = 0.05,
        maintenance_per_year: float = 0.0,
        inflation_rate: float = 0.03,
    ) -> None:
        self._years = coverage_years
        self._sa = sum_assured
        self._expense_ratio = expense_ratio
        self._maintenance = maintenance_per_year
        self._inflation = inflation_rate

        # Konversi scalar ke list
        if isinstance(gross_premium, (int, float)):
            self._premiums: list[float] = [float(gross_premium)] * coverage_years
        else:
            self._premiums = list(gross_premium)

        # Pad atau potong asumsi agar sesuai coverage_years
        self._qx = self._pad(list(mortality_rates), coverage_years)
        self._lx = self._pad(list(lapse_rates), coverage_years)

    @staticmethod
    def _pad(data: list[float], length: int) -> list[float]:
        """Pad list dengan nilai terakhir, atau potong jika lebih panjang."""
        if len(data) >= length:
            return data[:length]
        return data + [data[-1]] * (length - len(data))

    def project(self) -> CashFlowProjection:
        """
        Proyeksikan arus kas selama coverage_years tahun.

        Menggunakan metode kohort tunggal (1 polis aktif di t=0).
        Policyholder decrements: mortalitas dan lapse (multiple-decrement).
        """
        inflows: list[float] = []
        outflows: list[float] = []

        # l(x) = jumlah polis aktif (dimulai dari 1.0 = 100%)
        active = 1.0

        for t in range(self._years):
            qx = self._qx[t]
            lx = self._lx[t]

            # Premi masuk di awal tahun (dari polis yang masih aktif)
            premium_inflow = active * self._premiums[t]

            # Klaim mortalitas: active × qx × SA
            death_claims = active * qx * self._sa

            # Biaya (pro rata terhadap premi + inflasi)
            inflated_maintenance = self._maintenance * ((1 + self._inflation) ** t)
            expenses = active * (self._expense_ratio * self._premiums[t] + inflated_maintenance)

            # Total outflow tahun ini
            total_outflow = death_claims + expenses

            inflows.append(round(premium_inflow, 6))
            outflows.append(round(total_outflow, 6))

            # Decrement: kurangi aktif karena mortalitas dan lapse
            active = active * (1 - qx) * (1 - lx)

        return CashFlowProjection(
            inflows=inflows,
            outflows=outflows,
            periods=list(range(1, self._years + 1)),
        )
