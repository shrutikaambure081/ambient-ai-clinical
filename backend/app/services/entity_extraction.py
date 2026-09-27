"""
Clinical entity extraction: pulls symptoms, medications, conditions,
tests, and vitals out of a consultation transcript using the LLM.
"""
import json
from typing import List, Dict

from app.services.llm_service import llm_service

SYSTEM_PROMPT = """You are a clinical NLP system. Extract structured clinical
entities from a doctor-patient consultation transcript. Return ONLY compact
JSON of the form:
{"entities": [{"text": "<entity text>", "type": "SYMPTOM|MEDICATION|CONDITION|TEST|VITAL|OTHER"}]}
Do not invent information that is not present in the transcript."""


def extract_entities(transcript_text: str) -> List[Dict[str, str]]:
    response = llm_service.complete(SYSTEM_PROMPT, transcript_text, json_mode=True)
    try:
        parsed = json.loads(response)
        entities = parsed.get("entities", [])
        cleaned = []
        for e in entities:
            text = str(e.get("text", "")).strip()
            etype = str(e.get("type", "OTHER")).upper()
            if text:
                cleaned.append({"text": text, "type": etype if etype in
                                 {"SYMPTOM", "MEDICATION", "CONDITION", "TEST", "VITAL", "OTHER"}
                                 else "OTHER"})
        return cleaned
    except Exception:
        return []
