"""
ui_helpers.py — Shared UX utilities for AI² pages.

Centralises patterns that were previously copy-pasted (or missing entirely)
across all pages:
  - safe_agent_chat()    wraps agent.chat() with error handling
  - contextual_spinner() returns mode-appropriate spinner text
  - show_xp_toast()      surfaces XP awards as visible toasts
  - confirm_destructive() standardised 2-step confirmation pattern
"""

from __future__ import annotations

from typing import Any

import streamlit as st

# ── Spinner text ────────────────────────────────────────────────────────────────

_SPINNER_MAP: dict[str, str] = {
    # Learning / Atlas
    "coach":    "Planning your next step…",
    "atlas":    "Thinking…",
    "research": "Researching…",
    # Practice / Dojo
    "quiz":       "Grading your answer…",
    "challenge":  "Reviewing your solution…",
    "interview":  "Evaluating your response…",
    "dojo":       "Thinking…",
    # Ideas / Spark
    "brainstorm": "Generating ideas…",
    "brief":      "Building your project brief…",
    "feedback":   "Evaluating your idea…",
    "spark":      "Thinking…",
    # Fallback
    "default":  "Thinking…",
}


def contextual_spinner(mode: str) -> str:
    """Return a human-readable spinner message for the given agent mode."""
    return _SPINNER_MAP.get(mode, _SPINNER_MAP["default"])


# ── Safe agent chat ─────────────────────────────────────────────────────────────

def safe_agent_chat(
    agent: Any,
    user_input: str,
    spinner_text: str = "Thinking…",
) -> tuple | None:
    """
    Call agent.chat(user_input) safely.

    Returns the tuple (response, extra) from the agent on success.
    On any exception, renders a user-facing st.error() and returns None
    so the caller can do:

        result = safe_agent_chat(agent, user_input, spinner_text)
        if result is None:
            st.stop()
        response, handoff = result
    """
    try:
        with st.spinner(spinner_text):
            return agent.chat(user_input)
    except Exception as exc:
        etype = type(exc).__name__
        # Surface a friendly, actionable error — don't just crash the page.
        if "AuthenticationError" in etype or "api_key" in str(exc).lower():
            st.error(
                "**API key error** — the Anthropic API key is missing or invalid. "
                "Check your `.env` file and restart the app.",
                icon="🔑",
            )
        elif "RateLimitError" in etype or "rate_limit" in str(exc).lower():
            st.error(
                "**Rate limit reached** — too many requests. Wait a moment then try again.",
                icon="⏳",
            )
        elif "Timeout" in etype or "timeout" in str(exc).lower():
            st.error(
                "**Request timed out** — the AI took too long to respond. Try again.",
                icon="⌛",
            )
        else:
            st.error(
                f"**Something went wrong** — {etype}: {exc}  \n"
                "If this keeps happening, restart the app.",
                icon="⚠️",
            )
        return None


# ── XP toasts ───────────────────────────────────────────────────────────────────

def show_xp_toast(amount: int, reason: str = "") -> None:
    """Show a brief toast notifying the user they earned XP."""
    msg = f"⚡ +{amount} XP"
    if reason:
        msg += f" — {reason}"
    st.toast(msg)


# ── Destructive action confirmation ────────────────────────────────────────────

def confirm_destructive(
    label: str,
    confirm_key: str,
    danger_text: str = "This action cannot be undone.",
) -> bool:
    """
    Two-step confirmation pattern for destructive actions.

    First click sets a flag and shows a warning; second click actually proceeds.
    Returns True only when the user has confirmed.

    Usage:
        if confirm_destructive("Delete idea", "del_idea_42"):
            agent.delete_idea(idea_id)
            st.rerun()
    """
    pending_key = f"_confirm_pending_{confirm_key}"

    if not st.session_state.get(pending_key):
        if st.button(label, key=confirm_key):
            st.session_state[pending_key] = True
            st.rerun()
        return False
    else:
        st.warning(f"⚠️ {danger_text}")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Yes, proceed", key=f"{confirm_key}_yes", type="primary"):
                st.session_state[pending_key] = False
                return True
        with col_no:
            if st.button("Cancel", key=f"{confirm_key}_no"):
                st.session_state[pending_key] = False
                st.rerun()
        return False
