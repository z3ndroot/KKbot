from pydantic import BaseModel


class AdminCreate(BaseModel):
    """
    Validation of administrators
    """
    login: str
    id: int

    @classmethod
    def from_list(cls, data: list):
        if len(data) != 2:
            raise IndexError('List should contain 2 values')

        login = data[0]
        _id = data[1]
        return cls(login=login, id=_id)
