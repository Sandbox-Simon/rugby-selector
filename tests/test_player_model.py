import pytest
from pydantic import ValidationError

from rugby_selector.models.player import (Skill_Rating, Position_Group, Player_Skill, Player)

@pytest.fixture
def player() ->Player:
        return Player(
        name = "Joe Bloggs",
        group = Position_Group.BACK,
        skills = Player_Skill(
            attack = 0,
            defence = 1,
            handling = 2,
            breakdown = 0,
            vision = 1 
        )
    )

def test_create_player(player):
    assert player.name == "Joe Bloggs"
    assert player.group == Position_Group.BACK
    assert player.skills.attack == Skill_Rating.WEAK
    assert player.skills.defence == Skill_Rating.AVERAGE
    assert player.skills.handling == Skill_Rating.STRONG
    assert player.skills.breakdown == Skill_Rating.WEAK
    assert player.skills.vision == Skill_Rating.AVERAGE