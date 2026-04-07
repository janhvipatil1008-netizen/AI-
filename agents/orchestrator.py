"""
orchestrator.py — Central routing layer for the AI² platform.

HOW IT WORKS (step by step):
─────────────────────────────
1. classify()
   Sends ONE fast claude-haiku call (temperature=0, max_tokens=10).
   The prompt describes each agent's job and the learner's current context.
   Returns a single word: atlas | dojo | spark.
   Cost: ~$0.0001 per message routed.

2. _get_agent()
   Lazy-loads agent instances on first use and caches them in self._agents{}.
   This means Atlas, Dojo, and Spark each maintain their own
   conversation history across all messages in the session.

3. chat()
   classify → get_agent → call agent.chat() → normalise return type
   → strip ACTION/HANDOFF lines from display → detect handoffs → return.

4. Handoffs (_detect_handoff)
   If the agent's reply contains a line like:
     HANDOFF: DOJO | RAG systems
   ...the orchestrator sets self._pre_route = "dojo" so the NEXT message
   is automatically sent to Dojo — no user action needed.
   This is how Atlas can say "go practice this in Dojo" and actually make it happen.

WHY NO CHANGES TO INDIVIDUAL AGENTS:
   LearningAgent.chat() → returns (str, dict) (result = handoff or None)
   PracticeAgent.chat() → returns (list[str], dict) (result = quiz/score result)
   IdeaAgent.chat()     → returns (str, dict) (result = save notification)
   The orchestrator handles all return shapes transparently.
"""

import json
from pathlib import Path

from utils.claude_client import ClaudeClient

PROFILE_PATH = Path("data/learning_profile.json")

# ── Classification prompt ──────────────────────────────────────────────────────
# WHY: We give the AI exactly 3 choices with clear, non-overlapping examples.
# "Last agent used" helps the classifier maintain conversational continuity.

_CLASSIFY_PROMPT = """You are a router for the AI² learning platform.
Route the learner's message to one of these 3 agents:

atlas  — study planning, "what should I learn next", progress tracking, goal setting, topic explanation, research a concept, coding concepts explained
dojo   — "quiz me", "test my knowledge", practice exercises, mock interview, coding challenge, "how well do I know X"
spark  — "give me project ideas", brainstorming, "what should I build", project planning, project feedback

Context:
  Current phase: {phase}
  Skill level: {skill}
  Last agent used: {last_agent}

Learner message: "{message}"

Respond with ONLY one word (no punctuation, no explanation): atlas | dojo | spark"""

# ── Handoff prefix → target agent ─────────────────────────────────────────────
# Any agent can emit "HANDOFF: DOJO | topic" to pre-route the next message.
_HANDOFF_PREFIXES = {
    "HANDOFF: ATLAS":    "atlas",
    "HANDOFF: DOJO":     "dojo",
    "HANDOFF: SPARK":    "spark",
    "HANDOFF: RESEARCH": "atlas",   # atlas handles research in its own mode
}


