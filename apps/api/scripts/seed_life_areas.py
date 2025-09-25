#!/usr/bin/env python3
import os
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from app.models.core import User, LifeArea, LifeAreaLink


DEFAULT_AREAS: List[str] = [
    "Health",
    "Relationships",
    "Finance",
    "Career",
    "Learning",
    "Creativity",
    "Wellbeing",
    "Community",
]


def main() -> None:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise SystemExit("DATABASE_URL env is required")

    email = os.environ.get("SEED_USER_EMAIL", "seed@example.com")
    timezone = os.environ.get("SEED_USER_TZ", "UTC")

    engine = create_engine(db_url, future=True)
    with Session(engine) as session:
        user = session.query(User).filter(User.email == email).one_or_none()
        if not user:
            user = User(email=email, timezone=timezone)
            session.add(user)
            session.flush()
            print(f"[+] Created user {email}: {user.id}")

        existing = {la.name for la in session.query(LifeArea).filter(LifeArea.user_id == user.id).all()}
        to_add = [name for name in DEFAULT_AREAS if name not in existing]
        for name in to_add:
            la = LifeArea(user_id=user.id, name=name)
            session.add(la)
        session.commit()
        print(f"[✓] Seeded {len(to_add)} life areas for {email}")


if __name__ == "__main__":
    main()

