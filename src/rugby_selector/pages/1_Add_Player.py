from pathlib import Path

import streamlit as st
from pydantic import ValidationError

from rugby_selector.models.player import Player, Player_Skill, Position_Group, Skill_Rating
from rugby_selector.services.player_service import add_player, load_players, update_player


DATA_FILE = Path(__file__).resolve().parents[3] / "data" / "players.json"
RATING_LABELS = {
    Skill_Rating.POOR: "Poor",
    Skill_Rating.GOOD: "Good",
    Skill_Rating.EXCELLENT: "Excellent",
}
SKILLS = ("attack", "defence", "handling", "breakdown", "vision")


st.set_page_config(page_title="Player | Rugby Selector", page_icon="🏉")
st.title("Player")

try:
    players = load_players(DATA_FILE)
except FileNotFoundError:
    players = []
except (OSError, ValidationError, ValueError):
    st.error("The player list could not be loaded. Please check the saved player data.")
    players = []

requested_id = st.query_params.get("player_id")
if requested_id is None:
    selected_from_table = st.session_state.get("edit_player_id")
    requested_id = str(selected_from_table) if selected_from_table is not None else None
has_edit_selection = requested_id is not None and any(
    str(player.id) == requested_id for player in players
)
is_editing = has_edit_selection
selected_player = None

if is_editing and not players:
    st.info("No players have been added to the squad yet.")
elif is_editing:
    player_ids = [player.id for player in players]
    selected_index = next(
        (index for index, player_id in enumerate(player_ids) if str(player_id) == requested_id),
        0,
    )
    selected_id = st.selectbox(
        "Player",
        options=player_ids,
        index=selected_index,
        format_func=lambda player_id: next(
            player.name for player in players if player.id == player_id
        ),
        key="edit_player_selection",
    )
    selected_player = next(player for player in players if player.id == selected_id)

if not is_editing or selected_player is not None:
    form_suffix = "edit" if is_editing else "add"
    widget_suffix = f"{form_suffix}_{selected_player.id}" if selected_player else form_suffix
    title = "Edit player" if is_editing else "Add player"
    st.subheader(title)
    with st.form(f"{form_suffix}-player", clear_on_submit=not is_editing):
        name = st.text_input(
            "Player name",
            value=selected_player.name if selected_player else "",
            key=f"{widget_suffix}_player_name",
        )
        group = st.selectbox(
            "Position group",
            options=list(Position_Group),
            index=(list(Position_Group).index(selected_player.group) if selected_player else 0),
            format_func=lambda position: position.value.title(),
            key=f"{widget_suffix}_player_group",
        )

        st.subheader("Skills")
        columns = st.columns(2)
        skill_values = {}
        for index, skill in enumerate(SKILLS):
            with columns[index % 2]:
                skill_values[skill] = st.select_slider(
                    skill.title(),
                    options=list(Skill_Rating),
                    value=(getattr(selected_player.skills, skill) if selected_player else Skill_Rating.GOOD),
                    format_func=lambda rating: RATING_LABELS[rating],
                    key=f"{widget_suffix}_{skill}",
                )

        submitted = st.form_submit_button(
            "Save changes" if is_editing else "Add player", type="primary"
        )

    if submitted:
        try:
            if not name.strip():
                raise ValueError("Player name is required.")
            player = Player(
                id=selected_player.id if selected_player else None,
                name=name.strip(),
                group=group,
                skills=Player_Skill(**skill_values),
            )
            DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
            if not DATA_FILE.exists():
                DATA_FILE.write_text("[]", encoding="utf-8")
            if is_editing:
                update_player(player, DATA_FILE)
            else:
                add_player(player, DATA_FILE)
        except (ValidationError, ValueError) as error:
            message = error.errors()[0]["msg"] if isinstance(error, ValidationError) else str(error)
            st.error(f"Please correct the player details: {message}")
        except OSError:
            st.error("The player could not be saved. Please check the data file permissions.")
        else:
            st.success(f"{player.name} was {'updated' if is_editing else 'added'}.")

st.page_link("pages/2_Player_List.py", label="Back to players")
