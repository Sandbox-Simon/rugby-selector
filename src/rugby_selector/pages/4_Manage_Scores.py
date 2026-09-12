from pathlib import Path

import pandas as pd
import streamlit as st
from pydantic import ValidationError

from rugby_selector.models.fixture import SCORE_POINTS, ScoreEvent, ScoreSide, ScoreType
from rugby_selector.services.fixture_service import (
    load_fixture_scores,
    load_fixtures,
    save_fixture_score,
)
from rugby_selector.services.player_service import load_players


DATA_DIR = Path(__file__).resolve().parents[3] / "data"
FIXTURES_FILE = DATA_DIR / "fixtures.json"
PLAYERS_FILE = DATA_DIR / "players.json"
SCORES_FILE = DATA_DIR / "fixture_scores.json"


st.set_page_config(
    page_title="Fixture scores | Rugby Selector",
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
    st.error("The fixture list could not be loaded. Please check the saved fixture data.")
    fixtures = []
    players = []

fixtures.sort(key=lambda fixture: fixture.date, reverse=True)
fixture_ids = [fixture.id for fixture in fixtures]
selected_fixture = None
selected_fixture_id = None

if fixture_ids:
    requested_fixture_id = st.query_params.get("fixture_id")
    if requested_fixture_id is not None:
        try:
            requested_fixture_id = int(requested_fixture_id)
        except ValueError:
            requested_fixture_id = None
        if requested_fixture_id in fixture_ids:
            st.session_state["scores_fixture_selection"] = requested_fixture_id
        st.query_params.pop("fixture_id", None)

    selected_fixture_id = st.session_state.get("scores_fixture_selection")
    if selected_fixture_id not in fixture_ids:
        selected_fixture_id = fixture_ids[0]
        st.session_state["scores_fixture_selection"] = selected_fixture_id
    selected_fixture = next(
        fixture for fixture in fixtures if fixture.id == selected_fixture_id
    )

fixture_title = (
    f"{selected_fixture.date:%d %b %Y} — "
    f"{selected_fixture.opponent} ({selected_fixture.venue})"
    if selected_fixture
    else "Fixture scores"
)
st.title(fixture_title)
st.caption("Record scoring events for both teams in this fixture.")

if not selected_fixture:
    st.info("Add a fixture before recording scores.")
else:
    players.sort(key=lambda player: player.name.casefold())
    player_names = [player.name for player in players]

    side = st.selectbox(
        "Scoring side",
        options=list(ScoreSide),
        format_func=lambda value: value.value,
    )
    with st.form("add-score", clear_on_submit=True):
        score_type = st.selectbox(
            "Score type",
            options=list(ScoreType),
            format_func=lambda value: f"{value.value} ({SCORE_POINTS[value]} points)",
        )
        if side is ScoreSide.TEAM and player_names:
            scorer = st.selectbox("Scoring player", options=player_names)
        else:
            scorer = None
        minute = st.number_input(
            "Match minute",
            min_value=0,
            max_value=120,
            value=1,
            step=1,
        )
        submitted = st.form_submit_button("Add score", type="primary")

    if submitted:
        try:
            if side is ScoreSide.TEAM and not scorer:
                raise ValueError("The scoring player is required.")
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            save_fixture_score(
                selected_fixture_id,
                ScoreEvent(
                    side=side,
                    score_type=score_type,
                    minute=minute,
                    scorer=scorer,
                ),
                SCORES_FILE,
            )
        except (OSError, ValidationError, ValueError) as error:
            message = (
                error.errors()[0]["msg"]
                if isinstance(error, ValidationError)
                else str(error)
            )
            st.error(f"The score could not be saved: {message}")
        else:
            st.success("Score added.")

    scores = load_fixture_scores(SCORES_FILE).get(str(selected_fixture_id), [])
    team_score = sum(event.points for event in scores if event.side is ScoreSide.TEAM)
    opposition_score = sum(
        event.points for event in scores if event.side is ScoreSide.OPPOSITION
    )
    score_columns = st.columns(2)
    with score_columns[0]:
        st.metric("Our team", team_score)
    with score_columns[1]:
        st.metric("Opposition", opposition_score)

    st.subheader("Scoring events")
    if scores:
        score_rows = [
            {
                "Minute": event.minute,
                "Team": event.side.value,
                "Scorer": event.scorer or "—",
                "Type": event.score_type.value,
                "Points": event.points,
            }
            for event in sorted(scores, key=lambda event: event.minute)
        ]
        st.dataframe(pd.DataFrame(score_rows), hide_index=True, width="stretch")
    else:
        st.info("No scoring events have been recorded for this fixture.")
