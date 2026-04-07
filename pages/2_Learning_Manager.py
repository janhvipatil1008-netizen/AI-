"""
2_Learning_Manager.py — Streamlit UI for the Learning Management Agent.

HOW STREAMLIT MULTIPAGE WORKS:
--------------------------------
Streamlit automatically creates sidebar navigation when a 'pages/' folder
exists next to app.py. The filename prefix '2_' sets the sort order and
the name 'Learning_Manager' becomes the page label (underscores → spaces).

This page is completely independent of app.py — it has its own session
state, page config, and layout. The two pages share the same Python
process, so imports work the same way.

LAYOUT: Two columns
  Left (narrower)  — Progress dashboard + to-do list
  Right (wider)    — Chat with the Learning Coach
"""

import streamlit as st
from agents.learning_agent import LearningAgent
from config.prompts import CURRICULUM_TOPICS
from utils.ui_theme import inject_css
from utils.ui_helpers import safe_agent_chat, contextual_spinner

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI² — Learning Manager",
    page_icon="📚",
    layout="wide",
)
inject_css()

# ── Session state initialization ──────────────────────────────────────────────
# Runs only once per browser session (on first page load).
if "learning_agent" not in st.session_state:
    st.session_state.learning_agent = LearningAgent()

if "lm_messages" not in st.session_state:
    # Display list: [(role, content), ...] — mirrors agent history minus system msg
    st.session_state.lm_messages = []

if "last_handoff" not in st.session_state:
    st.session_state.last_handoff = None

if "reset_confirm" not in st.session_state:
    st.session_state.reset_confirm = False

# Shorthand for readability
agent = st.session_state.learning_agent

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.page_link("app.py", label="← Home")
    st.divider()
    st.title("🧭 Atlas")
    st.caption("Step 2 of the AI² Platform")
    st.divider()

    # Next topic suggestion (instant — no API call)
    st.subheader("Suggested Next Step")
    st.info(agent.suggest_next_topic())

    st.divider()

    # Reset chat (keeps all profile data)
    if st.button("🗑️ Reset Chat", use_container_width=True):
        agent.reset()
        st.session_state.lm_messages = []
        st.session_state.last_handoff = None
        st.rerun()

    # Reset all progress (destructive — needs confirmation)
    st.divider()
    if not st.session_state.reset_confirm:
        if st.button("⚠️ Reset All Progress", use_container_width=True):
            st.session_state.reset_confirm = True
            st.rerun()
    else:
        st.warning("This will erase ALL progress, todos, and notes. Are you sure?")
        col1, col2 = st.columns(2)
        if col1.button("Yes, reset", type="primary", use_container_width=True):
            # Rebuild a fresh profile and reinitialise the agent
            new_profile = agent._make_default_profile()
            from pathlib import Path
            import json
            Path(agent.PROFILE_PATH).write_text(json.dumps(new_profile, indent=2))
            st.session_state.learning_agent = LearningAgent()
            st.session_state.lm_messages = []
            st.session_state.last_handoff = None
            st.session_state.reset_confirm = False
            st.rerun()
        if col2.button("Cancel", use_container_width=True):
            st.session_state.reset_confirm = False
            st.rerun()

# ── Main layout: two columns ──────────────────────────────────────────────────
left_col, right_col = st.columns([2, 3])

