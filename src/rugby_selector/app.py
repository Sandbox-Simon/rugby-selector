from pathlib import Path

import streamlit as st

from rugby_selector.services.player_service import load_players


DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "players.json"


st.set_page_config(page_title="Rugby Selector", page_icon="🏉")
st.title("Rugby Selector")
st.write("Use the sidebar to add players or view your squad.")

try:
    player_count = len(load_players(DATA_FILE))
except FileNotFoundError:
    player_count = 0

st.metric("Players in squad", player_count)
