"""
Actuarial Engine – PSAK 117 Calculation Engine
Entry point utama aplikasi FastAPI.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from actuarial_engine.api.v1.router import api_router
from actuarial_engine.config.settings import get_settings
from actuarial_engine.utils.logging import setup_logging

settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Engine Perhitungan Aktuaria PSAK 117 – BBA, PAA, VFA",
    openapi_url=f"{settings.api_prefix}/openapi.json",
    docs_url=f"{settings.api_prefix}/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=r"https://.*\.(ngrok-free\.app|ngrok-free\.dev|ngrok\.io)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health", tags=["System"])
async def health_check() -> dict:
    """Docker health check endpoint."""
    return {"status": "ok", "version": settings.app_version}
