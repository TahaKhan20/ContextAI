from pydantic import BaseModel


class RenameRequest(BaseModel):
    title: str
