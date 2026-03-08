"""GyroFinance — FastAPI entry point."""

from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title="GyroFinance",
    description="Financial analysis engine with deterministic core and isolated LLM layer.",
    version="0.1.0",
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok", "service": "gyrofinance"}
