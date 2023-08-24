from pydantic import BaseModel, field_validator


class UserCreate(BaseModel):
    """
    User validation
    """
    login: str
    id: int
    skill: str

    @field_validator('skill')
    @classmethod
    def skill_not_empty(cls, v: str):
        if not v:
            raise ValueError("A skill can't be empty")
        return v

    @classmethod
    def from_list(cls, data):
        if len(data) != 3:
            raise IndexError('List should contain 3 values')
        login = data[0]
        _id = data[1]
        skill = data[2]
        return cls(login=login, id=_id, skill=skill)
