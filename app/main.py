# app/main.py
from fastapi import FastAPI

app = FastAPI(
    title="Darwix AI Call Analytics Service",
    description="An API to ingest and analyze sales call transcripts.",
    version="0.1.0"
)

@app.get("/")
def read_root():
    """A simple hello world endpoint."""
    return {"status": "ok", "message": "Welcome to Darwix AI Service!"}