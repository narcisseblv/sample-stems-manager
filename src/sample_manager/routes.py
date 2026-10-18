from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from sample_manager.database import get_db
from sample_manager.db_models import SampleDB
from sample_manager.models import Sample, SampleCreate, SampleUpdate

from mutagen import File as MutagenFile
from mutagen import MutagenError

UPLOAD_DIR = Path('uploads')
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3"}

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
async def upload_sample(
    name: str = Form(...),
    category: str = Form(...),
    bpm: int | None = Form(default=None),
    musical_key: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> SampleDB:
    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only WAV and MP3 files are allowed"
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid4()}{extension}"
    stored_path = UPLOAD_DIR / stored_filename

    file_content = await file.read()
    stored_path.write_bytes(file_content)
    await file.close()

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

    duration_seconds = round(
        float(audio.info.length),
        3
    )

    file_size_bytes = stored_path.stat().st_size
    audio_format = extension.removeprefix(".")

    new_sample = SampleDB(
        name=name,
        file_path=str(stored_path),
        bpm=bpm,
        musical_key=musical_key,
        category=category,
        duration_seconds=duration_seconds,
        file_size_bytes=file_size_bytes,
        audio_format=audio_format   
    )

    db.add(new_sample)
    db.commit()
    db.refresh(new_sample)

    return new_sample

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
    file_path = Path(sample.file_path).resolve()
    upload_directory = UPLOAD_DIR.resolve()

    if (
        upload_directory not in file_path.parents
        or not file_path.is_file()
    ):
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
        filename=f"{sample.name}{file_path.suffix}"
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