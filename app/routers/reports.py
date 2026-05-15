# reports.py = SEGNALAZIONI UTENTI (stub)
# Endpoint: /reports/

from fastapi import APIRouter, status, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportCreate(BaseModel):
    user_id: int
    reason: str


@router.post("/", status_code=status.HTTP_201_CREATED)
def report_user(data: ReportCreate):
    """Segnala un utente. Endpoint stub - non ancora implementato."""
    return {"message": f"Segnalazione per utente {data.user_id} ricevuta. Funzionalita' in sviluppo."}
