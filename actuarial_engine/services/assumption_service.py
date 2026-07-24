"""
Assumption Service – Load & simpan AssumptionSet dari file JSON.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from actuarial_engine.models.assumptions.base_assumptions import AssumptionSet
from actuarial_engine.config.settings import get_settings


class AssumptionService:
    """
    Manajemen asumsi aktuaria.
    Asumsi disimpan sebagai file JSON di data/assumptions/.
    Setiap file = satu AssumptionSet (versi-terkontrol).
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._base_path: Path = settings.default_assumptions_path.parent

    def _list_files(self) -> list[Path]:
        if not self._base_path.exists():
            return []
        return sorted(self._base_path.glob("*.json"))

    def _load_file(self, path: Path) -> Optional[AssumptionSet]:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return AssumptionSet(**data)
        except Exception:
            return None

    async def list_all(self) -> list[AssumptionSet]:
        """Ambil semua AssumptionSet yang ada."""
        result = []
        for p in self._list_files():
            obj = self._load_file(p)
            if obj:
                result.append(obj)
        return result

    async def get_by_id(self, assumption_id: str) -> Optional[AssumptionSet]:
        """Cari AssumptionSet berdasarkan assumption_id."""
        for p in self._list_files():
            obj = self._load_file(p)
            if obj and obj.assumption_id == assumption_id:
                return obj
        return None

    async def create(self, payload: AssumptionSet) -> AssumptionSet:
        """Simpan AssumptionSet ke file JSON baru."""
        self._base_path.mkdir(parents=True, exist_ok=True)
        filename = self._base_path / f"{payload.assumption_id}_v{payload.version}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(payload.model_dump(mode="json"), f, ensure_ascii=False, indent=2)
        return payload
