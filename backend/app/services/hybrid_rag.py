"""
Hybrid Retrieval-Augmented Generation for consultation continuity.

Combines:
  (a) SQL-based recency retrieval -- the last N SOAP notes for the patient.
  (b) Vector-based semantic retrieval -- cosine similarity search over
      stored consultation embeddings, optionally sharpened by a
      clinician-supplied focus phrase.

The merged, de-duplicated context is then summarized by the LLM into a
concise, continuity-aware patient summary.
"""
from typing import List

from sqlalchemy.orm import Session

from app import models
from app.services.embedding_service import embed_text, cosine_similarity
from app.services.llm_service import llm_service

RECENCY_LIMIT = 5

SYSTEM_PROMPT = """You are a clinical continuity assistant. Given a set of
past SOAP note summaries for a patient (most recent first, labelled C1, C2,
...), write a short continuity-aware summary that a clinician can scan
before a follow-up visit. Highlight changes, progress, and recommended
follow-ups. Use "* " bullet points grouped under each consultation label."""


def sql_recency_retrieval(db: Session, patient_id: str, limit: int = RECENCY_LIMIT) -> List[models.Consultation]:
    return (
        db.query(models.Consultation)
        .filter(models.Consultation.patient_id == patient_id)
        .filter(models.Consultation.status == models.ConsultationStatus.PROCESSED)
        .order_by(models.Consultation.consultation_date.desc())
        .limit(limit)
        .all()
    )


def vector_semantic_retrieval(
    db: Session, patient_id: str, focus_text: str, top_k: int = 5
) -> List[dict]:
    embeddings = (
        db.query(models.Embedding)
        .join(models.Consultation, models.Embedding.consultation_id == models.Consultation.consultation_id)
        .filter(models.Consultation.patient_id == patient_id)
        .all()
    )
    if not embeddings:
        return []

    query_vector = embed_text(focus_text or "recent consultation summary")
    scored = []
    for emb in embeddings:
        try:
            stored_vector = emb.embedding_vector if isinstance(emb.embedding_vector, list) else list(emb.embedding_vector)
            score = cosine_similarity(query_vector, stored_vector)
            scored.append((score, emb))
        except Exception:
            continue

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {"consultation_id": emb.consultation_id, "score": score, "text": emb.source_text}
        for score, emb in scored[:top_k]
    ]


def _soap_to_text(soap: models.SOAPNote) -> str:
    return (
        f"SUBJECTIVE:\n{soap.subjective}\n"
        f"OBJECTIVE:\n{soap.objective}\n"
        f"ASSESSMENT:\n{soap.assessment}\n"
        f"PLAN:\n{soap.plan}"
    )


def generate_continuity_summary(
    db: Session, patient_id: str, focus_text: str = "", top_k: int = 5
) -> dict:
    recent_consultations = sql_recency_retrieval(db, patient_id)
    semantic_hits = vector_semantic_retrieval(db, patient_id, focus_text, top_k)

    # C. Context merging: combine recency + semantic results, de-duplicated
    # by consultation id, most relevant / most recent first.
    merged: dict[str, str] = {}
    for c in recent_consultations:
        if c.soap_note:
            merged[c.consultation_id] = _soap_to_text(c.soap_note)
    for hit in semantic_hits:
        cid = hit["consultation_id"]
        if cid not in merged and hit["text"]:
            merged[cid] = hit["text"]

    if not merged:
        return {
            "soap_visits_used": 0,
            "semantic_index_available": bool(semantic_hits),
            "summary_text": "No prior consultations available for this patient yet.",
        }

    context_blocks = "\n\n".join(
        f"C{i+1}:\n{text}" for i, text in enumerate(merged.values())
    )
    summary = llm_service.complete(SYSTEM_PROMPT, context_blocks)

    return {
        "soap_visits_used": len(merged),
        "semantic_index_available": bool(semantic_hits),
        "summary_text": summary,
    }


def index_consultation(db: Session, consultation: models.Consultation) -> None:
    """
    Called after a consultation is processed: generates and stores the
    semantic embedding used for future Hybrid RAG retrieval.
    """
    if not consultation.soap_note:
        return
    source_text = _soap_to_text(consultation.soap_note)
    vector = embed_text(source_text)

    embedding = models.Embedding(
        consultation_id=consultation.consultation_id,
        embedding_vector=vector,
        model_name="all-MiniLM-L6-v2",
        source_text=source_text,
    )
    db.add(embedding)
    db.commit()
