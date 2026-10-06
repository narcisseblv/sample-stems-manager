from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Creation of samples.db at the root.
DATABASE_URL = "sqlite:///./samples.db"

# SQLAlchemy engine which enables the link between Python and SQLite.

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} # check_same_thread=False enables FastAPI to use SQLite connection from different threads. 
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
    