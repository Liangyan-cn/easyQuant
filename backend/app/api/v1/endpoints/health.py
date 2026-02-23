from fastapi import APIRouter

from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", message="Service is running")


@router.get("/ready", response_model=HealthResponse)
async def readiness_check():
    return HealthResponse(status="ready", message="Service is ready to accept requests")


@router.get("/live", response_model=HealthResponse)
async def liveness_check():
    return HealthResponse(status="alive", message="Service is alive")
