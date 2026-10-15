from fastapi import FastAPI
from sample_manager.routes import router


app = FastAPI(
    title = "Sample & Stems Manager",
    version="0.1.0"
)

app.include_router(router)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
