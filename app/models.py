from pydantic import BaseModel, ConfigDict

#modelli pydantic (struttura dati)
class StatusResponse(BaseModel):
    status: str
    message: str


class SkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
