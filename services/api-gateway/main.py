from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"status": "ok", "service": "api"}


@app.get("/health")
def health():
    return {"status": "ok"}
