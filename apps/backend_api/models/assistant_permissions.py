"""
Assistant permission models for sharing and access control.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from .base import Base


class PermissionLevel(enum.Enum):
    """Permission levels for assistant access."""

    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class AssistantPermission(Base):
    """Model for assistant sharing permissions."""

    __tablename__ = "assistant_permissions"

    id = Column(Integer, primary_key=True, index=True)
    assistant_id = Column(String, ForeignKey("assistant_profiles.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    permission_level = Column(
        SQLEnum(PermissionLevel), nullable=False, default=PermissionLevel.VIEWER
    )

    # Permission details
    can_edit = Column(Boolean, nullable=False, default=False)
    can_share = Column(Boolean, nullable=False, default=False)
    can_delete = Column(Boolean, nullable=False, default=False)

    # Expiration
    expires_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    assistant = relationship("AssistantProfile", back_populates="permissions")
    user = relationship("User", back_populates="assistant_permissions")

    # Indexes for performance
    __table_args__ = (
        Index(
            "ix_assistant_permissions_assistant_user",
            "assistant_id",
            "user_id",
            unique=True,
        ),
        Index("ix_assistant_permissions_user", "user_id"),
    )
