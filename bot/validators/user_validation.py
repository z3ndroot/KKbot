from pydantic import BaseModel


class UserCreate(BaseModel):
    """
    User validation
    """
    login: str
    id: int
    skill: str
