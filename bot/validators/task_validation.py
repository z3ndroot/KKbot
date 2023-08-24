from pydantic import BaseModel, field_validator
from datetime import datetime


class TaskCreate(BaseModel):
    """
    Validation of additional tasks
    """
    tag: str
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

    @classmethod
    def from_list(cls, data: list):
        if len(data) != 5:
            raise IndexError('List should contain 3 values')

        tag = data[0]
        login = data[1]
        task = data[2]
        date = data[3]
        quantity = data[4]

        return cls(tag=tag, login=login, task=task, date=date, quantity=quantity)
