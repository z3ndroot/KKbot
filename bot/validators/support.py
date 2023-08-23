from datetime import datetime

from pydantic import BaseModel, field_validator


class Support(BaseModel):
    """
    Validation of row supports
    """
    status: str
    date: str
    login: str
    link: str
    comment: str
    skillsup: str
    skill: str
    output: str
    appreciated: int
    autochecks: int
    residue: int

    @field_validator('status')
    @classmethod
    def status_check(cls, v: str):
        if v == "" or v == "НЕ ДЕКРЕТ":
            return v
        else:
            raise ValueError(f'Incorrect status: {v}')

    @field_validator('date')
    @classmethod
    def date_check(cls, v: str):
        if v == '' or v == '-':
            return v
        elif datetime.strptime(v, '%d.%m.%Y') < datetime.now():
            return v
        else:
            raise ValueError(f"Incorrect date: {v}")

    @field_validator('residue')
    @classmethod
    def reside_check(cls, v):
        if v == 0:
            raise ValueError(f'Incorrect residue: {v}')
        return v
