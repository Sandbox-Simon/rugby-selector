from pathlib import Path

import pandas as pd
import streamlit as st
from pydantic import ValidationError

from rugby_selector.models.position import (
    PLAYING_POSITION_COUNT,
    position_label,
    position_name,
)
from rugby_selector.services.fixture_service import (
    load_fixture_availability,
    load_fixtures,
    load_match_selections,
    save_match_selection,
)
from rugby_selector.services.player_service import load_players


DATA_DIR = Path(__file__).resolve().parents[3] / "data"
FIXTURES_FILE = DATA_DIR / "fixtures.json"
PLAYERS_FILE = DATA_DIR / "players.json"
AVAILABILITY_FILE = DATA_DIR / "fixture_availability.json"
SELECTIONS_FILE = DATA_DIR / "match_selections.json"
QUARTERS = ("Q1", "Q2", "Q3", "Q4")
SKILLS = ("attack", "defence", "handling", "breakdown", "vision")


def summary_cell_colour(value: int, category: str) -> str:
    if category == "played":
        colour = "#fecaca" if value < 2 else "#fed7aa" if value == 2 else "#bbf7d0"
    elif category == "subbed":
        colour = "#bbf7d0" if value < 2 else "#fed7aa" if value == 2 else "#fecaca"
    else:
        colour = "#bbf7d0" if value == 4 else "#fecaca"
    return f"background-color: {colour}; color: #1f2937;"


