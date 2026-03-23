"""
5_Idea_Agent.py — Streamlit UI for the Idea Generation Agent (Step 5).

WHAT THIS PAGE DOES:
---------------------
Provides a chat interface for brainstorming AI project ideas in three modes:
  - Brainstorm:      Generates 3-5 project ideas based on your interests
  - Project Brief:   Turns an idea into a structured, actionable build plan
  - Idea Feedback:   Scores your own idea honestly (feasibility, scope, etc.)

KEY CONCEPTS SHOWN HERE:
--------------------------
  - Temperature changes per mode (1.0 brainstorm, 0.3 brief, 0.5 feedback)
    — same model, completely different output character
  - Few-shot prompting in the system prompts drives consistent formatting
  - Action tokens trigger idea saves silently (user sees notification, not raw token)
  - Saved ideas persist across sessions in data/ideas.json

LAYOUT:
  Sidebar — mode, skill level, saved ideas library with delete buttons, reset
  Main    — full-width chat, welcome message, idea-saved notifications
"""

import streamlit as st
from agents.idea_agent import IdeaAgent
from utils.ui_theme import inject_css

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI² — Idea Agent",
    page_icon="💡",
    layout="wide",
)
inject_css()

# ── Session state initialization ──────────────────────────────────────────────
if "idea_agent" not in st.session_state:
    st.session_state.idea_agent = IdeaAgent()

if "ia_messages" not in st.session_state:
    # Display list: [(role, content), ...]
    st.session_state.ia_messages = []

if "ia_last_save" not in st.session_state:
    # Stores the most recent save notification so we can display it once
    st.session_state.ia_last_save = None

# Shorthand
agent = st.session_state.idea_agent

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.page_link("app.py", label="← Home")
    st.divider()
    st.title("💡 Spark")
    st.caption("Step 5 of the AI² Platform")
    st.divider()

    # ── Mode selector ─────────────────────────────────────────────────────────
    mode_options = ["Brainstorm", "Project Brief", "Idea Feedback"]
    mode_keys = {
        "Brainstorm":    "brainstorm",
        "Project Brief": "brief",
        "Idea Feedback": "feedback",
    }

    current_mode_label = {
        "brainstorm": "Brainstorm",
        "brief":      "Project Brief",
        "feedback":   "Idea Feedback",
    }.get(agent.mode, "Brainstorm")

    selected_mode_label = st.radio(
        "Mode",
        options=mode_options,
        index=mode_options.index(current_mode_label),
    )
    selected_mode = mode_keys[selected_mode_label]

    # Apply mode change immediately (no session guard — unlike Practice Agent)
    if selected_mode != agent.mode:
        agent.set_mode(selected_mode)
        st.session_state.ia_messages = []
        st.session_state.ia_last_save = None
        st.rerun()

    st.divider()

    # ── Skill level selector ──────────────────────────────────────────────────
    skill_options = ["beginner", "intermediate", "advanced"]
    selected_skill = st.radio(
        "Skill level",
        options=skill_options,
        index=skill_options.index(agent.skill_level) if agent.skill_level in skill_options else 0,
        format_func=str.capitalize,
    )
    if selected_skill != agent.skill_level:
        agent.set_skill_level(selected_skill)
        # Don't reset chat — just update language complexity going forward

    st.divider()

    # ── Saved Ideas library ───────────────────────────────────────────────────
    ideas = agent.get_ideas()
    idea_count = len(ideas)

    st.subheader(f"My Saved Ideas {'(' + str(idea_count) + ')' if idea_count else ''}")

    if ideas:
        for idea in ideas:
            with st.expander(idea["title"], expanded=False):
                st.markdown(f"**Topic:** {idea['topic']}")
                st.markdown(f"**Description:** {idea['description']}")
                st.caption(
                    f"Created in *{idea['mode_created_in']}* mode "
                    f"· {idea['saved_at'][:10]}"
                )
                if st.button("🗑️ Delete", key=f"del_{idea['id']}", use_container_width=True):
                    agent.delete_idea(idea["id"])
                    st.rerun()
    else:
        st.caption("No ideas saved yet.")
        st.caption(
            "Ideas are saved automatically when the AI suggests one "
            "you choose to keep (Brainstorm or Brief mode)."
        )

    st.divider()

    # ── Reset button ──────────────────────────────────────────────────────────
    if st.button("🗑️ Reset Chat", use_container_width=True):
        agent.reset()
        st.session_state.ia_messages = []
        st.session_state.ia_last_save = None
        st.rerun()

    st.caption("Resetting chat does **not** delete your saved ideas.")

