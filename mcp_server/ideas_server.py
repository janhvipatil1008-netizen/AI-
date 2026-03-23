"""
ideas_server.py — MCP Server: Project Ideas Library

WHAT IS THIS?
--------------
This server owns all data about the learner's saved project ideas.
It reads and writes `data/ideas.json`.

Previously, the Idea Agent saved ideas directly using its own methods.
Now this server is the single gateway — the Idea Agent calls it via MCP,
and in the future any other agent (e.g. Learning Manager) could also read ideas.

SIMPLE ANALOGY:
---------------
Think of this as the learner's idea notebook. The Idea Agent writes notes in it.
The Learning Manager can read it to connect learning topics with project ideas.
Everyone uses the same notebook.

TOOLS EXPOSED:
--------------
  save_idea(title, description, topic, mode)  → saves a new idea
  get_ideas(limit)                            → returns saved ideas (newest first)
  delete_idea(idea_id)                        → removes an idea by ID
  search_ideas(query)                         → keyword search across ideas

KEY CONCEPT — search_ideas():
------------------------------
Simple keyword search without any AI. We just check if the query word appears
in the title or description. This is called "full-text search" at its simplest.
Production apps use dedicated search engines (Elasticsearch, Typesense) but for
a small ideas library, this is fast and works well.

HOW TO TEST:
------------
  .venv\\Scripts\\python.exe mcp_server/ideas_server.py
  (should start without error — press Ctrl+C to stop)
"""

import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AI² Ideas Server")

# ── Constants ─────────────────────────────────────────────────────────────────

IDEAS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "ideas.json",
)

# ── Internal helpers ──────────────────────────────────────────────────────────

def _load_ideas() -> dict:
    if os.path.exists(IDEAS_PATH):
        with open(IDEAS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "ideas": [],
    }


def _save_ideas(store: dict) -> None:
    store["updated_at"] = datetime.now().isoformat()
    os.makedirs(os.path.dirname(IDEAS_PATH), exist_ok=True)
    with open(IDEAS_PATH, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)


# ── MCP Tools ─────────────────────────────────────────────────────────────────

@mcp.tool()
def save_idea(
    title: str,
    description: str,
    topic: str,
    mode: str = "brainstorm",
) -> str:
    """
    Save a project idea to the learner's ideas library.

    Call this when the learner has expressed interest in a specific project idea
    and wants to keep it. The idea is stored permanently and visible in the sidebar.

    Args:
        title:       Short project name (e.g. "AI Email Summariser")
        description: 1-3 sentence description of what it does and how
        topic:       The AI/ML topic area (e.g. "NLP", "RAG", "prompt engineering")
        mode:        Which mode generated it — "brainstorm", "brief", or "feedback"

    Returns the new idea's ID (e.g. "idea_1741776000") for reference.
    """
    if not title.strip():
        return "ERROR: title cannot be empty"
    if not description.strip():
        return "ERROR: description cannot be empty"

    store = _load_ideas()

    # Generate a stable unique ID from the current timestamp
    idea_id = f"idea_{int(time.time())}"

    store["ideas"].append({
        "id":              idea_id,
        "title":           title.strip(),
        "description":     description.strip(),
        "topic":           topic.strip(),
        "mode_created_in": mode,
        "saved_at":        datetime.now().isoformat(),
    })

    _save_ideas(store)
    return f"Idea saved with id={idea_id}: '{title}'"


@mcp.tool()
def get_ideas(limit: int = 20) -> str:
    """
    Get the learner's saved project ideas, newest first.

    Use this to:
    - Show the learner their ideas library
    - Find related ideas before suggesting a new one
    - Remind the learner what they were previously excited about

    Args:
        limit: Maximum number of ideas to return (default: 20)

    Returns a JSON list of ideas. Empty list if none saved yet.
    """
    store = _load_ideas()
    ideas = store.get("ideas", [])
    # Newest first
    recent = list(reversed(ideas))[:limit]
    return json.dumps(recent, indent=2)


@mcp.tool()
def delete_idea(idea_id: str) -> str:
    """
    Delete a saved idea by its ID.

    Call this when the learner explicitly asks to remove an idea.
    The ID is visible in the ideas library (format: "idea_<timestamp>").

    Args:
        idea_id: The idea's unique ID (e.g. "idea_1741776000")

    Returns "Deleted: <title>" if found, or an error message if not found.
    """
    store = _load_ideas()
    ideas = store.get("ideas", [])

    original_count = len(ideas)
    matching = [i for i in ideas if i["id"] == idea_id]
    store["ideas"] = [i for i in ideas if i["id"] != idea_id]

    if len(store["ideas"]) < original_count:
        title = matching[0]["title"] if matching else idea_id
        _save_ideas(store)
        return f"Deleted: '{title}'"
    else:
        return f"ERROR: No idea found with id='{idea_id}'"


@mcp.tool()
def search_ideas(query: str) -> str:
    """
    Search saved ideas by keyword.

    Searches across title, description, and topic fields.
    Case-insensitive. Returns all matching ideas (no limit).

    Use this when:
    - The learner asks "do I have any ideas about RAG?"
    - You want to avoid duplicating an idea that's already saved
    - The learner wants to find an old idea they remember partially

    Args:
        query: Search keyword or phrase (e.g. "RAG", "NLP", "summariser")

    Returns a JSON list of matching ideas, newest first.
    """
    if not query.strip():
        return json.dumps([])

    store = _load_ideas()
    ideas = store.get("ideas", [])
    query_lower = query.lower()

    matches = [
        idea for idea in reversed(ideas)
        if (
            query_lower in idea.get("title", "").lower()
            or query_lower in idea.get("description", "").lower()
            or query_lower in idea.get("topic", "").lower()
        )
    ]

    return json.dumps(matches, indent=2)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
