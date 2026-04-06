from fastapi import APIRouter, UploadFile, File, Depends
from services.ai_service import AIService
from models.AnalysisResponse import AnalysisResponse
import shutil

router = APIRouter()

# Dependency Injection (like @Autowired)
def get_ai_service():
    return AIService(api_key="your-key-here")

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_pitch(file: UploadFile = File(...), ai_service: AIService = Depends(get_ai_service)):
    # 1. Save the uploaded audio file temporarily
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 2. Process through AI Service
    transcript = ai_service.transcribe_audio(temp_path)
    analysis = ai_service.analyze_text(transcript)
    
    return {"status": "success", "data": analysis}