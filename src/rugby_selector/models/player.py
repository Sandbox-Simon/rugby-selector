from enum import IntEnum, Enum

from pydantic import BaseModel

class Skill_Rating(IntEnum):
    WEAK = 0
    AVERAGE = 1
    STRONG = 2

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


