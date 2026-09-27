# Ambient AI — End-to-End Clinical Documentation System

An end-to-end Ambient AI system that converts doctor–patient consultation
audio into structured, privacy-compliant clinical documentation, using
Automatic Speech Recognition (ASR), speaker diarization, Large Language
Models (LLMs), and Hybrid Retrieval-Augmented Generation (RAG) for
consultation continuity.

This repository implements the system described in the accompanying minor
project report: *"An End-to-End Ambient AI System for Clinical
Documentation using Automatic Speech Recognition and Large Language
Models"* (KLE Technological University, Dept. of CSE, 2025–2026).

## Features

- **Clinician authentication** — signup, OTP verification, JWT login,
  fluent-language selection, and guided voice enrollment.
- **Audio ingestion** — live microphone recording or file upload
  (`.wav`, `.mp3`, `.webm`).
- **ASR + speaker diarization** — pluggable Sarvam Saaras v3 integration
  with an offline mock fallback for local development.
- **Doctor/patient role identification** — LLM-assisted mapping of raw
  diarized speaker IDs to clinical roles.
- **Clinical entity extraction** — symptoms, medications, conditions,
  tests, and vitals pulled from the transcript.
- **SOAP note generation** — structured Subjective / Objective /
  Assessment / Plan notes, editable by the clinician before saving.
- **Automated PII redaction** — regex + LLM-assisted masking of names,
  phone numbers, emails, and ID numbers before persistence.
- **Hybrid RAG continuity** — combines SQL-based recency retrieval with
  pgvector semantic similarity search to summarize a patient's history
  for follow-up visits.
- **React + TypeScript dashboard** — consultation recording, transcript
  review, SOAP editing, and patient continuity panel.

## Architecture

```
frontend/  React + TypeScript + Tailwind CSS dashboard
backend/   FastAPI + SQLAlchemy + PostgreSQL (pgvector) API and AI pipeline
```

Pipeline stages (`backend/app/pipeline/orchestrator.py`):

1. Audio ingestion → 2. ASR transcription → 3. Speaker diarization & role
   identification → 4. Clinical entity extraction → 5. SOAP note
   generation → 6. PII redaction → 7. Embedding generation & storage.

Hybrid RAG continuity (`backend/app/services/hybrid_rag.py`) runs
on-demand: SQL recency retrieval + vector similarity search → context
merge → LLM summarization.

## Getting started

### 1. Database

```bash
docker compose up -d db
```

This starts a Postgres instance with the `pgvector` extension enabled.

### 2. Backend

```bash
cd backend
cp .env.example .env        # fill in ASR / LLM keys as needed
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python init_db.py           # creates tables
uvicorn app.main:app --reload
```

The API is served at `http://localhost:8000` (docs at `/docs`).

By default `LLM_PROVIDER=ollama` — run `ollama serve` locally (or
`docker compose up -d ollama`) and `ollama pull llama3.1`. To use Groq
instead, set `LLM_PROVIDER=groq` and `GROQ_API_KEY` in `.env`.

Without a Sarvam API key, ASR falls back to a deterministic offline mock
transcript so the pipeline remains runnable end-to-end during development.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

The dashboard is served at `http://localhost:5173`.

## Project structure

```
backend/
  app/
    main.py                 FastAPI app entrypoint
    config.py                Settings (env-driven)
    database.py               SQLAlchemy engine/session
    models.py                  ORM models (ER diagram entities)
    schemas.py                  Pydantic request/response schemas
    security.py                  JWT / bcrypt / OTP auth
    pipeline/orchestrator.py       Consultation processing DAG
    services/
      asr_service.py                Sarvam ASR + diarization client
      diarization_service.py         Doctor/patient role mapping
      entity_extraction.py            Clinical entity extraction
      soap_generation.py               SOAP note generation
      pii_redaction.py                  PII detection & redaction
      embedding_service.py               Sentence-transformer embeddings
      hybrid_rag.py                       Hybrid RAG continuity retrieval
      llm_service.py                       Groq / Ollama LLM wrapper
    routers/
      auth_router.py, patient_router.py, consultation_router.py,
      continuity_router.py
  init_db.py, requirements.txt, Dockerfile, .env.example

frontend/
  src/
    pages/     Login, VoiceEnrollment, Dashboard
    components/ Navbar, SpeakerTranscript, SOAPNotes, PatientContinuity
    api/client.ts
    types.ts
  package.json, tailwind.config.js, vite.config.ts

docker-compose.yml
```

## Notes

- All AI service integrations (ASR, LLM) are behind thin interfaces so
  providers can be swapped without touching the pipeline or routers.
- Every AI service call has an offline/graceful fallback so the system
  remains demoable without live API keys.
- PII redaction runs on every SOAP note field before it is written to
  the database, per the report's privacy-preservation requirement.
