"""
idea_agent.py — The Idea Generation Agent for the AI² platform (Step 5).

WHAT THIS AGENT DOES:
----------------------
Helps the learner discover and plan real-world AI projects through three modes:
  - Brainstorm:      Generates 3-5 concrete project ideas based on interests
  - Project Brief:   Turns an idea into a structured, actionable build plan
  - Idea Feedback:   Evaluates the learner's own idea honestly (scores + verdict)

KEY NEW CONCEPT — Temperature Control:
----------------------------------------
The `temperature` parameter controls how creative vs. structured the AI is.
Think of it as a "creativity dial" on the API call:

    temperature=1.0  →  High creativity: surprising, varied, sometimes unexpected.
                        Great for brainstorming where you WANT diverse suggestions.

    temperature=0.3  →  Low creativity: consistent, focused, structured.
                        Great for project briefs where you need reliable formatting.

    temperature=0.5  →  Balanced: honest but not rigid.
                        Great for feedback where you want directness without
                        being so "random" that scores are inconsistent.

Range is 0.0–2.0. Default (when you don't set it) is 1.0.
Same model, same prompt — completely different character of output.

KEY NEW CONCEPT — Few-Shot Prompting:
---------------------------------------
The system prompts for this agent include WORKED EXAMPLES of the ideal output.
This is called "few-shot prompting" and it's one of the most powerful techniques
in prompt engineering:

    Zero-shot: "Generate a project idea."
    Few-shot:  "Generate a project idea. Here is an example:
                  Title: AI Email Digest
                  What it does: ...
                Now generate one in the same format."

The AI sees the example and matches it exactly — no lengthy format instructions needed.
See config/prompts.py → build_idea_system_prompt() for the examples.

KEY CONCEPT REVISION — Action Tokens (from Step 2):
-----------------------------------------------------
Like the Learning Manager, this agent uses action tokens to save ideas.
The AI writes a special line in its response:
  ACTION: SAVE_IDEA | title | description | topic

Our code parses this line and saves the idea to data/ideas.json automatically.
The user never sees the raw token — it's hidden and acted upon silently.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from config.settings import MAX_HISTORY_TURNS, DEFAULT_SKILL_LEVEL
from config.prompts import build_idea_system_prompt
from utils.claude_client import ClaudeClient
from utils.skills_loader import load_combined_skill
from utils.browser_tools import browse_url, scrape_github_repo


class IdeaAgent:
    """
    An idea generation coach that brainstorms project ideas, builds project
    briefs, and evaluates the learner's own ideas.

    Usage:
        agent = IdeaAgent()
        agent.set_mode("brainstorm")
        reply, notification = agent.chat("I'm interested in building something with LLMs")
        if notification:
            print(f"Idea saved: {notification['idea']['title']}")

    The agent saves ideas to data/ideas.json automatically when the AI
    signals a save via the ACTION: SAVE_IDEA token.
    """

    IDEAS_PATH = "data/ideas.json"

    # ── Temperature map ───────────────────────────────────────────────────────
    # This is the core teaching concept for Step 5.
    # Each mode uses a different temperature — same model, different character.
    _TEMPERATURE: dict[str, float] = {
        "brainstorm": 1.0,   # creative and varied — we WANT surprising ideas
        "brief":      0.3,   # structured and consistent — we need reliable formatting
        "feedback":   0.5,   # balanced — direct but not erratic
    }

    def __init__(self) -> None:
        self.client = ClaudeClient()
        self.mode: str = "brainstorm"
        self.skill_level: str = DEFAULT_SKILL_LEVEL

        # Persistent ideas library — saved across browser sessions
        self.ideas = self._load_ideas()

        # Conversation history starts with a system prompt.
        # Unlike PracticeAgent, there's no start_session() — chat starts immediately.
        # The system prompt is rebuilt whenever mode or skill_level changes.
        system_text = build_idea_system_prompt(self.mode, self.skill_level)
        system_text += "\n\n" + load_combined_skill("ideas")
        self.conversation_history: list[dict] = [
            {"role": "system", "content": system_text}
        ]

    # ── Setters ───────────────────────────────────────────────────────────────

    def set_mode(self, mode: str) -> None:
        """
        Switch to a different mode: 'brainstorm', 'brief', or 'feedback'.

        KEY TEACHING MOMENT:
        This is all it takes to completely change the agent's personality.
        No new class, no new model, no new API key — just a new system prompt.
        The system prompt IS the agent's behaviour.

        We reset conversation history too, because mixing brainstorm and brief
        in the same history would confuse the AI.
        """
        self.mode = mode
        system_text = build_idea_system_prompt(self.mode, self.skill_level)
        system_text += "\n\n" + load_combined_skill("ideas")
        self.conversation_history = [
            {"role": "system", "content": system_text}
        ]

    def set_skill_level(self, level: str) -> None:
        """
        Change the skill level: 'beginner', 'intermediate', or 'advanced'.

        Also rebuilds the system prompt so the AI adapts its language
        immediately — same pattern as set_mode().
        """
        self.skill_level = level
        system_text = build_idea_system_prompt(self.mode, self.skill_level)
        system_text += "\n\n" + load_combined_skill("ideas")
        self.conversation_history[0] = {
            "role": "system",
            "content": system_text,
        }

    # ── Tool execution ────────────────────────────────────────────────────────

    def _execute_tool(self, tool_name: str, tool_args: dict) -> str:
        """
        Route browser tool calls from the ReAct loop.

        Spark has browse_url (research existing projects, docs, market context)
        and scrape_github_repo (examine trending or competing repos).
        """
        if tool_name == "browse_url":
            return browse_url(tool_args.get("url", ""), tool_args.get("question", ""))
        if tool_name == "scrape_github_repo":
            return scrape_github_repo(tool_args.get("repo_url", ""))
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    # ── Core chat ─────────────────────────────────────────────────────────────

    def chat(self, user_message: str) -> tuple[str, dict | None]:
        """
        Send a message and get back the AI's reply.

        Returns a tuple — same pattern as LearningAgent and PracticeAgent:
            (reply_text, notification_dict_or_None)

        notification_dict is non-None when an idea was saved this turn:
            {
                "idea_saved": True,
                "idea": {
                    "id":          "idea_1741776000",
                    "title":       "AI Flashcard Generator",
                    "description": "...",
                    "topic":       "Prompt engineering and LLM best practices",
                    "mode_created_in": "brainstorm",
                    "saved_at":    "2026-03-15T10:00:00+00:00",
                }
            }

        WHY temperature matters here:
        The API call uses self._TEMPERATURE[self.mode] — so brainstorm calls
        use temperature=1.0 and brief calls use temperature=0.3.
        Run the same brainstorm message twice and you'll get different ideas.
        Run the same brief message twice and you'll get very similar structure.

        Args:
            user_message: What the learner typed.

        Returns:
            (reply_text, notification_or_None)
        """
        # Step 1: Add user message to history
        self.conversation_history.append({"role": "user", "content": user_message})

        # Step 2: Call Claude — temperature changes per mode (key concept).
        # chat_with_tools() is used so Spark can browse_url and scrape_github_repo.
        system = self.conversation_history[0]["content"]
        messages = [m for m in self.conversation_history if m["role"] != "system"]
        reply = self.client.chat_with_tools(
            messages=messages,
            system=system,
            agent_name="ideas",
            tool_executor=self._execute_tool,
            temperature=self._TEMPERATURE[self.mode],   # ← brainstorm=1.0, brief=0.3, feedback=0.5
        )

        # Step 3: Add reply to history
        self.conversation_history.append({"role": "assistant", "content": reply})

        # Step 4: Trim history to avoid token bloat
        max_messages = 1 + (MAX_HISTORY_TURNS * 2)
        if len(self.conversation_history) > max_messages:
            self.conversation_history = (
                [self.conversation_history[0]]
                + self.conversation_history[-(MAX_HISTORY_TURNS * 2):]
            )

        # Step 5: Parse and apply any ACTION tokens in the reply
        action = self._parse_action(reply)
        notification = self._apply_action(action) if action else None

        return reply, notification

    # ── Action token parsing ──────────────────────────────────────────────────

    def _parse_action(self, reply: str) -> dict | None:
        """
        Scan the AI's reply for an ACTION: SAVE_IDEA token.

        The AI is instructed (via the system prompt) to embed this line
        when it has generated an idea the learner has chosen:
            ACTION: SAVE_IDEA | title | description | topic

        This is the same "action token" pattern introduced in Step 2
        (LearningAgent uses ACTION: COMPLETE_TOPIC, ADD_TODO, etc.).

        Args:
            reply: The AI's full response text.

        Returns:
            A dict with type + fields, or None if no action found.
        """
        for line in reply.splitlines():
            line = line.strip()
            if line.startswith("ACTION: SAVE_IDEA"):
                # Parse "SAVE_IDEA | title | description | topic"
                _, _, rest = line.partition(":")
                parts = [p.strip() for p in rest.split("|")]
                # parts[0] = " SAVE_IDEA", parts[1] = title, etc.
                if len(parts) >= 4:
                    return {
                        "type": "SAVE_IDEA",
                        "title": parts[1],
                        "description": parts[2],
                        "topic": parts[3],
                    }
        return None

    def _apply_action(self, action: dict) -> dict | None:
        """
        Execute a parsed action token — in this case, save an idea to disk.

        Args:
            action: Dict from _parse_action().

        Returns:
            Notification dict for the page, or None if action type unknown.
        """
        if action["type"] != "SAVE_IDEA":
            return None

        now = datetime.now(timezone.utc).isoformat()
        idea = {
            "id": f"idea_{int(time.time())}",
            "title": action["title"],
            "description": action["description"],
            "topic": action["topic"],
            "mode_created_in": self.mode,
            "saved_at": now,
        }
        self.ideas["ideas"].append(idea)
        self._save_ideas()

        return {"idea_saved": True, "idea": idea}

    # ── Ideas library ─────────────────────────────────────────────────────────

    def get_ideas(self) -> list[dict]:
        """Return all saved project ideas, newest first."""
        return list(reversed(self.ideas.get("ideas", [])))

    def delete_idea(self, idea_id: str) -> bool:
        """
        Remove an idea from the library by its ID.

        Args:
            idea_id: The "id" field, e.g. "idea_1741776000".

        Returns:
            True if found and deleted, False if not found.
        """
        ideas = self.ideas.get("ideas", [])
        original_len = len(ideas)
        self.ideas["ideas"] = [i for i in ideas if i["id"] != idea_id]
        if len(self.ideas["ideas"]) < original_len:
            self._save_ideas()
            return True
        return False

    # ── Persistence ───────────────────────────────────────────────────────────

    def _make_default_ideas(self) -> dict:
        """Create an empty ideas library structure."""
        now = datetime.now(timezone.utc).isoformat()
        return {"created_at": now, "updated_at": now, "ideas": []}

    def _load_ideas(self) -> dict:
        """Load ideas from disk. Create the file if it doesn't exist."""
        path = Path(self.IDEAS_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)

        if not path.exists():
            data = self._make_default_ideas()
            path.write_text(json.dumps(data, indent=2))
            return data

        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, Exception):
            data = self._make_default_ideas()
            path.write_text(json.dumps(data, indent=2))
            return data

    def _save_ideas(self) -> None:
        """Save the ideas library to disk."""
        self.ideas["updated_at"] = datetime.now(timezone.utc).isoformat()
        Path(self.IDEAS_PATH).write_text(json.dumps(self.ideas, indent=2))

    # ── Standard interface ────────────────────────────────────────────────────

    def reset(self) -> None:
        """
        Clear the conversation history.

        IMPORTANT: This does NOT delete saved ideas — only the chat.
        The ideas library persists across resets, exactly like
        LearningAgent preserves todos when you reset chat.
        """
        system_text = build_idea_system_prompt(self.mode, self.skill_level)
        system_text += "\n\n" + load_combined_skill("ideas")
        self.conversation_history = [
            {"role": "system", "content": system_text}
        ]

    def get_history(self) -> list[dict]:
        """Return the full conversation history."""
        return self.conversation_history

    def to_dict(self) -> dict:
        """Serialize agent state for the future orchestrator."""
        return {
            "agent": "idea",
            "mode": self.mode,
            "skill_level": self.skill_level,
            "history": self.conversation_history,
            "saved_ideas_count": len(self.ideas.get("ideas", [])),
        }
