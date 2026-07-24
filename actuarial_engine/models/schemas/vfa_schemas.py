"""
Pydantic Schemas untuk VFA – Variable Fee Approach (PSAK 117)
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class VFAInput(BaseModel):
    """Input untuk kalkulasi VFA."""
    contract_id: str
    product_code: str
    assumption_version: str = "2024.Q4.1"

    # Cash flows (sama seperti BBA)
    coverage_years: int = Field(ge=1, le=50)
    gross_premium: float = Field(gt=0)
    sum_assured: float = Field(gt=0)
    mortality_rates: list[float]
    lapse_rates: list[float]
    expense_ratio: float = Field(0.05, ge=0.0, le=1.0)
    maintenance_per_year: float = Field(0.0, ge=0.0)
    inflation_rate: float = Field(0.03, ge=0.0)
    discount_rates: dict[str, float]

    # RA
    ra_coc_rate: float = Field(0.06, ge=0.0)
    ra_capital_ratio: float = Field(0.10, ge=0.0)

    # VFA-specific: underlying items
    underlying_items_fair_value: float = Field(gt=0, description="Fair value total underlying items (IDR)")
    entity_share_pct: float = Field(ge=0.0, le=1.0, description="Porsi entitas atas underlying items (0-1)")

    model_config = {"json_schema_extra": {
        "example": {
            "contract_id": "CNTR-VFA-2024-001",
            "product_code": "UNITLINK-20T",
            "coverage_years": 20,
            "gross_premium": 24_000_000,
            "sum_assured": 500_000_000,
            "mortality_rates": [0.001, 0.0012, 0.0015, 0.002, 0.003],
            "lapse_rates": [0.05, 0.04, 0.03, 0.02, 0.01],
            "expense_ratio": 0.05,
            "maintenance_per_year": 200_000,
            "inflation_rate": 0.03,
            "discount_rates": {"1": 0.0525, "5": 0.0625, "10": 0.0700, "20": 0.0750},
            "ra_coc_rate": 0.06,
            "ra_capital_ratio": 0.10,
            "underlying_items_fair_value": 1_000_000_000,
            "entity_share_pct": 0.30,
        }
    }}


class VFAOutput(BaseModel):
    """Output kalkulasi VFA."""
    contract_id: str
    pvfcf: float
    risk_adjustment: float
    fulfilment_cash_flows: float
    underlying_items_fair_value: float
    entity_share: float = Field(description="Persentase share entitas (%)")
    entity_share_value: float = Field(description="Nilai share entitas (IDR)")
    variable_fee: float = Field(description="Variable fee = entity_share_value − PVFCF (IDR)")
    csm: float
    insurance_contract_liability: float
    trace_id: Optional[str] = None
    calculation_date: datetime
    assumption_version: str
