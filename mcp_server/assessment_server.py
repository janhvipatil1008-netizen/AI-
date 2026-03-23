"""
assessment_server.py — MCP Server: Practice Scores & Weak Topic Detection

WHAT IS THIS?
--------------
This server owns all data about how the learner is performing in practice sessions.
It reads and writes `data/practice_history.json`.

Previously, the Practice Agent wrote scores itself. Now this server is the
single place where scores live — both the Practice Agent and the Learning Manager
can read from it. This is why it's an MCP server: shared access, clean boundary.

SIMPLE ANALOGY:
---------------
Think of this as the school's gradebook. Every teacher (agent) can look up
a student's grades. But only the exam teacher (Practice Agent) adds new scores.
The advisor (Learning Manager) reads the gradebook to recommend what to study next.

TOOLS EXPOSED:
--------------
  save_score(topic, mode, score, max_score, agent)  → records a practice result
  get_scores(topic, mode, limit)                    → filtered score history
  get_weak_topics(threshold)                        → topics with low average scores
  get_stats_summary()                               → plain-English progress paragraph

KEY CONCEPT — Aggregation:
---------------------------
`get_weak_topics()` doesn't just return raw scores — it *aggregates* them.
It groups scores by topic, calculates the average, and returns only the ones
below a threshold. This is a small but important idea: raw data → insight.
This is what data science is, at its simplest.

HOW TO TEST:
------------
  .venv\\Scripts\\python.exe mcp_server/assessment_server.py
  (should start without error — press Ctrl+C to stop)
"""

import json
import os
import sys
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AI² Assessment Server")

# ── Constants ─────────────────────────────────────────────────────────────────

HISTORY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "practice_history.json",
)

VALID_MODES = ("quiz", "challenge", "interview")

# ── Internal helpers ──────────────────────────────────────────────────────────

def _load_history() -> dict:
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "created_at": datetime.now().isoformat(),
        "sessions": [],
    }


def _save_history(history: dict) -> None:
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


# ── MCP Tools ─────────────────────────────────────────────────────────────────

@mcp.tool()
def save_score(
    topic: str,
    mode: str,
    score: int,
    max_score: int,
    agent: str = "practice",
    notes: str = "",
) -> str:
    """
    Record a practice session score. Call this at the end of every practice session.

    This is the only way scores enter the system — think of it as "submitting the exam."
    The Learning Manager later reads these to recommend what topics need more work.

    Args:
        topic:     What topic was practiced (e.g. "transformer attention mechanism")
        mode:      "quiz", "challenge", or "interview"
        score:     Points the learner earned (e.g. 7)
        max_score: Maximum possible points (e.g. 10)
        agent:     Which agent recorded this (default: "practice")
        notes:     Optional observation (e.g. "struggled with HNSW index details")

    Returns a confirmation string.
    """
    if mode not in VALID_MODES:
        return f"ERROR: mode '{mode}' must be one of: {', '.join(VALID_MODES)}"
    if max_score <= 0:
        return "ERROR: max_score must be greater than 0"
    if score < 0 or score > max_score:
        return f"ERROR: score {score} is outside range 0–{max_score}"

    history = _load_history()
    history.setdefault("sessions", []).append({
        "topic":      topic,
        "mode":       mode,
        "score":      score,
        "max_score":  max_score,
        "percentage": round(score / max_score * 100, 1),
        "agent":      agent,
        "notes":      notes,
        "recorded_at": datetime.now().isoformat(),
    })
    _save_history(history)

    pct = round(score / max_score * 100)
    return f"Score saved: {topic} [{mode}] — {score}/{max_score} ({pct}%)"


