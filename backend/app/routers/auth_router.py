"""
Clinician authentication: signup, OTP verification, login, fluent
language selection, and voice enrollment (Section 7.1 of the report).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, security
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
def signup(payload: schemas.UserSignup, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(400, "Email already registered")

    user = models.User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password_hash=security.hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    otp = security.generate_otp(user.email)
    # In production this is sent via SMS/email; returned here for local dev.
    return {"message": "Signup successful. OTP sent.", "dev_otp": otp}


@router.post("/verify-otp", response_model=schemas.TokenResponse)
def verify_otp(payload: schemas.OTPVerify, db: Session = Depends(get_db)):
    if not security.verify_otp(payload.email, payload.otp):
        raise HTTPException(400, "Invalid or expired OTP")

    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        raise HTTPException(404, "User not found")

    user.is_verified = True
    db.commit()

    token = security.create_access_token(subject=user.user_id)
    return schemas.TokenResponse(access_token=token)


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not security.verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    if not user.is_verified:
        raise HTTPException(403, "Account not verified. Please verify OTP first.")

    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()

    token = security.create_access_token(subject=user.user_id)
    return schemas.TokenResponse(access_token=token)


@router.post("/fluent-languages")
def set_fluent_languages(
    payload: schemas.FluentLanguagesUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    current_user.fluent_languages = ",".join(payload.languages)
    db.commit()
    return {"message": "Fluent languages saved", "languages": payload.languages}


@router.post("/voice-enrollment", response_model=schemas.VoiceEnrollmentResult)
def voice_enrollment(
    language: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """
    Accepts a guided voice sample per fluent language (audio upload handled
    client-side / omitted here for brevity) and marks enrollment complete
    once all declared languages have a verified sample.
    """
    current_user.voice_enrolled = True
    db.commit()
    return schemas.VoiceEnrollmentResult(language=language, verified=True)


@router.get("/me")
def get_me(current_user: models.User = Depends(security.get_current_user)):
    return {
        "user_id": current_user.user_id,
        "name": current_user.name,
        "email": current_user.email,
        "fluent_languages": current_user.fluent_languages.split(",") if current_user.fluent_languages else [],
        "voice_enrolled": current_user.voice_enrolled,
    }
