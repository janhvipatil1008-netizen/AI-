"""
learner_state_server.py — MCP Server: Shared Learner State

WHAT IS THIS?
--------------
This is the most important server in the whole platform.

Every agent — Coding, Research, Practice, Ideas, Learning Manager — reads from
and writes to this server. It is the single source of truth for:

  - Who the learner is (skill level, goals)
  - What they've studied (topics, agents used, when)
  - How they're progressing (level changes, milestones)

WHY IS THIS A SEPARATE SERVER?
--------------------------------
Before this file existed, each agent had its own copy of the learner's data.
The Coding Agent didn't know what the Practice Agent had discovered.
The Research Agent didn't know what the learner's goal was.

Now ALL agents call this server. One write = all agents see the update.
This is called a "single source of truth" — a core system design principle.

SIMPLE ANALOGY:
---------------
Think of this server as the learner's school file. Every teacher (agent)
reads the same file before class and writes notes to the same file after.
No teacher is working with stale or incomplete information.

TOOLS EXPOSED:
--------------
  get_learner_profile()         → full profile snapshot
  update_skill_level(level)     → beginner / intermediate / advanced
  log_topic_studied(...)        → records what was just taught
  get_recent_topics(limit)      → what was studied recently (newest first)
  set_learning_goal(goal)       → saves the learner's stated goal
  get_learning_goals()          → all goals with status
  get_progress_summary()        → a plain-English summary for the AI to use

HOW TO TEST THIS SERVER:
--------------------------
In PowerShell (using your .venv):
    .venv\\Scripts\\python.exe mcp_server/learner_state_server.py

If it starts without error and waits, the server is working.
Press Ctrl+C to stop.
"""

import json
import os
import sys
from datetime import datetime

# Make sure imports from the parent AI² directory work when run standalone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP

# ── Constants ─────────────────────────────────────────────────────────────────

# Path to the shared learner profile file
PROFILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "learning_profile.json",
)

# Valid skill levels — enforced on every write
VALID_LEVELS = ("beginner", "intermediate", "advanced")

# ── MCP Server ────────────────────────────────────────────────────────────────

mcp = FastMCP("AI² Learner State Server")

# ── Internal helpers (not exposed as tools) ───────────────────────────────────

def _load_profile() -> dict:
    """
    Load the learner profile from disk.

    If the file doesn't exist yet (first-ever run), return a clean default.
    We never crash on a missing file — we return a sensible starting point.
    """
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    # Default profile for a brand-new learner
    return {
        "skill_level": "beginner",
        "goals": [],
        "topics_studied": [],
        "milestones": [],
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
    }


def _save_profile(profile: dict) -> None:
    """
    Save the learner profile to disk, always updating `last_updated`.

    Creates the `data/` directory if it doesn't exist (safe for fresh installs).
    """
    profile["last_updated"] = datetime.now().isoformat()
    os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)


# ── MCP Tools ─────────────────────────────────────────────────────────────────

@mcp.tool()
def get_learner_profile() -> str:
    """
    Get the full learner profile: skill level, goals, study history, and milestones.

    Use this at the START of any session to understand who you're teaching.
    This gives you the full picture — recent topics, current goals, skill level.

    Returns a JSON string with the complete profile.
    """
    profile = _load_profile()
    return json.dumps(profile, indent=2)


@mcp.tool()
def update_skill_level(level: str) -> str:
    """
    Update the learner's skill level based on what you have observed in this session.

    Call this when the learner demonstrates knowledge clearly beyond their current level,
    or when they consistently struggle with content at their current level.

    Valid values for level: "beginner", "intermediate", "advanced"

    Examples of when to call this:
    - Learner correctly explains gradient descent without prompting → upgrade to intermediate
    - Learner asks "what is a variable?" → downgrade to beginner
    - Learner discusses production deployment trade-offs → upgrade to advanced
    """
    if level not in VALID_LEVELS:
        return (
            f"ERROR: '{level}' is not a valid skill level. "
            f"Use one of: {', '.join(VALID_LEVELS)}"
        )

    profile = _load_profile()
    old_level = profile.get("skill_level", "beginner")

    if old_level == level:
        return f"Skill level is already '{level}' — no change made."

    profile["skill_level"] = level
    profile.setdefault("milestones", []).append({
        "event": "skill_level_change",
        "from": old_level,
        "to": level,
        "timestamp": datetime.now().isoformat(),
    })

    _save_profile(profile)
    return f"Skill level updated: {old_level} → {level}"


