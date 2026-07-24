"""
Pengaturan aplikasi dari environment variables.
Menggunakan Pydantic Settings agar semua konfigurasi bertipe dan tervalidasi.
"""
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Aplikasi
    app_name: str = "Actuarial Engine"
    app_version: str = "0.1.0"
    app_env: str = "development"
    log_level: str = "INFO"

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    # Keamanan
    secret_key: str = Field(..., description="Secret key untuk signing")
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "https://*.ngrok-free.app",
        "https://*.ngrok.io",
    ]

    # Path Data Aktuaria
    default_assumptions_path: Path = Path("data/assumptions/base_assumptions.json")
    portfolio_data_path: Path = Path("data/sample_portfolios/")

    # Audit Trail
    audit_log_path: Path = Path("audit_logs/")
    audit_enabled: bool = True

    # Parameter Perhitungan
    ra_simulation_count: int = Field(10_000, description="Jumlah simulasi Monte Carlo untuk RA")
    max_projection_years: int = Field(30, description="Horizon proyeksi maksimum (tahun)")


@lru_cache
def get_settings() -> Settings:
    """Singleton settings instance (cached)."""
    return Settings()
