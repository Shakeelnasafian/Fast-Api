"""
create_user.py
--------------
A convenience script to create a user.
"""
from __future__ import annotations

import logging
from getpass import getpass

from sqlmodel import Session, select

from db import get_engine, init_db
from schemas import User


logging.getLogger("passlib").setLevel(logging.ERROR)


def normalize_username(username: str) -> str:
    return username.strip().lower()


if __name__ == "__main__":
    print("Creating tables (if necessary)")
    init_db()

    print("--------")
    print("This script will create a user and save it in the database.")

    username = normalize_username(input("Please enter username\n"))
    password = getpass("Please enter password\n")

    with Session(get_engine()) as session:
        existing_user = session.exec(select(User).where(User.username == username)).first()
        if existing_user is not None:
            raise SystemExit("Username already exists.")

        user = User(username=username)
        user.set_password(password)
        session.add(user)
        session.commit()

    print("User created successfully.")
