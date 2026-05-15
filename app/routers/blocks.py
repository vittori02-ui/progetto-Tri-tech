# blocks.py = BLOCCO UTENTI (stub)
# Endpoint: /blocks/

from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(prefix="/blocks", tags=["blocks"])


class BlockCreate(BaseModel):
    blocked_user_id: int


@router.post("/", status_code=status.HTTP_201_CREATED)
def block_user(data: BlockCreate):
    """Blocca un utente. Endpoint stub - non ancora implementato."""
    return {"message": f"Utente {data.blocked_user_id} bloccato. Funzionalita' in sviluppo."}


@router.delete("/{blocked_user_id}")
def unblock_user(blocked_user_id: int):
    """Sblocca un utente. Endpoint stub - non ancora implementato."""
    return {"message": f"Utente {blocked_user_id} sbloccato. Funzionalita' in sviluppo."}


@router.get("/mine")
def get_blocked_users():
    """Lista utenti bloccati. Endpoint stub - non ancora implementato."""
    return []
