from fastapi import FastAPI

from sample_manager.routes import router as sample_router
from sample_manager.stem_routes import router as stem_router

app = FastAPI(title="Sample & Stems Manager", version="0.1.0")

app.include_router(sample_router)
app.include_router(stem_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
