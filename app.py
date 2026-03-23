"""
app.py — Entry point for AI².

Skips the welcome UI. Auto-initialises a profile if one doesn't exist,
then immediately redirects to the workspace hub.
"""

import json
from datetime import date
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="AI²",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PROFILE_PATH = Path("data/learning_profile.json")

# Load or create profile
profile: dict = {}
if PROFILE_PATH.exists():
    try:
        profile = json.loads(PROFILE_PATH.read_text())
    except Exception:
        profile = {}

if not profile:
    # First run — create a default profile
    profile = {
        "user_name":       "Learner",
        "skill_level":     "beginner",
        "selected_roles":  ["aipm", "evals", "context"],
        "xp":              0,
        "streak":          1,
        "last_login":      str(date.today()),
        "topics":          {},
        "todos":           [],
        "goals":           [],
        "syllabus_progress": {},
    }
    PROFILE_PATH.parent.mkdir(exist_ok=True)
    PROFILE_PATH.write_text(json.dumps(profile, indent=2))

# Update streak + last_login
today = str(date.today())
last  = profile.get("last_login", today)
if last != today:
    try:
        from datetime import date as _date
        delta = (_date.today() - _date.fromisoformat(last)).days
        profile["streak"] = (profile.get("streak", 0) + 1) if delta == 1 else 1
    except Exception:
        profile["streak"] = 1
    profile["last_login"] = today
    PROFILE_PATH.write_text(json.dumps(profile, indent=2))

# Seed session state and go straight to the hub
st.session_state.logged_in   = True
st.session_state.user_name   = profile.get("user_name", "Learner")
st.session_state.skill_level = profile.get("skill_level", "beginner")
st.session_state._ws_xp      = profile.get("xp", 0)
st.session_state._ws_streak  = profile.get("streak", 1)
st.switch_page("pages/workspace.py")
