import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_migrations_create_database(tmp_path: Path) -> None:
    database_path = tmp_path / "migration-test.db"
    database_url = f"sqlite:///{database_path}"

    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url

    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=PROJECT_ROOT,
        env=environment,
        check=True,
    )

    engine = create_engine(database_url)
    inspector = inspect(engine)

    assert set(inspector.get_table_names()) == {"alembic_version", "samples", "stems"}

    sample_columns = {column["name"] for column in inspector.get_columns("samples")}

    assert {
        "id",
        "name",
        "file_path",
        "bpm",
        "musical_key",
        "category",
        "duration_seconds",
        "file_size_bytes",
        "audio_format",
    } <= sample_columns

    stem_columns = {column["name"] for column in inspector.get_columns("stems")}

    assert {"id", "name", "file_path", "stem_type", "sample_id"} <= stem_columns

    engine.dispose()
