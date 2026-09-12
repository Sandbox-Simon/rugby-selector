from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class Fixture(BaseModel):
    id: int | None = None
    date: date
    venue: str
    opponent: str


class ScoreSide(str, Enum):
    TEAM = "Our team"
    OPPOSITION = "Opposition"


class ScoreType(str, Enum):
    TRY = "Try"
    CONVERSION = "Conversion"
    PENALTY = "Penalty"
    DROP_GOAL = "Drop goal"
    PENALTY_TRY = "Penalty try"


SCORE_POINTS = {
    ScoreType.TRY: 5,
    ScoreType.CONVERSION: 2,
    ScoreType.PENALTY: 3,
    ScoreType.DROP_GOAL: 3,
    ScoreType.PENALTY_TRY: 7,
}


class ScoreEvent(BaseModel):
    side: ScoreSide
    score_type: ScoreType
    minute: int = Field(ge=0, le=120)
    scorer: str | None = None

    @property
    def points(self) -> int:
        return SCORE_POINTS[self.score_type]
