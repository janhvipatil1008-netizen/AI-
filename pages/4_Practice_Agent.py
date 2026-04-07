"""
4_Practice_Agent.py — Streamlit UI for the Practice Agent (Step 4).

WHAT THIS PAGE DOES:
---------------------
Provides a practice interface with three modes:
  - Quiz             — Multiple-choice questions on any AI topic
  - Coding Challenge — A coding task with AI-powered code review
  - Mock Interview   — Simulated AI Builder or AI PM interview

LAYOUT:
  Sidebar — mode/topic/difficulty/role selector, Start button, stats expander, reset
  Main    — full-width chat (same pattern as Research Agent)

HOW THE RESULT DICT WORKS:
---------------------------
PracticeAgent.chat() returns a tuple: (reply_text, result_dict_or_None)
When result_dict is not None, the AI has graded something.
The page uses result_dict to show ✅/❌ callouts and update the session banner.
When result_dict["session_complete"] is True, we show a summary + balloons.
"""

import streamlit as st
from agents.practice_agent import PracticeAgent
from utils.ui_theme import inject_css
from utils.ui_helpers import contextual_spinner

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI² — Practice Agent",
    page_icon="🎯",
    layout="wide",
)
inject_css()

# ── Session state initialization ──────────────────────────────────────────────
if "practice_agent" not in st.session_state:
    st.session_state.practice_agent = PracticeAgent()

if "pa_messages" not in st.session_state:
    # Display list: [(role, content), ...]
    st.session_state.pa_messages = []

if "pa_last_result" not in st.session_state:
    # Stores the most recent result dict so we can display the callout
    st.session_state.pa_last_result = None

if "pa_mode_confirm" not in st.session_state:
    # Used for the "changing mode will end session" confirmation
    st.session_state.pa_mode_confirm = False

if "pa_pending_mode" not in st.session_state:
    st.session_state.pa_pending_mode = None

