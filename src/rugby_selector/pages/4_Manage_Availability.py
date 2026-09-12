from pathlib import Path

import streamlit as st
from pydantic import ValidationError

from rugby_selector.services.fixture_service import (
    load_fixture_availability,
    load_fixtures,
    save_fixture_availability,
)
from rugby_selector.services.player_service import load_players


FIXTURES_FILE = Path(__file__).resolve().parents[3] / "data" / "fixtures.json"
PLAYERS_FILE = Path(__file__).resolve().parents[3] / "data" / "players.json"
AVAILABILITY_FILE = Path(__file__).resolve().parents[3] / "data" / "fixture_availability.json"


st.set_page_config(
    page_title="Fixture availability | Rugby Selector",
    page_icon="🏉",
    layout="wide",
)

try:
    fixtures = load_fixtures(FIXTURES_FILE)
    players = load_players(PLAYERS_FILE)
except FileNotFoundError:
    fixtures = []
    players = []
except (OSError, ValidationError, ValueError):
    st.error("The fixtures or player list could not be loaded.")
    fixtures = []
    players = []

fixtures.sort(key=lambda fixture: fixture.date, reverse=True)
fixture_ids = [fixture.id for fixture in fixtures]
selected_fixture_id = None
selected_fixture = None
if fixture_ids:
    requested_fixture_id = st.query_params.get("fixture_id")
    if requested_fixture_id is not None:
        try:
            requested_fixture_id = int(requested_fixture_id)
        except ValueError:
            requested_fixture_id = None
        if requested_fixture_id in fixture_ids:
            st.session_state["availability_fixture_selection"] = requested_fixture_id
        st.query_params.pop("fixture_id", None)

    selected_fixture_id = st.session_state.get("availability_fixture_selection")
    if selected_fixture_id not in fixture_ids:
        selected_fixture_id = fixture_ids[0]
        st.session_state["availability_fixture_selection"] = selected_fixture_id
    selected_fixture = next(
        fixture for fixture in fixtures if fixture.id == selected_fixture_id
    )

fixture_title = (
    f"{selected_fixture.date:%d %b %Y} — "
    f"{selected_fixture.opponent} ({selected_fixture.venue})"
    if selected_fixture
    else "Fixture availability"
)
st.title(fixture_title)
st.caption("Record which players are available for this fixture.")

if not fixtures:
    st.info("Add a fixture before recording player availability.")
elif not players:
    st.info("Add players before recording fixture availability.")
    st.page_link("pages/1_Add_Player.py", label="Add a player")
else:
    players.sort(key=lambda player: player.name.casefold())
    player_ids = [player.id for player in players]
    player_names = {
        player.id: player.name for player in players
    }

    availability = load_fixture_availability(AVAILABILITY_FILE)
    saved_player_ids = {
        player_id
        for player_id in availability.get(str(selected_fixture_id), [])
        if player_id in player_ids
    }

    st.subheader("Player availability")
    selected_player_ids = []
    player_group_count = min(3, len(player_ids))
    player_groups = st.columns(player_group_count, gap=None)
    for group, group_column in enumerate(player_groups):
        with group_column:
            name_column, available_column = st.columns([2, 3], gap=None)
            with name_column:
                st.markdown("**Player**")
            with available_column:
                st.markdown("**Available?**")

    for row_start in range(0, len(player_ids), player_group_count):
        player_groups = st.columns(player_group_count, gap=None)
        for player_id, group_column in zip(
            player_ids[row_start : row_start + player_group_count], player_groups
        ):
            with group_column:
                name_column, available_column = st.columns([2, 3], gap=None)
                with name_column:
                    st.write(player_names[player_id])
                with available_column:
                    player_available = st.radio(
                        f"Is {player_names[player_id]} available?",
                        options=("Yes", "No"),
                        index=0 if player_id in saved_player_ids else 1,
                        horizontal=True,
                        label_visibility="collapsed",
                        key=f"availability_{selected_fixture_id}_{player_id}",
                    )
            if player_available == "Yes":
                selected_player_ids.append(player_id)

    if st.button("Save availability", type="primary"):
        try:
            AVAILABILITY_FILE.parent.mkdir(parents=True, exist_ok=True)
            save_fixture_availability(
                selected_fixture_id, selected_player_ids, AVAILABILITY_FILE
            )
        except (OSError, ValueError):
            st.error("Availability could not be saved. Please check the data file permissions.")
        else:
            st.success(
                f"Availability for {fixture_title} was saved."
            )
