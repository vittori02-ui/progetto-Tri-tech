from pydantic import BaseModel

#modelli pydantic (struttura dati)
class StatusResponse(BaseModel):
    status: str
    message: str
