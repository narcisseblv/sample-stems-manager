import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status
)
from fastapi.responses import FileResponse
from mutagen import File as MutagenFile
from mutagen import MutagenError
from sqlalchemy.orm import Session

from sample_manager.database import get_db
from sample_manager.db_models import SampleDB, StemDB
from sample_manager.models import Stem
from sample_manager.config import settings

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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stem not found"
        )
    return stem

@router.post(
    "/samples/{sample_id}/stems/upload",
    response_model=Stem,
    status_code=status.HTTP_201_CREATED
)
def upload_stem(
    sample_id: int,
    name: str = Form(...),
    stem_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> StemDB:
    sample = db.get(SampleDB, sample_id)

    if sample is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sample not found"
        )

    original_filename = file.filename or ""
    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only WAV and MP3 files are not allowed"
        )

    STEM_UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    stored_path = (STEM_UPLOAD_DIR / f"{uuid4()}{extension}")

    try:
        with stored_path.open("wb") as destination:
            shutil.copyfileobj(
                file.file,
                destination
            )
    finally:
        file.file.close()

    try:
        audio = MutagenFile(stored_path)
    except (MutagenError, OSError):
        stored_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid audio file"
        )

    if audio is None or not hasattr(audio, "info"):
        stored_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid audio file"         
        )

    stem = StemDB(
        name=name,
        file_path=str(stored_path),
        stem_type=stem_type,
        sample_id=sample_id
    )

    try:
        db.add(stem)
        db.commit()
        db.refresh(stem)
    except Exception:
        db.rollback()
        stored_path.unlink(missing_ok=True)
        raise

    return stem

@router.get(
    "/samples/{sample_id}/stems",
    response_model=list[Stem]
)
def get_sample_stems(
    sample_id: int,
    db: Session = Depends(get_db)
) -> list[StemDB]:
    sample = db.get(SampleDB, sample_id)

    if sample is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sample not found"
        )

    return(
        db.query(StemDB)
        .filter(StemDB.sample_id == sample_id)
        .order_by(StemDB.id)
        .all()
    )

@router.get("/stems/{stem_id}",
            response_model=Stem)
def get_stem(
    stem_id: int,
    db: Session = Depends(get_db)
) -> StemDB:
    return get_stem_or_err(stem_id, db)

@router.get("/stems/{stem_id}/audio")
def download_stem_audio(
    stem_id: int,
    db: Session = Depends(get_db)
) -> FileResponse:
    stem = get_stem_or_err(stem_id, db)

    file_path = Path(stem.file_path)

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )

    media_types = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg"
    }

    media_type = media_types.get(
        file_path.suffix.lower(),
        "application/octet-stream"
    )

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=file_path.name
    )

@router.delete(
    "/stems/{stem_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_stem(
    stem_id: int,
    db: Session = Depends(get_db)
) -> Response:
    stem = get_stem_or_err(stem_id, db)

    file_path = Path(stem.file_path).resolve()
    upload_directory = STEM_UPLOAD_DIR.resolve()

    is_managed_file = (
        upload_directory in file_path.parents
    )

    db.delete(stem)
    db.commit()

    if is_managed_file:
        file_path.unlink(missing_ok=True)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )