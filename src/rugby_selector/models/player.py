from enum import IntEnum, Enum

from pydantic import BaseModel, model_validator

class Skill_Rating(IntEnum):
    POOR = 0
    GOOD = 1
    EXCELLENT = 2

class Position_Group(Enum):
    FORWARD = "forward"
    BACK = "back"

class Player_Skill(BaseModel):
    attack: Skill_Rating
    defence: Skill_Rating
    handling: Skill_Rating
    breakdown: Skill_Rating
    vision: Skill_Rating

class Player(BaseModel):
    id: int | None = None
    name: str
    group: Position_Group
    skills: Player_Skill
    match_rating: Player_Skill

    @model_validator(mode="before")
    @classmethod
    def default_match_rating(cls, values):
        if isinstance(values, dict) and "match_rating" not in values:
            values = values.copy()
            values["match_rating"] = values["skills"]
        return values
