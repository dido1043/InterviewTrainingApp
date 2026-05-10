"""Tests for AIService — all private helpers and public analyze_text."""
import os
import wave
import struct
import tempfile
from collections import Counter
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.services.ai_service import AIService, AudioProcessingError
from app.models.InterviewAnalysis import InterviewAnalysis



def _make_wav(path: str, duration_s: float = 0.5, sample_rate: int = 16000) -> None:
    """Write a minimal valid mono WAV file."""
    n_samples = int(duration_s * sample_rate)
    samples = [int(32767 * 0.5 * (i % sample_rate < sample_rate // 2)) for i in range(n_samples)]
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{n_samples}h", *samples))



class TestCountFillers:
    def test_single_filler(self, ai_service):
        counts = ai_service._count_fillers("um, I think um it is good")
        assert counts["um"] == 2

    def test_no_fillers(self, ai_service):
        counts = ai_service._count_fillers("This is a perfectly clean sentence.")
        assert len(counts) == 0

    def test_multiple_fillers(self, ai_service):
        counts = ai_service._count_fillers("You know, like, it is, um, you know, basically fine")
        assert counts["you know"] == 2
        assert counts["like"] == 1
        assert counts["um"] == 1
        assert counts["basically"] == 1

    def test_case_insensitive(self, ai_service):
        counts = ai_service._count_fillers("UM and Um and uM")
        assert counts["um"] == 3

    def test_partial_word_not_counted(self, ai_service):
        # "summer" contains "um" but should not be counted
        counts = ai_service._count_fillers("summer is great")
        assert "um" not in counts

    def test_empty_string(self, ai_service):
        counts = ai_service._count_fillers("")
        assert len(counts) == 0




class TestScoreTranscript:
    def test_baseline(self, ai_service):
        score = ai_service._score_transcript(100, 0, 3)
        assert score == 88  # 82 + 6 (no fillers)

    def test_very_short_response(self, ai_service):
        score = ai_service._score_transcript(20, 0, 1)
        # -14 (short) -8 (<=1 sentence) +6 (no fillers) = 66
        assert score == 66

    def test_single_sentence_penalty(self, ai_service):
        score_multi = ai_service._score_transcript(100, 0, 3)
        score_single = ai_service._score_transcript(100, 0, 1)
        assert score_single < score_multi

    def test_high_filler_ratio_penalty(self, ai_service):
        # 13 fillers / 100 words = 13% > 12% → -28
        score = ai_service._score_transcript(100, 13, 3)
        assert score == 54  # 82 - 28

    def test_moderate_filler_ratio(self, ai_service):
        # 9 fillers / 100 words = 9% → -18
        score = ai_service._score_transcript(100, 9, 3)
        assert score == 64

    def test_score_clamped_to_100(self, ai_service):
        score = ai_service._score_transcript(150, 0, 5)
        assert score <= 100

    def test_score_clamped_to_zero(self, ai_service):
        score = ai_service._score_transcript(5, 100, 1)
        assert score >= 0

    def test_very_long_response_slight_penalty(self, ai_service):
        score = ai_service._score_transcript(300, 0, 10)
        assert score == 84  # 82 -4 +6




class TestBuildCritique:
    def test_short_response_opening(self, ai_service):
        critique = ai_service._build_critique("short", Counter(), 70)
        assert "very short" in critique.lower()

    def test_high_score_opening(self, ai_service):
        text = " ".join(["word"] * 50)
        critique = ai_service._build_critique(text, Counter(), 85)
        assert "clear and direct" in critique.lower()

    def test_medium_score_opening(self, ai_service):
        text = " ".join(["word"] * 50)
        critique = ai_service._build_critique(text, Counter(), 70)
        assert "tighter structure" in critique.lower()

    def test_low_score_opening(self, ai_service):
        text = " ".join(["word"] * 50)
        critique = ai_service._build_critique(text, Counter(), 50)
        assert "hesitant" in critique.lower()

    def test_filler_line_with_fillers(self, ai_service):
        counts = Counter({"um": 5, "like": 3})
        text = " ".join(["word"] * 50)
        critique = ai_service._build_critique(text, counts, 70)
        assert "um" in critique or "like" in critique

    def test_filler_line_without_fillers(self, ai_service):
        text = " ".join(["word"] * 50)
        critique = ai_service._build_critique(text, Counter(), 80)
        assert "well controlled" in critique.lower()




class TestCleanScriptText:
    def test_removes_fillers(self, ai_service):
        cleaned = ai_service._clean_script_text("I um like really want this job")
        assert "um" not in cleaned
        assert "like" not in cleaned

    def test_collapses_whitespace(self, ai_service):
        cleaned = ai_service._clean_script_text("hello   world")
        assert "  " not in cleaned

    def test_strips_leading_trailing_punctuation(self, ai_service):
        cleaned = ai_service._clean_script_text("hello.")
        assert not cleaned.startswith(",")

    def test_empty_fallback(self, ai_service):
        # All fillers → falls back to original stripped text
        result = ai_service._clean_script_text("um")
        assert result  # not empty

    def test_double_comma_cleanup(self, ai_service):
        cleaned = ai_service._clean_script_text("hello,, world")
        assert ",," not in cleaned



class TestLooksLikeBulgarian:
    def test_cyrillic_detected(self, ai_service):
        assert ai_service._looks_like_bulgarian("Здравейте, аз съм Иван.") is True

    def test_transliterated_markers(self, ai_service):
        assert ai_service._looks_like_bulgarian("zdravei az intervyu") is True

    def test_english_not_detected(self, ai_service):
        assert ai_service._looks_like_bulgarian("Hello, I am a software engineer.") is False

    def test_single_marker_not_enough(self, ai_service):
        assert ai_service._looks_like_bulgarian("zdravei everyone") is False




class TestExtractCandidateName:
    def test_az_sum_pattern(self, ai_service):
        assert ai_service._extract_candidate_name("аз съм Иван") == "Иван"

    def test_kazvam_se_pattern(self, ai_service):
        assert ai_service._extract_candidate_name("казвам се Мария") == "Мария"

    def test_no_name(self, ai_service):
        assert ai_service._extract_candidate_name("Hello world") is None

    def test_capitalizes_name(self, ai_service):
        result = ai_service._extract_candidate_name("аз съм иван")
        assert result is None or result[0].isupper()




class TestExtractCandidateRole:
    def test_java(self, ai_service):
        assert ai_service._extract_candidate_role("I work with Java") == "Java разработчик"

    def test_python(self, ai_service):
        assert ai_service._extract_candidate_role("python developer") == "Python разработчик"

    def test_frontend(self, ai_service):
        assert ai_service._extract_candidate_role("frontend engineer") == "Frontend разработчик"

    def test_backend(self, ai_service):
        assert ai_service._extract_candidate_role("I do backend work") == "Backend разработчик"

    def test_fullstack(self, ai_service):
        assert ai_service._extract_candidate_role("fullstack developer") == "Full-stack разработчик"

    def test_generic_developer(self, ai_service):
        assert ai_service._extract_candidate_role("I am a developer") == "разработчик"

    def test_unknown(self, ai_service):
        assert ai_service._extract_candidate_role("I love music") is None




class TestNormalizeBulgarianScript:
    def test_ya_replaced_with_az(self, ai_service):
        result = ai_service._normalize_bulgarian_script("я съм тук")
        assert "аз" in result.lower()

    def test_djava_replaced(self, ai_service):
        result = ai_service._normalize_bulgarian_script("работя с джава")
        assert "Java" in result

    def test_capitalizes_first_letter(self, ai_service):
        result = ai_service._normalize_bulgarian_script("hello world")
        assert result[0].isupper()

    def test_empty_string(self, ai_service):
        result = ai_service._normalize_bulgarian_script("")
        assert result == ""




class TestBuildImprovedScript:
    def test_ends_with_period(self, ai_service):
        result = ai_service._build_improved_script("I want to work here")
        assert result[-1] in ".!?"

    def test_bulgarian_path(self, ai_service):
        result = ai_service._build_improved_script("Здравейте, аз съм Иван.")
        assert result  # non-empty

    def test_english_path(self, ai_service):
        result = ai_service._build_improved_script("I am a software engineer with five years of experience.")
        assert result



class TestAnalyzeText:
    def test_empty_text_raises(self, ai_service):
        with pytest.raises(ValueError):
            ai_service.analyze_text("")

    def test_whitespace_only_raises(self, ai_service):
        with pytest.raises(ValueError):
            ai_service.analyze_text("   ")

    def test_returns_interview_analysis(self, ai_service):
        result = ai_service.analyze_text("I am a software engineer with experience in Python and cloud services.")
        assert isinstance(result, InterviewAnalysis)

    def test_score_in_range(self, ai_service):
        result = ai_service.analyze_text("I am a software engineer with experience in Python and cloud services.")
        assert 0 <= result.score <= 100

    def test_filler_words_detected(self, ai_service):
        result = ai_service.analyze_text("Um, I like, you know, basically want this job, um.")
        assert "um" in result.filler_words

    def test_no_filler_words(self, ai_service):
        result = ai_service.analyze_text("I am a software engineer with five years of experience.")
        assert result.filler_words == []

    def test_injected_analyzer_used(self, ai_service_with_analyzer, mock_analysis):
        result = ai_service_with_analyzer.analyze_text("some text about something")
        assert result == mock_analysis

    def test_critique_is_string(self, ai_service):
        result = ai_service.analyze_text("I built a payment system that processed one million transactions daily.")
        assert isinstance(result.critique, str) and len(result.critique) > 0

    def test_improved_script_is_string(self, ai_service):
        result = ai_service.analyze_text("I built a payment system that processed one million transactions daily.")
        assert isinstance(result.improved_script, str) and len(result.improved_script) > 0



class TestTranscribeAudio:
    def test_missing_file_raises(self, ai_service):
        mock_transcriber = MagicMock()
        ai_service._transcriber = mock_transcriber
        with pytest.raises(AudioProcessingError):
            ai_service.transcribe_audio("/nonexistent/path/audio.wav")

    def test_successful_transcription(self, ai_service):
        mock_transcriber = MagicMock()
        mock_transcriber.return_value = {"text": "Hello world"}
        mock_transcriber.feature_extractor = MagicMock(sampling_rate=16000)
        ai_service._transcriber = mock_transcriber

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name

        try:
            _make_wav(wav_path)
            result = ai_service.transcribe_audio(wav_path)
            assert result == "Hello world"
        finally:
            os.remove(wav_path)

    def test_empty_transcription_raises(self, ai_service):
        mock_transcriber = MagicMock()
        mock_transcriber.return_value = {"text": ""}
        mock_transcriber.feature_extractor = MagicMock(sampling_rate=16000)
        ai_service._transcriber = mock_transcriber

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name

        try:
            _make_wav(wav_path)
            with pytest.raises(AudioProcessingError):
                ai_service.transcribe_audio(wav_path)
        finally:
            os.remove(wav_path)
