from pathlib import Path
import json

from rugby_selector.models.fixture import Fixture


def load_fixtures(data_file: Path) -> list[Fixture]:
    with data_file.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return [Fixture.model_validate(fixture) for fixture in data]


def add_fixture(fixture: Fixture, data_file: Path) -> None:
    fixture_list = load_fixtures(data_file)

    if fixture_list:
        fixture.id = max(saved_fixture.id for saved_fixture in fixture_list) + 1
    else:
        fixture.id = 1

    fixture_list.append(fixture)

    with data_file.open("w", encoding="utf-8") as file:
        json.dump(
            [saved_fixture.model_dump(mode="json") for saved_fixture in fixture_list],
            file,
            indent=4,
        )


def load_fixture_availability(data_file: Path) -> dict[str, list[int]]:
    """Load player availability keyed by fixture ID."""
    if not data_file.exists():
        return {}

    with data_file.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return {
        str(fixture_id): [int(player_id) for player_id in player_ids]
        for fixture_id, player_ids in data.items()
    }


def save_fixture_availability(
    fixture_id: int, player_ids: list[int], data_file: Path
) -> None:
    availability = load_fixture_availability(data_file)
    availability[str(fixture_id)] = player_ids

    with data_file.open("w", encoding="utf-8") as file:
        json.dump(availability, file, indent=4)


def load_match_selections(data_file: Path) -> dict[str, dict[str, list[int | None]]]:
    """Load quarter positions keyed by fixture ID."""
    if not data_file.exists():
        return {}

    with data_file.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_match_selection(
    fixture_id: int,
    quarter_positions: dict[str, list[int | None]],
    data_file: Path,
) -> None:
    selections = load_match_selections(data_file)
    selections[str(fixture_id)] = quarter_positions

    with data_file.open("w", encoding="utf-8") as file:
        json.dump(selections, file, indent=4)
