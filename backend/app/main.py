"""
Ambient AI Clinical Documentation System -- FastAPI application entrypoint.

An end-to-end system that converts doctor-patient consultation audio into
structured, privacy-compliant clinical documentation using ASR, speaker
diarization, LLM-based SOAP note generation, and Hybrid RAG-based
continuity summarization.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth_router, patient_router, consultation_router, continuity_router

app = FastAPI(
    title="Ambient AI Clinical Documentation System",
    description=(
        "End-to-end Ambient AI system for clinical documentation using "
        "Automatic Speech Recognition and Large Language Models."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(patient_router.router)
app.include_router(consultation_router.router)
app.include_router(continuity_router.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ambient-ai-clinical-doc-backend"}
