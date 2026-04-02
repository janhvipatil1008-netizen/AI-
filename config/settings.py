"""
settings.py — Central configuration for the AI² platform.

Everything that can change between environments (API keys, model names,
limits) lives here. All other files import from this module instead of
reading environment variables directly.
"""

import os
from dotenv import load_dotenv

# Load the .env file so os.getenv() can read our API key.
# load_dotenv() does nothing if .env doesn't exist — no errors.
load_dotenv()

# ── API Key ──────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# NOTE: Not required for core functionality. Only used by ask_chatgpt() in
# search_tools.py (Research Agent cross-reference). If missing, that tool
# returns a graceful error message instead of crashing.

# ── Model ─────────────────────────────────────────────────────────────────────
# gpt-4o-mini is fast and cheap — great for learning and iteration.
# Change this to "gpt-4o" if you want higher quality responses.
MODEL_NAME = "gpt-4o-mini"

# ── Conversation limits ───────────────────────────────────────────────────────
# How many back-and-forth exchanges to keep in history.
# Each exchange = 1 user message + 1 assistant reply = 2 messages.
# Older exchanges are dropped to avoid hitting the token limit.
MAX_HISTORY_TURNS = 20

# ── Anthropic API Key (Step 3 — Research Agent) ───────────────────────────────
# We do NOT raise an error here if missing — the rest of the app (Coding Agent,
# Learning Manager) still works without it. The ResearchAgent raises its own
# clear error when you try to use it without the key.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# ── Skill levels ─────────────────────────────────────────────────────────────
SKILL_LEVELS = ["beginner", "intermediate", "advanced"]
DEFAULT_SKILL_LEVEL = "beginner"
