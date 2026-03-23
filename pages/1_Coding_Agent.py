"""
1_Coding_Agent.py — Forge: AI Coding Tutor
"""

import streamlit as st
from agents.coding_agent import CodingAgent
from config.prompts import SKILL_DESCRIPTIONS
from config.settings import SKILL_LEVELS
from utils.ui_theme import inject_css

st.set_page_config(
    page_title="AI² — Forge",
    page_icon="💻",
    layout="wide",
)
inject_css()

if "agent" not in st.session_state:
    st.session_state.agent = CodingAgent(skill_level="beginner")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "skill_detected" not in st.session_state:
    st.session_state.skill_detected = False

with st.sidebar:
    st.title("💻 Forge")
    st.caption("AI Coding Tutor")
    st.divider()

    st.subheader("Your Skill Level")
    selected_level = st.radio(
        label="Select your level:",
        options=SKILL_LEVELS,
        index=SKILL_LEVELS.index(st.session_state.agent.skill_level),
        format_func=lambda x: x.capitalize(),
        key="skill_radio",
    )
    st.caption(SKILL_DESCRIPTIONS[selected_level])

    if selected_level != st.session_state.agent.skill_level:
        st.session_state.agent.set_skill_level(selected_level)
        st.session_state.skill_detected = True

    st.divider()

    auto_detect = st.checkbox(
        "Auto-detect level from first message",
        value=not st.session_state.skill_detected,
        help="The agent will guess your level from your first message.",
    )

    st.divider()

    if st.button("🗑️ New Chat", use_container_width=True):
        st.session_state.agent.reset()
        st.session_state.messages = []
        st.session_state.skill_detected = False
        st.rerun()

    st.divider()

    with st.expander("📚 Topics I Can Teach"):
        st.markdown("""
- Python (functions, OOP, async)
- APIs with requests / httpx
- Data with pandas & numpy
- Prompt engineering
- OpenAI & Claude SDKs
- RAG & vector databases
- AI agents & function calling
- FastAPI, Flask, Streamlit
- Git, Docker
- AI system design & evals
        """)

    st.divider()
    st.page_link("app.py", label="← Back to Home")

st.title("Forge — AI Coding Tutor")
st.caption(
    f"Currently in **{st.session_state.agent.skill_level.capitalize()}** mode. "
    "Change your level in the sidebar anytime."
)

for role, content in st.session_state.messages:
    with st.chat_message(role):
        st.markdown(content)

if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown(
            "👋 Hi! I'm **Forge**, your AI Coding Tutor.\n\n"
            "I'll help you build AI applications from scratch — Python, APIs, LLMs, RAG, agents, and more.\n\n"
            "What would you like to build today?"
        )

user_input = st.chat_input("Ask me anything about AI coding...")

if user_input:
    if auto_detect and not st.session_state.skill_detected:
        detected_level = st.session_state.agent.detect_skill_level(user_input)
        st.session_state.agent.set_skill_level(detected_level)
        st.session_state.skill_detected = True
        st.session_state.pending_message = user_input
        st.rerun()

    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append(("user", user_input))

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.agent.chat(user_input)
        st.markdown(response)
    st.session_state.messages.append(("assistant", response))

if "pending_message" in st.session_state:
    pending = st.session_state.pop("pending_message")
    with st.chat_message("user"):
        st.markdown(pending)
    st.session_state.messages.append(("user", pending))
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.agent.chat(pending)
        st.markdown(response)
    st.session_state.messages.append(("assistant", response))
