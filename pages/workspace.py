"""
workspace.py — Main AI² workspace.

Everything happens here after the user enters the lab.

Layout:
  ┌─────────────────────────────────────────────────────────┐
  │  AI²  │ 💻Forge │ 🧭Atlas │ 🎯Dojo │ 💡Spark │ 🔥3 ⚡240XP  J │
  ├─────────────────────────────────────────────────────────┤
  │                                                         │
  │   [Dashboard] or [Agent View]                           │
  │                                                         │
  └─────────────────────────────────────────────────────────┘

Session state keys used here:
  logged_in       — set by app.py; if False → redirect to welcome
  user_name       — learner's name
  skill_level     — beginner / intermediate / advanced
  active_agent          — None (dashboard) or "forge"/"atlas"/"dojo"/"spark"
  forge_agent           — CodingAgent instance
  fa_messages           — [(role, content), ...] for Forge
  atlas_agent           — LearningAgent instance
  la_messages           — [(role, content), ...]
  la_last_handoff       — handoff dict or None
  la_reset_confirm      — bool
  atlas_mode            — "coach" | "research"
  atlas_research_agent  — ResearchAgent instance (embedded in Atlas)
  ar_messages           — [(role, content), ...] for Atlas research mode
  atlas_research_handoff— pending topic string or None
  dojo_agent            — PracticeAgent instance
  da_messages     — [(role, content), ...]
  da_last_result  — result dict or None
  da_mode_confirm — bool
  da_pending_mode — str or None
  spark_agent     — IdeaAgent instance
  sa_messages     — [(role, content), ...]
  sa_last_save    — save notification dict or None
"""

import json
from datetime import date
from pathlib import Path

import streamlit as st
from utils.ui_theme import inject_css, inject_welcome_css

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI² — Workspace",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()
inject_welcome_css()