class Orchestrator:
    """
    Central router that wraps all 4 AI² agents.

    Usage (from workspace.py):
        orch = Orchestrator()
        agent_key, display, result = orch.chat("how do I implement RAG?")
        # agent_key = "forge"
        # display   = clean markdown, ACTION/HANDOFF lines stripped
        # result    = None (Forge) | dict (Dojo/Spark/Atlas special results)
    """

    def __init__(self):
        self.client       = ClaudeClient()
        self._agents: dict = {}              # {key: agent_instance}
        self._last_agent: str | None = None
        self._pre_route:  str | None = None  # forced next agent (from handoff)

    # ── Profile ───────────────────────────────────────────────────────────────

    def _load_profile(self) -> dict:
        if PROFILE_PATH.exists():
            try:
                return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    # ── Agent cache ───────────────────────────────────────────────────────────

    def _get_agent(self, key: str, profile: dict):
        """
        Lazy-load and cache an agent instance.

        WHY LAZY: We don't want to create all 4 agents on startup — each one
        loads its profile, history, and skill files. Only create what's needed.
        WHY CACHE: Each agent keeps its own conversation_history in memory.
        Returning the same instance means history is preserved across turns.
        """
        if key not in self._agents:
            skill = profile.get("skill_level", "beginner")
            if key == "atlas":
                from agents.learning_agent import LearningAgent
                self._agents[key] = LearningAgent()
            elif key == "dojo":
                from agents.practice_agent import PracticeAgent
                self._agents[key] = PracticeAgent()
            elif key == "spark":
                from agents.idea_agent import IdeaAgent
                a = IdeaAgent()
                a.set_skill_level(skill)
                self._agents[key] = a
        return self._agents[key]

    # ── Classification ────────────────────────────────────────────────────────

    def classify(self, message: str, profile: dict) -> str:
        """
        One claude-haiku-4-5 call → returns agent key.

        WHY HAIKU: It's the fastest and cheapest Claude model. For a routing
        decision that just needs to pick one of 4 options, haiku is perfect.
        We use temperature=0 for deterministic, consistent routing.
        """
        from config.syllabus import get_current_phase_id
        phase = get_current_phase_id(
            profile.get("syllabus_progress", {}),
            profile.get("selected_roles", ["aipm"]),
        )
        prompt = _CLASSIFY_PROMPT.format(
            phase=phase,
            skill=profile.get("skill_level", "beginner"),
            last_agent=self._last_agent or "none",
            message=message,
        )
        result = self.client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10,
            model="claude-haiku-4-5-20251001",
        ).strip().lower()

        # Validate — fall back to atlas if haiku returns something unexpected
        return result if result in ("atlas", "dojo", "spark") else "atlas"

    # ── Handoff detection ─────────────────────────────────────────────────────

    def _detect_handoff(self, reply: str) -> str | None:
        """
        Scan a reply for HANDOFF: lines and return the target agent key.

        WHY: Any agent can signal "route the next message to X" by including
        a line like: HANDOFF: DOJO | RAG systems
        The orchestrator catches this and sets self._pre_route so the next
        call to chat() bypasses classification and goes directly to that agent.
        """
        for line in reply.splitlines():
            line = line.strip()
            for prefix, target in _HANDOFF_PREFIXES.items():
                if line.startswith(prefix):
                    return target
        return None

    # ── Core interface ────────────────────────────────────────────────────────

    def chat(self, message: str) -> tuple[str, str, object]:
        """
        Route a message to the correct agent and return the response.

        Returns:
            (agent_key, display_text, result)

            agent_key:    "atlas" | "dojo" | "spark"
            display_text: Clean markdown ready to show the user.
                          ACTION: and HANDOFF: lines are stripped out.
            result:       None for Atlas chat,
                          or the structured result dict from Dojo/Spark.
                          - Dojo: {"correct": bool, "score": int, "session_complete": bool, ...}
                          - Spark: {"idea_saved": True, "idea": {...}} or None

        Flow:
            1. If a handoff was detected last turn, use pre_route (skip classify)
            2. Otherwise, classify the message
            3. Get (or create) the target agent from cache
            4. Call agent.chat() — normalise the return type
            5. Strip action/handoff tokens from display text
            6. Detect any handoff signal for the NEXT message
            7. Return (agent_key, display, result)
        """
        profile = self._load_profile()

        # Step 1: Honour a pre-routed handoff
        if self._pre_route:
            agent_key = self._pre_route
            self._pre_route = None
        else:
            agent_key = self.classify(message, profile)

        # Step 2: Get the agent instance
        agent = self._get_agent(agent_key, profile)

        # Step 3: Call agent.chat() — handle polymorphic return types
        try:
            raw = agent.chat(message)
        except Exception as e:
            return agent_key, f"Something went wrong with {agent_key}: {e}", None
        if isinstance(raw, tuple):
            reply, result = raw
        else:
            reply, result = raw, None

        # PracticeAgent returns a list of strings (grade + next question as
        # separate items); flatten to a single string for the orchestrator display.
        if isinstance(reply, list):
            reply = "\n\n---\n\n".join(reply)

        # Step 4: Strip internal tokens from what the user sees
        display = "\n".join(
            line for line in reply.splitlines()
            if not line.strip().startswith(("ACTION:", "HANDOFF:"))
        ).strip()

        # Step 5: Detect handoff signal for the NEXT message
        self._pre_route = self._detect_handoff(reply)

        # Step 6: Track and return
        self._last_agent = agent_key
        print(f"[router] → {agent_key}")  # visible in Streamlit server logs
        return agent_key, display, result

    # ── Utility ───────────────────────────────────────────────────────────────

    def get_last_agent(self) -> str | None:
        """Return the key of the agent that handled the most recent message."""
        return self._last_agent

    def reset_agent(self, key: str) -> bool:
        """
        Reset a specific agent's conversation history.

        Useful if the user wants to start fresh with one agent while keeping
        others' histories intact.
        """
        if key in self._agents and hasattr(self._agents[key], "reset"):
            self._agents[key].reset()
            return True
        return False
