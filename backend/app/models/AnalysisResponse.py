from pydantic import BaseModel

from app.models.InterviewAnalysis import InterviewAnalysis

class AnalysisResponse(BaseModel):
    status: str
    data: InterviewAnalysis
