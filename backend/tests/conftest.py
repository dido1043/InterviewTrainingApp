import pytest
from unittest.mock import MagicMock

from app.services.ai_service import AIService
from app.models.InterviewAnalysis import InterviewAnalysis


@pytest.fixture
def ai_service():
    """AIService with no real ML models loaded."""
    return AIService(api_key=None, transcriber=None, analyzer=None)


@pytest.fixture
def mock_analysis():
    return InterviewAnalysis(
        score=80,
        filler_words=["um", "like"],
        critique="Good response.",
        improved_script="Hello, I am a software engineer.",
    )


@pytest.fixture
def ai_service_with_analyzer(mock_analysis):
    analyzer = MagicMock(return_value=mock_analysis)
    return AIService(api_key=None, transcriber=None, analyzer=analyzer)
