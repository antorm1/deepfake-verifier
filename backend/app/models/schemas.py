from pydantic import BaseModel
from typing import Optional

class AnalysisResponse(BaseModel):
    type: str
    filename: Optional[str] = None
    confidence: float
    verdict: str
    hints: list[str]
