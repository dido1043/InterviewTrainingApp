import math
import os
import re
import shutil
from collections import Counter
import numpy as np
import soundfile as sf
from scipy import signal
from transformers import pipeline

from app.models.InterviewAnalysis import InterviewAnalysis


class AudioProcessingError(RuntimeError):
    """Raised when uploaded audio cannot be decoded for transcription."""


class AIService:
    def __init__(self, api_key: str = None, transcriber=None, analyzer=None):
        self.api_key = api_key
        self._transcriber = transcriber
        self._analyzer = analyzer
        self._filler_patterns = [
            "um",
            "uh",
            "like",
            "you know",
            "i mean",
            "basically",
            "actually",
            "literally",
            "sort of",
            "kind of",
            "so",
            "well",
            "right",
        ]

    @property
    def transcriber(self):
        if self._transcriber is None:
            print("Loading Hugging Face transcription model...")
            self._transcriber = pipeline(
                "automatic-speech-recognition",
                model="openai/whisper-small",
            )
        return self._transcriber

    @property
    def analyzer(self):
        return self._analyzer

    def _resample_audio(self, audio: np.ndarray, sampling_rate: int, target_rate: int) -> np.ndarray:
        if sampling_rate == target_rate:
            return np.ascontiguousarray(audio, dtype=np.float32)

        divisor = math.gcd(sampling_rate, target_rate)
        resampled = signal.resample_poly(audio, target_rate // divisor, sampling_rate // divisor)
        return np.ascontiguousarray(resampled, dtype=np.float32)

    def _load_audio_with_soundfile(self, audio_path: str) -> dict:
        try:
            audio, sampling_rate = sf.read(audio_path, dtype="float32", always_2d=False)
        except Exception as exc:
            raise AudioProcessingError(
                "This audio format needs an external decoder. Install ffmpeg "
                "(`brew install ffmpeg`) or upload a WAV file."
            ) from exc

        if audio.size == 0:
            raise ValueError("Uploaded audio file is empty")

        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        target_rate = self.transcriber.feature_extractor.sampling_rate
        audio = self._resample_audio(audio, sampling_rate, target_rate)

        return {
            "array": audio,
            "sampling_rate": target_rate,
        }

    def transcribe_audio(self, audio_path: str) -> str:
        try:
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")

            print(f"Transcribing audio: {audio_path}")

            try:
                audio_input = self._load_audio_with_soundfile(audio_path)
            except AudioProcessingError:
                if shutil.which("ffmpeg"):
                    audio_input = audio_path
                else:
                    raise

            result = self.transcriber(audio_input)
            transcript = result.get("text", "")
            if not transcript:
                raise ValueError("Transcription returned empty result")

            print(f"Transcription successful: {len(transcript)} characters")
            return transcript
        except AudioProcessingError as exc:
            print(f"Audio decoding error: {exc}")
            raise
        except Exception as exc:
            print(f"Error during transcription: {exc}")
            raise AudioProcessingError(f"Transcription failed: {str(exc)}") from exc

    def _count_fillers(self, text: str) -> Counter:
        lowered = text.lower()
        counts = Counter()

        for filler in self._filler_patterns:
            pattern = rf"(?<!\w){re.escape(filler)}(?!\w)"
            matches = re.findall(pattern, lowered)
            if matches:
                counts[filler] = len(matches)

        return counts

    def _score_transcript(self, word_count: int, filler_total: int, sentence_count: int) -> int:
        score = 82

        if word_count < 40:
            score -= 14
        elif word_count < 80:
            score -= 7
        elif word_count > 260:
            score -= 4

        if sentence_count <= 1:
            score -= 8

        filler_ratio = filler_total / max(word_count, 1)
        if filler_ratio > 0.12:
            score -= 28
        elif filler_ratio > 0.08:
            score -= 18
        elif filler_ratio > 0.04:
            score -= 10
        elif filler_total == 0:
            score += 6

        return max(0, min(100, score))

    def _build_critique(self, text: str, filler_counts: Counter, score: int) -> str:
        word_count = len(re.findall(r"\b[\w']+\b", text))
        top_fillers = [word for word, _count in filler_counts.most_common(3)]

        if word_count < 40:
            opening = "The response is very short, so it does not yet give enough proof of impact, structure, or confidence."
        elif score >= 80:
            opening = "The response is fairly clear and direct, with a solid base to build on."
        elif score >= 65:
            opening = "The response communicates the main idea, but it would land better with tighter structure and cleaner delivery."
        else:
            opening = "The response currently feels hesitant and under-structured, which makes the main message less persuasive."

        if top_fillers:
            filler_line = (
                f"Filler language such as {', '.join(top_fillers)} weakens confidence and makes key points less crisp."
            )
        else:
            filler_line = "Filler language is well controlled, which helps the answer sound more confident."

        closing = (
            "Aim for a simple flow: situation, action, measurable result, and why it matters. "
            "Shorter sentences and concrete outcomes will make the pitch stronger."
        )

        return " ".join([opening, filler_line, closing])

    def _clean_script_text(self, text: str) -> str:
        cleaned = text

        for filler in sorted(self._filler_patterns, key=len, reverse=True):
            pattern = rf"(?<!\w){re.escape(filler)}(?!\w)"
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = re.sub(r",\s*,", ", ", cleaned)
        cleaned = re.sub(r"\b(and|but|or|so)\s*,", r"\1", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\b(and|but|or|so)\s+,", r"\1", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
        cleaned = re.sub(r"([,.;:!?]){2,}", r"\1", cleaned)
        cleaned = cleaned.strip(" ,.;:-")

        if not cleaned:
            cleaned = text.strip()

        return cleaned

    def _looks_like_bulgarian(self, text: str) -> bool:
        if re.search(r"[А-Яа-яЁёЍѝ]", text):
            return True

        lowered = text.lower()
        transliterated_markers = [
            "zdravei",
            "az",
            "sum",
            "intervyu",
            "poziciya",
            "razrabotchik",
        ]
        return sum(marker in lowered for marker in transliterated_markers) >= 2

    def _extract_candidate_name(self, text: str) -> str | None:
        patterns = [
            r"\bаз съм\s+([A-ZА-Я][A-Za-zА-Яа-я-]+)",
            r"\bаз\s+([A-ZА-Я][A-Za-zА-Яа-я-]+)",
            r"\bя\s+([A-ZА-Я][A-Za-zА-Яа-я-]+)",
            r"\bказвам се\s+([A-ZА-Я][A-Za-zА-Яа-я-]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                return f"{name[:1].upper()}{name[1:]}"

        return None

    def _extract_candidate_role(self, text: str) -> str | None:
        lowered = text.lower()

        if any(token in lowered for token in ["java", "джава", "джаво"]):
            return "Java разработчик"
        if any(token in lowered for token in ["python", "пайтън"]):
            return "Python разработчик"
        if any(token in lowered for token in ["frontend", "front-end", "фронтенд"]):
            return "Frontend разработчик"
        if any(token in lowered for token in ["backend", "back-end", "бекенд"]):
            return "Backend разработчик"
        if any(token in lowered for token in ["fullstack", "full-stack", "фулстак"]):
            return "Full-stack разработчик"
        if any(token in lowered for token in ["developer", "разработчик", "девелопър"]):
            return "разработчик"

        return None

    def _normalize_bulgarian_script(self, text: str) -> str:
        normalized = text
        replacements = [
            (r"\bя\b", "аз"),
            (r"\bйа\b", "аз"),
            (r"\bi\b", "аз"),
            (r"\bмето\b", "моето"),
            (r"\bинтервью\b", "интервю"),
            (r"\bджаво\b", "Java"),
            (r"\bджава\b", "Java"),
            (r"\bjava developer\b", "Java разработчик"),
            (r"\bдевелоп[еъ]р\b", "разработчик"),
        ]

        for pattern, replacement in replacements:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

        normalized = re.sub(r"\s+", " ", normalized)
        normalized = re.sub(r"\s+([,.;:!?])", r"\1", normalized)
        normalized = re.sub(r"([,.;:!?]){2,}", r"\1", normalized)
        normalized = normalized.strip(" ,.;:-")

        if normalized:
            normalized = f"{normalized[:1].upper()}{normalized[1:]}"

        return normalized

    def _build_bulgarian_improved_script(self, text: str) -> str:
        normalized = self._normalize_bulgarian_script(self._clean_script_text(text))
        word_count = len(re.findall(r"\b[\w']+\b", normalized))
        name = self._extract_candidate_name(normalized)
        role = self._extract_candidate_role(normalized)
        has_intro_shape = any(token in normalized.lower() for token in ["здравей", "аз ", "кандидат", "интервю"])

        if word_count <= 45 and (has_intro_shape or name or role):
            intro_lines = []

            if name:
                intro_lines.append(f"Здравейте! Аз съм {name}.")
            else:
                intro_lines.append("Здравейте!")

            if role:
                intro_lines.append(f"Кандидатствам за позиция {role}.")

            intro_lines.append(
                "Ще се радвам накратко да представя своя опит, умения и мотивация."
            )
            return " ".join(intro_lines)

        return normalized

    def _build_improved_script(self, text: str) -> str:
        if self._looks_like_bulgarian(text):
            cleaned = self._build_bulgarian_improved_script(text)
        else:
            cleaned = self._clean_script_text(text)

        if cleaned and cleaned[-1] not in ".!?":
            cleaned += "."

        return cleaned

    def analyze_text(self, text: str) -> InterviewAnalysis:
        if not text or len(text.strip()) == 0:
            raise ValueError("Text for analysis is empty")

        try:
            print("Analyzing interview...")
            filler_counts = self._count_fillers(text)
            filler_words = [word for word, count in filler_counts.most_common() if count > 0]
            word_count = len(re.findall(r"\b[\w']+\b", text))
            sentence_count = max(1, len(re.findall(r"[.!?]+", text)))
            score = self._score_transcript(word_count, sum(filler_counts.values()), sentence_count)

            if self.analyzer is not None:
                print("Using injected analyzer backend...")
                response = self.analyzer(text)
                if isinstance(response, InterviewAnalysis):
                    return response

            return InterviewAnalysis(
                score=score,
                filler_words=filler_words,
                critique=self._build_critique(text, filler_counts, score),
                improved_script=self._build_improved_script(text),
            )
        except Exception as exc:
            print(f"Error during analysis: {exc}")
            raise
