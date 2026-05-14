# ============================================================
# Router: Skill (CRUD skill globali + associazione utente-skill)
# ============================================================
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models import Skill, UserSkill
from app.models import (
    SkillResponse,
    SkillCreate,
    UserSkillResponse,
    UserSkillCreate,
)
# 👇 Importiamo _get_user_id da auth.py, così non lo riscriviamo qui
from app.routers.auth import _get_user_id

router = APIRouter(prefix="/skills", tags=["skills"])


# ============================================================
# GET /skills - Elenco di tutte le skill globali
# ============================================================
@router.get("/", response_model=list[SkillResponse])
def get_all_skills(db: Session = Depends(get_db)):
    """
    Restituisce l'elenco completo di tutte le skill nel catalogo globale.
    Usato per autocomplete e filtri di ricerca.
    """
    skills = db.query(Skill).all()
    return skills


# ============================================================
# POST /skills - Crea una nuova skill nel catalogo globale
# ============================================================
@router.post("/", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
def create_skill(
    skill_data: SkillCreate,
    db: Session = Depends(get_db),
):
    """
    Crea una nuova skill nel catalogo globale.
    Se la skill esiste già (stesso nome), restituisce errore 409.
    """
    # Verifica se la skill esiste già per nome (unique constraint)
    existing = db.query(Skill).filter(Skill.name == skill_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Skill '{skill_data.name}' già esistente.",
        )

    # Crea la nuova skill
    new_skill = Skill(name=skill_data.name, description=skill_data.description or "")
    db.add(new_skill)
    db.commit()
    db.refresh(new_skill)
    return new_skill


# ============================================================
# GET /skills/my - Skill dell'utente corrente (offerte + cercate)
# ============================================================
@router.get("/my", response_model=list[UserSkillResponse])
def get_my_skills(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Restituisce tutte le skill associate all'utente autenticato.
    Ogni record contiene: id, skill_id, skill_name, level, user_id.
    """
    user_id = _get_user_id(authorization)

    # Query che unisce UserSkill con Skill per ottenere il nome
    user_skills = (
        db.query(UserSkill, Skill.name)
        .join(Skill, UserSkill.skill_id == Skill.id)
        .filter(UserSkill.user_id == user_id)
        .all()
    )

    # Costruisce la risposta combinando i dati
    result = []
    for us, skill_name in user_skills:
        result.append(
            UserSkillResponse(
                id=us.id,
                skill_id=us.skill_id,
                skill_name=skill_name,
                level=us.level,
                user_id=us.user_id,
            )
        )
    return result


# ============================================================
# POST /skills/my - Aggiunge una skill all'utente corrente
# ============================================================
@router.post("/my", response_model=UserSkillResponse, status_code=status.HTTP_201_CREATED)
def add_my_skill(
    skill_data: UserSkillCreate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Aggiunge una skill all'utente autenticato.
    - Se la skill non esiste nel catalogo globale, la crea automaticamente.
    - Se l'utente ha già quella skill, restituisce errore.
    """
    user_id = _get_user_id(authorization)

    # Cerca la skill nel catalogo globale per nome
    skill = db.query(Skill).filter(Skill.name == skill_data.skill_name).first()
    if not skill:
        # Se non esiste, la crea automaticamente
        skill = Skill(name=skill_data.skill_name, description="")
        db.add(skill)
        db.commit()
        db.refresh(skill)

    # Verifica che l'utente non abbia già questa skill
    existing = (
        db.query(UserSkill)
        .filter(UserSkill.user_id == user_id, UserSkill.skill_id == skill.id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Skill '{skill_data.skill_name}' già associata al tuo profilo.",
        )

    # Crea l'associazione utente-skill
    new_user_skill = UserSkill(
        user_id=user_id,
        skill_id=skill.id,
        level=skill_data.level,
    )
    db.add(new_user_skill)
    db.commit()
    db.refresh(new_user_skill)

    return UserSkillResponse(
        id=new_user_skill.id,
        skill_id=new_user_skill.skill_id,
        skill_name=skill.name,
        level=new_user_skill.level,
        user_id=new_user_skill.user_id,
    )


# ============================================================
# PUT /skills/my/{user_skill_id} - Aggiorna il livello di una skill
# ============================================================
@router.put("/my/{user_skill_id}", response_model=UserSkillResponse)
def update_my_skill(
    user_skill_id: int,
    skill_data: UserSkillCreate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Aggiorna il livello di una skill associata all'utente.
    Nota: se il nome skill cambia, aggiorna anche il riferimento.
    """
    user_id = _get_user_id(authorization)

    # Cerca la UserSkill specifica
    user_skill = (
        db.query(UserSkill)
        .filter(UserSkill.id == user_skill_id, UserSkill.user_id == user_id)
        .first()
    )
    if not user_skill:
        raise HTTPException(status_code=404, detail="Skill non trovata nel tuo profilo.")

    # Se il nome è cambiato, cerca/crea la nuova skill
    skill = db.query(Skill).filter(Skill.name == skill_data.skill_name).first()
    if not skill:
        skill = Skill(name=skill_data.skill_name, description="")
        db.add(skill)
        db.commit()
        db.refresh(skill)

    # Aggiorna i campi
    user_skill.skill_id = skill.id
    user_skill.level = skill_data.level
    db.commit()
    db.refresh(user_skill)

    return UserSkillResponse(
        id=user_skill.id,
        skill_id=user_skill.skill_id,
        skill_name=skill.name,
        level=user_skill.level,
        user_id=user_skill.user_id,
    )


# ============================================================
# DELETE /skills/my/{user_skill_id} - Rimuove una skill dall'utente
# ============================================================
@router.delete("/my/{user_skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_skill(
    user_skill_id: int,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Rimuove una skill dall'utente autenticato.
    Elimina solo l'associazione (UserSkill), non la skill globale.
    """
    user_id = _get_user_id(authorization)

    user_skill = (
        db.query(UserSkill)
        .filter(UserSkill.id == user_skill_id, UserSkill.user_id == user_id)
        .first()
    )
    if not user_skill:
        raise HTTPException(status_code=404, detail="Skill non trovata nel tuo profilo.")

    db.delete(user_skill)
    db.commit()
