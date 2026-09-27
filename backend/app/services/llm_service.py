"""
Thin wrapper around the two supported LLM backends: Groq (cloud) and
Ollama (local). Every higher-level module (role detection, entity
extraction, SOAP generation, continuity summarization) calls
`llm_service.complete()` so the backend can be swapped centrally.
"""
import json
import httpx

from app.config import settings


class LLMService:
    def __init__(self):
        self.provider = settings.llm_provider

    def complete(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        if self.provider == "groq" and settings.groq_api_key:
            return self._complete_groq(system_prompt, user_prompt, json_mode)
        return self._complete_ollama(system_prompt, user_prompt, json_mode)

    def _complete_groq(self, system_prompt: str, user_prompt: str, json_mode: bool) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {settings.groq_api_key}"}
        body = {
            "model": settings.groq_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        try:
            resp = httpx.post(url, headers=headers, json=body, timeout=60)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as exc:  # network / API unavailable -> graceful fallback
            return self._fallback(user_prompt, json_mode, error=str(exc))

    def _complete_ollama(self, system_prompt: str, user_prompt: str, json_mode: bool) -> str:
        url = f"{settings.ollama_base_url}/api/chat"
        body = {
            "model": settings.ollama_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }
        if json_mode:
            body["format"] = "json"
        try:
            resp = httpx.post(url, json=body, timeout=120)
            resp.raise_for_status()
            return resp.json()["message"]["content"]
        except Exception as exc:  # Ollama not running locally -> graceful fallback
            return self._fallback(user_prompt, json_mode, error=str(exc))

    @staticmethod
    def _fallback(user_prompt: str, json_mode: bool, error: str) -> str:
        """
        Deterministic offline fallback so the pipeline keeps working (and is
        demoable) even when no LLM backend is reachable.
        """
        if json_mode:
            return json.dumps({"warning": f"LLM unavailable ({error})", "entities": []})
        return f"[LLM unavailable: {error}] Unable to generate content for: {user_prompt[:120]}"


llm_service = LLMService()
