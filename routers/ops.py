from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlmodel import Session

from db import get_session
from schemas import HealthStatus


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=HealthStatus)
def live() -> HealthStatus:
    return HealthStatus(status="ok")


@router.get("/ready", response_model=HealthStatus)
def ready(session: Annotated[Session, Depends(get_session)]) -> HealthStatus:
    session.exec(text("SELECT 1"))
    return HealthStatus(status="ok")
