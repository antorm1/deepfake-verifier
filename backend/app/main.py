from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import analyze, health

app = FastAPI(title="Deepfake Verifier", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(analyze.router, prefix="/api/v1", tags=["analyze"])

@app.get("/")
def root():
    return {"service": "deepfake-verifier", "status": "ready"}
