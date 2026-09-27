"""
End-to-end consultation processing pipeline (DAG), matching Algorithm 1 /
Algorithm 2 in the project report:

  1. Audio ingestion
  2. ASR transcription
  3. Speaker diarization + role identification
  4. Clinical entity extraction
  5. SOAP note generation
  6. PII redaction
  7. Semantic embedding + storage
  8. (Hybrid RAG continuity retrieval happens on-demand, see routers/continuity_router.py)

Each stage is isolated so failures in one AI service do not corrupt the
whole consultation record; the consultation status is updated at each
step and set to FAILED with a stored error if a stage raises.
"""
from sqlalchemy.orm import Session

from app import models
from app.services.asr_service import asr_service
from app.services.diarization_service import assign_roles
from app.services.entity_extraction import extract_entities
from app.services.soap_generation import generate_soap_note
from app.services.pii_redaction import redact_text
from app.services.hybrid_rag import index_consultation


def run_consultation_pipeline(
    db: Session,
    consultation: models.Consultation,
    audio_bytes: bytes,
    filename: str,
    clinician_name: str = "",
) -> models.Consultation:
    try:
        consultation.status = models.ConsultationStatus.PROCESSING
        db.commit()

        # --- Stage 1: ASR transcription ---
        asr_result = asr_service.transcribe(audio_bytes, filename)
        transcript = models.ASRTranscript(
            consultation_id=consultation.consultation_id,
            full_text=asr_result.full_text,
            language=asr_result.language,
        )
        db.add(transcript)
        db.flush()

        # --- Stage 2: Speaker diarization + role identification ---
        resolved_segments = assign_roles(asr_result.segments, clinician_name)
        for seg in resolved_segments:
            db.add(models.SpeakerSegment(transcript_id=transcript.transcript_id, **seg))
        db.flush()

        # --- Stage 3: Clinical entity extraction ---
        entities = extract_entities(asr_result.full_text)
        for ent in entities:
            db.add(
                models.Entity(
                    consultation_id=consultation.consultation_id,
                    entity_text=ent["text"],
                    entity_type=ent["type"],
                )
            )
        db.flush()

        # --- Stage 4: SOAP note generation ---
        soap_fields = generate_soap_note(asr_result.full_text, entities)

        # --- Stage 5: PII redaction (applied per SOAP field) ---
        redacted_fields = {}
        all_redactions = []
        for field_name, value in soap_fields.items():
            redacted_value, redactions = redact_text(value)
            redacted_fields[field_name] = redacted_value
            for r in redactions:
                all_redactions.append(r)

        soap_note = models.SOAPNote(
            consultation_id=consultation.consultation_id, **redacted_fields
        )
        db.add(soap_note)
        db.flush()

        for r in all_redactions:
            db.add(models.PIIRedaction(soap_id=soap_note.soap_id, **r))

        consultation.status = models.ConsultationStatus.PROCESSED
        db.commit()
        db.refresh(consultation)

        # --- Stage 6: Semantic embedding for Hybrid RAG continuity ---
        index_consultation(db, consultation)

        return consultation

    except Exception:
        consultation.status = models.ConsultationStatus.FAILED
        db.commit()
        raise
