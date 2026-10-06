from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

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
