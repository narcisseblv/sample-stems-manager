from pydantic import BaseModel, Field

class SampleCreate(BaseModel):
    name: str
    file_path: str
    bpm: int | None = Field(default=None, ge=20, le=300)
    musical_key: str | None = None
    category: str

class Sample(SampleCreate):
    id: int

class SampleUpdate(BaseModel):
    name: str | None = None
    file_path: str | None = None
    bpm: int | None = Field(default=None, ge=20, le=300)
    musical_key : str | None = None
    category: str | None = None

