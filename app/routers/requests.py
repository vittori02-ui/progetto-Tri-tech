# requests.py = RICHIESTE DI SESSIONE TRA UTENTI
# Endpoint: /requests/
# Cosa si puo' fare:
#   POST /requests/         = inviare una richiesta
#   GET  /requests/         = vedere le proprie richieste
#   PATCH /requests/{id}    = accettare, rifiutare, cancellare, confermare completamento

from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models import SessionRequest, User, Skill
from app.models import SessionRequestCreate, SessionRequestResponse, SessionRequestAction
from app.routers.auth import _get_user_id

router = APIRouter(prefix="/requests", tags=["requests"])


# ============================================================
# FUNZIONE DI SUPPORTO: prepara la risposta di una richiesta
# ============================================================
# Prende un oggetto SessionRequest e lo trasforma in un dizionario
# con tutti i campi pronti per essere mandati al frontend.
def _build_request_response(req: SessionRequest) -> SessionRequestResponse:
    return SessionRequestResponse(
        id=req.id,
        sender_id=req.sender_id,
        sender_name=req.sender.name if req.sender else "",       # Nome del mittente
        receiver_id=req.receiver_id,
        receiver_name=req.receiver.name if req.receiver else "", # Nome del destinatario
        skill_id=req.skill_id,
        skill_name=req.skill.name if req.skill else "",          # Nome della skill
        status=req.status,
        message=req.message or "",
        proposed_date=req.proposed_date,
        mode=req.mode or "remoto",
        sender_confirmed=req.sender_confirmed,
        receiver_confirmed=req.receiver_confirmed,
        created_at=req.created_at,
        updated_at=req.updated_at,
    )


# ============================================================
# REGOLE: quando si puo' fare cosa
# ============================================================
# pending  -> accept  (solo il destinatario)  -> accepted
# pending  -> reject  (solo il destinatario)  -> rejected
# pending  -> cancel  (solo il mittente)      -> cancelled
# accepted -> cancel  (solo il mittente)      -> cancelled
# accepted -> confirm_completion (entrambi)   -> completed (quando entrambi confermano)

_ALLOWED_TRANSITIONS = {
    "pending": {"accept", "reject", "cancel"},
    "accepted": {"cancel", "confirm_completion"},
}


def _validate_transition(current_status: str, action: str):
    """Controlla se l'azione e' permessa nello stato attuale."""
    allowed = _ALLOWED_TRANSITIONS.get(current_status, set())
    if action not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Non puoi fare '{action}' quando la richiesta e' '{current_status}'.",
        )


# ============================================================
# POST /requests  - INVIARE UNA RICHIESTA DI SESSIONE
# ============================================================
@router.post("/", response_model=SessionRequestResponse, status_code=status.HTTP_201_CREATED)
def create_request(req_data: SessionRequestCreate, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Invia una richiesta di sessione a un altro utente per imparare/insegnare una skill."""
    sender_id = _get_user_id(authorization, db)

    # Non puoi inviare richieste a te stesso
    if sender_id == req_data.receiver_id:
        raise HTTPException(status_code=400, detail="Non puoi inviare una richiesta a te stesso.")

    # Controlla che il destinatario e la skill esistano
    receiver = db.query(User).filter(User.id == req_data.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Destinatario non trovato.")
    skill = db.query(Skill).filter(Skill.id == req_data.skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill non trovata.")

    new_req = SessionRequest(
        sender_id=sender_id,
        receiver_id=req_data.receiver_id,
        skill_id=req_data.skill_id,
        message=req_data.message or "",
        proposed_date=req_data.proposed_date,
        mode=req_data.mode,
    )
    db.add(new_req); db.commit(); db.refresh(new_req)

    # Ricarica la richiesta dal DB per avere anche i nomi (mittente, destinatario, skill)
    req = db.query(SessionRequest).filter(SessionRequest.id == new_req.id).first()
    return _build_request_response(req)


# ============================================================
# GET /requests  - VEDERE LE PROPRIE RICHIESTE
# ============================================================
@router.get("/", response_model=dict)
def get_my_requests(tab: str = "received", authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Mostra le richieste ricevute, inviate o tutte. Con conteggio delle pending."""
    user_id = _get_user_id(authorization, db)

    query = db.query(SessionRequest)
    if tab == "received":
        query = query.filter(SessionRequest.receiver_id == user_id)    # Richieste RICEVUTE
    elif tab == "sent":
        query = query.filter(SessionRequest.sender_id == user_id)      # Richieste INVIATE
    else:
        query = query.filter((SessionRequest.sender_id == user_id) | (SessionRequest.receiver_id == user_id))  # Tutte

    requests = query.order_by(SessionRequest.created_at.desc()).all()  # Dalla piu' recente

    # Quante richieste in attesa di risposta (pending) ci sono per me?
    pending_count = sum(1 for r in requests if r.status == "pending" and r.receiver_id == user_id)

    return {"requests": [_build_request_response(r) for r in requests], "pending_count": pending_count}


# ============================================================
# PATCH /requests/{id}  - AZIONE SU UNA RICHIESTA
# ============================================================
@router.patch("/{request_id}", response_model=SessionRequestResponse)
def act_on_request(request_id: int, action_data: SessionRequestAction, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Esegue un'azione su una richiesta: accept, reject, cancel, confirm_completion."""
    user_id = _get_user_id(authorization, db)
    action = action_data.action

    req = db.query(SessionRequest).filter(SessionRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Richiesta non trovata.")

    # Chi puo' fare cosa:
    if action == "accept":
        if req.receiver_id != user_id:
            raise HTTPException(status_code=403, detail="Solo il destinatario puo' accettare.")
    elif action == "reject":
        if req.receiver_id != user_id:
            raise HTTPException(status_code=403, detail="Solo il destinatario puo' rifiutare.")
    elif action == "cancel":
        if req.sender_id != user_id:
            raise HTTPException(status_code=403, detail="Solo il mittente puo' cancellare.")
    elif action == "confirm_completion":
        if req.receiver_id != user_id and req.sender_id != user_id:
            raise HTTPException(status_code=403, detail="Solo chi partecipa puo' confermare.")

    # Controlla se l'azione e' permessa nello stato attuale
    if action != "confirm_completion":
        _validate_transition(req.status, action)

    now = datetime.now(timezone.utc)

    if action == "accept":
        req.status = "accepted"
    elif action == "reject":
        req.status = "rejected"
    elif action == "cancel":
        req.status = "cancelled"
    elif action == "confirm_completion":
        if req.status != "accepted":
            raise HTTPException(status_code=400, detail="Puoi confermare solo sessioni gia' accettate.")

        # Segna chi ha confermato
        if user_id == req.sender_id:
            req.sender_confirmed = True
        elif user_id == req.receiver_id:
            req.receiver_confirmed = True

        # Se entrambi hanno confermato -> sessione completata!
        if req.sender_confirmed and req.receiver_confirmed:
            req.status = "completed"

    req.updated_at = now
    db.commit(); db.refresh(req)
    return _build_request_response(req)
