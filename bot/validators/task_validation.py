from pydantic import BaseModel, field_validator
from datetime import datetime


class TaskCreate(BaseModel):
    """
    Validation of additional tasks
    """
    login: str
    task: str
    date: str
    quantity: int

    @field_validator("date")
    @classmethod
    def date_check(cls, v: str):
        if not datetime.strptime(v, '%d.%m.%Y'):
            raise ValueError(f'Date does not match the format: {v}')
        return v
