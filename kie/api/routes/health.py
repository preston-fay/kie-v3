"""
Health check endpoints.
"""

from fastapi import APIRouter
from datetime import datetime
from pathlib import Path
import sys

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns system status and basic diagnostics.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "3.0.0",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }


@router.get("/status")
async def status():
    """
    Detailed status endpoint.

    Returns more comprehensive system information.
    """
    from kie.config import get_config

    config = get_config()

    return {
        "status": "operational",
        "version": "3.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "config": {
            "output_dir": str(config.output_dir),
            "export_dir": str(config.export_dir),
            "data_dir": str(config.data_dir),
        },
        "features": {
            "geocoding": True,
            "charts": True,
            "mapping": True,
            "brand_validation": True,
        },
    }
