from fastapi import FastAPI

app = FastAPI(title="TrackingDB26 API")


@app.get("/")
def home():
    return {"message": "TrackingDB26 API funcionando"}


@app.get("/health")
def health():
    return {"status": "ok"}
