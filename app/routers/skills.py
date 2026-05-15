# skills.py = GESTIONE DELLE SKILL (competenze)
# Endpoint: catalogo globale (/skills/) e skill personali (/skills/my)

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models import Skill, UserSkill
from app.models import SkillResponse, SkillCreate, UserSkillResponse, UserSkillCreate
from app.routers.auth import _get_user_id  # Funzione condivisa per leggere il token

router = APIRouter(prefix="/skills", tags=["skills"])


# ============================================================
# GET /skills  - VEDERE TUTTE LE SKILL DEL CATALOGO
# ============================================================
# Esempio risposta: [{"id": 1, "name": "Python", "description": "..."}, ...]
@router.get("/", response_model=list[SkillResponse])
def get_all_skills(db: Session = Depends(get_db)):
    """Restituisce tutte le skill disponibili nel catalogo globale."""
    return db.query(Skill).all()  # SELECT * FROM skills


# ============================================================
# POST /skills  - CREARE UNA NUOVA SKILL NEL CATALOGO
# ============================================================
@router.post("/", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
def create_skill(skill_data: SkillCreate, db: Session = Depends(get_db)):
    """Aggiunge una nuova skill al catalogo. Se gia' esiste, da' errore 409."""
    existing = db.query(Skill).filter(Skill.name == skill_data.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Skill '{skill_data.name}' gia' esistente.")
    new_skill = Skill(name=skill_data.name, description=skill_data.description or "")
    db.add(new_skill)
    db.commit()
    db.refresh(new_skill)
    return new_skill


# ============================================================
# GET /skills/my  - SKILL DELL'UTENTE LOGGATO
# ============================================================
# Restituisce sia le skill offerte (type="offered") che quelle cercate (type="wanted")
@router.get("/my", response_model=list[UserSkillResponse])
def get_my_skills(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Restituisce tutte le skill dell'utente loggato (offerte + cercate)."""
    user_id = _get_user_id(authorization, db)  # Prende l'ID dall'hash
    # JOIN tra user_skills e skills per avere anche il nome della skill
    user_skills = db.query(UserSkill, Skill.name).join(Skill, UserSkill.skill_id == Skill.id).filter(UserSkill.user_id == user_id).all()
    result = []
    for us, skill_name in user_skills:
        result.append(UserSkillResponse(id=us.id, skill_id=us.skill_id, skill_name=skill_name, level=us.level, user_id=us.user_id, type=us.type))
    return result


# ============================================================
# POST /skills/my  - AGGIUNGERE UNA SKILL AL PROPRIO PROFILO
# ============================================================
@router.post("/my", response_model=UserSkillResponse, status_code=status.HTTP_201_CREATED)
def add_my_skill(skill_data: UserSkillCreate, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Aggiunge una skill al profilo dell'utente (offerta o cercata). Se la skill non esiste nel catalogo, la crea."""
    user_id = _get_user_id(authorization, db)

    # La skill esiste gia' nel catalogo globale?
    skill = db.query(Skill).filter(Skill.name == skill_data.skill_name).first()
    if not skill:
        # Se non esiste, la creiamo automaticamente
        skill = Skill(name=skill_data.skill_name, description="")
        db.add(skill); db.commit(); db.refresh(skill)

    # L'utente ha gia' questa stessa skill (stesso tipo)?
    existing = db.query(UserSkill).filter(UserSkill.user_id == user_id, UserSkill.skill_id == skill.id, UserSkill.type == skill_data.type).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Skill '{skill_data.skill_name}' ({skill_data.type}) gia' presente nel tuo profilo.")

    new_us = UserSkill(user_id=user_id, skill_id=skill.id, level=skill_data.level, type=skill_data.type)
    db.add(new_us); db.commit(); db.refresh(new_us)
    return UserSkillResponse(id=new_us.id, skill_id=new_us.skill_id, skill_name=skill.name, level=new_us.level, user_id=new_us.user_id, type=new_us.type)


# ============================================================
# PUT /skills/my/{id}  - MODIFICARE LIVELLO O TIPO DI UNA SKILL
# ============================================================
@router.put("/my/{user_skill_id}", response_model=UserSkillResponse)
def update_my_skill(user_skill_id: int, skill_data: UserSkillCreate, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Aggiorna il livello o il tipo (offered/wanted) di una skill del profilo."""
    user_id = _get_user_id(authorization, db)
    user_skill = db.query(UserSkill).filter(UserSkill.id == user_skill_id, UserSkill.user_id == user_id).first()
    if not user_skill:
        raise HTTPException(status_code=404, detail="Skill non trovata nel tuo profilo.")

    skill = db.query(Skill).filter(Skill.name == skill_data.skill_name).first()
    if not skill:
        skill = Skill(name=skill_data.skill_name, description="")
        db.add(skill); db.commit(); db.refresh(skill)

    user_skill.skill_id = skill.id
    user_skill.level = skill_data.level
    user_skill.type = skill_data.type
    db.commit(); db.refresh(user_skill)
    return UserSkillResponse(id=user_skill.id, skill_id=user_skill.skill_id, skill_name=skill.name, level=user_skill.level, user_id=user_skill.user_id, type=user_skill.type)


# ============================================================
# DELETE /skills/my/{id}  - RIMUOVERE UNA SKILL DAL PROFILO
# ============================================================
@router.delete("/my/{user_skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_skill(user_skill_id: int, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Rimuove una skill dal profilo dell'utente (non cancella la skill dal catalogo globale)."""
    user_id = _get_user_id(authorization, db)
    user_skill = db.query(UserSkill).filter(UserSkill.id == user_skill_id, UserSkill.user_id == user_id).first()
    if not user_skill:
        raise HTTPException(status_code=404, detail="Skill non trovata nel tuo profilo.")
    db.delete(user_skill)
    db.commit()