# ════════════════════════════════════════════════════════════════════
# LEFT COLUMN — Progress Dashboard + To-Do List
# ════════════════════════════════════════════════════════════════════
with left_col:
    st.subheader("Learning Progress")

    progress = agent.get_progress()
    pct = progress["pct"]

    # Progress bar
    st.progress(pct / 100)
    st.caption(f"{len(progress['completed'])} / {progress['total']} topics complete ({pct}%)")

    st.divider()

    # ── Topic status sections ─────────────────────────────────────────
    # IN PROGRESS — expanded by default so it's immediately visible
    with st.expander(f"▶ In Progress ({len(progress['in_progress'])})", expanded=True):
        if progress["in_progress"]:
            for topic in progress["in_progress"]:
                col_a, col_b = st.columns([4, 1])
                col_a.markdown(f"**{topic}**")
                if col_b.button("Done ✓", key=f"done_{topic}"):
                    agent.set_topic_status(topic, "completed")
                    st.rerun()
        else:
            st.caption("No topics in progress. Click 'Start' on a pending topic below.")

    # PENDING
    with st.expander(f"⏳ Pending ({len(progress['pending'])})", expanded=False):
        if progress["pending"]:
            for topic in progress["pending"]:
                col_a, col_b = st.columns([4, 1])
                col_a.write(topic)
                if col_b.button("Start", key=f"start_{topic}"):
                    agent.set_topic_status(topic, "in_progress")
                    st.rerun()
        else:
            st.caption("No pending topics.")

    # COMPLETED
    with st.expander(f"✅ Completed ({len(progress['completed'])})", expanded=False):
        if progress["completed"]:
            for topic in progress["completed"]:
                col_a, col_b = st.columns([4, 1])
                col_a.markdown(f"~~{topic}~~")
                if col_b.button("Undo", key=f"undo_{topic}"):
                    agent.set_topic_status(topic, "pending")
                    st.rerun()
        else:
            st.caption("No completed topics yet. Keep going!")

    st.divider()

    # ── To-Do List ────────────────────────────────────────────────────
    st.subheader("To-Do List")

    # Add new to-do manually
    with st.form("add_todo_form", clear_on_submit=True):
        new_task = st.text_input("New task:", placeholder="e.g. Practice writing a FastAPI endpoint")
        submitted = st.form_submit_button("Add", use_container_width=True)
        if submitted and new_task.strip():
            agent.add_todo(new_task.strip())
            st.success("To-do added!", icon="✅")
            st.rerun()

    # Display pending to-dos
    pending_todos = agent.get_todos(status="pending")
    if pending_todos:
        for todo in pending_todos:
            col_a, col_b = st.columns([5, 1])
            col_a.markdown(f"- {todo['text']}")
            col_a.caption(f"  *{todo.get('topic', 'General')}*")
            if col_b.button("✓", key=f"td_{todo['id']}", help="Mark done"):
                agent.complete_todo(todo["id"])
                st.rerun()
    else:
        st.caption("No pending tasks. Ask the coach to add some!")

    # Completed to-dos (collapsed)
    done_todos = agent.get_todos(status="completed")
    if done_todos:
        with st.expander(f"Completed tasks ({len(done_todos)})"):
            for todo in done_todos:
                st.markdown(f"- ~~{todo['text']}~~")


# ════════════════════════════════════════════════════════════════════
# RIGHT COLUMN — Chat Interface
# ════════════════════════════════════════════════════════════════════
with right_col:
    st.subheader("Learning Coach")
    st.caption(
        "Ask me what to study next, how to find resources, or to track your progress."
    )

    # Show handoff banner if the previous message triggered one
    if st.session_state.last_handoff:
        handoff = st.session_state.last_handoff
        st.session_state.last_handoff = None  # clear after displaying
        if handoff["agent"] == "research":
            st.session_state["research_handoff_topic"] = handoff["topic"]
            st.info(
                f"Ready to research **{handoff['topic']}** in depth.",
                icon="🔬",
            )
            st.page_link("pages/3_Research_Agent.py", label="Go to Research Agent →", icon="🔬")

    # Render existing messages
    for role, content in st.session_state.lm_messages:
        with st.chat_message(role):
            st.markdown(content)

    # Welcome message if chat is empty
    if not st.session_state.lm_messages:
        with st.chat_message("assistant"):
            st.markdown(
                "👋 Hi! I'm your **Learning Coach**.\n\n"
                "I can help you:\n"
                "- **Plan** — *What should I study next?*\n"
                "- **Track** — *I finished Python basics*\n"
                "- **Organise** — *Add a todo: practice writing a FastAPI endpoint*\n"
                "- **Find resources** — *What are the best resources for RAG?*\n"
                "- **Take notes** — *Save a note that async is used for I/O-bound tasks*\n\n"
                "What would you like to work on today?"
            )

    # Chat input
    user_input = st.chat_input("Ask your learning coach...")

    if user_input:
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.lm_messages.append(("user", user_input))

        # Get response from agent (wrapped in error handling)
        with st.chat_message("assistant"):
            result = safe_agent_chat(
                agent, user_input, contextual_spinner("coach")
            )
            if result is None:
                st.stop()

            response, handoff = result

            # Filter out action token lines before displaying to the user.
            # We don't want "ACTION: COMPLETE_TOPIC | ..." to appear in the chat.
            display_lines = [
                line for line in response.splitlines()
                if not line.strip().startswith("ACTION:")
                and not line.strip().startswith("HANDOFF:")
            ]
            display_response = "\n".join(display_lines).strip()
            st.markdown(display_response)

        st.session_state.lm_messages.append(("assistant", display_response))

        # Store handoff for display on next rerun (above the chat)
        if handoff:
            st.session_state.last_handoff = handoff

        st.rerun()
