"""
Pydantic request/response schemas.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


# ---------- Auth ----------
class UserSignup(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class OTPVerify(BaseModel):
    email: EmailStr
    otp: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class FluentLanguagesUpdate(BaseModel):
    languages: List[str]


class VoiceEnrollmentResult(BaseModel):
    language: str
    verified: bool


# ---------- Patient ----------
class PatientCreate(BaseModel):
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None


class PatientOut(PatientCreate):
    patient_id: str

    class Config:
        from_attributes = True


# ---------- Consultation / pipeline ----------
class SpeakerSegmentOut(BaseModel):
    speaker_type: str
    speaker_label: str
    start_time: float
    end_time: float
    text: str

    class Config:
        from_attributes = True


class EntityOut(BaseModel):
    entity_text: str
    entity_type: str

    class Config:
        from_attributes = True


class SOAPNoteOut(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan: str

    class Config:
        from_attributes = True


class SOAPNoteUpdate(BaseModel):
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None


class ConsultationResult(BaseModel):
    consultation_id: str
    status: str
    transcript_text: Optional[str] = None
    segments: List[SpeakerSegmentOut] = []
    entities: List[EntityOut] = []
    soap_note: Optional[SOAPNoteOut] = None


class ContinuitySummaryRequest(BaseModel):
    patient_id: str
    focus_text: Optional[str] = None
    top_k: int = 5


class ContinuitySummaryOut(BaseModel):
    patient_id: str
    soap_visits_used: int
    semantic_index_available: bool
    summary_text: str
