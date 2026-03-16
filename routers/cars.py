from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from db import get_session
from schemas import Car, CarInput, CarOutput, CarSize, Trip, TripInput, TripOutput


router = APIRouter(prefix="/api/cars", tags=["cars"])


def list_cars(
    session: Session,
    size: CarSize | None = None,
    doors: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Car]:
    query = (
        select(Car)
        .options(selectinload(Car.trips))
        .order_by(Car.id)
        .offset(offset)
        .limit(limit)
    )
    if size:
        query = query.where(Car.size == size)
    if doors:
        query = query.where(Car.doors >= doors)
    return session.exec(query).all()


def get_car_or_404(session: Session, car_id: int) -> Car:
    query = select(Car).options(selectinload(Car.trips)).where(Car.id == car_id)
    car = session.exec(query).first()
    if car is None:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


@router.get("/", response_model=list[CarOutput])
def get_cars(
    session: Annotated[Session, Depends(get_session)],
    size: Annotated[CarSize | None, Query()] = None,
    doors: Annotated[int | None, Query(ge=2, le=7)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Car]:
    return list_cars(session=session, size=size, doors=doors, limit=limit, offset=offset)


@router.get("/{car_id}", response_model=CarOutput)
def read_car(
    session: Annotated[Session, Depends(get_session)],
    car_id: int,
) -> Car:
    return get_car_or_404(session, car_id)


@router.post("/", response_model=CarOutput, status_code=status.HTTP_201_CREATED)
def save_car(
    session: Annotated[Session, Depends(get_session)],
    car_input: CarInput,
) -> Car:
    new_car = Car.model_validate(car_input)
    session.add(new_car)
    session.commit()
    session.refresh(new_car)
    return get_car_or_404(session, new_car.id)


@router.delete("/{car_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_car(
    session: Annotated[Session, Depends(get_session)],
    car_id: int,
) -> Response:
    car = get_car_or_404(session, car_id)
    session.delete(car)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{car_id}", response_model=CarOutput)
def update_car(
    session: Annotated[Session, Depends(get_session)],
    car_id: int,
    new_data: CarInput,
) -> Car:
    car = get_car_or_404(session, car_id)
    update_data = new_data.model_dump()
    for field_name, value in update_data.items():
        setattr(car, field_name, value)

    session.add(car)
    session.commit()
    session.refresh(car)
    return get_car_or_404(session, car_id)


@router.post(
    "/{car_id}/trips",
    response_model=TripOutput,
    status_code=status.HTTP_201_CREATED,
)
def add_trip(
    session: Annotated[Session, Depends(get_session)],
    car_id: int,
    trip_input: TripInput,
) -> Trip:
    car = get_car_or_404(session, car_id)
    new_trip = Trip.model_validate(trip_input, update={"car_id": car.id})
    session.add(new_trip)
    session.commit()
    session.refresh(new_trip)
    return new_trip
