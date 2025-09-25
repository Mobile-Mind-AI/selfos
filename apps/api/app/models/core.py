from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_mixin

from ..db import Base


def ulid() -> str:
    # Runtime dependency provided via ulid-py
    from ulid import ULID

    return str(ULID())


@declarative_mixin
class IdMixin:
    id = Column(String, primary_key=True, default=ulid)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class User(Base, IdMixin):
    __tablename__ = "users"
    __table_args__ = {"schema": "core"}

    email = Column(String, nullable=False)
    timezone = Column(String, nullable=True)
    prefs = Column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        UniqueConstraint("email", name="ux_users_email"),
        {"schema": "core"},
    )


class LifeArea(Base, IdMixin):
    __tablename__ = "life_areas"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="ux_life_areas_user_name"),
        {"schema": "core"},
    )

    user_id = Column(String, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    color = Column(String, nullable=True)


class LifeAreaLink(Base):
    __tablename__ = "life_area_links"
    __table_args__ = (
        UniqueConstraint("life_area_id", "object_type", "object_id", name="pk_life_area_link"),
        Index("ix_lal_user_object", "user_id", "object_type", "object_id"),
        CheckConstraint("object_type in ('dream','goal','project','task','habit')", name="ck_lal_object_type"),
        {"schema": "core"},
    )

    life_area_id = Column(String, ForeignKey("core.life_areas.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False)
    object_type = Column(String, nullable=False)
    object_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Dream(Base, IdMixin):
    __tablename__ = "dreams"
    __table_args__ = {"schema": "core"}

    user_id = Column(String, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="incubating")
    horizon = Column(String, nullable=True)  # short|medium|long


class Project(Base, IdMixin):
    __tablename__ = "projects"
    __table_args__ = {"schema": "core"}

    user_id = Column(String, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="active")


class Goal(Base, IdMixin):
    __tablename__ = "goals"
    __table_args__ = (
        Index("ix_goals_user_created", "user_id", "created_at"),
        {"schema": "core"},
    )

    user_id = Column(String, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False)
    dream_id = Column(String, ForeignKey("core.dreams.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(String, ForeignKey("core.projects.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    target_date = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="active")


class Habit(Base, IdMixin):
    __tablename__ = "habits"
    __table_args__ = {"schema": "core"}

    user_id = Column(String, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    schedule_rrule = Column(Text, nullable=True)
    cadence_target = Column(Integer, nullable=True)
    period = Column(String, nullable=True)  # day|week|month
    streak = Column(Integer, nullable=False, default=0)
    last_done_at = Column(DateTime, nullable=True)


class HabitLog(Base):
    __tablename__ = "habit_logs"
    __table_args__ = (
        UniqueConstraint("habit_id", "occurred_at", name="pk_habit_log"),
        {"schema": "core"},
    )

    habit_id = Column(String, ForeignKey("core.habits.id", ondelete="CASCADE"), primary_key=True)
    occurred_at = Column(DateTime, primary_key=True)
    value = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)


class Task(Base, IdMixin):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_user_status", "user_id", "status"),
        Index("ix_tasks_user_due", "user_id", "due_at"),
        {"schema": "core"},
    )

    user_id = Column(String, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False)
    goal_id = Column(String, ForeignKey("core.goals.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(String, ForeignKey("core.projects.id", ondelete="SET NULL"), nullable=True)
    habit_id = Column(String, ForeignKey("core.habits.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="pending")
    due_at = Column(DateTime, nullable=True)
    rrule = Column(Text, nullable=True)
    effort_minutes = Column(Integer, nullable=True)


class Attachment(Base, IdMixin):
    __tablename__ = "attachments"
    __table_args__ = {"schema": "core"}

    user_id = Column(String, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False)
    ref_type = Column(String, nullable=False)  # dream|goal|project|task|habit|entity
    ref_id = Column(String, nullable=False)
    gcs_path = Column(String, nullable=False)
    mime = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=True)