# Hide sidebar entirely in workspace
st.markdown("""
<style>
[data-testid="stSidebar"]   { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
/* Primary buttons = active/selected state (nav tabs, skill cards, start buttons) */
.stButton > button[kind="primary"] {
    background: rgba(137, 220, 235, 0.10) !important;
    border: 1px solid rgba(137,220,235,0.45) !important;
    color: #89DCEB !important;
    box-shadow: 0 0 12px rgba(137,220,235,0.12) !important;
}
.stButton > button[kind="primary"]:hover {
    background: rgba(137, 220, 235, 0.18) !important;
    box-shadow: 0 0 18px rgba(137,220,235,0.2) !important;
}
/* Remove column divider in header — it looks odd for nav */
.ws-header-cols [data-testid="column"] + [data-testid="column"] {
    border-left: none !important;
    padding-left: 0 !important;
}
/* Tighten top padding */
[data-testid="stMain"] > div:first-child { padding-top: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ── Session guard ─────────────────────────────────────────────────────────────
if not st.session_state.get("logged_in"):
    st.switch_page("app.py")

# ── Profile helpers ───────────────────────────────────────────────────────────
PROFILE_PATH = Path("data/learning_profile.json")
IDEAS_PATH   = Path("data/ideas.json")


def _load_profile() -> dict:
    if PROFILE_PATH.exists():
        try:
            return json.loads(PROFILE_PATH.read_text())
        except Exception:
            pass
    return {}


def _save_profile(p: dict) -> None:
    PROFILE_PATH.parent.mkdir(exist_ok=True)
    PROFILE_PATH.write_text(json.dumps(p, indent=2, default=str))


def _award_xp(amount: int) -> None:
    """Add XP to profile and update session state."""
    p = _load_profile()
    p["xp"] = p.get("xp", 0) + amount
    _save_profile(p)
    st.session_state._ws_xp = p["xp"]


def _get_orchestrator():
    """
    Get or create the Orchestrator singleton for this browser session.

    WHY SINGLETON: The Orchestrator caches agent instances so their
    conversation histories persist across messages. Creating a new one
    on every rerun would lose all history.
    """
    if "orch_agent" not in st.session_state:
        from agents.orchestrator import Orchestrator
        st.session_state.orch_agent    = Orchestrator()
        st.session_state.orch_messages = []  # [(agent_key, role, content), ...]
    return st.session_state.orch_agent


# ── One-time streak update per session ────────────────────────────────────────
if not st.session_state.get("_ws_streak_checked"):
    p = _load_profile()
    today = str(date.today())
    last  = p.get("last_login", today)
    if last != today:
        try:
            delta = (date.today() - date.fromisoformat(last)).days
            p["streak"] = (p.get("streak", 0) + 1) if delta == 1 else 1
        except Exception:
            p["streak"] = 1
        p["last_login"] = today
        _save_profile(p)
    st.session_state._ws_xp            = p.get("xp", 0)
    st.session_state._ws_streak        = p.get("streak", 1)
    st.session_state._ws_streak_checked = True

# ── Active agent state ────────────────────────────────────────────────────────
if "active_agent" not in st.session_state:
    st.session_state.active_agent = None

# ── Header ────────────────────────────────────────────────────────────────────
profile = _load_profile()
user_name = profile.get("user_name") or st.session_state.get("user_name", "You")
xp        = st.session_state.get("_ws_xp", profile.get("xp", 0))
streak    = st.session_state.get("_ws_streak", profile.get("streak", 1))
initial   = user_name[0].upper() if user_name else "?"

AGENTS_META = [
    ("forge",    "💻", "Forge"),
    ("atlas",    "🧭", "Atlas"),
    ("dojo",     "🎯", "Dojo"),
    ("spark",    "💡", "Spark"),
    ("syllabus", "📋", "Syllabus"),
]

# Header row: [logo(1.5)] [5 nav buttons] [user pill(2)]
st.markdown('<div class="ws-header-cols">', unsafe_allow_html=True)
h_logo, h_nav1, h_nav2, h_nav3, h_nav4, h_nav5, h_user = st.columns(
    [1.5, 1.1, 1.1, 1.1, 1.1, 1.3, 2.0]
)
st.markdown('</div>', unsafe_allow_html=True)

with h_logo:
    if st.button("AI²", key="ws_logo_btn", use_container_width=True):
        st.session_state.active_agent = None
        st.rerun()

nav_cols = [h_nav1, h_nav2, h_nav3, h_nav4, h_nav5]
for col, (agent_key, icon, label) in zip(nav_cols, AGENTS_META):
    with col:
        if st.button(
            f"{icon} {label}",
            key=f"nav_{agent_key}",
            type="secondary",
            use_container_width=True,
        ):
            st.session_state.active_agent = agent_key
            st.switch_page("pages/agent_view.py")

with h_user:
    st.markdown(
        f"""
        <div class="ws-user" style="justify-content:flex-end; padding-top:6px;">
            <span class="streak-badge">🔥{streak}</span>
            <span class="xp-badge">⚡ {xp} XP</span>
            <div class="ws-avatar">{initial}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    "<div style='border-bottom:1px solid rgba(255,255,255,0.08); margin-bottom:24px;'></div>",
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def render_dashboard() -> None:
    topics    = profile.get("topics", {})
    completed = sum(1 for t in topics.values() if t.get("status") == "completed")
    total     = len(topics)
    pct       = round(completed / total * 100) if total else 0

    ideas_count = 0
    if IDEAS_PATH.exists():
        try:
            ideas_count = len(json.loads(IDEAS_PATH.read_text()))
        except Exception:
            pass

    # Welcome header
    st.markdown(
        f"""
        <div style="margin-bottom:28px;">
            <div style="font-family:'Inter',sans-serif; font-size:26px;
                        font-weight:700; color:#CDD6F4; letter-spacing:-0.01em;">
                Welcome back, {user_name}.
            </div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:12px;
                        color:#45475A; margin-top:8px; letter-spacing:0.04em;">
                {str(date.today())} &nbsp;·&nbsp; {streak}-day streak &nbsp;·&nbsp; {xp} XP earned
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Quick stats
    s1, s2, s3, s4 = st.columns(4, gap="small")
    stats = [
        (s1, str(completed),     "Topics Complete",   "#89DCEB"),
        (s2, f"{pct}%",          "Curriculum Done",   "#A78BFA"),
        (s3, str(xp),            "XP Earned",         "#FBBF24"),
        (s4, str(ideas_count),   "Ideas Saved",        "#F472B6"),
    ]
    for col, val, lbl, color in stats:
        with col:
            st.markdown(
                f"""
                <div class="dash-stat" style="border-top-color:{color};">
                    <div class="dash-stat-val" style="color:{color};">{val}</div>
                    <div class="dash-stat-lbl">{lbl}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── Mission Control chat ───────────────────────────────────────────────────
    st.markdown(
        """
        <div style="font-family:'Inter',sans-serif; font-size:18px; font-weight:700;
                    color:#CDD6F4; margin-bottom:4px;">
            🤖 Mission Control
        </div>
        <div style="font-family:'Inter',sans-serif; font-size:13px; color:#585B70;
                    margin-bottom:20px;">
            Just type — I'll route to the right agent automatically.
            Use the nav above to open an agent directly.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Agent badge styling: (icon, color, display name)
    _AGENT_BADGE = {
        "forge": ("💻", "#4A9EFF", "Forge — Coding Tutor"),
        "atlas": ("🧭", "#A78BFA", "Atlas — Learning Coach"),
        "dojo":  ("🎯", "#FBBF24", "Dojo — Practice Arena"),
        "spark": ("💡", "#F472B6", "Spark — Idea Generator"),
    }

    orch = _get_orchestrator()

    # Render recent messages
    for msg_agent_key, role, content in st.session_state.orch_messages[-12:]:
        with st.chat_message(role):
            if role == "assistant" and msg_agent_key in _AGENT_BADGE:
                icon, color, name = _AGENT_BADGE[msg_agent_key]
                st.markdown(
                    f'<span style="font-size:10px; color:{color}; '
                    f'font-family:\'JetBrains Mono\',monospace; '
                    f'letter-spacing:0.05em;">{icon} {name}</span>',
                    unsafe_allow_html=True,
                )
            st.markdown(content)

    orch_input = st.chat_input(
        "Ask anything — code help, what to study next, quiz me, project ideas...",
        key="orch_chat_input",
    )
    if orch_input:
        # Show user message immediately
        with st.chat_message("user"):
            st.markdown(orch_input)
        st.session_state.orch_messages.append(("", "user", orch_input))

        # Route + respond
        with st.chat_message("assistant"):
            with st.spinner("Routing to the right agent..."):
                agent_key, display, result = orch.chat(orch_input)
            icon, color, name = _AGENT_BADGE.get(agent_key, ("🤖", "#89DCEB", "AI²"))
            st.markdown(
                f'<span style="font-size:10px; color:{color}; '
                f'font-family:\'JetBrains Mono\',monospace; '
                f'letter-spacing:0.05em;">{icon} {name}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(display)

        st.session_state.orch_messages.append((agent_key, "assistant", display))

        # XP awards — same logic as individual agent views
        _award_xp(5)
        if result and isinstance(result, dict):
            if result.get("correct") is True:   # correct quiz answer
                _award_xp(10)
            if result.get("idea_saved"):         # Spark saved an idea
                _award_xp(20)

        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTER — always show the hub
# ═══════════════════════════════════════════════════════════════════════════════

render_dashboard()

