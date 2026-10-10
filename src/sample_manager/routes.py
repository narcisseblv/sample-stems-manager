from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from sample_manager.database import get_db
from sample_manager.db_models import SampleDB
from sample_manager.models import Sample, SampleCreate, SampleUpdate

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

    return query.order_by(SampleDB.id).all()

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

    db.delete(sample)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Sample not found"
    )




