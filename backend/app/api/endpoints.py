import os
import shutil
from functools import lru_cache
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from models.AnalysisResponse import AnalysisResponse
from services.ai_service import AIService
from services.ai_service import AudioProcessingError

router = APIRouter()

# Dependency Injection (like @Autowired)
@lru_cache(maxsize=1)
def get_ai_service():
    return AIService(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_pitch(file: UploadFile = File(...), ai_service: AIService = Depends(get_ai_service)):
    temp_path = None

    try:
        suffix = Path(file.filename or "upload.wav").suffix or ".wav"
        with NamedTemporaryFile(delete=False, suffix=suffix, prefix="upload_", dir=".") as buffer:
            shutil.copyfileobj(file.file, buffer)
            temp_path = buffer.name

        transcript = ai_service.transcribe_audio(temp_path)
        analysis = ai_service.analyze_text(transcript)

        return {"status": "success", "data": analysis}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AudioProcessingError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc
    finally:
        await file.close()
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