# ── Main chat area ────────────────────────────────────────────────────────────

# Mode explanation banner
mode_info = {
    "brainstorm": (
        "🧠 **Brainstorm mode** — Tell me your interests and I'll generate 3-5 concrete "
        "AI project ideas tailored to you. *(temperature=1.0 → creative & varied)*"
    ),
    "brief": (
        "📋 **Project Brief mode** — Describe an idea and I'll build a full structured "
        "plan: tech stack, implementation steps, timeline, risks. *(temperature=0.3 → structured & consistent)*"
    ),
    "feedback": (
        "🔍 **Idea Feedback mode** — Pitch your own idea and I'll score it honestly "
        "on feasibility, scope, learning value, and real-world usefulness. *(temperature=0.5 → balanced)*"
    ),
}
st.info(mode_info[agent.mode])

# Welcome message if chat is empty
if not st.session_state.ia_messages:
    with st.chat_message("assistant"):
        welcome = {
            "brainstorm": (
                "👋 Hi! I'm your **Idea Agent** in Brainstorm mode.\n\n"
                "Tell me:\n"
                "- What topics in AI interest you?\n"
                "- What's your goal — learning, portfolio, or solving a real problem?\n"
                "- Any tech you already know or want to use?\n\n"
                "I'll generate 3-5 concrete project ideas you could actually build. "
                "Pick one and I'll save it to your ideas library!"
            ),
            "brief": (
                "👋 Hi! I'm your **Idea Agent** in Project Brief mode.\n\n"
                "Describe an AI project idea — even a rough one — and I'll turn it into "
                "a structured build plan with:\n"
                "- Problem statement\n"
                "- Recommended tech stack (with reasons)\n"
                "- 5 implementation steps\n"
                "- Estimated time and learning outcomes\n"
                "- Risks to watch out for\n\n"
                "What idea would you like to plan out?"
            ),
            "feedback": (
                "👋 Hi! I'm your **Idea Agent** in Idea Feedback mode.\n\n"
                "Pitch me your project idea and I'll evaluate it honestly "
                "across four dimensions:\n"
                "- **Feasibility** — Can you actually build this?\n"
                "- **Scope** — Is it the right size?\n"
                "- **Learning Value** — Will you learn real skills?\n"
                "- **Real-world Usefulness** — Does it solve a genuine problem?\n\n"
                "I'm a senior engineer, not a cheerleader — you'll get a genuine score "
                "and a clear verdict. What's your idea?"
            ),
        }[agent.mode]
        st.markdown(welcome)

# Render existing messages
for role_label, content in st.session_state.ia_messages:
    with st.chat_message(role_label):
        st.markdown(content)

# Show idea-saved notification after the latest assistant message
last_save = st.session_state.ia_last_save
if last_save:
    st.success(f"💡 Idea saved: **{last_save['idea']['title']}**")
    # Clear after one render so it doesn't persist on next rerun
    st.session_state.ia_last_save = None

# ── Chat input ────────────────────────────────────────────────────────────────
placeholder = {
    "brainstorm": "Tell me your interests or ask for ideas...",
    "brief":      "Describe the idea you want to plan out...",
    "feedback":   "Pitch your idea and I'll evaluate it...",
}.get(agent.mode, "Type your message...")

user_input = st.chat_input(placeholder)

if user_input:
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.ia_messages.append(("user", user_input))

    # Get response
    with st.chat_message("assistant"):
        spinner_msg = {
            "brainstorm": "Generating ideas...",
            "brief":      "Building your project brief...",
            "feedback":   "Evaluating your idea...",
        }.get(agent.mode, "Thinking...")
        with st.spinner(spinner_msg):
            reply, notification = agent.chat(user_input)

        # Strip the ACTION token line from the displayed reply
        # (the user sees the idea saved notification instead)
        display_reply = "\n".join(
            line for line in reply.splitlines()
            if not line.strip().startswith("ACTION:")
        ).strip()
        st.markdown(display_reply)

    st.session_state.ia_messages.append(("assistant", display_reply))

    # Store notification — will render on next rerun above the chat input
    if notification:
        st.session_state.ia_last_save = notification

    st.rerun()
