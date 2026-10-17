from pydantic import BaseModel, ConfigDict, Field

class SampleCreate(BaseModel):
    name: str
    file_path: str
    bpm: int | None = Field(default=None, ge=20, le=300)
    musical_key: str | None = None
    category: str

class Sample(SampleCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    duration_seconds: float | None = None
    file_size_bytes: int | None = None
    audio_format: str | None = None

class SampleUpdate(BaseModel):
    name: str | None = None
    file_path: str | None = None
    bpm: int | None = Field(default=None, ge=20, le=300)
    musical_key : str | None = None
    category: str | None = None

