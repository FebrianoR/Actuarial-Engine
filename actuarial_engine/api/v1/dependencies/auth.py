"""
Dependency FastAPI untuk autentikasi berbasis API Key.
Digunakan di semua endpoint yang memerlukan autentikasi.
"""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from actuarial_engine.config.settings import get_settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


async def verify_api_key(api_key: str = Security(_api_key_header)) -> str:
    """Verifikasi API Key dari header X-API-Key."""
    settings = get_settings()
    if api_key != settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key tidak valid",
        )
    return api_key
