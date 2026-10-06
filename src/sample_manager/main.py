from fastapi import FastAPI
from sample_manager.routes import router
from sample_manager import db_models
from sample_manager.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title = "Sample & Stems Manager",
    version="0.1.0"
)

app.include_router(router)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
