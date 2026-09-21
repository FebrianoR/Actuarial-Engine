"""
OJK Line of Business Codes – Mapping sandi OJK ke lini usaha.

Dari file: SANDI LINI USAHA BERDASARKAN OJK APOLLO - KIRIM.xlsx
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OJKCode:
    """Satu mapping sandi OJK ke lini usaha."""
    sandi: int = 0          # Kode OJK (501, 502, ...)
    lini_usaha: str = ""    # Nama lini usaha ("Harta Benda", "Kendaraan Bermotor", ...)

    def __str__(self) -> str:
        return f"{self.sandi} - {self.lini_usaha}"


@dataclass
class OJKCodeTable:
    """Tabel lengkap kode OJK."""
    codes: list[OJKCode] = field(default_factory=list)

    def get_name(self, sandi: int) -> str | None:
        """Cari nama lini usaha berdasarkan sandi."""
        for code in self.codes:
            if code.sandi == sandi:
                return code.lini_usaha
        return None

    def get_sandi(self, lini_usaha: str) -> int | None:
        """Cari sandi berdasarkan nama (case-insensitive partial match)."""
        for code in self.codes:
            if lini_usaha.lower() in code.lini_usaha.lower():
                return code.sandi
        return None

    def as_dict(self) -> dict[int, str]:
        """Return as {sandi: lini_usaha} dict."""
        return {c.sandi: c.lini_usaha for c in self.codes}
