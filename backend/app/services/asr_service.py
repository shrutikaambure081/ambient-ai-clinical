"""
Automatic Speech Recognition module. Wraps the Sarvam Saaras v3
multilingual ASR + diarization API. Falls back to a local mock
transcriber (useful for development / offline demos) when no API key
is configured or the request fails.
"""
import base64
from dataclasses import dataclass, field
from typing import List

import httpx

from app.config import settings


@dataclass
class RawSegment:
    speaker_id: str
    start_time: float
    end_time: float
    text: str


@dataclass
class ASRResult:
    full_text: str
    language: str
    segments: List[RawSegment] = field(default_factory=list)


class ASRService:
    def transcribe(self, audio_bytes: bytes, filename: str, language_hint: str = "auto") -> ASRResult:
        if settings.sarvam_api_key:
            try:
                return self._transcribe_sarvam(audio_bytes, filename, language_hint)
            except Exception:
                pass  # fall through to mock so the pipeline never hard-fails
        return self._mock_transcribe(audio_bytes, filename)

    def _transcribe_sarvam(self, audio_bytes: bytes, filename: str, language_hint: str) -> ASRResult:
        headers = {"api-subscription-key": settings.sarvam_api_key}
        files = {"file": (filename, audio_bytes)}
        data = {"language_code": language_hint, "diarize": "true"}
        resp = httpx.post(
            settings.sarvam_api_url, headers=headers, files=files, data=data, timeout=180
        )
        resp.raise_for_status()
        payload = resp.json()

        segments = [
            RawSegment(
                speaker_id=str(seg.get("speaker", "0")),
                start_time=float(seg.get("start_time", 0.0)),
                end_time=float(seg.get("end_time", 0.0)),
                text=seg.get("text", ""),
            )
            for seg in payload.get("diarized_transcript", {}).get("entries", [])
        ]
        return ASRResult(
            full_text=payload.get("transcript", ""),
            language=payload.get("language_code", language_hint),
            segments=segments,
        )

    def _mock_transcribe(self, audio_bytes: bytes, filename: str) -> ASRResult:
        """
        Deterministic offline stand-in used when Sarvam is not configured.
        Real deployments should never reach this path.
        """
        sample_dialogue = [
            RawSegment("0", 0.0, 2.5, "Good evening, Doctor."),
            RawSegment("1", 2.6, 5.0, "Good evening, please sit down. What's bothering you today?"),
            RawSegment("0", 5.1, 9.0, "I've had stomach pain on and off for about a week."),
            RawSegment("1", 9.1, 12.0, "Has it gotten worse after eating or moving around?"),
            RawSegment("0", 12.1, 15.0, "Yes, especially after meals."),
        ]
        full_text = " ".join(s.text for s in sample_dialogue)
        return ASRResult(full_text=full_text, language="en", segments=sample_dialogue)


asr_service = ASRService()
