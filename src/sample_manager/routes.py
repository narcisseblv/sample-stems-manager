from pathlib import Path
# from uuid import uuid4
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from sample_manager.audio_files import save_audio_file, resolve_managed_file
from sample_manager.config import settings
from sample_manager.database import get_db
from sample_manager.db_models import SampleDB
from sample_manager.models import Sample, SampleCreate, SampleUpdate
from sample_manager.config import settings

#from mutagen import File as MutagenFile
#from mutagen import MutagenError

UPLOAD_DIR = settings.upload_dir
# ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3"}

router = APIRouter(
    prefix="/samples",
    tags=["samples"]
)

@router.post(
    "",
    response_model=Sample,
    status_code=status.HTTP_201_CREATED
)
def create_sample(
    sample_data: SampleCreate, 
    db: Session = Depends(get_db)) -> SampleDB:
    new_sample = SampleDB(**sample_data.model_dump())

    db.add(new_sample)
    db.commit()
    db.refresh(new_sample)

    return new_sample

@router.get("", response_model=list[Sample])
def get_samples(
    name: str | None = None,
    category: str | None = None,
    musical_key: str | None = None,
    min_bpm: int | None = Query(default=None, ge=20, le=300),
    max_bpm: int | None = Query(default=None, ge=20, le=300),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)) -> list[SampleDB]:
    if (
        min_bpm is not None 
        and max_bpm is not None
        and min_bpm > max_bpm
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_bpm cannot be greater than max_bpm"
        )
    query = db.query(SampleDB)

    if name is not None:
        query = query.filter(
            SampleDB.name.ilike(f"%{name}%")
        )

    if category is not None:
        query = query.filter(
            SampleDB.category.ilike(category)
        )

    if musical_key is not None:
        query = query.filter(
            SampleDB.musical_key.ilike(musical_key)
        )

    if min_bpm is not None:
        query = query.filter(
            SampleDB.bpm >= min_bpm
        )

    if max_bpm is not None:
        query = query.filter(
            SampleDB.bpm <= max_bpm
        )

    return query.order_by(SampleDB.id).offset(offset).limit(limit).all()

@router.post(
    "/upload",
    response_model=Sample,
    status_code=status.HTTP_201_CREATED
)
def upload_sample(
    name: str = Form(...),
    category: str = Form(...),
    bpm: int | None = Form(default=None, ge=20, le=300),
    musical_key: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> SampleDB:
    saved_audio = save_audio_file(
        upload=file,
        upload_directory=UPLOAD_DIR,
        max_size_bytes=settings.max_audio_size_bytes
    )

    sample = SampleDB(
        name=name,
        file_path=str(saved_audio.path),
        bpm=bpm,
        musical_key=musical_key,
        category=category,
        duration_seconds=saved_audio.duration_seconds,
        file_size_bytes=saved_audio.size_bytes,
        audio_format=saved_audio.audio_format
    )

    try:
        db.add(sample)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        saved_audio.path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save sample"
        ) from exc
    db.refresh(sample)

    return sample

  
@router.get(
    "/{sample_id}/audio",
    response_class=FileResponse
)
def download_sample_audio(
    sample_id: int,
    db: Session = Depends(get_db)
) -> FileResponse:
    sample = db.get(SampleDB, sample_id)

    if sample is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sample not found"
        )
    file_path = resolve_managed_file(
        file_path=sample.file_path,
        upload_directory=UPLOAD_DIR
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
@router.get(
    "/{sample_id}",
    response_model=Sample
)
def get_sample(sample_id: int, db: Session = Depends(get_db)) -> SampleDB:
    sample = db.get(SampleDB, sample_id)
    if sample is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Sample not found"
        )
    return sample

@router.patch("/{sample_id}", response_model=Sample)
def update_sample(sample_id: int, sample_data:SampleUpdate,
                  db: Session = Depends(get_db)) -> SampleDB:
    sample = db.get(SampleDB, sample_id)

    if sample is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sample not found"
        )

    update_data = sample_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(sample, field, value)

    db.commit()
    db.refresh(sample)

    return sample

@router.delete(
    "/{sample_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_sample(sample_id: int, 
                  db: Session = Depends(get_db)) -> Response:  
    sample = db.get(SampleDB, sample_id)

    if sample is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sample not found"
            )

    file_path = Path(sample.file_path).resolve()
    upload_directory = UPLOAD_DIR.resolve()

    is_uploaded_file = upload_directory in file_path.parents

    db.delete(sample)
    db.commit()

    if is_uploaded_file:
        file_path.unlink(missing_ok=True)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT)