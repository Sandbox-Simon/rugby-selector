from datetime import date
from pathlib import Path

import streamlit as st
from pydantic import ValidationError

from rugby_selector.models.fixture import Fixture
from rugby_selector.services.fixture_service import add_fixture, load_fixtures, update_fixture


DATA_FILE = Path(__file__).resolve().parents[3] / "data" / "fixtures.json"


st.set_page_config(page_title="Add fixture | Rugby Selector", page_icon="🏉")
st.title("Add / edit fixture")
st.caption("Record the date, venue, and opponent for an upcoming match.")

try:
    fixtures = load_fixtures(DATA_FILE) if DATA_FILE.exists() else []
except (OSError, ValidationError, ValueError):
    st.error("The fixture list could not be loaded. Please check the saved fixture data.")
    fixtures = []

fixtures.sort(key=lambda fixture: fixture.date, reverse=True)
fixture_by_id = {fixture.id: fixture for fixture in fixtures}
requested_fixture_id = st.query_params.get("fixture_id")
if requested_fixture_id is not None:
    try:
        requested_fixture_id = int(requested_fixture_id)
    except ValueError:
        requested_fixture_id = None
selected_fixture_id = (
    requested_fixture_id if requested_fixture_id in fixture_by_id else None
)

selected_fixture = fixture_by_id.get(selected_fixture_id)
is_editing = selected_fixture is not None
form_suffix = f"edit_{selected_fixture_id}" if is_editing else "add"

with st.form(f"{form_suffix}-fixture", clear_on_submit=not is_editing):
    fixture_date = st.date_input(
        "Date",
        value=selected_fixture.date if selected_fixture else date.today(),
        key=f"{form_suffix}_date",
    )
    venue = st.text_input(
        "Venue",
        value=selected_fixture.venue if selected_fixture else "",
        placeholder="e.g. Home ground",
        key=f"{form_suffix}_venue",
    )
    opponent = st.text_input(
        "Opponent",
        value=selected_fixture.opponent if selected_fixture else "",
        placeholder="e.g. Riverside RFC",
        key=f"{form_suffix}_opponent",
    )
    submitted = st.form_submit_button(
        "Save changes" if is_editing else "Add fixture", type="primary"
    )

if submitted:
    try:
        if not venue.strip():
            raise ValueError("Venue is required.")
        if not opponent.strip():
            raise ValueError("Opponent is required.")

        fixture = Fixture(
            id=selected_fixture.id if selected_fixture else None,
            date=fixture_date,
            venue=venue.strip(),
            opponent=opponent.strip(),
        )
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not DATA_FILE.exists():
            DATA_FILE.write_text("[]", encoding="utf-8")
        if is_editing:
            update_fixture(fixture, DATA_FILE)
        else:
            add_fixture(fixture, DATA_FILE)
    except (ValidationError, ValueError) as error:
        message = error.errors()[0]["msg"] if isinstance(error, ValidationError) else str(error)
        st.error(f"Please correct the fixture details: {message}")
    except OSError:
        st.error("The fixture could not be saved. Please check the data file permissions.")
    else:
        st.success(
            f"Fixture against {fixture.opponent} was "
            f"{'updated' if is_editing else 'added'}."
        )
