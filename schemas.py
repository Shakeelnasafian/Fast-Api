from enum import Enum

from passlib.context import CryptContext
from pydantic import ConfigDict, model_validator
from sqlmodel import Column, Field, Relationship, SQLModel, VARCHAR


pwd_context = CryptContext(schemes=["bcrypt"])


class CarSize(str, Enum):
    small = "s"
    medium = "m"
    large = "l"


class FuelType(str, Enum):
    electric = "electric"
    petrol = "petrol"
    diesel = "diesel"
    hybrid = "hybrid"


class TransmissionType(str, Enum):
    automatic = "auto"
    manual = "manual"


class UserOutput(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


class UserCreate(SQLModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        regex=r"^[a-zA-Z0-9_.-]+$",
    )
    password: str = Field(min_length=8, max_length=128)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(
        sa_column=Column("username", VARCHAR(50), unique=True, index=True, nullable=False)
    )
    password_hash: str = Field(default="", max_length=255)

    def set_password(self, password: str) -> None:
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password_hash)


class TripInput(SQLModel):
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    description: str = Field(min_length=3, max_length=500)

    @model_validator(mode="after")
    def validate_trip_window(self) -> "TripInput":
        if self.start >= self.end:
            raise ValueError("Trip start time must be before the end time.")
        return self


class TripOutput(TripInput):
    model_config = ConfigDict(from_attributes=True)

    id: int


class Trip(TripInput, table=True):
    id: int | None = Field(default=None, primary_key=True)
    car_id: int = Field(foreign_key="car.id")
    car: "Car" = Relationship(back_populates="trips")


class CarInput(SQLModel):
    size: CarSize
    fuel: FuelType = FuelType.electric
    doors: int = Field(ge=2, le=7)
    transmission: TransmissionType = TransmissionType.automatic

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "size": "m",
                    "doors": 5,
                    "transmission": "manual",
                    "fuel": "hybrid",
                }
            ]
        }
    }


class Car(CarInput, table=True):
    id: int | None = Field(primary_key=True, default=None)
    trips: list["Trip"] = Relationship(
        back_populates="car",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )


class CarOutput(CarInput):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trips: list[TripOutput] = Field(default_factory=list)


class AccessToken(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    subject: str
    expires_at: int


class HealthStatus(SQLModel):
    status: str
