"""
Audit Trace – mencatat setiap langkah kalkulasi untuk keperluan audit SPA-04.
Diinjeksikan ke dalam core calculator (bukan bagian dari API layer).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


class AuditTrace:
    """
    Objek audit yang dilewatkan ke calculator untuk merekam langkah-langkah
    intermediate. Setelah kalkulasi selesai, trace-nya disimpan ke AuditService.
    """

    def __init__(self, calculation_type: str, assumption_version: str) -> None:
        self.trace_id: str = str(uuid.uuid4())
        self.calculation_type = calculation_type
        self.assumption_version = assumption_version
        self.created_at: datetime = datetime.now(timezone.utc)
        self.steps: dict[str, Any] = {}

    def record(self, step_name: str, value: Any) -> None:
        """Catat satu langkah kalkulasi beserta nilainya."""
        self.steps[step_name] = {
            "value": value,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "calculation_type": self.calculation_type,
            "assumption_version": self.assumption_version,
            "created_at": self.created_at.isoformat(),
            "steps": self.steps,
        }
