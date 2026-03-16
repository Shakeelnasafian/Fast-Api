from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select

from db import get_session
from schemas import AccessToken, User, UserCreate, UserOutput
from security import TokenValidationError, create_access_token, decode_access_token


URL_PREFIX = "/auth"
router = APIRouter(prefix=URL_PREFIX, tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{URL_PREFIX}/token")


def _normalize_username(username: str) -> str:
    return username.strip().lower()


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[Session, Depends(get_session)],
) -> User:
    try:
        payload = decode_access_token(token)
    except TokenValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    query = select(User).where(User.username == payload.subject)
    user = session.exec(query).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user does not exist.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/register", response_model=UserOutput, status_code=status.HTTP_201_CREATED)
def register_user(
    user_input: UserCreate,
    session: Annotated[Session, Depends(get_session)],
) -> User:
    normalized_username = _normalize_username(user_input.username)
    existing_user = session.exec(
        select(User).where(User.username == normalized_username)
    ).first()
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already registered.",
        )

    user = User(username=normalized_username)
    user.set_password(user_input.password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post("/token", response_model=AccessToken)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)],
) -> AccessToken:
    query = select(User).where(User.username == _normalize_username(form_data.username))
    user = session.exec(query).first()
    if user is None or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AccessToken(access_token=create_access_token(user.username))


@router.get("/me", response_model=UserOutput)
def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user
