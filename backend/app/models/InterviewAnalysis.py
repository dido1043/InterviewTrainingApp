from pydantic import BaseModel
from typing import List

class InterviewAnalysis(BaseModel):
    score: int
    filler_words: List[str]
    critique: str
    improved_script: str
