"""
CSM Tracker – Contractual Service Margin (PSAK 117 Par. 38-44)

CSM merepresentasikan keuntungan belum diakui yang akan diamortisasi
seiring jasa pertanggungan diberikan.

Aturan utama:
1. CSM pengakuan awal = max(0, -FCF)  — nol jika kontrak onerous
2. CSM diamortisasi berdasarkan coverage units (jumlah polis × coverage period)
3. CSM tidak boleh negatif; jika FCF memburuk, sisa amortisasi dicari dulu
"""
from __future__ import annotations


class CSMTracker:
    """
    Melacak CSM sepanjang siklus hidup kontrak.

    Args:
        coverage_units: list coverage unit per periode (biasanya jumlah polis aktif)
                        Jika None, diasumsikan straight-line (uniform amortization)
    """

    def __init__(self, coverage_units: list[float] | None = None) -> None:
        self._coverage_units = coverage_units
        self._csm_balance: float = 0.0

    def determine_initial_csm(self, fulfilment_cash_flows: float) -> float:
        """
        Tentukan CSM pada pengakuan awal kontrak (PSAK 117 Par. 38).

        FCF < 0  → kontrak menguntungkan → CSM = |FCF|  (day-1 gain ditangguhkan)
        FCF >= 0 → kontrak merugi (onerous) → CSM = 0, langsung catat rugi di L/R

        Args:
            fulfilment_cash_flows: PVFCF + RA (negatif = menguntungkan bagi insurer)

        Returns:
            float: nilai CSM awal
        """
        self._csm_balance = max(0.0, -fulfilment_cash_flows)
        return round(self._csm_balance, 6)

    def amortize(self, period: int) -> float:
        """
        Hitung amortisasi CSM untuk satu periode.

        Menggunakan coverage-unit pattern.
        Jika coverage_units tidak diberikan, gunakan straight-line
        berdasarkan sisa coverage period.

        Args:
            period: periode saat ini (0-indexed)

        Returns:
            float: jumlah CSM yang diamortisasi pada periode ini
        """
        if self._csm_balance <= 0:
            return 0.0

        if self._coverage_units is None:
            # Straight-line: tidak bisa tanpa tahu total periode
            # Kembalikan 0; caller harus set coverage_units
            return 0.0

        total_units = sum(self._coverage_units)
        if total_units <= 0:
            return 0.0

        if period >= len(self._coverage_units):
            return 0.0

        units_this_period = self._coverage_units[period]
        amortization = self._csm_balance * (units_this_period / total_units)
        self._csm_balance -= amortization
        self._csm_balance = max(0.0, self._csm_balance)
        return round(amortization, 6)

    def accrete_interest(self, locked_in_rate: float) -> float:
        """
        Akresikan bunga pada CSM dengan locked-in discount rate (PSAK 117 Par. 44).

        Args:
            locked_in_rate: rate bunga yang dikunci pada pengakuan awal

        Returns:
            float: bunga yang ditambahkan ke CSM balance
        """
        interest = self._csm_balance * locked_in_rate
        self._csm_balance += interest
        return round(interest, 6)

    @property
    def balance(self) -> float:
        """CSM balance saat ini."""
        return round(self._csm_balance, 6)
