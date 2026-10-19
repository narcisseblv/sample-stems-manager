from __future__ import annotations
from sqlalchemy import ForeignKey, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sample_manager.database import Base

class SampleDB(Base):
    __tablename__ = "samples"

    id: Mapped[int] = mapped_column(
        primary_key = True,
        index = True
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    bpm: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    musical_key: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )   

    duration_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    file_size_bytes: Mapped[int | None] = mapped_column(
        nullable=True
    )

    audio_format: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True
    )

    stems: Mapped[list["StemDB"]] = relationship(
        back_populates="sample",
        cascade="all, delete-orphan"
    )

class StemDB(Base):
    __tablename__ = "stems"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    stem_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    sample_id: Mapped[int] = mapped_column(
        ForeignKey(
            "samples.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    sample: Mapped["SampleDB"] = relationship(
        back_populates="stems"
    )