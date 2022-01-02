from uuid import UUID, uuid4

from pydantic import BaseModel
from typing import Optional


class FileData(BaseModel):
    file_id: Optional[UUID] = uuid4()
    name: str
    path: Optional[str] = None
    size: Optional[int]


class FileDataIn(BaseModel):
    name: str


class FileDataOut(BaseModel):
    name: str
    size: Optional[int] = None
