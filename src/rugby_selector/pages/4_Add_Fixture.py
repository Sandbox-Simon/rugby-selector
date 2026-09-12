from datetime import date
from pathlib import Path

import streamlit as st
from pydantic import ValidationError

from rugby_selector.models.fixture import Fixture
from rugby_selector.services.fixture_service import add_fixture


DATA_FILE = Path(__file__).resolve().parents[3] / "data" / "fixtures.json"


st.set_page_config(page_title="Add fixture | Rugby Selector", page_icon="🏉")
st.title("Add fixture")
st.caption("Record the date, venue, and opponent for an upcoming match.")

with st.form("add-fixture", clear_on_submit=True):
    fixture_date = st.date_input("Date", value=date.today())
    venue = st.text_input("Venue", placeholder="e.g. Home ground")
    opponent = st.text_input("Opponent", placeholder="e.g. Riverside RFC")
    submitted = st.form_submit_button("Add fixture", type="primary")

if submitted:
    try:
        if not venue.strip():
            raise ValueError("Venue is required.")
        if not opponent.strip():
            raise ValueError("Opponent is required.")

        fixture = Fixture(
            date=fixture_date,
            venue=venue.strip(),
            opponent=opponent.strip(),
        )
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not DATA_FILE.exists():
            DATA_FILE.write_text("[]", encoding="utf-8")
        add_fixture(fixture, DATA_FILE)
    except (ValidationError, ValueError) as error:
        message = error.errors()[0]["msg"] if isinstance(error, ValidationError) else str(error)
        st.error(f"Please correct the fixture details: {message}")
    except OSError:
        st.error("The fixture could not be saved. Please check the data file permissions.")
    else:
        st.success(f"Fixture against {fixture.opponent} was added.")
