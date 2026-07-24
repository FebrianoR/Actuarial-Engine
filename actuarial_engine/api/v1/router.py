"""
Router utama API v1.
Semua endpoint-specific router didaftarkan di sini.
"""
from fastapi import APIRouter

from actuarial_engine.api.v1.endpoints import bba, paa, vfa, assumptions, audit, upload, export

api_router = APIRouter()

api_router.include_router(bba.router, prefix="/bba", tags=["BBA – Building Block Approach"])
api_router.include_router(paa.router, prefix="/paa", tags=["PAA – Premium Allocation Approach"])
api_router.include_router(vfa.router, prefix="/vfa", tags=["VFA – Variable Fee Approach"])
api_router.include_router(assumptions.router, prefix="/assumptions", tags=["Asumsi Aktuaria"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Trail"])
api_router.include_router(upload.router, prefix="/upload", tags=["Upload Template Excel"])
api_router.include_router(export.router, prefix="/export", tags=["Export Hasil"])
