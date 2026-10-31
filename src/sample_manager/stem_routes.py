from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sample_manager.audio_files import resolve_managed_file, save_audio_file
from sample_manager.config import settings
from sample_manager.database import get_db
from sample_manager.db_models import SampleDB, StemDB
from sample_manager.models import Stem

router = APIRouter(tags=["stems"])

STEM_UPLOAD_DIR = settings.upload_dir / "stems"
ALLOWED_EXTENSIONS = {".wav", ".mp3"}


def get_stem_or_err(
    stem_id: int,
    db: Session,
) -> StemDB:
    stem = db.get(StemDB, stem_id)

    if stem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Stem not found"
        )
    return stem


@router.post(
    "/samples/{sample_id}/stems/upload",
    response_model=Stem,
    status_code=status.HTTP_201_CREATED,
)
def upload_stem(
    sample_id: int,
    name: str = Form(...),
    stem_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> StemDB:
    sample = db.get(SampleDB, sample_id)

    if sample is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sample not found",
        )

    saved_audio = save_audio_file(
        upload=file,
        upload_directory=STEM_UPLOAD_DIR,
        max_size_bytes=settings.max_audio_size_bytes,
    )

    stem = StemDB(
        name=name,
        stem_type=stem_type,
        file_path=str(saved_audio.path),
        sample_id=sample_id,
    )

    try:
        db.add(stem)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        saved_audio.path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save stem",
        ) from exc

    return stem


@router.get("/samples/{sample_id}/stems", response_model=list[Stem])
def get_sample_stems(sample_id: int, db: Session = Depends(get_db)) -> list[StemDB]:
    sample = db.get(SampleDB, sample_id)

    if sample is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found"
        )

    return (
        db.query(StemDB).filter(StemDB.sample_id == sample_id).order_by(StemDB.id).all()
    )


@router.get("/stems/{stem_id}", response_model=Stem)
def get_stem(stem_id: int, db: Session = Depends(get_db)) -> StemDB:
    return get_stem_or_err(stem_id, db)


@router.get("/stems/{stem_id}/audio")
def download_stem_audio(stem_id: int, db: Session = Depends(get_db)) -> FileResponse:
    stem = get_stem_or_err(stem_id, db)

    file_path = resolve_managed_file(
        file_path=stem.file_path,
        upload_directory=STEM_UPLOAD_DIR,
    )

    media_types = {".wav": "audio/wav", ".mp3": "audio/mpeg"}

    media_type = media_types.get(file_path.suffix.lower(), "application/octet-stream")

    return FileResponse(path=file_path, media_type=media_type, filename=file_path.name)


@router.delete("/stems/{stem_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stem(stem_id: int, db: Session = Depends(get_db)) -> Response:
    stem = get_stem_or_err(stem_id, db)

    file_path = Path(stem.file_path).resolve()
    upload_directory = STEM_UPLOAD_DIR.resolve()

    is_managed_file = upload_directory in file_path.parents

    db.delete(stem)
    db.commit()

    if is_managed_file:
        file_path.unlink(missing_ok=True)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
