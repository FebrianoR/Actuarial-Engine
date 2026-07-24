"""
Pydantic Schemas untuk PAA – Premium Allocation Approach (PSAK 117)
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class PAAInput(BaseModel):
    """Input untuk kalkulasi PAA."""
    contract_id: str
    product_code: str
    assumption_version: str = "2024.Q4.1"

    written_premium: float = Field(gt=0, description="Premi bruto yang ditulis (IDR)")
    coverage_start: date = Field(description="Tanggal mulai coverage")
    coverage_end: date = Field(description="Tanggal akhir coverage")
    reporting_date: date = Field(description="Tanggal pelaporan")

    claims_incurred: float = Field(ge=0, description="Total klaim yang terjadi s.d. reporting date (IDR)")
    outstanding_claims: float = Field(ge=0, description="Klaim terlaporkan belum dibayar (IDR)")
    ibnr_ratio: float = Field(0.10, ge=0.0, le=1.0, description="Rasio IBNR terhadap claims incurred")

    acquisition_cost_ratio: float = Field(0.05, ge=0.0, le=1.0, description="Biaya akuisisi % premi (DAC)")
    amortize_dac: bool = Field(True, description="True jika DAC diamortisasi mengikuti premi")
    discount_rate: float = Field(0.0, ge=0.0, description="Rate diskon untuk LIC (gunakan 0 jika < 1 tahun)")

    model_config = {"json_schema_extra": {
        "example": {
            "contract_id": "CNTR-PAA-2024-001",
            "product_code": "KEBAKARAN-1T",
            "assumption_version": "2024.Q4.1",
            "written_premium": 12_000_000,
            "coverage_start": "2024-01-01",
            "coverage_end": "2024-12-31",
            "reporting_date": "2024-06-30",
            "claims_incurred": 2_000_000,
            "outstanding_claims": 1_500_000,
            "ibnr_ratio": 0.10,
            "acquisition_cost_ratio": 0.05,
            "amortize_dac": True,
            "discount_rate": 0.0,
        }
    }}


class PAAOutput(BaseModel):
    """Output kalkulasi PAA."""
    contract_id: str
    lrc_gross: float = Field(description="LRC sebelum DAC (IDR)")
    dac: float = Field(description="Deferred Acquisition Cost (IDR)")
    lrc_net: float = Field(description="LRC neto = LRC − DAC (IDR)")
    outstanding_claims: float = Field(description="Klaim terlaporkan belum dibayar (IDR)")
    ibnr: float = Field(description="IBNR (IDR)")
    lic: float = Field(description="Liability for Incurred Claims = outstanding + IBNR (IDR)")
    total_liability: float = Field(description="Total liabilitas PAA = LRC neto + LIC (IDR)")
    earned_premium: float = Field(description="Premi yang sudah diakui (IDR)")
    unearned_premium: float = Field(description="Premi belum earned (IDR)")
    loss_ratio: float = Field(description="Loss Ratio = LIC / Earned Premium")
    trace_id: Optional[str] = None
    calculation_date: datetime
    assumption_version: str
