from pydantic import BaseModel, ConfigDict

#modelli pydantic (struttura dati)
class StatusResponse(BaseModel):
    status: str
    message: str


class SkillResponse(BaseModel):  
    #checcare per che è cosi con l'ordine diverso
    id: int #accetta un intero e sotto una stringa
    name: str
    description: str|None="Inserisci qualcosa"
    model_config = ConfigDict(from_attributes=True) #riga importante dice a pydantic
                                                    #dice questi dati non vengono  da un dizionario
                                                    #ma da sqlAlchemy se non da errore
                                                    #fare una cartella dove ci sono i controller per far vedere i get al frontend

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    email: str

class UserSkillCreate(BaseModel):
    user_id: int
    skill_id: int
    level: str # Es: "Principiante", "Intermedio", "Avanzato"
    type: str

class SessionRequestCreate(BaseModel):
    sender_id: int
    receiver_id: int
    skill_id: int
    message: str | None = None

class SessionRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sender_id: int
    receiver_id: int
    skill_id: int
    status: str
    message: str

class SkillCreate(BaseModel):
    name: str
    description: str | None = None