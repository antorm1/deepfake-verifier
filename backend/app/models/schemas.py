from pydantic import BaseModel
from typing import Optional, List

class AnalysisResponse(BaseModel):
    type: str
    filename: Optional[str] = None
    confidence: float
    verdict: str
    hints: List[str]
