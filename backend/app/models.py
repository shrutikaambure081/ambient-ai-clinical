"""
SQLAlchemy ORM models mirroring the ER diagram:
Users, Clinician_Profile, Patients, Consultations, Audio_Files,
ASR_Transcripts, Speaker_Segments, Entities, SOAP_Notes, PII_Redactions,
Embeddings, Retrieval_Queries, Retrieved_Results, Patient_Records,
Continuity_Summaries.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Text, Integer,
    Float, Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

try:
    from pgvector.sqlalchemy import Vector
    EMBEDDING_DIM = 384  # all-MiniLM-L6-v2
    VECTOR_TYPE = Vector(EMBEDDING_DIM)
except Exception:  # pgvector not installed -> fall back to Text (JSON-encoded)
    VECTOR_TYPE = Text

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Role(str, enum.Enum):
    CLINICIAN = "CLINICIAN"
    ADMIN = "ADMIN"


class ConsultationStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class SpeakerType(str, enum.Enum):
    DOCTOR = "DOCTOR"
    PATIENT = "PATIENT"
    UNKNOWN = "UNKNOWN"


class EntityType(str, enum.Enum):
    SYMPTOM = "SYMPTOM"
    MEDICATION = "MEDICATION"
    CONDITION = "CONDITION"
    TEST = "TEST"
    VITAL = "VITAL"
    OTHER = "OTHER"


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String)
    password_hash = Column(String, nullable=False)
    role = Column(SAEnum(Role), default=Role.CLINICIAN, nullable=False)
    is_verified = Column(Boolean, default=False)
    fluent_languages = Column(Text, default="")  # comma-separated
    voice_enrolled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    patients = relationship("Patient", back_populates="clinician")
    consultations = relationship("Consultation", back_populates="clinician")


class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.user_id"), nullable=True)
    name = Column(String, nullable=False)
    dob = Column(DateTime, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String)
    phone = Column(String)
    email = Column(String)
    address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    clinician = relationship("User", back_populates="patients")
    consultations = relationship("Consultation", back_populates="patient")
    patient_record = relationship("PatientRecord", back_populates="patient", uselist=False)


class Consultation(Base):
    __tablename__ = "consultations"

    consultation_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    patient_id = Column(UUID(as_uuid=False), ForeignKey("patients.patient_id"), nullable=False)
    clinician_id = Column(UUID(as_uuid=False), ForeignKey("users.user_id"), nullable=False)
    consultation_date = Column(DateTime, default=datetime.utcnow)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration_sec = Column(Integer, default=0)
    visit_type = Column(String, default="NEW")  # NEW | FOLLOW_UP
    status = Column(SAEnum(ConsultationStatus), default=ConsultationStatus.UPLOADED)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("Patient", back_populates="consultations")
    clinician = relationship("User", back_populates="consultations")
    audio_file = relationship("AudioFile", back_populates="consultation", uselist=False)
    transcript = relationship("ASRTranscript", back_populates="consultation", uselist=False)
    entities = relationship("Entity", back_populates="consultation")
    soap_note = relationship("SOAPNote", back_populates="consultation", uselist=False)
    embeddings = relationship("Embedding", back_populates="consultation")


class AudioFile(Base):
    __tablename__ = "audio_files"

    audio_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    consultation_id = Column(UUID(as_uuid=False), ForeignKey("consultations.consultation_id"))
    file_name = Column(String)
    file_path = Column(String)
    file_type = Column(String)
    file_size = Column(Integer)
    duration_sec = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    consultation = relationship("Consultation", back_populates="audio_file")


class ASRTranscript(Base):
    __tablename__ = "asr_transcripts"

    transcript_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    consultation_id = Column(UUID(as_uuid=False), ForeignKey("consultations.consultation_id"))
    full_text = Column(Text)
    language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow)

    consultation = relationship("Consultation", back_populates="transcript")
    segments = relationship("SpeakerSegment", back_populates="transcript")


class SpeakerSegment(Base):
    __tablename__ = "speaker_segments"

    segment_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    transcript_id = Column(UUID(as_uuid=False), ForeignKey("asr_transcripts.transcript_id"))
    speaker_type = Column(SAEnum(SpeakerType), default=SpeakerType.UNKNOWN)
    speaker_label = Column(String, default="")  # e.g. clinician name once identified
    start_time = Column(Float, default=0.0)
    end_time = Column(Float, default=0.0)
    text = Column(Text)
    order_index = Column(Integer, default=0)

    transcript = relationship("ASRTranscript", back_populates="segments")


class Entity(Base):
    __tablename__ = "entities"

    entity_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    consultation_id = Column(UUID(as_uuid=False), ForeignKey("consultations.consultation_id"))
    entity_text = Column(String)
    entity_type = Column(SAEnum(EntityType), default=EntityType.OTHER)
    start_index = Column(Integer, default=0)
    end_index = Column(Integer, default=0)

    consultation = relationship("Consultation", back_populates="entities")


class SOAPNote(Base):
    __tablename__ = "soap_notes"

    soap_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    consultation_id = Column(UUID(as_uuid=False), ForeignKey("consultations.consultation_id"))
    subjective = Column(Text)
    objective = Column(Text)
    assessment = Column(Text)
    plan = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    consultation = relationship("Consultation", back_populates="soap_note")
    redactions = relationship("PIIRedaction", back_populates="soap_note")


class PIIRedaction(Base):
    __tablename__ = "pii_redactions"

    redaction_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    soap_id = Column(UUID(as_uuid=False), ForeignKey("soap_notes.soap_id"))
    entity_type = Column(String)  # NAME, PHONE, EMAIL, ADDRESS, ID_NUMBER ...
    original_text = Column(Text)
    redacted_text = Column(Text)
    redacted_at = Column(DateTime, default=datetime.utcnow)

    soap_note = relationship("SOAPNote", back_populates="redactions")


class Embedding(Base):
    __tablename__ = "embeddings"

    embedding_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    consultation_id = Column(UUID(as_uuid=False), ForeignKey("consultations.consultation_id"), nullable=True)
    record_id = Column(UUID(as_uuid=False), nullable=True)
    embedding_vector = Column(VECTOR_TYPE)
    model_name = Column(String)
    source_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    consultation = relationship("Consultation", back_populates="embeddings")


class RetrievalQuery(Base):
    __tablename__ = "retrieval_queries"

    query_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.user_id"))
    patient_id = Column(UUID(as_uuid=False), ForeignKey("patients.patient_id"))
    query_text = Column(Text)
    top_k = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)


class RetrievedResult(Base):
    __tablename__ = "retrieved_results"

    result_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    query_id = Column(UUID(as_uuid=False), ForeignKey("retrieval_queries.query_id"))
    consultation_id = Column(UUID(as_uuid=False), ForeignKey("consultations.consultation_id"))
    similarity_score = Column(Float, default=0.0)
    retrieved_text = Column(Text)
    retrieved_at = Column(DateTime, default=datetime.utcnow)


class PatientRecord(Base):
    __tablename__ = "patient_records"

    record_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    patient_id = Column(UUID(as_uuid=False), ForeignKey("patients.patient_id"), unique=True)
    summary_text = Column(Text)
    last_consultation_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("Patient", back_populates="patient_record")


class ContinuitySummary(Base):
    __tablename__ = "continuity_summaries"

    summary_id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    consultation_id = Column(UUID(as_uuid=False), ForeignKey("consultations.consultation_id"), nullable=True)
    patient_id = Column(UUID(as_uuid=False), ForeignKey("patients.patient_id"))
    summary_text = Column(Text)
    model_used = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
