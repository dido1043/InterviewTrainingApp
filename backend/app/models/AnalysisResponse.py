from pydantic import BaseModel
from models.InterviewAnalysis import InterviewAnalysis

class AnalysisResponse(BaseModel):
    status: str
    data: InterviewAnalysis