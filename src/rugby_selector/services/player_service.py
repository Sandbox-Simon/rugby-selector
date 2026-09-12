from pathlib import Path
import json

from rugby_selector.models.player import Player


def load_players(data_file: Path) -> list[Player]:
    with data_file.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return [Player.model_validate(player) for player in data]


def add_player(player: Player, data_file: Path) -> None:
    player_list = load_players(data_file)

    if player_list:
        player.id = max(p.id for p in player_list) + 1
    else:
        player.id = 1

    player_list.append(player)

    with data_file.open("w", encoding="utf-8") as file:
        json.dump(
            [player.model_dump(mode="json") for player in player_list],
            file,
            indent=4,
        )


def update_player(player: Player, data_file: Path) -> None:
    """Replace an existing player while keeping the player's ID."""
    if player.id is None:
        raise ValueError("A player ID is required to update a player.")

    player_list = load_players(data_file)
    for index, saved_player in enumerate(player_list):
        if saved_player.id == player.id:
            player_list[index] = player
            break
    else:
        raise ValueError(f"Player with ID {player.id} was not found.")

    with data_file.open("w", encoding="utf-8") as file:
        json.dump(
            [saved_player.model_dump(mode="json") for saved_player in player_list],
            file,
            indent=4,
        )
