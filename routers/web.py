from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from db import get_session
from routers.cars import list_cars
from schemas import CarSize


router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def read_index(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> HTMLResponse:
    cars = list_cars(session=session, limit=25)
    return templates.TemplateResponse("index.html", {"request": request, "cars": cars})


@router.post("/search", response_class=HTMLResponse)
def search(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    size: Annotated[CarSize, Form()],
    doors: Annotated[int, Form(gt=1, lt=8)],
) -> HTMLResponse:
    cars = list_cars(session=session, size=size, doors=doors, limit=25)
    return templates.TemplateResponse(
        "search_results.html",
        {"request": request, "cars": cars, "selected_size": size, "selected_doors": doors},
    )
