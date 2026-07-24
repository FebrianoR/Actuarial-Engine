"""
Pydantic Schemas untuk BBA – Building Block Approach (PSAK 117)
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BBAInput(BaseModel):
    """Input untuk kalkulasi BBA."""
    contract_id: str = Field(description="ID kontrak / portfolio")
    product_code: str = Field(description="Kode produk asuransi")
    assumption_version: str = Field("2024.Q4.1", description="Versi asumsi yang digunakan")

    # Cash flows (list panjang N periode/tahun)
    coverage_years: int = Field(ge=1, le=50, description="Lama pertanggungan (tahun)")
    gross_premium: float = Field(gt=0, description="Premi bruto per tahun (IDR)")
    sum_assured: float = Field(gt=0, description="Uang pertanggungan (IDR)")

    # Asumsi mortalitas dan lapse
    mortality_rates: list[float] = Field(
        description="Qx per tahun (harus memiliki coverage_years elemen atau lebih pendek)"
    )
    lapse_rates: list[float] = Field(
        description="Lapse rate per tahun"
    )

    # Biaya
    expense_ratio: float = Field(0.05, ge=0.0, le=1.0, description="Rasio biaya terhadap premi")
    maintenance_per_year: float = Field(0.0, ge=0.0, description="Biaya pemeliharaan per tahun (IDR)")
    inflation_rate: float = Field(0.03, ge=0.0, description="Inflasi biaya per tahun")

    # Yield curve
    discount_rates: dict[str, float] = Field(
        description="Tenor (tahun, string) → spot rate. Contoh: {'1': 0.0525, '5': 0.0625}"
    )

    # Risk Adjustment
    ra_coc_rate: float = Field(0.06, ge=0.0, description="Cost of Capital rate untuk RA")
    ra_capital_ratio: float = Field(0.10, ge=0.0, description="Rasio Required Capital terhadap PV outflows")

    model_config = {"json_schema_extra": {
        "example": {
            "contract_id": "CNTR-2024-001",
            "product_code": "JIWA-20T",
            "assumption_version": "2024.Q4.1",
            "coverage_years": 20,
            "gross_premium": 10_000_000,
            "sum_assured": 200_000_000,
            "mortality_rates": [0.001, 0.0012, 0.0015, 0.002, 0.003],
            "lapse_rates": [0.05, 0.04, 0.03, 0.02, 0.01],
            "expense_ratio": 0.05,
            "maintenance_per_year": 150_000,
            "inflation_rate": 0.03,
            "discount_rates": {"1": 0.0525, "2": 0.0550, "5": 0.0625, "10": 0.0700, "20": 0.0750},
            "ra_coc_rate": 0.06,
            "ra_capital_ratio": 0.10,
        }
    }}


class BBAOutput(BaseModel):
    """Output kalkulasi BBA."""
    contract_id: str
    pvfcf: float = Field(description="Present Value of Future Cash Flows (IDR)")
    risk_adjustment: float = Field(description="Risk Adjustment / RA (IDR)")
    csm: float = Field(description="Contractual Service Margin (IDR). Nol jika kontrak onerous")
    fulfilment_cash_flows: float = Field(description="FCF = PVFCF + RA (IDR)")
    insurance_contract_liability: float = Field(description="ICL = FCF + CSM (IDR)")
    is_onerous: bool = Field(description="True jika kontrak merugi (CSM = 0)")
    trace_id: Optional[str] = Field(None, description="ID audit trace")
    calculation_date: datetime = Field(description="Timestamp kalkulasi (UTC)")
    assumption_version: str
