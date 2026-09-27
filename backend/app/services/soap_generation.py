"""
SOAP note generation from a consultation transcript + extracted
clinical entities, using the LLM. Produces the four standard sections:
Subjective, Objective, Assessment, Plan.
"""
import json
from typing import Dict, List

from app.services.llm_service import llm_service

SYSTEM_PROMPT = """You are a clinical scribe assistant. Given a doctor-patient
consultation transcript and a list of extracted clinical entities, write a
structured SOAP note. Be concise, use short bullet phrases (not full
paragraphs), and never fabricate findings that are not supported by the
transcript. Respond ONLY as compact JSON:
{"subjective": "...", "objective": "...", "assessment": "...", "plan": "..."}
Use "* " bullet prefixes within each field, separated by newlines."""


def generate_soap_note(transcript_text: str, entities: List[Dict[str, str]]) -> Dict[str, str]:
    user_prompt = (
        f"TRANSCRIPT:\n{transcript_text}\n\n"
        f"EXTRACTED ENTITIES:\n{json.dumps(entities)}"
    )
    response = llm_service.complete(SYSTEM_PROMPT, user_prompt, json_mode=True)
    try:
        parsed = json.loads(response)
        return {
            "subjective": parsed.get("subjective", ""),
            "objective": parsed.get("objective", "* No objective findings discussed during consultation."),
            "assessment": parsed.get("assessment", ""),
            "plan": parsed.get("plan", ""),
        }
    except Exception:
        return {
            "subjective": "* Unable to generate note automatically. Please edit manually.",
            "objective": "",
            "assessment": "",
            "plan": "",
        }