st.set_page_config(
    page_title="Select team | Rugby Selector",
    page_icon="🏉",
    layout="wide",
)
st.markdown(
    """
    <style>
    .st-key-match-header {
        position: fixed;
        top: 3rem;
        left: 0;
        width: 100%;
        z-index: 1000;
        box-sizing: border-box;
        background-color: var(--background-color, #ffffff);
        padding: 0.5rem 5rem 1rem;
        border-bottom: 1px solid rgba(128, 128, 128, 0.25);
    }
    body:has([data-testid="stSidebar"][aria-expanded="true"]) .st-key-match-header {
        left: 21rem;
        width: calc(100% - 21rem);
        padding-left: 2rem;
    }
    .match-header-spacer {
        height: 5rem;
    }
    .st-key-save-match-button {
        position: static !important;
    }
    .st-key-save-match-button button {
        position: fixed !important;
        top: auto !important;
        left: auto !important;
        right: 1.5rem !important;
        bottom: 1.5rem !important;
        z-index: 1000000 !important;
        width: max-content !important;
        min-width: 5rem;
        white-space: nowrap;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
with st.container(key="match-header"):
    title_column, fixture_column = st.columns([1.5, 1.2])
    with title_column:
        st.title("Select team")
        st.caption("Choose the available players and assign them for each quarter.")
st.markdown("<div class='match-header-spacer'></div>", unsafe_allow_html=True)

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
    st.info("Add a fixture before selecting a team.")
    st.page_link("pages/4_Add_Fixture.py", label="Add a fixture")
elif not players:
    st.info("Add players before selecting a team.")
    st.page_link("pages/1_Player.py", label="Add a player")
else:
    players.sort(key=lambda player: player.name.casefold())
    player_names = {player.id: player.name for player in players}
    players_by_id = {player.id: player for player in players}
    fixture_ids = [fixture.id for fixture in fixtures]
    fixture_labels = {
        fixture.id: f"{fixture.date:%d %b %Y} — {fixture.opponent} ({fixture.venue})"
        for fixture in fixtures
    }
    with fixture_column:
        selected_fixture_id = st.selectbox(
            "Fixture",
            options=fixture_ids,
            format_func=lambda fixture_id: fixture_labels[fixture_id],
        )

    availability = load_fixture_availability(AVAILABILITY_FILE)
    available_ids = list(
        dict.fromkeys(
            player_id
            for player_id in availability.get(str(selected_fixture_id), [])
            if player_id in player_names
        )
    )
    available_ids.sort(key=lambda player_id: player_names[player_id].casefold())

    if not available_ids:
        with fixture_column:
            st.info("No players have been marked available for this fixture.")
        st.page_link("pages/5_Fixture_Availability.py", label="Set fixture availability")
    else:
        with fixture_column:
            st.success(f"{len(available_ids)} player(s) available for this fixture.")
        with st.container(key="save-match-button"):
            save_requested = st.button(
                "Save",
                type="primary",
                key=f"save_{selected_fixture_id}",
            )
        saved_selections = load_match_selections(SELECTIONS_FILE).get(
            str(selected_fixture_id), {}
        )
        position_count = max(PLAYING_POSITION_COUNT, len(available_ids))
        player_options = [None, *available_ids]
        quarter_positions = {quarter: [] for quarter in QUARTERS}

        pending_clear_quarter = st.session_state.pop("pending_clear_quarter", None)
        if pending_clear_quarter:
            for position in range(position_count):
                clear_key = f"{selected_fixture_id}_{pending_clear_quarter.lower()}_{position + 1}"
                st.session_state[clear_key] = None

        pending_copy_request = st.session_state.pop("pending_copy_request", None)
        if pending_copy_request:
            source_quarter, target_quarter = pending_copy_request
            source_positions = saved_selections.get(source_quarter, [])
            for position in range(position_count):
                source_key = f"{selected_fixture_id}_{source_quarter.lower()}_{position + 1}"
                target_key = f"{selected_fixture_id}_{target_quarter.lower()}_{position + 1}"
                source_player_id = st.session_state.get(
                    source_key,
                    source_positions[position] if len(source_positions) > position else None,
                )
                st.session_state[target_key] = (
                    source_player_id if source_player_id in available_ids else None
                )

        planned_positions = {}
        for quarter in QUARTERS:
            saved_positions = saved_selections.get(quarter, [])
            planned_positions[quarter] = [
                (
                    st.session_state.get(
                        f"{selected_fixture_id}_{quarter.lower()}_{position + 1}",
                        saved_positions[position] if len(saved_positions) > position else None,
                    )
                    if st.session_state.get(
                        f"{selected_fixture_id}_{quarter.lower()}_{position + 1}",
                        saved_positions[position] if len(saved_positions) > position else None,
                    ) in available_ids
                    else None
                )
                for position in range(position_count)
            ]

        assignment_colours = {
            "same_position": "#92d050",
            "first_appearance": "#ff0000",
            "returning_from_bench": "#ffc000",
            "different_position": "#d9a0d9",
        }
        colour_rules = []
        for quarter_index, quarter in enumerate(QUARTERS):
            if quarter_index == 0:
                continue
            previous_quarter = QUARTERS[quarter_index - 1]
            for position, player_id in enumerate(planned_positions[quarter]):
                if position >= PLAYING_POSITION_COUNT:
                    continue
                if player_id is None:
                    continue
                previous_positions = planned_positions[previous_quarter]
                if position < len(previous_positions) and previous_positions[position] == player_id:
                    colour = assignment_colours["same_position"]
                elif player_id in previous_positions[:PLAYING_POSITION_COUNT]:
                    colour = assignment_colours["different_position"]
                else:
                    prior_appearances = any(
                        player_id in planned_positions[prior_quarter][:position_count]
                        for prior_quarter in QUARTERS[:quarter_index]
                    )
                    colour = assignment_colours[
                        "returning_from_bench" if prior_appearances else "first_appearance"
                    ]
                key = f"{selected_fixture_id}_{quarter.lower()}_{position + 1}"
                colour_container_key = f"colour_{key}"
                selector_keys = (key, colour_container_key)
                selectbox_selectors = []
                for selector_key in selector_keys:
                    selectbox_selectors.extend(
                        [
                            f".st-key-{selector_key}",
                            f".st-key-{selector_key}[data-testid='stSelectbox']",
                            f".st-key-{selector_key}[data-baseweb='select']",
                            f".st-key-{selector_key} [data-baseweb='select']",
                        ]
                    )
                selectbox_selectors.extend(
                    [
                        f".st-key-{selector_key} [data-baseweb='select'] > div"
                        for selector_key in selector_keys
                    ]
                )
                selectbox_selectors.extend(
                    [
                        f".st-key-{selector_key} [data-baseweb='select'] > div > div"
                        for selector_key in selector_keys
                    ]
                )
                for selector_key in selector_keys:
                    selectbox_selectors.extend(
                        [
                            f".st-key-{selector_key} [data-testid='stSelectbox'] [data-baseweb='select']",
                            f".st-key-{selector_key} [data-testid='stSelectbox'] [data-baseweb='select'] > div",
                            f".st-key-{selector_key} [data-testid='stSelectbox'] [data-baseweb='select'] > div > div",
                            f".st-key-{selector_key} [role='combobox']",
                        ]
                    )
                colour_rules.append(
                    ", ".join(selectbox_selectors)
                    + f" {{ background: {colour} !important; background-color: {colour} !important; }}"
                )
        summary_column, selection_column = st.columns([1.25, 3])

        with selection_column:
            st.subheader("Selection")
            selection_column_widths = [1.25, 1, 1, 1, 1]
            copy_requests = (("Q1", "Q2"), ("Q2", "Q3"), ("Q3", "Q4"))
            copy_requests_clicked = []
            clear_requests = []
            header_columns = st.columns(selection_column_widths)
            with header_columns[0]:
                st.markdown("**Pos.**")
            for index, (column, quarter) in enumerate(zip(header_columns[1:], QUARTERS)):
                with column:
                    heading_column, controls_column = st.columns(
                        [1.2, 1], gap="small", vertical_alignment="center"
                    )
                    with heading_column:
                        st.markdown(f"**{quarter}**")
                    if index > 0:
                        source_quarter, target_quarter = copy_requests[index - 1]
                        with controls_column:
                            button_columns = st.columns(2, gap=None)
                            with button_columns[0]:
                                if st.button(
                                    "",
                                    icon=":material/content_copy:",
                                    help=f"Copy {source_quarter} to {target_quarter}",
                                    key=f"copy_{selected_fixture_id}_{target_quarter.lower()}",
                                ):
                                    copy_requests_clicked.append((source_quarter, target_quarter))
                            clear_column = button_columns[1]
                    else:
                        with controls_column:
                            if st.button(
                                "",
                                icon=":material/delete:",
                                help=f"Clear {quarter}",
                                type="primary",
                                key=f"clear_{selected_fixture_id}_{quarter.lower()}",
                            ):
                                clear_requests.append(quarter)
                    if index > 0:
                        with clear_column:
                            if st.button(
                                "",
                                icon=":material/delete:",
                                help=f"Clear {quarter}",
                                type="primary",
                                key=f"clear_{selected_fixture_id}_{quarter.lower()}",
                            ):
                                clear_requests.append(quarter)

            for position in range(position_count):
                row_columns = st.columns(selection_column_widths)
                with row_columns[0]:
                    st.markdown(
                        f"<div style='height: 40px; line-height: 40px; text-align: center; font-weight: 700;'>"
                        f"{position_label(position + 1)}</div>",
                        unsafe_allow_html=True,
                    )

                for column_index, quarter in enumerate(QUARTERS, start=1):
                    with row_columns[column_index]:
                        key = f"{selected_fixture_id}_{quarter.lower()}_{position + 1}"
                        colour_container_key = f"colour_{key}"
                        saved_positions = saved_selections.get(quarter, [])
                        saved_player_id = (
                            saved_positions[position]
                            if len(saved_positions) > position
                            and saved_positions[position] in available_ids
                            else None
                        )
                        current_player_id = st.session_state.get(key, saved_player_id)
                        used_player_ids = {
                            player_id
                            for player_id in quarter_positions[quarter]
                            if player_id is not None
                        }
                        options = [
                            player_id
                            for player_id in player_options
                            if player_id not in used_player_ids or player_id == current_player_id
                        ]
                        if current_player_id not in options:
                            current_player_id = None

                        with st.container(key=colour_container_key):
                            selected_player_id = st.selectbox(
                                position_label(position + 1),
                                options=options,
                                index=options.index(current_player_id),
                                format_func=lambda player_id: "—" if player_id is None else player_names[player_id],
                                key=key,
                                label_visibility="collapsed",
                            )
                        quarter_positions[quarter].append(selected_player_id)

            if colour_rules:
                st.markdown(
                    "<style>" + "".join(colour_rules) + "</style>",
                    unsafe_allow_html=True,
                )

            if copy_requests_clicked:
                st.session_state["pending_copy_request"] = copy_requests_clicked[0]
                st.rerun()
            elif clear_requests:
                st.session_state["pending_clear_quarter"] = clear_requests[0]
                st.rerun()

            if save_requested:
                incomplete_quarters = [
                    quarter
                    for quarter in QUARTERS
                    if any(
                        player_id is None
                        for player_id in quarter_positions[quarter][:PLAYING_POSITION_COUNT]
                    )
                ]
                duplicate_quarters = [
                    quarter
                    for quarter in QUARTERS
                    if len([player_id for player_id in quarter_positions[quarter] if player_id is not None])
                    != len(set(player_id for player_id in quarter_positions[quarter] if player_id is not None))
                ]
                if incomplete_quarters:
                    st.error(
                        "Assign all named playing positions for "
                        + ", ".join(incomplete_quarters)
                        + "."
                    )
                elif duplicate_quarters:
                    st.error("A player can only be selected once per quarter: " + ", ".join(duplicate_quarters) + ".")
                else:
                    DATA_DIR.mkdir(parents=True, exist_ok=True)
                    save_match_selection(selected_fixture_id, quarter_positions, SELECTIONS_FILE)
                    st.success("Match selection saved.")

        with summary_column:
            st.subheader("Player match summary")
            st.caption("Totals showing the amount of quarters being played")
            summary_table = pd.DataFrame(
                [
                    {
                        "Player": player_names[player_id],
                        "Played": sum(
                            player_id in quarter_positions[quarter][:PLAYING_POSITION_COUNT]
                            for quarter in QUARTERS
                        ),
                        "Subbed": sum(
                            player_id in quarter_positions[quarter][PLAYING_POSITION_COUNT:]
                            for quarter in QUARTERS
                        ),
                        "Total": sum(
                            player_id in quarter_positions[quarter] for quarter in QUARTERS
                        ),
                    }
                    for player_id in available_ids
                ]
            )
            st.table(
                summary_table.style
                .map(lambda value: summary_cell_colour(value, "played"), subset=["Played"])
                .map(lambda value: summary_cell_colour(value, "subbed"), subset=["Subbed"])
                .map(lambda value: summary_cell_colour(value, "total"), subset=["Total"])
            )

            st.subheader("Substitution summary")
            substitution_bullets = []
            for quarter_index in range(1, len(QUARTERS)):
                quarter = QUARTERS[quarter_index]
                previous_quarter = QUARTERS[quarter_index - 1]
                previous_positions = quarter_positions[previous_quarter][:PLAYING_POSITION_COUNT]
                current_positions = quarter_positions[quarter][:PLAYING_POSITION_COUNT]
                previous_playing_positions = {
                    player_id: position + 1
                    for position, player_id in enumerate(previous_positions)
                    if player_id is not None
                }
                current_bench_players = {
                    player_id
                    for player_id in quarter_positions[quarter][PLAYING_POSITION_COUNT:]
                    if player_id is not None
                }

                for position, current_player_id in enumerate(current_positions):
                    previous_player_id = previous_positions[position]
                    if current_player_id is None or current_player_id == previous_player_id:
                        continue

                    current_player_name = player_names[current_player_id]
                    if current_player_id in previous_playing_positions:
                        substitution_bullets.append(
                            f"- **{quarter}:** {current_player_name} moves to "
                            f"{position_name(position + 1)}"
                        )
                    elif previous_player_id is not None:
                        substitution_bullets.append(
                            f"- **{quarter}:** {current_player_name} replaces "
                            f"{player_names[previous_player_id]} at {position_name(position + 1)}"
                        )

                for player_id, previous_position in previous_playing_positions.items():
                    if player_id in current_bench_players:
                        substitution_bullets.append(
                            f"- **{quarter}:** {player_names[player_id]} moves from "
                            f"{position_name(previous_position)} to the bench"
                        )

            if substitution_bullets:
                st.markdown("\n".join(substitution_bullets))
            else:
                st.caption("No substitutions or positional changes yet.")

            st.subheader("Quarter skill totals")
            st.caption(
                "Totals for named playing positions only. "
                "Ratings: Poor = 0, Good = 1, Excellent = 2."
            )
            skill_total_rows = []
            for skill in SKILLS:
                skill_total_rows.append(
                    {
                        "Skill": skill.title(),
                        **{
                            quarter: sum(
                                getattr(players_by_id[player_id].skills, skill)
                                for player_id in quarter_positions[quarter][:PLAYING_POSITION_COUNT]
                                if player_id is not None
                            )
                            for quarter in QUARTERS
                        },
                    }
                )
            skill_total_rows.append(
                {
                    "Skill": "TOTAL",
                    **{
                        quarter: sum(row[quarter] for row in skill_total_rows)
                        for quarter in QUARTERS
                    },
                }
            )
            skill_totals_table = pd.DataFrame(skill_total_rows).set_index("Skill")
            st.table(
                skill_totals_table.style.apply(
                    lambda row: [
                        "font-weight: bold; font-size: 1.1em;" if row.name == "TOTAL" else ""
                    ]
                    * len(row),
                    axis=1,
                )
            )
