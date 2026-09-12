import pytest
from pydantic import ValidationError

from rugby_selector.models.player import (Skill_Rating, Position_Group, Player_Skill, Player)
from rugby_selector.services.player_service import (add_player, load_players, update_player)

@pytest.fixture
def player() ->Player:
        return Player(
        name = "Joe Bloggs",
        group = Position_Group.BACK,
        skills = Player_Skill(
            attack = Skill_Rating.WEAK,
            defence = Skill_Rating.AVERAGE,
            handling = Skill_Rating.STRONG,
            breakdown = Skill_Rating.WEAK,
            vision = Skill_Rating.AVERAGE
        )
    )

def test_add_player(player, tmp_path):
    data_file = tmp_path / "players.json"
    data_file.write_text("[]")

    add_player(player, data_file)

    player_list = load_players(data_file)

    assert len(player_list) == 1
    assert player_list[0].id == 1
    assert player_list[0].name == "Joe Bloggs"


def test_add_multiple_players(player, tmp_path):
    data_file = tmp_path / "players.json"
    data_file.write_text("[]")

    add_player(player, data_file)

    player_list = load_players(data_file)

    assert len(player_list) == 1
    assert player_list[0].id == 1
    assert player_list[0].name == "Joe Bloggs"

    player.name = "John Doe"

    add_player(player, data_file)

    player_list = load_players(data_file)

    assert len(player_list) == 2
    assert player_list[0].id == 1
    assert player_list[1].id == 2
    assert player_list[0].name == "Joe Bloggs"
    assert player_list[1].name == "John Doe"


def test_update_player_preserves_id_and_replaces_details(player, tmp_path):
    data_file = tmp_path / "players.json"
    data_file.write_text("[]")
    add_player(player, data_file)

    edited_player = Player(
        id=1,
        name="Jane Doe",
        group=Position_Group.FORWARD,
        skills=Player_Skill(
            attack=Skill_Rating.STRONG,
            defence=Skill_Rating.STRONG,
            handling=Skill_Rating.AVERAGE,
            breakdown=Skill_Rating.STRONG,
            vision=Skill_Rating.AVERAGE,
        ),
    )
    update_player(edited_player, data_file)

    player_list = load_players(data_file)

    assert len(player_list) == 1
    assert player_list[0] == edited_player


def test_update_player_requires_existing_id(player, tmp_path):
    data_file = tmp_path / "players.json"
    data_file.write_text("[]")

    with pytest.raises(ValueError, match="not found"):
        update_player(player.model_copy(update={"id": 99}), data_file)