@mcp.tool()
def log_topic_studied(topic: str, agent: str, summary: str = "") -> str:
    """
    Record that the learner just studied a topic. Call this at the END of a teaching session.

    This builds the learner's cumulative study history. The Learning Manager uses this
    history to recommend what to study next and to avoid repeating content.

    Args:
        topic:   The topic name. Be specific. Bad: "AI". Good: "transformer attention mechanism".
        agent:   Which agent taught it. One of: "coding", "research", "practice", "ideas", "learning".
        summary: Optional 1-sentence summary of the key thing the learner understood.

    Examples:
        log_topic_studied("RAG pipeline architecture", "research", "Understood how chunking affects retrieval quality")
        log_topic_studied("Python list comprehensions", "coding", "")
        log_topic_studied("Quiz: vector databases", "practice", "Scored 4/5, weak on HNSW index details")
    """
    profile = _load_profile()
    profile.setdefault("topics_studied", []).append({
        "topic": topic,
        "agent": agent,
        "summary": summary,
        "studied_at": datetime.now().isoformat(),
    })
    _save_profile(profile)
    return f"Logged: '{topic}' (via {agent} agent)."


@mcp.tool()
def get_recent_topics(limit: int = 5) -> str:
    """
    Get the most recently studied topics, newest first.

    Use this to:
    - Avoid repeating what the learner just covered
    - Find the natural next step in their learning path
    - Give context-aware recommendations ("Since you just studied X, next try Y")

    Args:
        limit: How many recent topics to return (default: 5, max meaningful: 20)
    """
    profile = _load_profile()
    topics = profile.get("topics_studied", [])

    if not topics:
        return json.dumps([], indent=2)

    # Return the most recent `limit` topics, newest first
    recent = list(reversed(topics[-limit:]))
    return json.dumps(recent, indent=2)


@mcp.tool()
def set_learning_goal(goal: str) -> str:
    """
    Save the learner's current learning goal.

    Call this when the user explicitly states what they want to achieve.
    Goals help all agents align their teaching toward the learner's actual objective.

    Examples of goals to capture:
    - "I want to build a RAG app by end of month"
    - "I need to pass an AI PM interview"
    - "I want to understand how transformers work mathematically"
    - "I want to ship my first AI side project"

    Args:
        goal: The goal statement, as the learner described it (keep their words).
    """
    profile = _load_profile()
    profile.setdefault("goals", []).append({
        "goal": goal,
        "status": "active",
        "set_at": datetime.now().isoformat(),
    })
    _save_profile(profile)
    return f"Goal saved: '{goal}'"


@mcp.tool()
def get_learning_goals() -> str:
    """
    Get all of the learner's goals with their status (active / completed).

    Use this to:
    - Remind the learner what they said they wanted to achieve
    - Tailor explanations toward their stated objective
    - Detect when a goal has been met and celebrate it

    Returns a JSON list of goals with status and timestamps.
    """
    profile = _load_profile()
    goals = profile.get("goals", [])
    return json.dumps(goals, indent=2)


@mcp.tool()
def get_progress_summary() -> str:
    """
    Get a plain-English summary of the learner's progress so far.

    Use this to give context-aware encouragement, track milestones, and
    personalize the learning experience. Returns a short readable paragraph
    instead of raw JSON — designed to be included directly in an AI response.
    """
    profile = _load_profile()

    skill_level = profile.get("skill_level", "beginner")
    topics = profile.get("topics_studied", [])
    goals = [g for g in profile.get("goals", []) if g.get("status") == "active"]
    milestones = profile.get("milestones", [])

    topic_count = len(topics)
    goal_text = goals[0]["goal"] if goals else "no specific goal set yet"
    recent_topic = topics[-1]["topic"] if topics else "nothing yet"

    summary_lines = [
        f"Skill level: {skill_level}.",
        f"Topics studied so far: {topic_count}.",
        f"Most recently studied: {recent_topic}.",
        f"Current goal: {goal_text}.",
    ]

    if milestones:
        last = milestones[-1]
        if last.get("event") == "skill_level_change":
            summary_lines.append(
                f"Notable milestone: progressed from {last['from']} to {last['to']}."
            )

    return " ".join(summary_lines)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Run as a standalone MCP server (stdio mode — standard for local servers)
    # Test it: .venv\Scripts\python.exe mcp_server/learner_state_server.py
    mcp.run()
