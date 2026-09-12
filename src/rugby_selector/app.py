from collections import Counter
from datetime import date
from pathlib import Path

import streamlit as st

from rugby_selector.models.fixture import ScoreSide, ScoreType
from rugby_selector.models.position import PLAYING_POSITION_COUNT
from rugby_selector.services.fixture_service import (
    load_fixture_availability,
    load_fixtures,
    load_fixture_scores,
    load_match_selections,
)
from rugby_selector.services.player_service import load_players


st.set_page_config(
    page_title="Rugby Selector",
    page_icon="🏉",
    layout="wide",
)


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PLAYERS_FILE = DATA_DIR / "players.json"
FIXTURES_FILE = DATA_DIR / "fixtures.json"
AVAILABILITY_FILE = DATA_DIR / "fixture_availability.json"
SCORES_FILE = DATA_DIR / "fixture_scores.json"
SELECTIONS_FILE = DATA_DIR / "match_selections.json"


def leader_display(counter: Counter, name_for_key=str) -> tuple[str, int | None]:
    if not counter:
        return "—", None

    top_count = max(counter.values())
    leaders = [
        name_for_key(key)
        for key, count in counter.items()
        if count == top_count
    ]
    if len(leaders) == 1:
        return leaders[0], top_count
    if len(leaders) == 2:
        return ", ".join(leaders), top_count
    return f"{len(leaders)} players", top_count


def home() -> None:
    st.title("Rugby Selector")
    st.write("Use the sidebar to manage your squad and fixtures.")

    try:
        players = load_players(PLAYERS_FILE)
    except FileNotFoundError:
        players = []
    player_names = {player.id: player.name for player in players}

    try:
        fixtures = load_fixtures(FIXTURES_FILE)
    except FileNotFoundError:
        fixtures = []

    availability = load_fixture_availability(AVAILABILITY_FILE)
    scores = load_fixture_scores(SCORES_FILE)
    selections = load_match_selections(SELECTIONS_FILE)
    upcoming_fixtures = sorted(
        (fixture for fixture in fixtures if fixture.date >= date.today()),
        key=lambda fixture: fixture.date,
    )

    next_fixture = upcoming_fixtures[0] if upcoming_fixtures else None
    next_fixture_availability = (
        len(availability.get(str(next_fixture.id), [])) if next_fixture else 0
    )

    stat_columns = st.columns(4)
    with stat_columns[0]:
        st.metric("Players in squad", len(players))
    with stat_columns[1]:
        st.metric("Fixtures", len(fixtures))
    with stat_columns[2]:
        st.metric("Upcoming fixtures", len(upcoming_fixtures))
    with stat_columns[3]:
        st.metric("Next fixture availability", next_fixture_availability)

    team_score_events = [
        event
        for fixture_scores in scores.values()
        for event in fixture_scores
        if event.side is ScoreSide.TEAM and event.scorer
    ]
    try_scorers = Counter(
        event.scorer
        for event in team_score_events
        if event.score_type is ScoreType.TRY
    )
    points_scorers = Counter()
    for event in team_score_events:
        points_scorers[event.scorer] += event.points

    appearances = Counter()
    for quarter_positions in selections.values():
        players_in_fixture = {
            player_id
            for quarter in quarter_positions.values()
            for player_id in quarter[:PLAYING_POSITION_COUNT]
            if player_id is not None
        }
        appearances.update(players_in_fixture)

    score_type_labels = (
        ("Most conversions", ScoreType.CONVERSION),
        ("Most penalties", ScoreType.PENALTY),
        ("Most drop goals", ScoreType.DROP_GOAL),
    )
    score_type_scorers = {
        score_type: Counter(
            event.scorer
            for event in team_score_events
            if event.score_type is score_type
        )
        for _, score_type in score_type_labels
    }

    st.subheader("Scoring leaders")
    leader_columns = st.columns(5)
    with leader_columns[0]:
        appearance_leaders, fixture_count = leader_display(
            appearances,
            lambda player_id: player_names.get(player_id, "—"),
        )
        if fixture_count is not None:
            st.metric(
                "Most appearances",
                appearance_leaders,
                f"{fixture_count} fixtures",
            )
        else:
            st.metric("Most appearances", "—")
    with leader_columns[1]:
        try_leaders, tries = leader_display(try_scorers)
        if tries is not None:
            st.metric("Top try scorer", try_leaders, f"{tries} tries")
        else:
            st.metric("Top try scorer", "—")
    with leader_columns[2]:
        points_leaders, points = leader_display(points_scorers)
        if points is not None:
            st.metric("Top points scorer", points_leaders, f"{points} points")
        else:
            st.metric("Top points scorer", "—")
    for column, (label, score_type) in zip(leader_columns[3:], score_type_labels):
        with column:
            scorers = score_type_scorers[score_type]
            scorer_leaders, count = leader_display(scorers)
            if count is not None:
                st.metric(label, scorer_leaders, str(count))
            else:
                st.metric(label, "—")

    if next_fixture:
        st.subheader("Next fixture")
        st.write(
            f"{next_fixture.date:%d %b %Y} — "
            f"{next_fixture.opponent} ({next_fixture.venue})"
        )
    elif fixtures:
        st.info("There are no upcoming fixtures.")


home_page = st.Page(home, title="Home", icon="🏉", default=True)
add_player_page = st.Page(
    "pages/1_Add_Player.py",
    title="Add Player",
    icon="🏉",
    visibility="hidden",
)
player_list_page = st.Page(
    "pages/2_Player_List.py", title="Players", icon="👥"
)
fixture_list_page = st.Page(
    "pages/3_Fixture_List.py", title="Fixtures", icon="📅"
)
add_fixture_page = st.Page(
    "pages/3_Add_Fixture.py",
    title="Add / Edit Fixture",
    icon="➕",
    url_path="add-fixture",
    visibility="hidden",
)
manage_availability_page = st.Page(
    "pages/4_Manage_Availability.py",
    title="Manage Availability",
    icon="✅",
    url_path="manage-availability",
    visibility="hidden",
)
select_team_page = st.Page(
    "pages/5_Select_Team.py",
    title="Select Team",
    icon="🏉",
    url_path="select-team",
    visibility="hidden",
)
manage_scores_page = st.Page(
    "pages/4_Manage_Scores.py",
    title="Manage Scores",
    icon="🏆",
    url_path="fixture-scores",
    visibility="hidden",
)

page = st.navigation(
    [
        home_page,
        add_player_page,
        player_list_page,
        fixture_list_page,
        add_fixture_page,
        manage_availability_page,
        select_team_page,
        manage_scores_page,
    ]
)
page.run()
