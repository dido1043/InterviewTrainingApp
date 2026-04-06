import openai
import os
from transformers import pipeline
from models.InterviewAnalysis import InterviewAnalysis

class AIService:
    def __init__(self, api_key: str = None):
        print("Loading Hugging Face models...")
        
        self.transcriber = pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-small"
        )
        
        self.analyzer = pipeline(
            "text-generation",
            model="mistralai/Mistral-7B-Instruct-v0.1"
        )
        
    def transcribe_audio(self, audio_path: str) -> str:
        try:
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            print(f"Transcribing audio: {audio_path}")
            result = self.transcriber(audio_path)
            transcript = result.get("text", "")
            if not transcript:
                raise ValueError("Transcription returned empty result")
            print(f"✓ Transcription successful: {len(transcript)} characters")
            return transcript
        except Exception as e:
            print(f"Error during transcription: {e}")
            raise Exception(f"Transcription failed: {str(e)}")
    def analyze_text(self, text: str) -> InterviewAnalysis:
        """Analyze interview using free Mistral model"""
        if not text or len(text.strip()) == 0:
            raise ValueError("Text for analysis is empty")
        try:
            print("Analyzing interview...")
            prompt = f"""You are a sales coach. Analyze this interview and return ONLY valid JSON with these fields:
- strengths: list of 3-5 key strengths
- weaknesses: list of 3-5 areas to improve
- overall_score: integer from 0-100
- recommendations: list of 3-5 actionable recommendations

Interview: {text}

Return ONLY JSON, no other text:"""
            
            response = self.analyzer(
                prompt,
                max_length=800,
                temperature=0.7,
                do_sample=True
            )
            
            # Extract JSON from response
            generated_text = response[0]["generated_text"]
            # Find JSON in the response
            json_start = generated_text.find('{')
            json_end = generated_text.rfind('}') + 1
            
            if json_start == -1 or json_end <= json_start:
                raise ValueError("No valid JSON found in response")
            
            json_text = generated_text[json_start:json_end]
            return InterviewAnalysis.model_validate_json(json_text)
        except Exception as e:
            print(f"Error during analysis: {e}")
            raise
    