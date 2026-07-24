"""
Pydantic schema untuk model Asumsi Aktuaria.
Digunakan sebagai kontrak antara API layer dan storage layer.
"""
from __future__ import annotations

from datetime import date
from pydantic import BaseModel, Field


class MortalityTable(BaseModel):
    """Tabel mortalitas (qx)."""
    name: str = Field(description="Nama tabel, contoh: TMI-3 2011")
    improvement_factor: float = Field(0.0, ge=0.0, le=0.1, description="Faktor perbaikan mortalitas per tahun")

class MorbidityAssumption(BaseModel):
    """Asumsi morbiditas untuk produk kesehatan dan cacat."""
    incidence_rate_table: str
    recovery_rate_table: str

class LapseAssumption(BaseModel):
    """Asumsi lapse (penghentian polis)."""
    rate_per_year: list[float] = Field(description="Lapse rate untuk tahun ke-1 s/d N")

class ExpenseAssumption(BaseModel):
    """Asumsi biaya akuisisi dan pemeliharaan."""
    acquisition_ratio: float = Field(ge=0.0, le=1.0, description="Biaya akuisisi sebagai % premi")
    maintenance_per_policy: float = Field(ge=0.0, description="Biaya pemeliharaan per polis per tahun")
    inflation_rate: float = Field(ge=0.0, description="Inflasi biaya per tahun")

class DiscountCurveAssumption(BaseModel):
    """Yield curve untuk mendiskon arus kas (PSAK 117 Par. 36)."""
    source: str = Field(description="Sumber kurva, contoh: OJK Risk-Free Rate, IBPA")
    reference_date: date
    rates: dict[int, float] = Field(description="Tenor (tahun) -> Rate")

class AssumptionSet(BaseModel):
    """
    Kumpulan lengkap asumsi untuk satu produk/kohort.
    Setiap set asumsi memiliki ID dan versi untuk keperluan audit.
    """
    assumption_id: str
    version: str = Field(description="Versi (SemVer), contoh: 2024.Q4.1")
    product_code: str
    effective_date: date
    mortality: MortalityTable
    morbidity: MorbidityAssumption | None = None
    lapse: LapseAssumption
    expense: ExpenseAssumption
    discount_curve: DiscountCurveAssumption
    notes: str = Field("", description="Catatan perubahan asumsi untuk dokumentasi aktuaria")
