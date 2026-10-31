import math
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from mutagen import File as MutagenFile
from mutagen import MutagenError
from mutagen.mp3 import MP3
from mutagen.wave import WAVE

ALLOWED_AUDIO_TYPES = {".wav": WAVE, ".mp3": MP3}

CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class SavedAudio:
    path: Path
    size_bytes: int
    duration_seconds: float
    audio_format: str


def validate_filename(filename: str | None) -> str:
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename"
        )

    if (
        filename != Path(filename).name
        or "/" in filename
        or "\\" in filename
        or "\x00" in filename
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename"
        )

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only WAV and MP3 files are allowed",
        )

    return extension


def save_audio_file(
    upload: UploadFile, upload_directory: Path, max_size_bytes: int
) -> SavedAudio:
    extension = validate_filename(upload.filename)

    upload_directory.mkdir(parents=True, exist_ok=True)

    safe_directory = upload_directory.resolve()

    destination = (safe_directory / f"{uuid4().hex}{extension}").resolve()

    if safe_directory not in destination.parents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid upload path"
        )

    size_bytes = 0

    try:
        with destination.open("wb") as output:
            while chunk := upload.file.read(CHUNK_SIZE):
                size_bytes += len(chunk)

                if size_bytes > max_size_bytes:
                    raise HTTPException(
                        status_code=413, detail="Audio file is too large"
                    )

                output.write(chunk)

    except HTTPException:
        destination.unlink(missing_ok=True)
        raise

    except OSError as exc:
        destination.unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not store audio file",
        ) from exc

    finally:
        upload.file.close()

    if size_bytes == 0:
        destination.unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Audio file is empty"
        )

    try:
        audio = MutagenFile(str(destination))
    except (MutagenError, OSError, ValueError) as exc:
        print(
            "MUTAGEN ERROR:",
            type(exc).__name__,
            repr(exc),
        )
        destination.unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid audio file"
        ) from exc

    expected_type = ALLOWED_AUDIO_TYPES[extension]

    if audio is None or not isinstance(audio, expected_type):
        destination.unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio content does not match its extension",
        )

    duration = float(audio.info.length)

    if not math.isfinite(duration) or duration <= 0:
        destination.unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid audio duration"
        )

    return SavedAudio(
        path=destination,
        size_bytes=size_bytes,
        duration_seconds=round(duration, 3),
        audio_format=extension.removeprefix("."),
    )


def resolve_managed_file(file_path: str, upload_directory: Path) -> Path:
    safe_directory = upload_directory.resolve()
    resolved_path = Path(file_path).resolve()

    if safe_directory not in resolved_path.parents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found"
        )

    if not resolved_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found"
        )

    return resolved_path