# Shorthand
agent = st.session_state.practice_agent

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.page_link("app.py", label="← Home")
    st.divider()
    st.title("🎯 Dojo")
    st.caption("Step 4 of the AI² Platform")
    st.divider()

    # ── Mode selector ─────────────────────────────────────────────────────────
    mode_options = ["Quiz", "Coding Challenge", "Mock Interview"]
    mode_keys = {"Quiz": "quiz", "Challenge": "challenge", "Mock Interview": "interview",
                 "Coding Challenge": "challenge"}

    selected_mode_label = st.radio(
        "Mode",
        options=mode_options,
        index=mode_options.index(
            "Quiz" if agent.mode == "quiz"
            else "Coding Challenge" if agent.mode == "challenge"
            else "Mock Interview"
        ),
    )
    selected_mode = mode_keys[selected_mode_label]

    # ── Mode change protection ────────────────────────────────────────────────
    # If the learner changes mode mid-session, ask them to confirm.
    # NOTE: do NOT call st.rerun() here — let the page re-render naturally so
    # the confirmation dialog is visible immediately (avoids UI flicker).
    if selected_mode != agent.mode and agent.session_active:
        if not st.session_state.pa_mode_confirm:
            st.session_state.pa_pending_mode = selected_mode
            st.session_state.pa_mode_confirm = True

    if st.session_state.pa_mode_confirm:
        st.warning("Changing mode will end your current session.")
        col1, col2 = st.columns(2)
        if col1.button("Yes, switch", use_container_width=True):
            agent.reset()
            agent.set_mode(st.session_state.pa_pending_mode)
            st.session_state.pa_messages = []
            st.session_state.pa_last_result = None
            st.session_state.pa_mode_confirm = False
            st.session_state.pa_pending_mode = None
            st.rerun()
        if col2.button("Cancel", use_container_width=True):
            st.session_state.pa_mode_confirm = False
            st.session_state.pa_pending_mode = None
            st.rerun()
    elif not agent.session_active:
        # No session running — apply mode change immediately
        agent.set_mode(selected_mode)

    st.divider()

    # ── Topic selector (all modes, optional) ─────────────────────────────────
    topic = st.text_input(
        "Topic",
        value=agent.topic,
        placeholder="e.g. diffusion models, RLHF, AI safety, evals, vector databases",
        help="Enter any AI topic. Leave blank for mixed practice across all AI topics.",
        disabled=agent.session_active,
    )
    if not agent.session_active:
        agent.set_topic(topic)

    difficulty_options = ["Beginner", "Intermediate", "Advanced"]
    difficulty = st.radio(
        "Difficulty",
        options=difficulty_options,
        index=difficulty_options.index(agent.difficulty) if agent.difficulty in difficulty_options else 1,
        horizontal=True,
        disabled=agent.session_active,
    )
    if not agent.session_active:
        agent.set_difficulty(difficulty)

    # ── Role selector (always shown — relevant to interview, optional for others) ──
    role = st.radio(
        "Target role",
        options=["AI Builder", "AI PM"],
        index=0 if agent.role == "AI Builder" else 1,
    )
    if not agent.session_active:
        agent.set_role(role)

    st.divider()

    # ── Start New Session button ──────────────────────────────────────────────
    mode_label = {
        "quiz": "Quiz",
        "challenge": "Coding Challenge",
        "interview": "Mock Interview",
    }.get(agent.mode, "Session")

    if st.button(f"▶ Start New {mode_label}", use_container_width=True, type="primary"):
        agent.reset()
        agent.set_mode(selected_mode)
        agent.set_topic(topic)
        agent.set_difficulty(difficulty)
        agent.set_role(role)

        with st.spinner("Setting up your session..."):
            opening = agent.start_session()

        st.session_state.pa_messages = [("assistant", opening)]
        st.session_state.pa_last_result = None
        st.rerun()

    st.divider()

    # ── Stats expander ────────────────────────────────────────────────────────
    with st.expander("📊 My Stats"):
        stats = agent.get_stats()

        q = stats["quiz"]
        if q["sessions"] > 0:
            st.markdown(f"**Quiz** — {q['sessions']} session(s)")
            st.markdown(f"Accuracy: **{q['accuracy_pct']}%** ({q['correct']}/{q['total_questions']} correct)")
        else:
            st.caption("No quiz sessions yet.")

        st.divider()

        c = stats["challenge"]
        if c["sessions"] > 0:
            st.markdown(f"**Coding Challenge** — {c['sessions']} session(s)")
            st.markdown(f"Avg score: **{c['avg_score']}/10**")
        else:
            st.caption("No challenge sessions yet.")

        st.divider()

        i = stats["interview"]
        if i["sessions"] > 0:
            st.markdown(f"**Mock Interview** — {i['sessions']} session(s)")
            for r_name, r_data in i["by_role"].items():
                if r_data["sessions"] > 0:
                    st.markdown(f"{r_name}: {r_data['sessions']} session(s), avg {r_data['avg_score']}/5")
        else:
            st.caption("No interview sessions yet.")

    st.divider()

    # ── Reset button ──────────────────────────────────────────────────────────
    if st.button("🗑️ Reset Chat", use_container_width=True):
        agent.reset()
        st.session_state.pa_messages = []
        st.session_state.pa_last_result = None
        st.rerun()

# ── Main chat area ────────────────────────────────────────────────────────────

# Active session badge
if agent.session_active:
    mode_badge = {
        "quiz": f"🎯 Quiz — {agent.difficulty} — {agent.get_topic_label()}",
        "challenge": f"💻 Coding Challenge — {agent.difficulty} — {agent.get_topic_label()}",
        "interview": f"🤝 Mock Interview — {agent.role} — {agent.difficulty} — {agent.get_topic_label()}",
    }.get(agent.mode, "")
    st.info(mode_badge)

# Welcome message if no session is active and no messages
if not st.session_state.pa_messages:
    with st.chat_message("assistant"):
        st.markdown(
            "👋 Hi! I'm your **Practice Agent**.\n\n"
            "I can assess your AI knowledge in three ways:\n\n"
            "**🎯 Quiz** — I ask 10 multiple-choice questions on any AI topic you choose, "
            "or across a mixed set of AI topics if you leave the topic blank. "
            "Answer with A, B, C, or D. I'll grade each one and explain the answer.\n\n"
            "**💻 Coding Challenge** — I give you a real coding task. "
            "Paste your solution and I'll review it like a senior engineer would.\n\n"
            "**🤝 Mock Interview** — I play a hiring manager at an AI company. "
            "Choose AI Builder (technical) or AI PM (product) and practice "
            "answering interview questions with honest feedback.\n\n"
            "**Pick a mode, enter any AI topic or leave it blank for mixed practice, and click Start!**"
        )

