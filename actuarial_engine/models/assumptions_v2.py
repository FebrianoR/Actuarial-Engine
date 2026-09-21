"""
Consolidated Assumptions Models (v2) – From ASUMSI 2020-2025 file.

This replaces the simpler AssumptionRow model for production use.
The ASUMSI file contains 7 sheets with comprehensive actuarial assumptions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


# ──────────────────────────────────────────────
#  Sheet 1: Loss Ratio Per Produk
# ──────────────────────────────────────────────

@dataclass
class LossRatioProduct:
    """Loss Ratio untuk satu produk di satu COB."""
    cob: str = ""               # e.g. "PROPERTY"
    business_code: str = ""     # e.g. "R01"
    business_name: str = ""     # e.g. "FIRE (DAI)"
    # year -> loss ratio
    ratios: dict[int, float] = field(default_factory=dict)


# ──────────────────────────────────────────────
#  Sheet 2: Loss Ratio Per COB
# ──────────────────────────────────────────────

@dataclass
class LossRatioCOB:
    """Loss Ratio aggregat per COB."""
    cob: str = ""
    ratios: dict[int, float] = field(default_factory=dict)


# ──────────────────────────────────────────────
#  Sheet 3: PAD (Provision for Adverse Deviation)
# ──────────────────────────────────────────────

@dataclass
class PADEntry:
    """PAD untuk satu COB di satu confidence level."""
    cob: str = ""
    ratios: dict[int, float] = field(default_factory=dict)


@dataclass
class PADTable:
    """PAD tabel untuk satu confidence level (75% atau 95%)."""
    confidence_level: str = "75%"        # "75%" atau "95%"
    gross: list[PADEntry] = field(default_factory=list)
    reinsurance: list[PADEntry] = field(default_factory=list)
    net: list[PADEntry] = field(default_factory=list)


# ──────────────────────────────────────────────
#  Sheet 4: ICHE
# ──────────────────────────────────────────────

@dataclass
class ICHEEntry:
    """ICHE rate per COB."""
    cob: str = ""
    ratios: dict[int, float] = field(default_factory=dict)


# ──────────────────────────────────────────────
#  Sheet 5: Bunga Diskonto (Discount Rates)
# ──────────────────────────────────────────────

@dataclass
class DiscountRateYear:
    """Discount rates untuk satu tahun (Term x monthly rates + SAK + SAP)."""
    year: int = 0
    label: str = ""             # e.g. "Indonesian Gov Bond Yield (IDR)"
    # term -> {month_date: rate, "SAK": rate, "SAP": rate}
    terms: dict[int, dict[str, float]] = field(default_factory=dict)


# ──────────────────────────────────────────────
#  Sheet 6: Inflasi
# ──────────────────────────────────────────────

@dataclass
class InflationEntry:
    """Satu baris inflasi bulanan."""
    month: str = ""         # e.g. "Desember"
    year: int = 0
    rate: float = 0.0


@dataclass
class InflationAverage:
    """Rata-rata inflasi 3 tahun per valuasi."""
    valuation_date: str = ""    # e.g. "31 Des 2020"
    average_3yr: float = 0.0


# ──────────────────────────────────────────────
#  Sheet 7: Lapse Rasio
# ──────────────────────────────────────────────

@dataclass
class LapseRatioTable:
    """Lapse ratio: duration_year -> {valuation_year -> rate}."""
    # year_duration (1,2,3,...) -> {calendar_year -> lapse_rate}
    ratios: dict[int, dict[int, float]] = field(default_factory=dict)


# ──────────────────────────────────────────────
#  Sheet 8: Expense Rasio
# ──────────────────────────────────────────────

@dataclass
class ExpenseDetail:
    """Detail expense per kategori per tahun."""
    category: str = ""              # e.g. "Beban Pemasaran"
    amounts: dict[int, float] = field(default_factory=dict)


@dataclass
class ExpenseRatio:
    """Expense ratios per tahun."""
    # Total ratio
    total_ratios: dict[int, float] = field(default_factory=dict)
    # By subcategory
    gross_premium: dict[int, float] = field(default_factory=dict)
    total_operating_expense: dict[int, float] = field(default_factory=dict)
    details: list[ExpenseDetail] = field(default_factory=list)
    sub_ratios: list[ExpenseDetail] = field(default_factory=list)


# ──────────────────────────────────────────────
#  Summary Sheet
# ──────────────────────────────────────────────

@dataclass
class SummaryRow:
    """Satu baris dari sheet SUMMARY: COB + Loss Ratio + PAD + Expense + Total."""
    cob: str = ""
    loss_ratio: float = 0.0
    pad: float = 0.0
    expense: float = 0.0
    total: float = 0.0


@dataclass
class SummaryYear:
    """Summary per valuation year."""
    year: int = 0
    rows: list[SummaryRow] = field(default_factory=list)


# ──────────────────────────────────────────────
#  Consolidated: All assumptions in one object
# ──────────────────────────────────────────────

@dataclass
class ConsolidatedAssumptions:
    """Semua asumsi dari file ASUMSI 2020-2025 dalam satu objek."""
    loss_ratio_by_product: list[LossRatioProduct] = field(default_factory=list)
    loss_ratio_by_cob: list[LossRatioCOB] = field(default_factory=list)
    pad_tables: list[PADTable] = field(default_factory=list)     # CL75% + CL95%
    iche: list[ICHEEntry] = field(default_factory=list)
    discount_rates: list[DiscountRateYear] = field(default_factory=list)
    inflation_monthly: list[InflationEntry] = field(default_factory=list)
    inflation_averages: list[InflationAverage] = field(default_factory=list)
    lapse: LapseRatioTable = field(default_factory=LapseRatioTable)
    expense: ExpenseRatio = field(default_factory=ExpenseRatio)
    summary: list[SummaryYear] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def available_years(self) -> list[int]:
        """Tahun-tahun yang tersedia di data asumsi."""
        years: set[int] = set()
        for lr in self.loss_ratio_by_cob:
            years.update(lr.ratios.keys())
        return sorted(years)

    def get_loss_ratio(self, cob: str, year: int) -> float | None:
        """Get loss ratio untuk COB dan tahun tertentu."""
        for lr in self.loss_ratio_by_cob:
            if lr.cob.lower() == cob.lower():
                return lr.ratios.get(year)
        return None

    def get_pad(self, cob: str, year: int, cl: str = "75%",
                basis: str = "net") -> float | None:
        """Get PAD rate untuk COB tertentu."""
        for pad_table in self.pad_tables:
            if pad_table.confidence_level == cl:
                entries = getattr(pad_table, basis, [])
                for entry in entries:
                    if entry.cob.lower() == cob.lower():
                        return entry.ratios.get(year)
        return None

    def get_expense_ratio(self, year: int) -> float | None:
        """Get total expense ratio untuk tahun tertentu."""
        return self.expense.total_ratios.get(year)

    def get_discount_rate_sak(self, year: int, term: int) -> float | None:
        """Get SAK discount rate untuk tahun dan term tertentu."""
        for dr in self.discount_rates:
            if dr.year == year:
                term_data = dr.terms.get(term)
                if term_data:
                    return term_data.get("SAK")
        return None
