# users.py = ROTTE PER GLI UTENTI (profili, ricerca, statistiche)
# Tutti gli endpoint iniziano con /users

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import func  # func = funzioni SQL come COUNT, AVG

from app.database import get_db
from app.db_models import User, Skill, UserSkill, Feedback, SessionRequest
from app.models import UserSearchResponse, UserSkillResponse, DashboardStats
from app.routers.auth import _get_user_id

router = APIRouter(prefix="/users", tags=["users"])


# ============================================================
# FUNZIONE DI SUPPORTO: recupera le skill di un utente
# ============================================================
# Divide le skill in "offerte" (type=offered) e "cercate" (type=wanted)
def _get_user_skills(user_id: int, db: Session):
    # JOIN tra user_skills e skill per avere il nome della skill
    user_skills = (
        db.query(UserSkill, Skill.name)
        .join(Skill, UserSkill.skill_id == Skill.id)
        .filter(UserSkill.user_id == user_id)
        .all()
    )
    offered, wanted = [], []
    for us, skill_name in user_skills:
        item = UserSkillResponse(id=us.id, skill_id=us.skill_id, skill_name=skill_name, level=us.level, user_id=us.user_id, type=us.type)
        if us.type == "wanted":
            wanted.append(item)
        else:
            offered.append(item)
    return offered, wanted


# ============================================================
# FUNZIONE DI SUPPORTO: calcola la media dei voti di un utente
# ============================================================
def _get_avg_rating(user_id: int, db: Session):
    # Calcola la media di tutti i feedback ricevuti da questo utente
    avg = (
        db.query(func.avg(Feedback.rating))
        .join(SessionRequest, Feedback.session_request_id == SessionRequest.id)
        .filter((SessionRequest.sender_id == user_id) | (SessionRequest.receiver_id == user_id))
        .scalar()
    )
    return round(float(avg), 2) if avg else None


# ============================================================
# FUNZIONE DI SUPPORTO: verifica se c'e' match reciproco
# ============================================================
# Match = io offro una skill che TU cerchi E tu offri una skill che IO cerco
def _check_match(current_user_id: int, target_user_id: int, db: Session) -> bool:
    my_offered = {us.skill_id for us in db.query(UserSkill).filter(UserSkill.user_id == current_user_id, UserSkill.type == "offered").all()}
    my_wanted = {us.skill_id for us in db.query(UserSkill).filter(UserSkill.user_id == current_user_id, UserSkill.type == "wanted").all()}
    their_offered = {us.skill_id for us in db.query(UserSkill).filter(UserSkill.user_id == target_user_id, UserSkill.type == "offered").all()}
    their_wanted = {us.skill_id for us in db.query(UserSkill).filter(UserSkill.user_id == target_user_id, UserSkill.type == "wanted").all()}
    # & = intersezione tra set (elementi in comune)
    return bool(my_offered & their_wanted and their_offered & my_wanted)


# ============================================================
# GET /users/public/{id}  - PROFILO PUBBLICO DI UN UTENTE
# ============================================================
@router.get("/public/{user_id}", response_model=dict)
def get_public_profile(user_id: int, db: Session = Depends(get_db)):
    """Mostra il profilo pubblico di un utente (nome, bio, citta', voto medio)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato.")
    avg_rating = _get_avg_rating(user_id, db)
    return {
        "id": user.id,
        "name": user.name,
        "bio": user.bio or "",
        "location": user.location or "",
        "average_rating": avg_rating,  # Media dei voti ricevuti
    }


# ============================================================
# GET /users/{id}/skills  - SKILL PUBBLICHE DI UN UTENTE
# ============================================================
@router.get("/{user_id}/skills", response_model=dict)
def get_user_skills_public(user_id: int, db: Session = Depends(get_db)):
    """Mostra le skill (offerte e cercate) di un utente specifico."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato.")
    offered, wanted = _get_user_skills(user_id, db)
    return {"offered_skills": [s.model_dump() for s in offered], "wanted_skills": [s.model_dump() for s in wanted]}


# ============================================================
# GET /users/search  - RICERCA UTENTI (con match reciproco)
# ============================================================
# Cerca utenti per nome, bio o skill. Esempi:
#   /users/search?q=Python     (cerca chi ha Python)
#   /users/search?q=Mario      (cerca chi si chiama Mario)
#   /users/search              (tutti gli utenti)
@router.get("/search", response_model=list[UserSearchResponse])
def search_users(
    q: str = Query("", description="Testo da cercare (nome, bio, skill)"),
    limit: int = Query(20, description="Quanti risultati mostrare"),
    offset: int = Query(0, description="Da dove partire (paginazione)"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Cerca utenti. Se sei loggato, mostra anche se c'e' match reciproco."""
    # Prova a leggere il token per mostrare il match (se fallisce, cerca lo stesso)
    current_user_id = None
    if authorization:
        try:
            current_user_id = _get_user_id(authorization)
        except HTTPException:
            pass

    if not q.strip():
        users = db.query(User).offset(offset).limit(limit).all()
    else:
        name_filter = User.name.ilike(f"%{q}%")     # Cerca nel nome
        bio_filter = User.bio.ilike(f"%{q}%")        # Cerca nella bio
        # Cerca anche chi ha skill con quel nome
        skill_users = (
            db.query(UserSkill.user_id).join(Skill, UserSkill.skill_id == Skill.id)
            .filter(Skill.name.ilike(f"%{q}%")).subquery()
        )
        users = (
            db.query(User).filter(name_filter | bio_filter | User.id.in_(db.query(skill_users.c.user_id)))
            .offset(offset).limit(limit).all()
        )

    result = []
    for user in users:
        offered, wanted = _get_user_skills(user.id, db)
        is_match = False
        if current_user_id and current_user_id != user.id:
            is_match = _check_match(current_user_id, user.id, db)
        result.append(UserSearchResponse(
            id=user.id,
            name=user.name,
            email=user.email or "",
            location=user.location or "",
            level=user.level or "",
            image_url=user.image_url or "",
            offerte=[s.skill_name for s in offered],
            cercate=[s.skill_name for s in wanted],
            is_match=is_match,
            offered_skills=offered,
            wanted_skills=wanted,
        ))
    return result


# ============================================================
# GET /users/stats  - STATISTICHE GLOBALI
# ============================================================
@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    """Quanti utenti, quante skill, quante associazioni."""
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_skills = db.query(func.count(Skill.id)).scalar() or 0
    total_matches = db.query(func.count(UserSkill.id)).scalar() or 0
    return DashboardStats(total_users=total_users, total_skills=total_skills, total_matches=total_matches)
