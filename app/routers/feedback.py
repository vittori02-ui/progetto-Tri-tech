# feedback.py = VALUTAZIONI POST-SESSIONE
# Dopo che una sessione e' completata, i partecipanti possono
# lasciare un voto (1-5) e un commento.
# Endpoint: /feedback/

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from sqlalchemy import func  # Per funzioni SQL come AVG (media)

from app.database import get_db
from app.db_models import Feedback, SessionRequest, User
from app.models import FeedbackCreate, FeedbackResponse
from app.routers.auth import _get_user_id

router = APIRouter(prefix="/feedback", tags=["feedback"])


# ============================================================
# POST /feedback  - LASCIARE UN FEEDBACK
# ============================================================
@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(fb_data: FeedbackCreate, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Lascia un voto (1-5) e un commento per una sessione completata."""
    reviewer_id = _get_user_id(authorization)

    # La sessione esiste ed e' completata?
    session_req = db.query(SessionRequest).filter(SessionRequest.id == fb_data.session_request_id).first()
    if not session_req:
        raise HTTPException(status_code=404, detail="Richiesta di sessione non trovata.")
    if session_req.status != "completed":
        raise HTTPException(status_code=400, detail="Puoi lasciare un feedback solo per sessioni completate.")

    # Solo chi ha partecipato puo' lasciare feedback
    if reviewer_id != session_req.sender_id and reviewer_id != session_req.receiver_id:
        raise HTTPException(status_code=403, detail="Non hai partecipato a questa sessione.")

    # Gia' lasciato un feedback per questa sessione? (si puo' solo una volta)
    existing = db.query(Feedback).filter(Feedback.session_request_id == fb_data.session_request_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Hai gia' lasciato un feedback per questa sessione.")

    new_fb = Feedback(
        session_request_id=fb_data.session_request_id,
        reviewer_id=reviewer_id,
        rating=fb_data.rating,
        comment=fb_data.comment or "",
    )
    db.add(new_fb); db.commit(); db.refresh(new_fb)

    # Ricarica per avere il nome del recensore
    fb = db.query(Feedback).filter(Feedback.id == new_fb.id).first()
    reviewer_name = fb.reviewer.name if fb.reviewer else ""

    return FeedbackResponse(
        id=fb.id,
        session_request_id=fb.session_request_id,
        reviewer_id=fb.reviewer_id,
        reviewer_name=reviewer_name,
        rating=fb.rating,
        comment=fb.comment or "",
        created_at=fb.created_at,
    )


# ============================================================
# GET /feedback/user/{id}  - FEEDBACK RICEVUTI DA UN UTENTE
# ============================================================
@router.get("/user/{user_id}", response_model=dict)
def get_user_feedback(user_id: int, db: Session = Depends(get_db)):
    """Mostra tutti i feedback ricevuti da un utente e la media dei voti."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato.")

    # Cerca tutti i feedback delle sessioni a cui l'utente ha partecipato
    feedbacks = (
        db.query(Feedback)
        .join(SessionRequest, Feedback.session_request_id == SessionRequest.id)
        .filter((SessionRequest.sender_id == user_id) | (SessionRequest.receiver_id == user_id))
        .order_by(Feedback.created_at.desc())
        .all()
    )

    # Calcola la media dei voti
    avg_rating = (
        db.query(func.avg(Feedback.rating))
        .join(SessionRequest, Feedback.session_request_id == SessionRequest.id)
        .filter((SessionRequest.sender_id == user_id) | (SessionRequest.receiver_id == user_id))
        .scalar()
    )

    result = []
    for fb in feedbacks:
        reviewer_name = fb.reviewer.name if fb.reviewer else ""
        result.append(FeedbackResponse(
            id=fb.id,
            session_request_id=fb.session_request_id,
            reviewer_id=fb.reviewer_id,
            reviewer_name=reviewer_name,
            rating=fb.rating,
            comment=fb.comment or "",
            created_at=fb.created_at,
        ))

    return {
        "feedback": result,
        "average_rating": round(float(avg_rating), 2) if avg_rating else None,
        "total_feedback": len(result),
    }
