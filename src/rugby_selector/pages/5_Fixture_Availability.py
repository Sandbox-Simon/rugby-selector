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


st.set_page_config(page_title="Fixture availability | Rugby Selector", page_icon="🏉")
st.title("Fixture availability")
st.caption("Select a fixture and record which players are available.")

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

if not fixtures:
    st.info("Add a fixture before recording player availability.")
    st.page_link("pages/4_Add_Fixture.py", label="Add a fixture")
elif not players:
    st.info("Add players before recording fixture availability.")
    st.page_link("pages/1_Player.py", label="Add a player")
else:
    players.sort(key=lambda player: player.name.casefold())
    player_ids = [player.id for player in players]
    player_names = {
        player.id: player.name for player in players
    }
    fixture_ids = [fixture.id for fixture in fixtures]
    fixture_labels = {
        fixture.id: f"{fixture.date:%d %b %Y} — {fixture.opponent} ({fixture.venue})"
        for fixture in fixtures
    }
    selected_fixture_id = st.selectbox(
        "Fixture",
        options=fixture_ids,
        format_func=lambda fixture_id: fixture_labels[fixture_id],
    )

    availability = load_fixture_availability(AVAILABILITY_FILE)
    saved_player_ids = {
        player_id
        for player_id in availability.get(str(selected_fixture_id), [])
        if player_id in player_ids
    }

    st.subheader("Player availability")
    header_name, header_available = st.columns([3, 1])
    with header_name:
        st.markdown("**Player**")
    with header_available:
        st.markdown("**Available?**")

    selected_player_ids = []
    for player_id in player_ids:
        player_column, available_column = st.columns([3, 1])
        with player_column:
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
            st.success(f"Availability for {fixture_labels[selected_fixture_id]} was saved.")
