"""Tests for FastAPI endpoints."""
import io
import wave
import struct
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.api.endpoints import get_ai_service
from app.services.ai_service import AIService, AudioProcessingError
from app.models.InterviewAnalysis import InterviewAnalysis


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wav_bytes(duration_s: float = 0.3, sample_rate: int = 16000) -> bytes:
    n = int(duration_s * sample_rate)
    buf = io.BytesIO()
    with wave.open(buf, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{n}h", *[0] * n))
    return buf.getvalue()


def _make_mock_service(analysis: InterviewAnalysis | None = None) -> AIService:
    svc = MagicMock(spec=AIService)
    svc.transcribe_audio.return_value = "Hello, I am a software engineer."
    svc.analyze_text.return_value = analysis or InterviewAnalysis(
        score=78,
        filler_words=["um"],
        critique="Good overall.",
        improved_script="Hello, I am a software engineer.",
    )
    return svc


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    def test_returns_200(self):
        with TestClient(app) as client:
            response = client.get("/api/health")
        assert response.status_code == 200

    def test_returns_ok(self):
        with TestClient(app) as client:
            response = client.get("/api/health")
        assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# POST /api/analyze
# ---------------------------------------------------------------------------

class TestAnalyzePitch:
    def _client_with_service(self, service: AIService) -> TestClient:
        app.dependency_overrides[get_ai_service] = lambda: service
        return TestClient(app)

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_successful_analysis(self):
        client = self._client_with_service(_make_mock_service())
        response = client.post(
            "/api/analyze",
            files={"file": ("test.wav", _wav_bytes(), "audio/wav")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert "data" in body

    def test_response_shape(self):
        client = self._client_with_service(_make_mock_service())
        response = client.post(
            "/api/analyze",
            files={"file": ("test.wav", _wav_bytes(), "audio/wav")},
        )
        data = response.json()["data"]
        assert "score" in data
        assert "filler_words" in data
        assert "critique" in data
        assert "improved_script" in data

    def test_missing_file_returns_422(self):
        client = self._client_with_service(_make_mock_service())
        response = client.post("/api/analyze")
        assert response.status_code == 422

    def test_value_error_returns_400(self):
        svc = _make_mock_service()
        svc.transcribe_audio.side_effect = ValueError("audio is empty")
        client = self._client_with_service(svc)
        response = client.post(
            "/api/analyze",
            files={"file": ("test.wav", _wav_bytes(), "audio/wav")},
        )
        assert response.status_code == 400
        assert "audio is empty" in response.json()["detail"]

    def test_audio_processing_error_returns_500(self):
        svc = _make_mock_service()
        svc.transcribe_audio.side_effect = AudioProcessingError("bad codec")
        client = self._client_with_service(svc)
        response = client.post(
            "/api/analyze",
            files={"file": ("test.wav", _wav_bytes(), "audio/wav")},
        )
        assert response.status_code == 500
        assert "bad codec" in response.json()["detail"]

    def test_unexpected_error_returns_500(self):
        svc = _make_mock_service()
        svc.transcribe_audio.side_effect = RuntimeError("unexpected")
        client = self._client_with_service(svc)
        response = client.post(
            "/api/analyze",
            files={"file": ("test.wav", _wav_bytes(), "audio/wav")},
        )
        assert response.status_code == 500

    def test_score_is_integer(self):
        client = self._client_with_service(_make_mock_service())
        response = client.post(
            "/api/analyze",
            files={"file": ("test.wav", _wav_bytes(), "audio/wav")},
        )
        assert isinstance(response.json()["data"]["score"], int)
