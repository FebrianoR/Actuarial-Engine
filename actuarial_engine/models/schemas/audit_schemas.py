"""
Pydantic Schemas untuk Audit Record – PSAK 117 SPA-04
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class AuditRecord(BaseModel):
    """Satu record audit dari satu kalkulasi."""
    trace_id: str = Field(description="UUID unik untuk setiap kalkulasi")
    calculation_type: str = Field(description="BBA | PAA | VFA")
    contract_id: str
    assumption_version: str
    created_at: datetime
    input_snapshot: dict[str, Any] = Field(description="Input lengkap yang digunakan")
    output_snapshot: dict[str, Any] = Field(description="Output final kalkulasi")
    steps: dict[str, Any] = Field(description="Intermediate values setiap langkah")
    spa04_compliant: bool = Field(True, description="Flag kepatuhan SPA-04")
