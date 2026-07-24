"""
Audit Service – Menyimpan dan mengambil AuditRecord (PSAK 117 SPA-04).

Implementasi: in-memory dictionary.
Untuk production, ganti dengan file-based JSON atau SQLite.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from actuarial_engine.audit.trace import AuditTrace
from actuarial_engine.models.schemas.audit_schemas import AuditRecord
from actuarial_engine.config.settings import get_settings


class AuditService:
    """
    Menyimpan AuditRecord dari setiap kalkulasi.

    Storage: JSON file per-session di audit_log_path dari settings.
    In-memory cache untuk performa.
    """

    _store: dict[str, AuditRecord] = {}  # In-memory, shared dalam satu proses

    def save(
        self,
        trace: AuditTrace,
        contract_id: str,
        input_snapshot: dict[str, Any],
        output_snapshot: dict[str, Any],
    ) -> AuditRecord:
        """Simpan trace kalkulasi sebagai AuditRecord."""
        record = AuditRecord(
            trace_id=trace.trace_id,
            calculation_type=trace.calculation_type,
            contract_id=contract_id,
            assumption_version=trace.assumption_version,
            created_at=trace.created_at,
            input_snapshot=input_snapshot,
            output_snapshot=output_snapshot,
            steps=trace.steps,
            spa04_compliant=True,
        )
        AuditService._store[record.trace_id] = record

        # Optional: tulis ke file
        settings = get_settings()
        if settings.audit_enabled:
            self._persist_to_file(record, settings.audit_log_path)

        return record

    @staticmethod
    def _persist_to_file(record: AuditRecord, log_dir: Path) -> None:
        """Tulis audit record ke file JSON."""
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            filename = log_dir / f"{record.trace_id}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(record.model_dump(mode="json"), f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # Logging gagal tidak boleh menggagalkan kalkulasi

    async def list_records(self, limit: int = 50, offset: int = 0) -> list[AuditRecord]:
        """Ambil daftar audit record (terbaru dulu)."""
        records = sorted(
            AuditService._store.values(),
            key=lambda r: r.created_at,
            reverse=True,
        )
        return records[offset: offset + limit]

    async def get_record(self, record_id: str) -> AuditRecord:
        """Ambil satu audit record berdasarkan trace_id."""
        from fastapi import HTTPException, status
        if record_id not in AuditService._store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audit record '{record_id}' tidak ditemukan",
            )
        return AuditService._store[record_id]
