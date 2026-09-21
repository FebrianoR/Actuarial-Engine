"""
Inforce Data Models – Extended policy records from production inforce files.

Extends the base PolicyRecord with reinsurance fields and additional metadata
from the INFORCE 31 DESEMBER YYYY files.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class InforceRecord:
    """Satu baris dari sheet INSURANCE CONTRACT pada file INFORCE."""
    sguser: str = ""
    id: str = ""
    batchnr: str = ""
    cob: str = ""               # Kode COB (510, 515, dll)
    product: str = ""           # Nama produk (Tanggung Gugat, Aneka, dll)
    sob: str = ""               # Sub-class of business
    mkt: str = ""               # Market / channel
    uw: str = ""                # Underwriting year
    policyno: str = ""
    begindt: date | None = None
    enddt: date | None = None
    begindtlt: date | None = None   # Begin date latest (for renewal tracking)
    valdate: date | None = None     # Valuation date
    stspolis: str = "INFORCE"
    aktif: str = "AKTIF"
    tsi: float = 0.0                # Total Sum Insured
    gwp: float = 0.0                # Gross Written Premium
    discount: float = 0.0
    outgo: float = 0.0
    ngwp: float = 0.0               # Net GWP = GWP - discount - outgo
    ripremi: float = 0.0            # Reinsurance premium
    ricom: float = 0.0              # Reinsurance commission
    ripreminett: float = 0.0        # Net reinsurance premium
    grace: str = ""
    smethode: str = "PAA"           # PAA atau GMM

    @property
    def is_active(self) -> bool:
        return self.aktif == "AKTIF"

    @property
    def retention(self) -> float:
        """Net premium after reinsurance."""
        return self.ngwp - self.ripreminett


@dataclass
class StoplossRecord:
    """Satu baris dari sheet STOPLOSS pada file INFORCE."""
    sguser: str = ""
    id: str = ""
    batchnr: str = ""
    cob: str = ""
    product: str = ""
    sob: str = ""
    mkt: str = ""
    uw: str = ""
    policyno: str = ""
    begindt: date | None = None
    enddt: date | None = None
    begindtlt: date | None = None
    valdate: date | None = None
    stspolis: str = "INFORCE"
    aktif: str = "AKTIF"
    tsi: float = 0.0
    gwp: float = 0.0
    discount: float = 0.0
    outgo: float = 0.0
    ngwp: float = 0.0
    ripremi: float = 0.0
    ricom: float = 0.0
    ripreminett: float = 0.0
    grace: str = ""
    smethode: str = ""


@dataclass
class InforceSummary:
    """Ringkasan dari sheet Pivot."""
    year: int = 0
    by_product: dict[str, dict[str, Any]] = field(default_factory=dict)
    # e.g. {"Aneka": {"count": 418, "gwp": 4444687763.33, "ngwp": ..., "tsi": ...}}
    total_policies: int = 0
    total_gwp: float = 0.0
    total_ngwp: float = 0.0
    total_tsi: float = 0.0

    stoploss_by_product: dict[str, dict[str, Any]] = field(default_factory=dict)
    stoploss_total_policies: int = 0
    stoploss_total_gwp: float = 0.0


@dataclass
class ParsedInforce:
    """Kumpulan hasil parsing satu file inforce."""
    year: int = 0
    month: int = 0  # 1-12, 0 jika tidak diketahui
    records: list[InforceRecord] = field(default_factory=list)
    stoploss: list[StoplossRecord] = field(default_factory=list)
    summary: InforceSummary | None = None
    errors: list[str] = field(default_factory=list)
