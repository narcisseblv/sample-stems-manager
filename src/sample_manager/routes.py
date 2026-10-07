from fastapi import APIRouter, Depends, HTTPException, Response, status
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
def create_sample(sample_data: SampleCreate, 
                  db: Session = Depends(get_db)) -> SampleDB:
    new_sample = SampleDB(**sample_data.model_dump())

    db.add(new_sample)
    db.commit()
    db.refresh(new_sample)

    return new_sample

@router.get("", response_model=list[Sample])
def get_samples(db: Session = Depends(get_db)) -> list[SampleDB]:
    return db.query(SampleDB).all()

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




