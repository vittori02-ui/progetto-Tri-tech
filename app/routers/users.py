# ============================================================
# Router: Utenti (profili pubblici, ricerca, statistiche)
# ============================================================
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.db_models import User, Skill, UserSkill
from app.models import (
    UserPublicResponse,
    UserSearchResponse,
    UserSkillResponse,
    DashboardStats,
)
# 👇 Importiamo _get_user_id da auth.py, non lo riscriviamo qui
from app.routers.auth import _get_user_id

router = APIRouter(prefix="/users", tags=["users"])


# ============================================================
# Helper: recupera le skill di un utente (offerte e cercate)
# ============================================================
def _get_user_skills(user_id: int, db: Session) -> tuple[list[UserSkillResponse], list[UserSkillResponse]]:
    """
    Recupera le skill di un utente divise in due gruppi:
    - offered_skills: tutte le skill (il frontend le mostra come "offerte")
    - Nota: per semplicità, tutte le skill sono considerate "offerte"
      Il frontend gestisce la distinzione offerte/cercate
    """
    user_skills = (
        db.query(UserSkill, Skill.name)
        .join(Skill, UserSkill.skill_id == Skill.id)
        .filter(UserSkill.user_id == user_id)
        .all()
    )

    offered = []
    for us, skill_name in user_skills:
        offered.append(
            UserSkillResponse(
                id=us.id,
                skill_id=us.skill_id,
                skill_name=skill_name,
                level=us.level,
                user_id=us.user_id,
            )
        )
    return offered, []  # Per ora tutte le skill sono "offerte"


# ============================================================
# GET /users/public/{user_id} - Profilo pubblico di un utente
# ============================================================
@router.get("/public/{user_id}", response_model=UserPublicResponse)
def get_public_profile(user_id: int, db: Session = Depends(get_db)):
    """
    Restituisce il profilo pubblico di un utente (visibile senza login).
    Include bio, location, nome.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato.")
    return user


# ============================================================
# GET /users/{user_id}/skills - Skill pubbliche di un utente
# ============================================================
@router.get("/{user_id}/skills", response_model=dict)
def get_user_skills_public(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Restituisce le skill pubbliche di un utente specifico.
    Divide in offered_skills e wanted_skills.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato.")

    offered, wanted = _get_user_skills(user_id, db)

    return {
        "offered_skills": [s.model_dump() for s in offered],
        "wanted_skills": [s.model_dump() for s in wanted],
    }


# ============================================================
# GET /users/search - Cerca utenti per skill/nome
# ============================================================
@router.get("/search", response_model=list[UserSearchResponse])
def search_users(
    q: str = Query("", description="Testo da cercare in nome, bio, skill"),
    # 👇 Paginazione: limit e offset per non caricare 10.000 utenti in memoria
    limit: int = Query(20, description="Numero massimo di risultati"),
    offset: int = Query(0, description="Quanti risultati saltare (paginazione)"),
    db: Session = Depends(get_db),
):
    """
    Cerca utenti per:
    - Nome (parziale, case-insensitive)
    - Bio (parziale)
    - Skill possedute (per nome)
    Restituisce una lista di utenti con le loro skill.

    🔍 Paginazione: usa limit=20&offset=0 per la prima pagina,
    limit=20&offset=20 per la seconda, ecc.
    """
    if not q.strip():
        # Se la query è vuota, restituisce tutti gli utenti (con paginazione)
        users = db.query(User).offset(offset).limit(limit).all()
    else:
        # Cerca per nome (LIKE %query%)
        name_filter = User.name.ilike(f"%{q}%")
        bio_filter = User.bio.ilike(f"%{q}%")

        # Cerca anche utenti che hanno skill con quel nome
        skill_users = (
            db.query(UserSkill.user_id)
            .join(Skill, UserSkill.skill_id == Skill.id)
            .filter(Skill.name.ilike(f"%{q}%"))
            .subquery()
        )

        users = (
            db.query(User)
            .filter(
                name_filter
                | bio_filter
                | User.id.in_(db.query(skill_users.c.user_id))
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

    # Arricchisce ogni utente con le sue skill
    result = []
    for user in users:
        offered, wanted = _get_user_skills(user.id, db)
        # 👇 PRIMA restituiva un dict con email. ORA usa UserSearchResponse
        #    (che NON ha email = privacy salvata). FastAPI converte
        #    automaticamente il dict usando il response_model.
        result.append(
            {
                "id": user.id,
                "name": user.name,
                "bio": user.bio or "",
                "location": user.location or "",
                "offered_skills": [s.model_dump() for s in offered],
                "wanted_skills": [s.model_dump() for s in wanted],
            }
        )

    return result


# ============================================================
# GET /users/stats - Statistiche per la dashboard/home
# ============================================================
@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    """
    Restituisce statistiche globali dell'app:
    - totale utenti registrati
    - totale skill nel catalogo
    - totale associazioni (match)
    """
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_skills = db.query(func.count(Skill.id)).scalar() or 0
    total_matches = db.query(func.count(UserSkill.id)).scalar() or 0

    return DashboardStats(
        total_users=total_users,
        total_skills=total_skills,
        total_matches=total_matches,
    )

