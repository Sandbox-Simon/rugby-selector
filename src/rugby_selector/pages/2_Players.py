from pathlib import Path

import pandas as pd
import streamlit as st
from pydantic import ValidationError

from rugby_selector.models.player import Skill_Rating
from rugby_selector.services.player_service import load_players


DATA_FILE = Path(__file__).resolve().parents[3] / "data" / "players.json"
RATING_LABELS = {
    Skill_Rating.WEAK: "Weak",
    Skill_Rating.AVERAGE: "Average",
    Skill_Rating.STRONG: "Strong",
}
SKILL_COLUMNS = ["Attack", "Defence", "Handling", "Breakdown", "Vision", "Overall"]
RATING_COLOURS = {
    "Weak": "#fecaca",
    "Average": "#fde68a",
    "Strong": "#bbf7d0",
}


def rating_cell_colour(rating: str) -> str:
    """Return the background colour used for a displayed skill rating."""
    if colour := RATING_COLOURS.get(rating):
        return f"background-color: {colour}; color: #1f2937;"
    return ""


st.set_page_config(page_title="Players | Rugby Selector", page_icon="🏉")
st.title("Players")
st.caption("Your current squad and their skill ratings.")
st.query_params.clear()

try:
    players = load_players(DATA_FILE)
except FileNotFoundError:
    players = []
except (OSError, ValidationError, ValueError):
    st.error("The player list could not be loaded. Please check the saved player data.")
    players = []

if not players:
    st.info("No players have been added to the squad yet.")
else:
    player_rows = [
        {
            "Name": player.name,
            "Position group": player.group.value.title(),
            "Attack": RATING_LABELS[player.skills.attack],
            "Defence": RATING_LABELS[player.skills.defence],
            "Handling": RATING_LABELS[player.skills.handling],
            "Breakdown": RATING_LABELS[player.skills.breakdown],
            "Vision": RATING_LABELS[player.skills.vision],
            "Overall": RATING_LABELS[
                Skill_Rating(
                    round(
                        sum(
                            (
                                player.skills.attack,
                                player.skills.defence,
                                player.skills.handling,
                                player.skills.breakdown,
                                player.skills.vision,
                            )
                        )
                        / 5
                    )
                )
            ],
        }
        for player in players
    ]
    player_table = pd.DataFrame(player_rows)
    table_event = st.dataframe(
        player_table.style.map(rating_cell_colour, subset=SKILL_COLUMNS),
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    selected_rows = table_event.selection.rows
    if selected_rows:
        selected_index = selected_rows[0]
        if selected_index < len(players):
            selected_player_id = players[selected_index].id
            st.session_state["edit_player_id"] = selected_player_id
            st.query_params["player_id"] = str(selected_player_id)
            st.switch_page("pages/1_Player.py")
