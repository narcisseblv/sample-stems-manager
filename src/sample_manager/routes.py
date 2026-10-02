from fastapi import APIRouter, HTTPException, status
from sample_manager.models import Sample, SampleCreate

router = APIRouter(
    prefix="/samples",
    tags=["samples"]
)

samples: list[Sample] = []

@router.post(
    "",
    response_model=Sample,
    status_code=status.HTTP_201_CREATED
)
def create_sample(sample_data: SampleCreate) -> Sample:

    next_id = max(
        (sample.id for sample in samples),
        default=0
    ) + 1

    new_sample = Sample(
        id = next_id,
        **sample_data.model_dump()
    )

    samples.append(new_sample)
    return new_sample

@router.get("", response_model=list[Sample])
def get_samples() -> list[Sample]:
    return samples

@router.get(
    "/{sample_id}",
    response_model=Sample
)
def get_sample(sample_id: int) -> Sample:
    for sample in samples:
        if sample.id == sample_id:
            return sample

    raise HTTPException(
        status_code = status.HTTP_404_NOT_FOUND,
        detail = "Sample not found"
    )



