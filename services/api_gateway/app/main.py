from fastapi import FastAPI

from services.api_gateway.app.db import get_engine

app = FastAPI(title="TODO API Gateway")


@app.on_event("startup")
async def _startup() -> None:
    get_engine()


@app.get("/")
def root():
    return {"status": "ok", "service": "api"}


@app.get("/health")
def health():
    return {"status": "ok"}
