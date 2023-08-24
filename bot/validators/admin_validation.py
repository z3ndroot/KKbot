from pydantic import BaseModel


class AdminCreate(BaseModel):
    """
    Validation of administrators
    """
    login: str
    id: int
