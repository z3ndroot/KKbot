from datetime import datetime

from pydantic import BaseModel, field_validator


class SupportCreate(BaseModel):
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
    autochecks: int | str
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

    @classmethod
    def from_list(cls, data: list):
        if len(data) != 11:
            raise IndexError('List should contain 3 values')

        status = data[0]
        date = data[1]
        login = data[2]
        link = data[3]
        comment = data[4]
        skillsup = data[5]
        skill = data[6]
        output = data[7]
        appreciated = data[8]
        autochecks = data[9]
        residue = data[10]

        return cls(
            status=status,
            data=date,
            login=login,
            link=link,
            comment=comment,
            skillsup=skillsup,
            skill=skill,
            output=output,
            appreciated=appreciated,
            autochecks=autochecks,
            residue=residue
        )
