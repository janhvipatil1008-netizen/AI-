"""
3_Research_Agent.py — Redirects to the main workspace.

Research functionality has been merged into Atlas (Learning Coach + Research).
This file exists only to handle any direct links to the old page.
"""

import streamlit as st

st.set_page_config(page_title="AI² — Redirecting", page_icon="🤖", layout="wide")

st.session_state["active_agent"] = "atlas"
st.session_state["atlas_mode"]   = "research"
st.switch_page("pages/workspace.py")
