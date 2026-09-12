from datetime import date

from rugby_selector.models.fixture import Fixture
from rugby_selector.services.fixture_service import (
    add_fixture,
    load_fixture_availability,
    load_fixtures,
    load_match_selections,
    save_match_selection,
    save_fixture_availability,
)


def test_add_fixture(tmp_path):
    data_file = tmp_path / "fixtures.json"
    data_file.write_text("[]")
    fixture = Fixture(
        date=date(2026, 9, 20),
        venue="Home ground",
        opponent="Riverside RFC",
    )

    add_fixture(fixture, data_file)

    fixtures = load_fixtures(data_file)
    assert len(fixtures) == 1
    assert fixtures[0].id == 1
    assert fixtures[0].date == date(2026, 9, 20)
    assert fixtures[0].venue == "Home ground"
    assert fixtures[0].opponent == "Riverside RFC"


def test_save_and_load_fixture_availability(tmp_path):
    data_file = tmp_path / "fixture_availability.json"

    save_fixture_availability(1, [3, 1, 2], data_file)
    save_fixture_availability(2, [4], data_file)

    assert load_fixture_availability(data_file) == {"1": [3, 1, 2], "2": [4]}


def test_save_and_load_match_selection(tmp_path):
    data_file = tmp_path / "match_selections.json"
    quarter_positions = {
        "Q1": [1, 2, None],
        "Q2": [2, 1, None],
    }

    save_match_selection(1, quarter_positions, data_file)

    assert load_match_selections(data_file) == {"1": quarter_positions}
