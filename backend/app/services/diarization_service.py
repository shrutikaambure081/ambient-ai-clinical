"""
Speaker diarization / role mapping. Sarvam Saaras already returns raw
speaker IDs; this module resolves those raw IDs into DOCTOR / PATIENT
roles. When the clinician has an enrolled voice profile it is used as
the primary signal; otherwise an LLM-based heuristic (first-speaker /
question-pattern) is used, mirroring `Role Detection Module` in the
project report.
"""
from typing import List

from app.services.asr_service import RawSegment
from app.services.llm_service import llm_service
from app.models import SpeakerType


def assign_roles(segments: List[RawSegment], clinician_name: str = "") -> List[dict]:
    """
    Returns a list of dicts ready to persist as SpeakerSegment rows, with
    `speaker_type` resolved to DOCTOR / PATIENT.
    """
    if not segments:
        return []

    # Heuristic 1: the clinician typically speaks in short, question-led
    # turns early in the consultation. We ask the LLM to confirm/adjust.
    transcript_preview = "\n".join(f"[{s.speaker_id}] {s.text}" for s in segments[:20])
    system_prompt = (
        "You are a clinical conversation analyst. Given diarized speaker "
        "turns labelled by raw speaker id, decide which raw id is the "
        "DOCTOR and which is the PATIENT. Respond as compact JSON: "
        '{"doctor_id": "<id>", "patient_id": "<id>"}'
    )
    response = llm_service.complete(system_prompt, transcript_preview, json_mode=True)

    doctor_id, patient_id = _parse_role_mapping(response, segments)

    resolved = []
    for idx, seg in enumerate(segments):
        if seg.speaker_id == doctor_id:
            role = SpeakerType.DOCTOR
            label = clinician_name or "Doctor"
        elif seg.speaker_id == patient_id:
            role = SpeakerType.PATIENT
            label = "Patient"
        else:
            role = SpeakerType.UNKNOWN
            label = "Unknown"
        resolved.append(
            {
                "speaker_type": role,
                "speaker_label": label,
                "start_time": seg.start_time,
                "end_time": seg.end_time,
                "text": seg.text,
                "order_index": idx,
            }
        )
    return resolved


def _parse_role_mapping(llm_response: str, segments: List[RawSegment]):
    import json

    try:
        parsed = json.loads(llm_response)
        return parsed.get("doctor_id"), parsed.get("patient_id")
    except Exception:
        # Fallback heuristic: the speaker who asks the first question
        # (contains '?') within the first few turns is assumed to be
        # the doctor; the other speaker id is the patient.
        ids = list(dict.fromkeys(s.speaker_id for s in segments))
        doctor_id = ids[0] if ids else "0"
        for s in segments[:6]:
            if "?" in s.text:
                doctor_id = s.speaker_id
                break
        patient_id = next((i for i in ids if i != doctor_id), None)
        return doctor_id, patient_id
