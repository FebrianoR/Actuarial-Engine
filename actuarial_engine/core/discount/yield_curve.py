"""
Yield Curve / Discount Curve – PSAK 117 Par. 36

Mendiskon arus kas masa depan ke nilai kini menggunakan
spot rate curve sesuai dengan persyaratan PSAK 117.

Karakteristik kurva PSAK 117:
- Konsisten dengan harga aset keuangan yang dapat diobservasi
- Bebas dari risiko kredit (risk-free / OJK benchmark)
- Denominasi sesuai mata uang liabilitas (IDR)
"""
from __future__ import annotations

from typing import Sequence
import numpy as np


class DiscountCurve:
    """
    Spot rate discount curve.

    rates: dict mapping tenor (tahun, int) -> annual spot rate (desimal)
           Contoh: {1: 0.0525, 2: 0.0550, 5: 0.0625, 10: 0.0700}

    Tenor di luar rentang akan di-ekstrapolasi menggunakan rate terakhir.
    Tenor di antara titik kurva akan diinterpolasi secara linear.
    """

    def __init__(self, rates: dict[int, float]) -> None:
        if not rates:
            raise ValueError("Rates tidak boleh kosong.")
        # Urutkan berdasarkan tenor
        sorted_items = sorted(rates.items())
        self._tenors = [t for t, _ in sorted_items]
        self._rates = [r for _, r in sorted_items]

    def spot_rate(self, tenor: float) -> float:
        """Dapatkan spot rate untuk tenor tertentu (interpolasi linear)."""
        if tenor <= self._tenors[0]:
            return self._rates[0]
        if tenor >= self._tenors[-1]:
            return self._rates[-1]
        # Cari bracket
        for i in range(len(self._tenors) - 1):
            t0, t1 = self._tenors[i], self._tenors[i + 1]
            if t0 <= tenor <= t1:
                r0, r1 = self._rates[i], self._rates[i + 1]
                # Interpolasi linear
                frac = (tenor - t0) / (t1 - t0)
                return r0 + frac * (r1 - r0)
        return self._rates[-1]  # fallback

    def discount_factor(self, tenor: float) -> float:
        """
        Hitung discount factor untuk tenor tertentu.
        df(t) = 1 / (1 + r(t))^t
        """
        r = self.spot_rate(tenor)
        return 1.0 / ((1.0 + r) ** tenor)

    def discount(self, cash_flows: Sequence[float]) -> list[float]:
        """
        Diskon setiap cash flow ke nilai kini.

        Cash flow ke-i diasumsikan terjadi di akhir periode (t = i+1).

        Returns:
            list[float]: present value tiap cash flow
        """
        pv_flows: list[float] = []
        for i, cf in enumerate(cash_flows):
            t = i + 1  # akhir periode ke-1, 2, 3, ...
            pv = cf * self.discount_factor(t)
            pv_flows.append(pv)
        return pv_flows

    def discount_annuity(self, annual_payment: float, years: int) -> float:
        """
        PV anuitas: pembayaran tahunan konstan selama N tahun.
        Berguna untuk perhitungan LRC pada PAA.
        """
        pv = sum(
            annual_payment * self.discount_factor(t)
            for t in range(1, years + 1)
        )
        return pv

    def to_dict(self) -> dict:
        return {
            "tenors": self._tenors,
            "rates": self._rates,
        }


def flat_curve(rate: float, max_tenor: int = 30) -> DiscountCurve:
    """
    Helper: buat kurva flat (satu rate untuk semua tenor).
    Berguna untuk testing dan skenario sederhana.
    """
    return DiscountCurve({t: rate for t in range(1, max_tenor + 1)})
