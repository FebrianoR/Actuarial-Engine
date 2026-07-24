"""
PAA Calculator – Premium Allocation Approach (PSAK 117 Par. 53-59)

Digunakan untuk kontrak asuransi jangka pendek (≤ 1 tahun) atau
kontrak yang eligible PAA (coverage period ≤ 1 tahun atau RA tidak material).

Komponen PAA:
  LRC  = Liability for Remaining Coverage
       = Unearned Premium − Deferred Acquisition Cost (DAC)
  LIC  = Liability for Incurred Claims
       = Claims IBNR + Outstanding Claims + Claim Handling Expenses
  Total = LRC + LIC
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class PAAResult:
    """Hasil perhitungan PAA."""
    # Liability for Remaining Coverage
    lrc_gross: float          # LRC sebelum dikurangi DAC
    dac: float                # Deferred Acquisition Cost
    lrc_net: float            # LRC neto = lrc_gross - dac

    # Liability for Incurred Claims
    outstanding_claims: float # Klaim terlaporkan yang belum dibayar
    ibnr: float               # Incurred But Not Reported
    lic: float                # LIC = outstanding + ibnr

    # Total
    total_liability: float    # LRC neto + LIC

    # Diagnostics
    earned_premium: float     # Premi yang sudah diakui
    unearned_premium: float   # Premi yang belum earned
    loss_ratio: float         # LIC / earned_premium
    intermediate_steps: dict = field(default_factory=dict)


class PAACalculator:
    """
    Perhitungan PAA untuk satu period of coverage.

    Args:
        written_premium       : Premi bruto yang ditulis
        coverage_start        : Tanggal mulai coverage
        coverage_end          : Tanggal akhir coverage
        reporting_date        : Tanggal pelaporan
        claims_incurred       : Total klaim yang terjadi s.d. reporting date
        outstanding_claims    : Klaim terlaporkan belum dibayar
        ibnr_ratio            : Rasio IBNR terhadap claims_incurred (default 10%)
        acquisition_cost_ratio: Biaya akuisisi sebagai % premi (untuk DAC)
        amortize_dac          : Jika True, amortisasi DAC mengikuti earning premi
        discount_rate         : Rate untuk mendiskon LIC jika material
    """

    def __init__(
        self,
        written_premium: float,
        coverage_start: date,
        coverage_end: date,
        reporting_date: date,
        claims_incurred: float,
        outstanding_claims: float,
        ibnr_ratio: float = 0.10,
        acquisition_cost_ratio: float = 0.05,
        amortize_dac: bool = True,
        discount_rate: float = 0.0,  # PAA: diskon LIC hanya jika > 1 tahun
    ) -> None:
        self._premium = written_premium
        self._cov_start = coverage_start
        self._cov_end = coverage_end
        self._report_date = reporting_date
        self._claims = claims_incurred
        self._outstanding = outstanding_claims
        self._ibnr_ratio = ibnr_ratio
        self._acq_ratio = acquisition_cost_ratio
        self._amortize_dac = amortize_dac
        self._disc_rate = discount_rate

    def _earned_fraction(self) -> float:
        """
        Hitung fraksi premi yang sudah earned (time-proportion).
        earned = (days_elapsed) / (total_coverage_days)
        """
        total_days = (self._cov_end - self._cov_start).days
        if total_days <= 0:
            return 1.0
        elapsed = (self._report_date - self._cov_start).days
        elapsed = max(0, min(elapsed, total_days))  # clamp ke [0, total]
        return elapsed / total_days

    def calculate(self) -> PAAResult:
        """Hitung komponen PAA."""
        earned_frac = self._earned_fraction()
        unearned_frac = 1.0 - earned_frac

        # Premi earned dan unearned
        earned_premium = self._premium * earned_frac
        unearned_premium = self._premium * unearned_frac

        # LRC gross = unearned premium
        lrc_gross = unearned_premium

        # DAC = biaya akuisisi yang dideferred
        total_dac = self._premium * self._acq_ratio
        if self._amortize_dac:
            # Sisa DAC = DAC × fraksi premium yang belum earned
            dac = total_dac * unearned_frac
        else:
            dac = total_dac

        lrc_net = lrc_gross - dac

        # LIC
        ibnr = self._claims * self._ibnr_ratio
        lic = self._outstanding + ibnr

        # Diskon LIC jika ada discount rate
        if self._disc_rate > 0:
            remaining_months = (self._cov_end - self._report_date).days / 365.25
            lic = lic / ((1 + self._disc_rate) ** remaining_months)

        total_liability = lrc_net + lic

        loss_ratio = (lic / earned_premium) if earned_premium > 0 else 0.0

        steps = {
            "earned_fraction": earned_frac,
            "unearned_fraction": unearned_frac,
            "total_dac": total_dac,
            "earned_premium": earned_premium,
            "unearned_premium": unearned_premium,
        }

        return PAAResult(
            lrc_gross=round(lrc_gross, 6),
            dac=round(dac, 6),
            lrc_net=round(lrc_net, 6),
            outstanding_claims=round(self._outstanding, 6),
            ibnr=round(ibnr, 6),
            lic=round(lic, 6),
            total_liability=round(total_liability, 6),
            earned_premium=round(earned_premium, 6),
            unearned_premium=round(unearned_premium, 6),
            loss_ratio=round(loss_ratio, 6),
            intermediate_steps=steps,
        )
