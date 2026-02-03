from fastapi import FastAPI

app = FastAPI(title="TODO API Gateway")


@app.get("/")
def root():
    return {"status": "ok", "service": "api"}


@app.get("/health")
def health():
    return {"status": "ok"}
