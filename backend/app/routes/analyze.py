from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.analyzer_service import analyze_file

router = APIRouter()

@router.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    try:
        result = await analyze_file(file)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
def root():
    return {"service": "deepfake-verifier", "status": "ready"}
