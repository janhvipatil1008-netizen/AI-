"""
agent_view.py — Agent detail view (Page 2 of AI²).

Reached via st.switch_page() from workspace.py when the learner
selects an agent. Reads active_agent from session state.
The ← Back button returns to workspace.py (the hub).
"""

import json
import re
from datetime import date
from pathlib import Path

import streamlit as st
from utils.ui_theme import inject_css, inject_welcome_css
from utils.ui_helpers import safe_agent_chat, contextual_spinner, show_xp_toast
from config.syllabus import (
    PHASES, ROLE_TRACKS, ROLE_SKILLS,
    get_progress, get_task_key, get_next_tasks, get_current_phase_id,
)

# ── Compiled regex for paper tag detection ─────────────────────────────────────
_SUGGEST_PAPERS_RE = re.compile(
    r'<!--\s*SUGGEST_PAPERS:\s*(.+?)\s*-->', re.IGNORECASE
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI² — Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()
inject_welcome_css()

st.markdown("""
<style>
[data-testid="stSidebar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
.ws-header-cols [data-testid="column"] + [data-testid="column"] {
    border-left: none !important;
    padding-left: 0 !important;
}
[data-testid="stMain"] > div:first-child { padding-top: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ── Session guards ─────────────────────────────────────────────────────────────
if not st.session_state.get("logged_in"):
    st.switch_page("app.py")

if not st.session_state.get("active_agent"):
    st.switch_page("pages/workspace.py")

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
    p = _load_profile()
    p["xp"] = p.get("xp", 0) + amount
    _save_profile(p)
    st.session_state._ws_xp = p["xp"]


# ── Profile data ──────────────────────────────────────────────────────────────
profile   = _load_profile()
user_name = profile.get("user_name") or st.session_state.get("user_name", "You")
xp        = st.session_state.get("_ws_xp", profile.get("xp", 0))
streak    = st.session_state.get("_ws_streak", profile.get("streak", 1))
initial   = user_name[0].upper() if user_name else "?"

# ── Slim header ───────────────────────────────────────────────────────────────
AGENT_LABELS = {
    "atlas":    "🧭 Atlas — Learning Coach",
    "dojo":     "🎯 Dojo — Practice Arena",
    "spark":    "💡 Spark — Idea Generator",
    "syllabus": "📋 Career Roadmap",
}

active = st.session_state.get("active_agent", "atlas")

st.markdown('<div class="ws-header-cols">', unsafe_allow_html=True)
h_back, h_title, h_user = st.columns([1.2, 5, 2])
st.markdown('</div>', unsafe_allow_html=True)

with h_back:
    if st.button("← Hub", key="av_back", use_container_width=True):
        st.switch_page("pages/workspace.py")

with h_title:
    st.markdown(
        f'<div style="font-family:\'Inter\',sans-serif; font-size:18px; '
        f'font-weight:700; color:#CDD6F4; padding-top:6px;">'
        f'AI<span style="color:#89DCEB;">²</span>'
        f'&nbsp;&nbsp;·&nbsp;&nbsp;'
        f'{AGENT_LABELS.get(active, active)}</div>',
        unsafe_allow_html=True,
    )

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
# PAPERS — helpers shared by Atlas Papers tab
# ═══════════════════════════════════════════════════════════════════════════════

_LEVEL_STYLE: dict[str, tuple[str, str]] = {
    "beginner":     ("🟢", "#A6E3A1"),
    "intermediate": ("🟡", "#F9E2AF"),
    "advanced":     ("🔴", "#F38BA8"),
}


def _log_paper_read(paper: dict, prof: dict) -> None:
    """Append a paper-read entry to learning_profile.json."""
    entry = {
        "title":    paper.get("title", ""),
        "url":      paper.get("url", ""),
        "level":    paper.get("level", "intermediate"),
        "topic":    paper.get("category", paper.get("topic", "")),
        "read_at":  str(date.today()),
        "xp_earned": 5,
    }
    prof.setdefault("papers_read", []).append(entry)
    _save_profile(prof)


def _render_paper_card(paper: dict, card_id: str, skill_level: str, prof: dict) -> None:
    """
    Render a 4-layer paper card:
      Layer 1 — compact header (title + level badge), always visible
      Layer 2 — TL;DR + why it matters (expand, no API call)
      Layer 3 — Atlas explains (Haiku call, +5 XP, logged to profile)
      Layer 4 — arXiv link (present from Layer 2 onwards)
    """
    from utils.paper_curator import explain_paper

    icon, color = _LEVEL_STYLE.get(paper.get("level", "intermediate"), ("🟡", "#F9E2AF"))
    title   = paper.get("title", "Untitled")
    authors = paper.get("authors", "")
    year    = paper.get("year", "")
    url     = paper.get("url", "#")
    tldr    = paper.get("tldr", paper.get("summary", ""))
    why     = paper.get("why_it_matters", "")

    # Layer 1 + 2: compact header + expandable TL;DR
    with st.expander(
        f"{icon} **{title[:70]}{'…' if len(title) > 70 else ''}** &nbsp; "
        f"<span style='font-size:10px;color:#585B70;'>{authors} · {year}</span>",
        expanded=False,
    ):
        # TL;DR block
        if tldr:
            st.markdown(
                f"""<div style="background:rgba(255,255,255,0.04);
                    border:1px solid rgba(255,255,255,0.08);
                    border-left:3px solid {color};
                    border-radius:8px;padding:12px 16px;margin-bottom:10px;">
                  <div style="font-size:13px;color:#CDD6F4;margin-bottom:5px;">
                    {tldr}</div>
                  {"<div style='font-size:12px;color:#89DCEB;margin-top:4px;'>"
                   "<strong style='color:#45475A;'>Why: </strong>" + why + "</div>"
                   if why else ""}
                  <div style="margin-top:10px;">
                    <span style="font-size:11px;font-family:'JetBrains Mono',monospace;
                                 color:{color};">{icon} {paper.get('level','intermediate').capitalize()}</span>
                    &nbsp;&nbsp;
                    <a href="{url}" target="_blank"
                       style="font-size:11px;color:#89DCEB;text-decoration:none;
                              font-family:'JetBrains Mono',monospace;">→ Read on arXiv</a>
                  </div>
                </div>""",
                unsafe_allow_html=True,
            )

        # Layer 3: Ask Atlas to explain
        expl_key = f"expl_{card_id}"
        btn_key  = f"ask_atlas_{card_id}"
        if not st.session_state.get(expl_key):
            if st.button("📖 Ask Atlas to explain", key=btn_key, use_container_width=True):
                with st.spinner("Atlas is reading the paper…"):
                    explanation = explain_paper(title, tldr, skill_level)
                st.session_state[expl_key] = explanation
                _award_xp(5)
                _log_paper_read(paper, prof)
                st.rerun()
        else:
            st.markdown(
                f"""<div style="background:rgba(137,220,235,0.05);
                    border:1px solid rgba(137,220,235,0.15);
                    border-radius:8px;padding:14px 16px;margin-top:6px;">
                  <div style="font-size:11px;font-family:'JetBrains Mono',monospace;
                              color:#89DCEB;margin-bottom:8px;letter-spacing:0.05em;">
                    ATLAS EXPLAINS</div>
                  <div style="font-size:13px;color:#CDD6F4;line-height:1.7;">
                  {st.session_state[expl_key].replace(chr(10), "<br>")}
                  </div>
                </div>""",
                unsafe_allow_html=True,
            )

            # Build-a-project button (appears after Atlas explanation)
            spark_key = f"spark_{card_id}"
            if st.button("💡 Build a project from this → Spark", key=spark_key, use_container_width=True):
                st.session_state.active_agent = "spark"
                st.session_state.spark_paper_context = (
                    f'I want to build a project inspired by the paper "{title}". '
                    f'The core technique: {why or tldr}. '
                    f"Generate 3 practical project ideas for an AI PM/builder "
                    f"at {skill_level} level."
                )
                _award_xp(10)
                st.switch_page("pages/agent_view.py")


def _render_papers_tab(skill_level: str, prof: dict) -> None:
    """
    Full Research Papers tab rendered inside the Atlas page.

    Layout:
      1. Free-text search  → arXiv + Haiku curation
      2. Level filter chips
      3. Landmark Papers   (static, always available)
    """
    from config.papers import LANDMARK_PAPERS, CATEGORIES
    from utils.search_tools import search_arxiv
    from utils.paper_curator import curate_papers

    # ── Init session state ────────────────────────────────────────────────────
    if "papers_cache" not in st.session_state:
        st.session_state.papers_cache = {}
    if "papers_search_results" not in st.session_state:
        st.session_state.papers_search_results = []
    if "papers_active_query" not in st.session_state:
        st.session_state.papers_active_query = ""
    if "papers_level_filter" not in st.session_state:
        st.session_state.papers_level_filter = ["beginner", "intermediate", "advanced"]

    # Pre-fill from push trigger (SUGGEST_PAPERS chip or COMPLETE_TOPIC card)
    preload = st.session_state.pop("papers_preload", None)

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        """<div style="margin-bottom:18px;">
          <div style="font-family:'Inter',sans-serif;font-size:18px;font-weight:700;
                      color:#CDD6F4;">📄 Research Papers</div>
          <div style="font-size:12px;color:#45475A;font-family:'JetBrains Mono',monospace;
                      margin-top:3px;">
            Search any AI/ML topic · Landmark library always available offline
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── Search bar ────────────────────────────────────────────────────────────
    default_query = preload or st.session_state.papers_active_query
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        query = st.text_input(
            "Search",
            value=default_query,
            placeholder="Search any AI/ML topic — e.g. 'diffusion models', 'AI safety', 'RLHF'…",
            key="papers_query_input",
            label_visibility="collapsed",
        )
    with col_btn:
        search_clicked = st.button("🔍 Search", key="papers_search_btn", type="primary", use_container_width=True)

    if search_clicked and query.strip():
        cache_key = f"{query.strip().lower()}_{skill_level}"
        if cache_key not in st.session_state.papers_cache:
            with st.spinner("Searching arXiv and curating with AI…"):
                try:
                    raw_json  = search_arxiv(query.strip(), max_results=15)
                    raw_list  = json.loads(raw_json)
                    if isinstance(raw_list, list):
                        curated = curate_papers(query.strip(), raw_list, skill_level)
                    else:
                        curated = []
                except Exception:
                    curated = []
            st.session_state.papers_cache[cache_key] = curated
        st.session_state.papers_search_results = st.session_state.papers_cache[cache_key]
        st.session_state.papers_active_query   = query.strip()
        st.rerun()

    # ── Search results ────────────────────────────────────────────────────────
    if st.session_state.papers_search_results:
        results = st.session_state.papers_search_results
        active_q = st.session_state.papers_active_query
        st.markdown(
            f'<div class="ctrl-label">🔍 {len(results)} curated results for "{active_q}"</div>',
            unsafe_allow_html=True,
        )
        if st.button("✕ Clear results", key="papers_clear_results"):
            st.session_state.papers_search_results = []
            st.session_state.papers_active_query   = ""
            st.rerun()
        for idx, paper in enumerate(results):
            _render_paper_card(paper, f"search_{idx}", skill_level, prof)
        st.divider()

    # ── Level filter for landmark section ─────────────────────────────────────
    st.markdown('<div class="ctrl-label">📌 Landmark Papers — 20 essential reads</div>', unsafe_allow_html=True)
    level_filter = st.multiselect(
        "Show levels",
        options=["beginner", "intermediate", "advanced"],
        default=st.session_state.papers_level_filter,
        format_func=lambda x: {"beginner": "🟢 Beginner", "intermediate": "🟡 Intermediate", "advanced": "🔴 Advanced"}[x],
        key="papers_level_ms",
        label_visibility="collapsed",
    )
    if level_filter != st.session_state.papers_level_filter:
        st.session_state.papers_level_filter = level_filter
        st.rerun()

    # ── Category browse ───────────────────────────────────────────────────────
    selected_cat = st.selectbox(
        "Category",
        CATEGORIES,
        key="papers_cat_select",
        label_visibility="collapsed",
    )

    # ── Landmark paper cards ──────────────────────────────────────────────────
    filtered = [
        p for p in LANDMARK_PAPERS
        if p.get("level") in (level_filter or ["beginner", "intermediate", "advanced"])
        and (selected_cat == "All" or p.get("category") == selected_cat)
    ]

    if not filtered:
        st.info("No landmark papers match the current filters. Try adjusting the level or category.")
    else:
        for idx, paper in enumerate(filtered):
            _render_paper_card(paper, f"lm_{idx}", skill_level, prof)


# ═══════════════════════════════════════════════════════════════════════════════
# ATLAS — Learning Manager
# ═══════════════════════════════════════════════════════════════════════════════

def render_atlas() -> None:
    from agents.learning_agent import LearningAgent
    from config.prompts import CURRICULUM_TOPICS
    from agents.research_agent import ResearchAgent

    if "atlas_agent" not in st.session_state:
        st.session_state.atlas_agent = LearningAgent()
    if "la_messages" not in st.session_state:
        st.session_state.la_messages = []
    if "la_last_handoff" not in st.session_state:
        st.session_state.la_last_handoff = None
    if "la_reset_confirm" not in st.session_state:
        st.session_state.la_reset_confirm = False
    if "la_last_achievement" not in st.session_state:
        st.session_state.la_last_achievement = None
    if "la_goal_feedback" not in st.session_state:
        st.session_state.la_goal_feedback = None
    if "atlas_mode" not in st.session_state:
        st.session_state.atlas_mode = "coach"
    if "atlas_research_agent" not in st.session_state:
        st.session_state.atlas_research_agent = ResearchAgent()
    if "ar_messages" not in st.session_state:
        st.session_state.ar_messages = []
    if "atlas_research_handoff" not in st.session_state:
        st.session_state.atlas_research_handoff = None
    # Papers feature session state
    if "papers_preload" not in st.session_state:
        st.session_state.papers_preload = None

    agent          = st.session_state.atlas_agent
    research_agent = st.session_state.atlas_research_agent

    # ── Top-level tabs: Learning Coach | Research Papers ──────────────────────
    tab_coach, tab_papers = st.tabs(["💬 Learning Coach", "📄 Research Papers"])

    # Switch to Papers tab when a push-trigger preload is set
    # (Streamlit can't programmatically switch tabs, but pre-filling the query
    #  and marking the tab active is the best approximation available)

    with tab_papers:
        _render_papers_tab(
            skill_level=st.session_state.get("skill_level", profile.get("skill_level", "intermediate")),
            prof=profile,
        )

    with tab_coach:
        ctrl, chat = st.columns([2, 5], gap="medium")

    with ctrl:
        st.markdown('<div class="ctrl-accent ctrl-accent-atlas"></div>', unsafe_allow_html=True)
        st.markdown("**🧭 Atlas**")
        st.caption("Learning Coach + Research")
        st.divider()

        mode_choice = st.radio(
            "Mode",
            ["🧭 Coach", "🔬 Research"],
            index=0 if st.session_state.atlas_mode == "coach" else 1,
            key="atlas_mode_radio",
            horizontal=True,
        )
        new_mode = "coach" if mode_choice == "🧭 Coach" else "research"
        if new_mode != st.session_state.atlas_mode:
            st.session_state.atlas_mode = new_mode
            st.rerun()

        st.divider()

        if st.session_state.atlas_mode == "coach":
            st.markdown('<div class="ctrl-label">Next step</div>', unsafe_allow_html=True)
            st.info(agent.suggest_next_topic())

        if st.session_state.atlas_mode == "coach":
            st.divider()
            st.markdown('<div class="ctrl-label">Active Goals</div>', unsafe_allow_html=True)
            active_goals = agent.get_goals(status="active") + agent.get_goals(status="overdue")
            if active_goals:
                HEALTH_COLORS = {
                    "on_track": "#A6E3A1", "at_risk": "#F9E2AF",
                    "stalled":  "#F38BA8", "overdue": "#F38BA8", "achieved": "#89DCEB",
                }
                HEALTH_LABELS = {
                    "on_track": "ON TRACK", "at_risk": "AT RISK",
                    "stalled":  "STALLED",  "overdue": "OVERDUE", "achieved": "ACHIEVED",
                }
                for g in active_goals:
                    color = HEALTH_COLORS.get(g["health"], "#585B70")
                    label = HEALTH_LABELS.get(g["health"], g["health"].upper())
                    ms_t  = len(g.get("milestones", []))
                    ms_d  = sum(1 for m in g.get("milestones", []) if m["status"] == "completed")
                    pct_g = ms_d / ms_t if ms_t > 0 else 0.0
                    dl    = g.get("deadline") or "no deadline"
                    hrs   = g.get("total_hours_logged", 0.0)
                    st.markdown(
                        f"""
                        <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.09);
                                    border-left:3px solid {color};border-radius:8px;padding:10px 12px;
                                    margin-bottom:8px;">
                            <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
                                        color:{color};text-transform:uppercase;letter-spacing:0.08em;">
                                {label}</div>
                            <div style="font-family:'Inter',sans-serif;font-size:13px;
                                        color:#CDD6F4;margin:4px 0 4px;line-height:1.4;">
                                {g['title']}</div>
                            <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#45475A;">
                                {dl} · {ms_d}/{ms_t} milestones · {hrs}h</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.progress(pct_g)
            else:
                st.caption("No active goals.")
                st.caption("Tell Atlas what you want to achieve and I'll track it.")

            st.divider()
            st.markdown('<div class="ctrl-label">Controls</div>', unsafe_allow_html=True)
            if st.button("🗑️ Reset Chat", key="atlas_reset", use_container_width=True):
                agent.reset()
                st.session_state.la_messages    = []
                st.session_state.la_last_handoff = None
                st.rerun()

            st.divider()
            if not st.session_state.la_reset_confirm:
                if st.button("⚠️ Reset All Progress", key="atlas_reset_all", use_container_width=True):
                    st.session_state.la_reset_confirm = True
                    st.rerun()
            else:
                st.warning("This will erase ALL progress. Are you sure?")
                c1, c2 = st.columns(2)
                if c1.button("Yes", type="primary", key="atlas_yes", use_container_width=True):
                    new_profile = agent._make_default_profile()
                    PROFILE_PATH.write_text(json.dumps(new_profile, indent=2))
                    st.session_state.atlas_agent     = LearningAgent()
                    st.session_state.la_messages     = []
                    st.session_state.la_reset_confirm = False
                    st.rerun()
                if c2.button("Cancel", key="atlas_cancel", use_container_width=True):
                    st.session_state.la_reset_confirm = False
                    st.rerun()

        else:  # research mode
            st.divider()
            if st.button("← Back to Coach", key="atlas_back_to_coach", use_container_width=True):
                st.session_state.atlas_mode = "coach"
                st.rerun()
            st.divider()
            st.markdown('<div class="ctrl-label">Sources</div>', unsafe_allow_html=True)
            st.markdown(
                "- 🔍 **Tavily** — live web\n"
                "- 📖 **Wikipedia** — encyclopedic\n"
                "- 📄 **arXiv** — papers\n"
                "- 🤖 **GPT-4o** — second opinion\n"
                "- 🧠 **Claude.ai** — synthesis\n\n"
                "*Every reply includes a Sources section.*"
            )
            current_topic = research_agent.get_handoff_topic()
            if current_topic:
                st.divider()
                st.markdown('<div class="ctrl-label">Active topic</div>', unsafe_allow_html=True)
                st.info(current_topic)
            st.divider()
            st.markdown('<div class="ctrl-label">Controls</div>', unsafe_allow_html=True)
            if st.button("🗑️ New Research Session", key="atlas_research_reset", use_container_width=True):
                research_agent.reset()
                st.session_state.ar_messages            = []
                st.session_state.atlas_research_handoff = None
                st.rerun()

    with chat:
        progress = agent.get_progress()
        pct = progress["pct"]
        st.progress(pct / 100)
        st.caption(
            f"{len(progress['completed'])} / {progress['total']} topics complete ({pct}%)"
        )

        if st.session_state.la_last_achievement:
            ach = st.session_state.la_last_achievement
            st.success(f"🎯 Goal achieved: **{ach['goal']['title']}** — +{ach['xp_earned']} XP!")
            st.balloons()
            _award_xp(ach["xp_earned"])
            st.session_state.la_last_achievement = None

        with st.expander("🔍 Analyse my goals", expanded=False):
            if st.button("Get goal feedback", key="atlas_goal_feedback_btn"):
                with st.spinner("Analysing your goals..."):
                    st.session_state.la_goal_feedback = agent.get_goal_feedback()
            if st.session_state.la_goal_feedback:
                st.markdown(st.session_state.la_goal_feedback)

        if st.session_state.la_last_handoff:
            handoff = st.session_state.la_last_handoff
            st.session_state.la_last_handoff = None
            if handoff.get("agent") == "research":
                st.session_state.atlas_mode             = "research"
                st.session_state.atlas_research_handoff = handoff["topic"]
                research_agent.receive_handoff(handoff["topic"])
                st.rerun()

        if st.session_state.atlas_mode == "coach":
            if not st.session_state.la_messages:
                with st.chat_message("assistant"):
                    st.markdown(
                        "👋 Hi! I'm **Atlas**, your learning coach.\n\n"
                        "I can help you:\n"
                        "- **Plan** — *What should I study next?*\n"
                        "- **Track** — *I finished Python basics*\n"
                        "- **Goals** — *I want to build a RAG pipeline by April*\n"
                        "- **Research** — *Deep-dive into transformers* (switches to Research mode)\n\n"
                        "What would you like to work on today?"
                    )

            for msg_idx, (role, content) in enumerate(st.session_state.la_messages):
                with st.chat_message(role):
                    if role == "assistant":
                        # Strip SUGGEST_PAPERS tag before display
                        suggest_match = _SUGGEST_PAPERS_RE.search(content)
                        clean_content = _SUGGEST_PAPERS_RE.sub("", content).strip()
                        st.markdown(clean_content)
                        # Render contextual chip if tag was present
                        if suggest_match:
                            keyword = suggest_match.group(1).strip()
                            if st.button(
                                f"📄 See papers on \"{keyword}\" →",
                                key=f"suggest_papers_{msg_idx}",
                            ):
                                st.session_state.papers_preload = keyword
                                st.rerun()
                    else:
                        st.markdown(content)

            user_input = st.chat_input("Ask your learning coach...", key="atlas_input")
            if user_input:
                with st.chat_message("user"):
                    st.markdown(user_input)
                st.session_state.la_messages.append(("user", user_input))

                with st.chat_message("assistant"):
                    result = safe_agent_chat(agent, user_input, contextual_spinner("coach"))
                    if result is None:
                        st.stop()
                    response, handoff = result

                    # Strip ACTION/HANDOFF lines for display
                    display = "\n".join(
                        line for line in response.splitlines()
                        if not line.strip().startswith("ACTION:")
                        and not line.strip().startswith("HANDOFF:")
                    ).strip()

                    # Strip SUGGEST_PAPERS tag before displaying live response
                    suggest_match = _SUGGEST_PAPERS_RE.search(display)
                    clean_display = _SUGGEST_PAPERS_RE.sub("", display).strip()
                    st.markdown(clean_display)

                    # Show paper chip immediately after response
                    if suggest_match:
                        keyword = suggest_match.group(1).strip()
                        if st.button(
                            f"📄 See papers on \"{keyword}\" →",
                            key="suggest_papers_live",
                        ):
                            st.session_state.papers_preload = keyword
                            st.rerun()

                # Store display with tag intact so chip reappears on reruns
                st.session_state.la_messages.append(("assistant", display))

                # COMPLETE_TOPIC push trigger — surface paper suggestion card
                for line in response.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("ACTION: COMPLETE_TOPIC |"):
                        completed_topic = stripped.split("|", 1)[-1].strip()
                        st.session_state.la_messages.append((
                            "assistant",
                            f"✅ **{completed_topic}** marked complete! "
                            f"📄 Want to go deeper? Switch to the **Research Papers** tab above "
                            f"and search for *{completed_topic[:40]}*.",
                        ))
                        break

                if handoff:
                    st.session_state.la_last_handoff = handoff
                if hasattr(agent, "_last_achievement") and agent._last_achievement:
                    st.session_state.la_last_achievement = agent._last_achievement
                    agent._last_achievement = None
                _award_xp(5)
                show_xp_toast(5, "for chatting")
                st.rerun()

        else:
            handoff_topic = st.session_state.atlas_research_handoff
            if handoff_topic and not st.session_state.ar_messages:
                st.session_state.atlas_research_handoff = None
                with st.spinner(f"Researching '{handoff_topic}'..."):
                    auto_response = research_agent.chat(
                        f"Research and explain: {handoff_topic}"
                    )
                st.session_state.ar_messages.append(("assistant", auto_response))
                _award_xp(15)
                st.rerun()

            if not st.session_state.ar_messages:
                with st.chat_message("assistant"):
                    st.markdown(
                        "👋 I'm **Atlas** in Research mode.\n\n"
                        "I search Tavily, Wikipedia, arXiv, and cross-reference with GPT-4o.\n\n"
                        "Try:\n"
                        "- *What is RAG and how does it work?*\n"
                        "- *Explain transformer architecture*\n"
                        "- *Compare Pinecone vs Chroma vs Weaviate*\n\n"
                        "What would you like to research?"
                    )

            for role, content in st.session_state.ar_messages:
                with st.chat_message(role):
                    st.markdown(content)

            user_input = st.chat_input("Ask a research question...", key="atlas_research_input")
            if user_input:
                with st.chat_message("user"):
                    st.markdown(user_input)
                st.session_state.ar_messages.append(("user", user_input))

                with st.chat_message("assistant"):
                    with st.spinner("Searching and synthesising..."):
                        response = research_agent.chat(user_input)
                    st.markdown(response)

                st.session_state.ar_messages.append(("assistant", response))
                _award_xp(15)
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# DOJO — Practice Agent
# ═══════════════════════════════════════════════════════════════════════════════

def render_dojo() -> None:
    from agents.practice_agent import PracticeAgent

    if "dojo_agent" not in st.session_state:
        st.session_state.dojo_agent = PracticeAgent()
    if "da_messages" not in st.session_state:
        st.session_state.da_messages = []
    if "da_last_result" not in st.session_state:
        st.session_state.da_last_result = None
    if "da_mode_confirm" not in st.session_state:
        st.session_state.da_mode_confirm = False
    if "da_pending_mode" not in st.session_state:
        st.session_state.da_pending_mode = None

    agent = st.session_state.dojo_agent
    ctrl, chat = st.columns([2, 5], gap="medium")

    with ctrl:
        st.markdown('<div class="ctrl-accent ctrl-accent-dojo"></div>', unsafe_allow_html=True)
        st.markdown("**🎯 Dojo**")
        st.caption("Practice Arena")
        st.divider()

        mode_opts   = ["Quiz", "Coding Challenge", "Mock Interview"]
        mode_keys   = {"Quiz": "quiz", "Coding Challenge": "challenge", "Mock Interview": "interview"}
        current_lbl = {"quiz": "Quiz", "challenge": "Coding Challenge", "interview": "Mock Interview"}.get(agent.mode, "Quiz")

        st.markdown('<div class="ctrl-label">Mode</div>', unsafe_allow_html=True)
        sel_mode_lbl = st.radio(
            "mode", mode_opts,
            index=mode_opts.index(current_lbl),
            label_visibility="collapsed",
            key="dojo_mode_radio",
        )
        sel_mode = mode_keys[sel_mode_lbl]

        if sel_mode != agent.mode and agent.session_active:
            if not st.session_state.da_mode_confirm:
                st.session_state.da_pending_mode = sel_mode
                st.session_state.da_mode_confirm = True
                # Do NOT st.rerun() here — let the page re-render naturally
                # so the confirmation dialog is immediately visible.

        if st.session_state.da_mode_confirm:
            st.warning("Changing mode ends your session.")
            c1, c2 = st.columns(2)
            if c1.button("Switch", key="dojo_switch", use_container_width=True):
                agent.reset()
                agent.set_mode(st.session_state.da_pending_mode)
                st.session_state.da_messages    = []
                st.session_state.da_last_result = None
                st.session_state.da_mode_confirm = False
                st.session_state.da_pending_mode = None
                st.rerun()
            if c2.button("Cancel", key="dojo_cancel", use_container_width=True):
                st.session_state.da_mode_confirm = False
                st.session_state.da_pending_mode = None
                st.rerun()
        elif not agent.session_active:
            agent.set_mode(sel_mode)

        st.markdown('<div class="ctrl-label" style="margin-top:12px;">Topic</div>', unsafe_allow_html=True)
        topic = st.text_input(
            "topic",
            value=agent.topic if agent.topic else "",
            placeholder="e.g. RAG systems, prompt engineering, LLM evals… Leave blank for mixed AI practice",
            label_visibility="collapsed",
            key="dojo_topic",
            disabled=agent.session_active,
        )
        if not agent.session_active:
            agent.set_topic(topic)

        st.markdown('<div class="ctrl-label" style="margin-top:12px;">Difficulty</div>', unsafe_allow_html=True)
        difficulty_opts = ["Beginner", "Intermediate", "Advanced"]
        difficulty = st.radio(
            "difficulty",
            difficulty_opts,
            index=difficulty_opts.index(agent.difficulty) if agent.difficulty in difficulty_opts else 1,
            label_visibility="collapsed",
            key="dojo_difficulty",
            horizontal=True,
            disabled=agent.session_active,
        )
        if not agent.session_active:
            agent.set_difficulty(difficulty)

        st.markdown('<div class="ctrl-label" style="margin-top:12px;">Target role</div>', unsafe_allow_html=True)
        role = st.radio(
            "role", ["AI Builder", "AI PM"],
            index=0 if agent.role == "AI Builder" else 1,
            label_visibility="collapsed",
            key="dojo_role_radio",
        )
        if not agent.session_active:
            agent.set_role(role)

        mode_label = {"quiz": "Quiz", "challenge": "Challenge", "interview": "Interview"}.get(agent.mode, "Session")
        st.divider()
        if st.button(f"▶ Start {mode_label}", key="dojo_start", use_container_width=True, type="primary"):
            agent.reset()
            agent.set_mode(sel_mode)
            agent.set_topic(topic)
            agent.set_difficulty(difficulty)
            agent.set_role(role)
            with st.spinner("Setting up..."):
                opening = agent.start_session()
            st.session_state.da_messages    = [("assistant", opening)]
            st.session_state.da_last_result = None
            st.rerun()

        with st.expander("📊 My Stats"):
            stats = agent.get_stats()
            q = stats["quiz"]
            if q["sessions"] > 0:
                st.markdown(f"**Quiz** — {q['sessions']} session(s)")
                st.markdown(f"Accuracy: **{q['accuracy_pct']}%**")
            else:
                st.caption("No quiz sessions yet.")
            c = stats["challenge"]
            if c["sessions"] > 0:
                st.markdown(f"**Challenge** — avg **{c['avg_score']}/10**")
            i = stats["interview"]
            if i["sessions"] > 0:
                st.markdown(f"**Interview** — {i['sessions']} session(s)")

        if st.button("🗑️ Reset Chat", key="dojo_reset", use_container_width=True):
            agent.reset()
            st.session_state.da_messages    = []
            st.session_state.da_last_result = None
            st.rerun()

    with chat:
        if agent.session_active:
            topic_label = agent.get_topic_label()
            _topic_display = topic_label[:45] + "…" if len(topic_label) > 45 else topic_label
            # Show question progress counter for quiz mode
            q_num = getattr(agent, "current_question_num", None)
            q_suffix = f" — Q{q_num}/10" if (agent.mode == "quiz" and q_num) else ""
            badge = {
                "quiz":      f"🎯 Quiz — {agent.difficulty} — {_topic_display}{q_suffix}",
                "challenge": f"💻 Challenge — {agent.difficulty} — {_topic_display}",
                "interview": f"🤝 Interview — {agent.role} — {agent.difficulty} — {_topic_display}",
            }.get(agent.mode, "")
            st.info(badge)

        if not st.session_state.da_messages:
            with st.chat_message("assistant"):
                st.markdown(
                    "👋 Hi! I'm **Dojo**, your practice arena.\n\n"
                    "**🎯 Quiz** — 10 multiple-choice questions on any AI topic you choose, or a mixed AI set if you leave the topic blank.\n\n"
                    "**💻 Coding Challenge** — A real task with AI code review.\n\n"
                    "**🤝 Mock Interview** — AI Builder or AI PM interview prep.\n\n"
                    "**Type any AI topic, or leave it blank for mixed-topic practice, then click Start!**"
                )

        for role, content in st.session_state.da_messages:
            with st.chat_message(role):
                st.markdown(content)

        last_result = st.session_state.da_last_result
        if last_result:
            if agent.mode == "quiz":
                if last_result.get("correct"):
                    st.success("✅ Correct!")
                else:
                    st.error("❌ Incorrect")
            elif agent.mode in ("challenge", "interview"):
                score     = last_result.get("score", 0)
                max_score = last_result.get("max_score", 10)
                st.info(f"Score: **{score}/{max_score}**")

            if last_result.get("session_complete"):
                st.balloons()
                with st.expander("🎉 Session Complete!", expanded=True):
                    s = agent.get_stats()
                    if agent.mode == "quiz":
                        q = s["quiz"]
                        st.markdown(f"**{q['correct']}/{q['total_questions']}** ({q['accuracy_pct']}%)")
                    elif agent.mode == "challenge":
                        st.markdown(f"Average: **{s['challenge']['avg_score']}/10**")
                    elif agent.mode == "interview":
                        r = s["interview"]["by_role"].get(agent.role, {})
                        st.markdown(f"Average: **{r.get('avg_score', 0)}/5**")
                _award_xp(50)
                show_xp_toast(50, "session complete!")
                c1, c2, c3 = st.columns(3)
                if c1.button("▶ Another", key="dojo_another", type="primary", use_container_width=True):
                    agent.reset()
                    with st.spinner("Setting up..."):
                        opening = agent.start_session()
                    st.session_state.da_messages    = [("assistant", opening)]
                    st.session_state.da_last_result = None
                    st.rerun()
                if c2.button("Change Mode", key="dojo_change", use_container_width=True):
                    agent.reset()
                    st.session_state.da_messages    = []
                    st.session_state.da_last_result = None
                    st.rerun()
                if c3.button("📖 Study in Atlas", key="dojo_to_atlas", use_container_width=True):
                    # Pre-fill Atlas with the topic we just practiced
                    st.session_state.active_agent = "atlas"
                    st.session_state.atlas_mode   = "coach"
                    topic_hint = agent.get_topic_label()
                    st.session_state.la_messages  = st.session_state.get("la_messages", [])
                    # Inject a prompt so Atlas knows what to help with
                    st.session_state._dojo_topic_hint = topic_hint
                    st.switch_page("pages/agent_view.py")

        if agent.session_active and not (last_result and last_result.get("session_complete")):
            placeholder = {
                "quiz":      "Type A, B, C, or D...",
                "challenge": "Paste your code solution here...",
                "interview": "Type your answer...",
            }.get(agent.mode, "Type your response...")

            user_input = st.chat_input(placeholder, key="dojo_input")
            if user_input:
                with st.chat_message("user"):
                    st.markdown(user_input)
                st.session_state.da_messages.append(("user", user_input))

                try:
                    with st.spinner(contextual_spinner(agent.mode)):
                        replies, result = agent.chat(user_input)
                except Exception as exc:
                    etype = type(exc).__name__
                    if "AuthenticationError" in etype or "api_key" in str(exc).lower():
                        st.error("**API key error** — check your `.env` file.", icon="🔑")
                    elif "RateLimitError" in etype or "rate_limit" in str(exc).lower():
                        st.error("**Rate limit** — wait a moment then try again.", icon="⏳")
                    else:
                        st.error(f"**Something went wrong** — {etype}: {exc}", icon="⚠️")
                    st.stop()

                for r in replies:
                    with st.chat_message("assistant"):
                        st.markdown(r)
                    st.session_state.da_messages.append(("assistant", r))

                st.session_state.da_last_result = result

                xp_gain = 15 if (result and agent.mode == "quiz" and result.get("correct")) else 10
                _award_xp(xp_gain)
                show_xp_toast(xp_gain, "correct!" if (result and result.get("correct")) else "for practising")
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# SPARK — Idea Agent
# ═══════════════════════════════════════════════════════════════════════════════

def render_spark() -> None:
    from agents.idea_agent import IdeaAgent

    if "spark_agent" not in st.session_state:
        st.session_state.spark_agent = IdeaAgent()
    if "sa_messages" not in st.session_state:
        st.session_state.sa_messages = []
    if "sa_last_save" not in st.session_state:
        st.session_state.sa_last_save = None
    if "sa_delete_confirm" not in st.session_state:
        st.session_state.sa_delete_confirm = None
    if "sa_mode_confirm" not in st.session_state:
        st.session_state.sa_mode_confirm = False
    if "sa_pending_mode" not in st.session_state:
        st.session_state.sa_pending_mode = None

    agent = st.session_state.spark_agent

    # Paper-to-Spark auto-send: if a paper context was passed from the Papers tab, inject it
    if st.session_state.get("spark_paper_context"):
        paper_ctx = st.session_state.pop("spark_paper_context")
        st.session_state.sa_messages.append(("user", paper_ctx))
        with st.spinner("Spark is generating ideas from the paper…"):
            reply, notification = agent.chat(paper_ctx)
        spark_display = "\n".join(
            line for line in reply.splitlines()
            if not line.strip().startswith("ACTION:")
        ).strip()
        st.session_state.sa_messages.append(("assistant", spark_display))
        if notification:
            st.session_state.sa_last_save = notification
        st.rerun()

    ctrl, chat = st.columns([2, 5], gap="medium")

    with ctrl:
        st.markdown('<div class="ctrl-accent ctrl-accent-spark"></div>', unsafe_allow_html=True)
        st.markdown("**💡 Spark**")
        st.caption("Idea Generator")
        st.divider()

        mode_opts = ["Brainstorm", "Project Brief", "Idea Feedback"]
        mode_keys = {"Brainstorm": "brainstorm", "Project Brief": "brief", "Idea Feedback": "feedback"}
        cur_lbl   = {"brainstorm": "Brainstorm", "brief": "Project Brief", "feedback": "Idea Feedback"}.get(agent.mode, "Brainstorm")

        st.markdown('<div class="ctrl-label">Mode</div>', unsafe_allow_html=True)
        sel_mode_lbl = st.radio(
            "mode", mode_opts,
            index=mode_opts.index(cur_lbl),
            label_visibility="collapsed",
            key="spark_mode_radio",
        )
        sel_mode = mode_keys[sel_mode_lbl]
        if sel_mode != agent.mode:
            has_history = len(st.session_state.sa_messages) > 2
            if has_history and not st.session_state.sa_mode_confirm:
                st.session_state.sa_pending_mode = sel_mode
                st.session_state.sa_mode_confirm = True
            elif not has_history:
                agent.set_mode(sel_mode)
                st.session_state.sa_messages  = []
                st.session_state.sa_last_save = None
                st.rerun()

        if st.session_state.sa_mode_confirm:
            st.warning("Switching mode will clear this conversation.")
            c1, c2 = st.columns(2)
            if c1.button("Yes, switch", key="spark_mode_yes", use_container_width=True):
                agent.set_mode(st.session_state.sa_pending_mode)
                st.session_state.sa_messages  = []
                st.session_state.sa_last_save = None
                st.session_state.sa_mode_confirm  = False
                st.session_state.sa_pending_mode  = None
                st.rerun()
            if c2.button("Cancel", key="spark_mode_no", use_container_width=True):
                st.session_state.sa_mode_confirm = False
                st.session_state.sa_pending_mode = None
                st.rerun()

        st.markdown('<div class="ctrl-label" style="margin-top:12px;">Skill level</div>', unsafe_allow_html=True)
        skill_opts = ["beginner", "intermediate", "advanced"]
        sel_skill = st.radio(
            "skill", skill_opts,
            index=skill_opts.index(agent.skill_level) if agent.skill_level in skill_opts else 0,
            label_visibility="collapsed",
            format_func=str.capitalize,
            key="spark_skill_radio",
        )
        if sel_skill != agent.skill_level:
            agent.set_skill_level(sel_skill)

        st.divider()

        ideas = agent.get_ideas()
        st.markdown(f'<div class="ctrl-label">Saved Ideas ({len(ideas)})</div>', unsafe_allow_html=True)
        if ideas:
            for idea in ideas:
                with st.expander(idea["title"][:30], expanded=False):
                    st.markdown(f"**{idea['topic']}**")
                    st.caption(idea["description"][:120])
                    # Cross-link to Dojo
                    if st.button("🎯 Practice this topic", key=f"spark_dojo_{idea['id']}", use_container_width=True):
                        st.session_state.active_agent = "dojo"
                        st.session_state.dojo_topic_hint = idea["topic"]
                        st.switch_page("pages/agent_view.py")
                    # Delete with confirmation
                    if st.session_state.sa_delete_confirm == idea["id"]:
                        st.warning("Delete this idea permanently?")
                        d1, d2 = st.columns(2)
                        if d1.button("Yes", key=f"spark_del_yes_{idea['id']}", use_container_width=True):
                            agent.delete_idea(idea["id"])
                            st.session_state.sa_delete_confirm = None
                            st.rerun()
                        if d2.button("No", key=f"spark_del_no_{idea['id']}", use_container_width=True):
                            st.session_state.sa_delete_confirm = None
                            st.rerun()
                    else:
                        if st.button("🗑️ Delete", key=f"spark_del_{idea['id']}", use_container_width=True):
                            st.session_state.sa_delete_confirm = idea["id"]
                            st.rerun()
        else:
            st.caption("No ideas saved yet.")

        st.divider()
        if st.button("🗑️ Reset Chat", key="spark_reset", use_container_width=True):
            agent.reset()
            st.session_state.sa_messages  = []
            st.session_state.sa_last_save = None
            st.rerun()

    with chat:
        mode_info = {
            "brainstorm": "🧠 **Brainstorm mode** — Generate 3-5 project ideas *(temperature=1.0)*",
            "brief":      "📋 **Project Brief mode** — Turn an idea into a full build plan *(temperature=0.3)*",
            "feedback":   "🔍 **Idea Feedback mode** — Honest scoring on feasibility & scope *(temperature=0.5)*",
        }
        st.info(mode_info[agent.mode])

        if not st.session_state.sa_messages:
            with st.chat_message("assistant"):
                welcome = {
                    "brainstorm": (
                        "👋 Hi! I'm **Spark** in Brainstorm mode.\n\n"
                        "Tell me your interests and I'll generate 3-5 concrete AI project ideas. "
                        "Pick one and I'll save it to your library!"
                    ),
                    "brief": (
                        "👋 Hi! I'm **Spark** in Project Brief mode.\n\n"
                        "Describe any AI idea — even rough — and I'll build a structured plan: "
                        "tech stack, implementation steps, timeline, and risks."
                    ),
                    "feedback": (
                        "👋 Hi! I'm **Spark** in Idea Feedback mode.\n\n"
                        "Pitch your idea and I'll score it on feasibility, scope, learning value, "
                        "and real-world usefulness. Honest feedback, not cheerleading."
                    ),
                }[agent.mode]
                st.markdown(welcome)

        for role, content in st.session_state.sa_messages:
            with st.chat_message(role):
                st.markdown(content)

        if st.session_state.sa_last_save:
            save = st.session_state.sa_last_save
            st.success(f"💡 Idea saved: **{save['idea']['title']}**")
            st.session_state.sa_last_save = None

        placeholder = {
            "brainstorm": "Tell me your interests or ask for ideas...",
            "brief":      "Describe the idea you want to plan out...",
            "feedback":   "Pitch your idea and I'll evaluate it...",
        }.get(agent.mode, "Type your message...")

        user_input = st.chat_input(placeholder, key="spark_input")
        if user_input:
            with st.chat_message("user"):
                st.markdown(user_input)
            st.session_state.sa_messages.append(("user", user_input))

            with st.chat_message("assistant"):
                result = safe_agent_chat(agent, user_input, contextual_spinner(agent.mode))
                if result is None:
                    st.stop()
                reply, notification = result
                display = "\n".join(
                    line for line in reply.splitlines()
                    if not line.strip().startswith("ACTION:")
                ).strip()
                st.markdown(display)

            st.session_state.sa_messages.append(("assistant", display))
            if notification:
                st.session_state.sa_last_save = notification
                _award_xp(20)
                show_xp_toast(20, "idea saved!")
            else:
                _award_xp(5)
                show_xp_toast(5, "for chatting")
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# SYLLABUS — 13-Week Career Roadmap
# ═══════════════════════════════════════════════════════════════════════════════

def _set_syllabus_task(key: str, status: str) -> None:
    """Toggle a syllabus task status and persist to profile."""
    p = _load_profile()
    p.setdefault("syllabus_progress", {})[key] = status
    _save_profile(p)


def render_syllabus() -> None:
    p              = _load_profile()
    syllabus_prog  = p.get("syllabus_progress", {})
    selected_roles = p.get("selected_roles", ["aipm", "evals", "context"])
    overall        = get_progress(syllabus_prog, selected_roles)

    st.markdown(
        f"""
        <div style="margin-bottom:18px;">
            <div style="font-family:'Inter',sans-serif; font-size:20px;
                        font-weight:700; color:#CDD6F4;">AI² Career Roadmap</div>
            <div style="font-size:12px; color:#45475A; margin-top:4px;
                        font-family:'JetBrains Mono',monospace;">
                13-week plan &nbsp;·&nbsp;
                {overall['done']}/{overall['total']} tasks done ({overall['pct']}%)
                &nbsp;·&nbsp; Tracks:&nbsp;
                {'&nbsp;'.join(ROLE_TRACKS[r]['icon'] + '&nbsp;' + ROLE_TRACKS[r]['label']
                               for r in selected_roles if r in ROLE_TRACKS)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="ctrl-label">Filter by role track</div>', unsafe_allow_html=True)
    role_filter_cols = st.columns(len(ROLE_TRACKS))
    active_filter: list[str] = list(
        st.session_state.get("syl_role_filter", selected_roles)
    )

    for col, (rk, rm) in zip(role_filter_cols, ROLE_TRACKS.items()):
        with col:
            is_on = rk in active_filter
            if st.button(
                f"{rm['icon']} {rm['label']}",
                key=f"syl_rf_{rk}",
                type="primary" if is_on else "secondary",
                use_container_width=True,
            ):
                new_f = list(active_filter)
                if is_on and len(new_f) > 1:
                    new_f.remove(rk)
                elif not is_on:
                    new_f.append(rk)
                st.session_state.syl_role_filter = new_f
                st.rerun()

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    current_phase_id = get_current_phase_id(syllabus_prog, active_filter)
    if "syl_active_phase" not in st.session_state:
        st.session_state.syl_active_phase = current_phase_id

    phase_tab_cols = st.columns(len(PHASES))
    for col, phase in zip(phase_tab_cols, PHASES):
        ph_prog = overall["by_phase"].get(phase["id"], {})
        pct     = ph_prog.get("pct", 0)
        is_sel  = st.session_state.syl_active_phase == phase["id"]
        with col:
            if st.button(
                f"{phase['icon']} {phase['phase']}",
                key=f"syl_phase_{phase['id']}",
                type="primary" if is_sel else "secondary",
                use_container_width=True,
                help=f"{phase['title']} — {pct}% done",
            ):
                st.session_state.syl_active_phase = phase["id"]
                st.rerun()

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    phase   = next((ph for ph in PHASES if ph["id"] == st.session_state.syl_active_phase), PHASES[0])
    ph_prog = overall["by_phase"].get(phase["id"], {})

    st.markdown(
        f"""
        <div style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.09);
                    border-left:3px solid #89DCEB; border-radius:10px; padding:14px 18px; margin-bottom:18px;
                    backdrop-filter:blur(12px);">
            <div style="font-family:'JetBrains Mono',monospace; font-size:10px;
                        text-transform:uppercase; color:#45475A; letter-spacing:0.1em;">
                {phase['phase']} &nbsp;·&nbsp; {phase['weeks']}
            </div>
            <div style="font-family:'Inter',sans-serif; font-size:16px;
                        font-weight:700; color:#CDD6F4; margin:4px 0;">
                {phase['icon']} {phase['title']}
            </div>
            <div style="font-size:12px; color:#6C7086;">{phase['description']}</div>
            <div style="margin-top:8px; height:4px; background:rgba(255,255,255,0.08); border-radius:99px;">
                <div style="height:4px; background:#89DCEB; border-radius:99px;
                            width:{ph_prog.get('pct', 0)}%;"></div>
            </div>
            <div style="font-size:10px; color:#45475A; margin-top:4px;
                        font-family:'JetBrains Mono',monospace;">
                {ph_prog.get('done', 0)}/{ph_prog.get('total', 0)} tasks
                &nbsp;·&nbsp; Deliverable: {phase['artifact']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for ti, track in enumerate(phase["tracks"]):
        visible_tasks = [
            (taski, task) for taski, task in enumerate(track["tasks"])
            if any(r in active_filter for r in task["roles"])
        ]
        if not visible_tasks:
            continue

        track_roles_str = " ".join(
            ROLE_TRACKS[r]["icon"]
            for r in track["roles"]
            if r in ROLE_TRACKS and r in active_filter
        )

        with st.expander(f"{track['name']}  {track_roles_str}", expanded=True):
            # Role dot legend — shown once per track
            legend_parts = [
                f'<span style="color:{ROLE_TRACKS[r]["color"]};">●</span> {ROLE_TRACKS[r]["label"]}'
                for r in ROLE_TRACKS if r in active_filter
            ]
            if legend_parts:
                st.markdown(
                    '<div style="font-size:10px; color:#45475A; font-family:\'JetBrains Mono\',monospace; '
                    f'margin-bottom:6px;">{" &nbsp;·&nbsp; ".join(legend_parts)}</div>',
                    unsafe_allow_html=True,
                )
            for taski, task in visible_tasks:
                key       = get_task_key(phase["id"], ti, taski)
                status    = syllabus_prog.get(key, "todo")
                task_cols = st.columns([0.06, 0.8, 0.14])

                status_icons = {"todo": "⬜", "in_progress": "🔶", "done": "✅"}
                with task_cols[0]:
                    if st.button(
                        status_icons.get(status, "⬜"),
                        key=f"syl_task_{key}",
                        help="Click to cycle: todo → active → done",
                    ):
                        next_status = {"todo": "in_progress", "in_progress": "done", "done": "todo"}
                        new_status  = next_status.get(status, "todo")
                        _set_syllabus_task(key, new_status)
                        st.rerun()

                with task_cols[1]:
                    text_style = (
                        "text-decoration:line-through; color:#45475A;"
                        if status == "done"
                        else "color:#A6ADC8;" if status == "in_progress"
                        else "color:#6C7086;"
                    )
                    role_dots = " ".join(
                        f'<span style="color:{ROLE_TRACKS[r]["color"]};">●</span>'
                        for r in task["roles"] if r in ROLE_TRACKS and r in active_filter
                    )
                    st.markdown(
                        f'<div style="padding:4px 0; font-size:13px; {text_style}">'
                        f'{task["text"]}&nbsp; {role_dots}</div>',
                        unsafe_allow_html=True,
                    )

                with task_cols[2]:
                    if status == "in_progress":
                        st.markdown(
                            '<span style="font-size:10px; color:#FBBF24; '
                            'font-family:\'JetBrains Mono\',monospace;">ACTIVE</span>',
                            unsafe_allow_html=True,
                        )

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div style="font-family:\'Inter\',sans-serif; font-size:13px; font-weight:600; '
        'color:#CDD6F4; margin-bottom:12px;">Skills you\'ll build this phase</div>',
        unsafe_allow_html=True,
    )

    phase_roles = set()
    for track in phase["tracks"]:
        for r in track["roles"]:
            if r in active_filter:
                phase_roles.add(r)

    skill_cols = st.columns(len(phase_roles)) if phase_roles else []
    for col, rk in zip(skill_cols, sorted(phase_roles)):
        rm   = ROLE_TRACKS[rk]
        cats = ROLE_SKILLS.get(rk, [])
        with col:
            st.markdown(
                f'<div style="font-size:12px; font-weight:700; color:{rm["color"]}; '
                f'margin-bottom:6px;">{rm["icon"]} {rm["label"]}</div>',
                unsafe_allow_html=True,
            )
            for cat in cats[:2]:
                st.markdown(
                    f'<div style="font-size:11px; color:#6C7086; margin-top:6px;">'
                    f'<strong style="color:#A6ADC8;">{cat["category"]}</strong><br>'
                    + "<br>".join(f'· {s}' for s in cat["skills"][:4])
                    + "</div>",
                    unsafe_allow_html=True,
                )


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

active = st.session_state.get("active_agent")

if active == "oracle":  # legacy redirect
    st.session_state.active_agent = "atlas"
    st.session_state.atlas_mode   = "research"
    st.rerun()

if   active == "atlas":    render_atlas()
elif active == "dojo":     render_dojo()
elif active == "spark":    render_spark()
elif active == "syllabus": render_syllabus()
else:
    st.switch_page("pages/workspace.py")
