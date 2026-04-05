import InterviewAnalysis
from pydantic import BaseModel

class AnalysisResponse(BaseModel):
    status: str
    data: InterviewAnalysis