# Render existing messages
for role_label, content in st.session_state.pa_messages:
    with st.chat_message(role_label):
        st.markdown(content)

# Show the result callout AFTER the last assistant message
last_result = st.session_state.pa_last_result
if last_result:
    if agent.mode == "quiz":
        if last_result.get("correct"):
            st.success("✅ Correct!")
        else:
            st.error("❌ Incorrect")
    elif agent.mode == "challenge":
        score = last_result.get("score", 0)
        max_score = last_result.get("max_score", 10)
        st.info(f"Score: **{score}/{max_score}**")
    elif agent.mode == "interview":
        score = last_result.get("score", 0)
        max_score = last_result.get("max_score", 5)
        st.info(f"Score: **{score}/{max_score}**")

    # Session complete banner
    if last_result.get("session_complete"):
        st.balloons()
        with st.expander("🎉 Session Complete! See your results", expanded=True):
            session_stats = agent.get_stats()
            if agent.mode == "quiz":
                q = session_stats["quiz"]
                st.markdown(
                    f"**Quiz finished!** You scored "
                    f"**{q['correct']}/{q['total_questions']}** "
                    f"({q['accuracy_pct']}%) overall."
                )
            elif agent.mode == "challenge":
                c = session_stats["challenge"]
                st.markdown(
                    f"**Challenge complete!** "
                    f"Your average score across all challenges: **{c['avg_score']}/10**."
                )
            elif agent.mode == "interview":
                i = session_stats["interview"]
                r_data = i["by_role"].get(agent.role, {})
                st.markdown(
                    f"**Interview complete!** "
                    f"{agent.role} average score: **{r_data.get('avg_score', 0)}/5**."
                )

        col1, col2 = st.columns(2)
        if col1.button("▶ Start Another Session", use_container_width=True, type="primary"):
            agent.reset()
            with st.spinner("Setting up your next session..."):
                opening = agent.start_session()
            st.session_state.pa_messages = [("assistant", opening)]
            st.session_state.pa_last_result = None
            st.rerun()
        if col2.button("Change Mode/Topic", use_container_width=True):
            agent.reset()
            st.session_state.pa_messages = []
            st.session_state.pa_last_result = None
            st.rerun()

# ── Chat input (only shown during active session) ─────────────────────────────
if agent.session_active and not (last_result and last_result.get("session_complete")):
    placeholder = {
        "quiz": "Type A, B, C, or D...",
        "challenge": "Paste your code solution here...",
        "interview": "Type your answer...",
    }.get(agent.mode, "Type your response...")

    user_input = st.chat_input(placeholder)

    if user_input:
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.pa_messages.append(("user", user_input))

        # Get response — replies is a list: [grade] or [grade, next_question]
        spinner_msg = contextual_spinner(agent.mode)
        try:
            with st.spinner(spinner_msg):
                replies, result = agent.chat(user_input)
        except Exception as exc:
            etype = type(exc).__name__
            if "AuthenticationError" in etype or "api_key" in str(exc).lower():
                st.error("**API key error** — check your `.env` file and restart.", icon="🔑")
            elif "RateLimitError" in etype or "rate_limit" in str(exc).lower():
                st.error("**Rate limit reached** — wait a moment then try again.", icon="⏳")
            elif "Timeout" in etype or "timeout" in str(exc).lower():
                st.error("**Request timed out** — try again.", icon="⌛")
            else:
                st.error(f"**Something went wrong** — {etype}: {exc}", icon="⚠️")
            st.stop()

        for r in replies:
            with st.chat_message("assistant"):
                st.markdown(r)
            st.session_state.pa_messages.append(("assistant", r))

        st.session_state.pa_last_result = result
        st.rerun()