@mcp.tool()
def get_scores(
    topic: str = "",
    mode: str = "",
    limit: int = 10,
) -> str:
    """
    Retrieve practice session scores, optionally filtered by topic or mode.

    Use this to review recent performance, show a learner their history,
    or check if a particular topic has been practiced before.

    Args:
        topic: Filter to sessions matching this topic (partial match, case-insensitive).
               Leave empty to get all topics.
        mode:  Filter by mode — "quiz", "challenge", or "interview".
               Leave empty to get all modes.
        limit: Maximum number of results to return (default: 10, newest first).

    Returns a JSON list of session records.
    """
    history = _load_history()
    sessions = history.get("sessions", [])

    # Apply filters
    if topic:
        sessions = [s for s in sessions if topic.lower() in s["topic"].lower()]
    if mode and mode in VALID_MODES:
        sessions = [s for s in sessions if s["mode"] == mode]

    # Return newest first, capped at limit
    recent = list(reversed(sessions))[:limit]
    return json.dumps(recent, indent=2)


@mcp.tool()
def get_weak_topics(threshold: float = 0.6) -> str:
    """
    Find topics where the learner's average score is below a threshold.

    Use this to recommend what the learner should study or practice next.
    A topic is "weak" if the learner's average score on it is below the threshold.

    CONCEPT — this is data aggregation:
    Raw scores → group by topic → calculate average → filter below threshold.
    Same principle used in any analytics dashboard.

    Args:
        threshold: Score ratio below which a topic is considered weak.
                   0.6 means "less than 60% average = needs work".
                   Default: 0.6 (60%)

    Returns a JSON list of weak topics, sorted by average score (worst first).
    Each item: {"topic": "...", "avg_score": 0.45, "sessions": 3, "modes": ["quiz"]}
    """
    history = _load_history()
    sessions = history.get("sessions", [])

    if not sessions:
        return json.dumps([])

    # Group scores by topic
    topic_data: dict[str, list[float]] = defaultdict(list)
    topic_modes: dict[str, set] = defaultdict(set)

    for s in sessions:
        ratio = s["score"] / s["max_score"] if s["max_score"] > 0 else 0
        topic_data[s["topic"]].append(ratio)
        topic_modes[s["topic"]].add(s["mode"])

    # Identify weak topics
    weak = []
    for topic, ratios in topic_data.items():
        avg = sum(ratios) / len(ratios)
        if avg < threshold:
            weak.append({
                "topic":     topic,
                "avg_score": round(avg, 3),
                "sessions":  len(ratios),
                "modes":     sorted(topic_modes[topic]),
            })

    # Sort worst first
    weak.sort(key=lambda x: x["avg_score"])
    return json.dumps(weak, indent=2)


@mcp.tool()
def get_stats_summary() -> str:
    """
    Get a plain-English summary of the learner's practice history.

    Use this to give context-aware encouragement and personalised study advice.
    Returns a readable paragraph (not JSON) designed to be included directly
    in a response to the learner.
    """
    history = _load_history()
    sessions = history.get("sessions", [])

    if not sessions:
        return "No practice sessions recorded yet. Start a quiz or coding challenge to begin tracking progress!"

    total = len(sessions)
    topics_done = set(s["topic"] for s in sessions)
    modes_done = set(s["mode"] for s in sessions)

    # Overall average
    avg_pct = sum(s["percentage"] for s in sessions) / total

    # Best and worst topics (need ≥2 sessions per topic to be meaningful)
    topic_avgs = {}
    for s in sessions:
        topic_avgs.setdefault(s["topic"], []).append(s["percentage"])
    topic_avgs = {t: sum(v) / len(v) for t, v in topic_avgs.items() if len(v) >= 1}

    lines = [
        f"Practice history: {total} session(s) across {len(topics_done)} topic(s).",
        f"Modes used: {', '.join(sorted(modes_done))}.",
        f"Overall average score: {avg_pct:.0f}%.",
    ]

    if topic_avgs:
        best = max(topic_avgs, key=topic_avgs.get)
        worst = min(topic_avgs, key=topic_avgs.get)
        lines.append(f"Strongest topic: {best} ({topic_avgs[best]:.0f}% avg).")
        if best != worst:
            lines.append(f"Needs most work: {worst} ({topic_avgs[worst]:.0f}% avg).")

    if avg_pct >= 80:
        lines.append("Overall performance is strong — ready for more advanced challenges.")
    elif avg_pct >= 60:
        lines.append("Solid progress — keep building on the weaker topics.")
    else:
        lines.append("Early stages — consistent practice will build confidence quickly.")

    return " ".join(lines)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
