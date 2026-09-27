"""
Hybrid RAG continuity summary endpoint (Section 7.5 of the report).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas, security
from app.database import get_db
from app.services.hybrid_rag import generate_continuity_summary

router = APIRouter(prefix="/continuity", tags=["continuity"])


@router.post("/summary", response_model=schemas.ContinuitySummaryOut)
def continuity_summary(
    payload: schemas.ContinuitySummaryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    result = generate_continuity_summary(
        db, payload.patient_id, payload.focus_text or "", payload.top_k
    )

    db.add(
        models.ContinuitySummary(
            patient_id=payload.patient_id,
            summary_text=result["summary_text"],
            model_used="hybrid-rag",
        )
    )
    db.commit()

    return schemas.ContinuitySummaryOut(
        patient_id=payload.patient_id,
        soap_visits_used=result["soap_visits_used"],
        semantic_index_available=result["semantic_index_available"],
        summary_text=result["summary_text"],
    )
