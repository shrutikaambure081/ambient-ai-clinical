"""
Consultation upload/processing and SOAP note review endpoints.
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, security
from app.database import get_db
from app.pipeline.orchestrator import run_consultation_pipeline

router = APIRouter(prefix="/consultations", tags=["consultations"])


@router.post("/{patient_id}/process", response_model=schemas.ConsultationResult)
def process_consultation(
    patient_id: str,
    visit_type: str = Form("NEW"),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    patient = db.query(models.Patient).filter(models.Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(404, "Patient not found")

    consultation = models.Consultation(
        patient_id=patient_id,
        clinician_id=current_user.user_id,
        visit_type=visit_type,
        status=models.ConsultationStatus.UPLOADED,
    )
    db.add(consultation)
    db.flush()

    audio_bytes = audio.file.read()
    db.add(
        models.AudioFile(
            consultation_id=consultation.consultation_id,
            file_name=audio.filename,
            file_type=audio.content_type,
            file_size=len(audio_bytes),
        )
    )
    db.commit()

    run_consultation_pipeline(
        db, consultation, audio_bytes, audio.filename, clinician_name=current_user.name
    )

    db.refresh(consultation)
    return _build_result(consultation)


@router.get("/{consultation_id}", response_model=schemas.ConsultationResult)
def get_consultation(
    consultation_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    consultation = (
        db.query(models.Consultation)
        .filter(models.Consultation.consultation_id == consultation_id)
        .first()
    )
    if not consultation:
        raise HTTPException(404, "Consultation not found")
    return _build_result(consultation)


@router.put("/{consultation_id}/soap", response_model=schemas.SOAPNoteOut)
def update_soap_note(
    consultation_id: str,
    payload: schemas.SOAPNoteUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    soap = (
        db.query(models.SOAPNote)
        .filter(models.SOAPNote.consultation_id == consultation_id)
        .first()
    )
    if not soap:
        raise HTTPException(404, "SOAP note not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(soap, field, value)
    db.commit()
    db.refresh(soap)
    return soap


def _build_result(consultation: models.Consultation) -> schemas.ConsultationResult:
    transcript_text = consultation.transcript.full_text if consultation.transcript else None
    segments = consultation.transcript.segments if consultation.transcript else []
    return schemas.ConsultationResult(
        consultation_id=consultation.consultation_id,
        status=consultation.status.value if hasattr(consultation.status, "value") else str(consultation.status),
        transcript_text=transcript_text,
        segments=[
            schemas.SpeakerSegmentOut(
                speaker_type=s.speaker_type.value if hasattr(s.speaker_type, "value") else str(s.speaker_type),
                speaker_label=s.speaker_label,
                start_time=s.start_time,
                end_time=s.end_time,
                text=s.text,
            )
            for s in segments
        ],
        entities=[
            schemas.EntityOut(
                entity_text=e.entity_text,
                entity_type=e.entity_type.value if hasattr(e.entity_type, "value") else str(e.entity_type),
            )
            for e in consultation.entities
        ],
        soap_note=schemas.SOAPNoteOut.model_validate(consultation.soap_note) if consultation.soap_note else None,
    )
