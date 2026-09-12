from html import escape
from pathlib import Path

import streamlit as st
from pydantic import ValidationError

from rugby_selector.services.fixture_service import load_fixtures


DATA_FILE = Path(__file__).resolve().parents[3] / "data" / "fixtures.json"


st.set_page_config(page_title="Fixtures | Rugby Selector", page_icon="🏉")
st.title("Fixtures")
st.caption("Your fixtures, with the newest matches shown first.")

try:
    fixtures = load_fixtures(DATA_FILE) if DATA_FILE.exists() else []
except (OSError, ValidationError, ValueError):
    st.error("The fixture list could not be loaded. Please check the saved fixture data.")
    fixtures = []

fixtures.sort(key=lambda fixture: fixture.date, reverse=True)

st.page_link("pages/3_Add_Fixture.py", label="Add or edit a fixture")

if not fixtures:
    st.info("No fixtures have been added yet.")
else:
    fixture_rows = "".join(
        f"""
        <tr>
            <td><a href="/add-fixture?fixture_id={fixture.id}" target="_self">Edit</a></td>
            <td>{escape(fixture.date.strftime("%d %b %Y"))}</td>
            <td>{escape(fixture.opponent)}</td>
            <td>{escape(fixture.venue)}</td>
            <td><a href="/manage-availability?fixture_id={fixture.id}" target="_self">Edit Availability</a></td>
            <td><a href="/select-team?fixture_id={fixture.id}" target="_self">Team Selection</a></td>
            <td><a href="/fixture-scores?fixture_id={fixture.id}" target="_self">Scores</a></td>
        </tr>
        """
        for fixture in fixtures
    )
    st.markdown(
        f"""
        <table class="fixture-table">
            <thead>
                <tr>
                    <th></th>
                    <th>Date</th>
                    <th>Opponent</th>
                    <th>Venue</th>
                    <th></th>
                    <th></th>
                    <th></th>
                </tr>
            </thead>
            <tbody>{fixture_rows}</tbody>
        </table>
        <style>
        .fixture-table {{
            width: 100%;
            border-collapse: collapse;
            border: 1px solid #d1d5db;
            color: var(--text-color);
            font-size: 1rem;
        }}
        .fixture-table th,
        .fixture-table td {{
            padding: 0.55rem 0.75rem;
            border: 1px solid #e5e7eb;
            text-align: left;
        }}
        .fixture-table th {{
            background-color: #f0f2f6;
            font-weight: 700;
        }}
        .fixture-table tbody tr:nth-child(even) {{
            background-color: #f9fafb;
        }}
        .fixture-table a {{
            color: #0066cc;
            text-decoration: underline;
        }}
        .fixture-table a:hover {{
            color: #004499;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
