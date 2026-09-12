from datetime import date

from pydantic import BaseModel


class Fixture(BaseModel):
    id: int | None = None
    date: date
    venue: str
    opponent: str
