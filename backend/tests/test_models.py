import pytest
from pydantic import ValidationError

from app.models.InterviewAnalysis import InterviewAnalysis
from app.models.AnalysisResponse import AnalysisResponse


class TestInterviewAnalysis:
    def test_valid_model(self):
        obj = InterviewAnalysis(score=75, filler_words=["um"], critique="ok", improved_script="Better.")
        assert obj.score == 75

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            InterviewAnalysis(score=75, filler_words=[], critique="ok")  # missing improved_script

    def test_filler_words_is_list(self):
        obj = InterviewAnalysis(score=80, filler_words=[], critique="Good.", improved_script="Great.")
        assert isinstance(obj.filler_words, list)

    def test_score_stored_as_int(self):
        obj = InterviewAnalysis(score=90, filler_words=[], critique="x", improved_script="y")
        assert isinstance(obj.score, int)


class TestAnalysisResponse:
    def _analysis(self):
        return InterviewAnalysis(score=70, filler_words=["like"], critique="ok", improved_script="Better.")

    def test_valid_model(self):
        obj = AnalysisResponse(status="success", data=self._analysis())
        assert obj.status == "success"

    def test_missing_status_raises(self):
        with pytest.raises(ValidationError):
            AnalysisResponse(data=self._analysis())

    def test_data_is_interview_analysis(self):
        obj = AnalysisResponse(status="success", data=self._analysis())
        assert isinstance(obj.data, InterviewAnalysis)

    def test_serialization(self):
        obj = AnalysisResponse(status="success", data=self._analysis())
        d = obj.model_dump()
        assert d["status"] == "success"
        assert d["data"]["score"] == 70
