"""
learning_agent.py — The Learning Management Agent for the AI² platform.

WHAT THIS AGENT DOES (simple explanation):
------------------------------------------
Think of this as your personal learning coach — not the teacher (that's
the Coding Agent), but the person who helps you:
  - Track which topics you've completed
  - Manage your to-do list
  - Decide what to study next
  - Save notes about what you've learned
  - Find resources for any topic
  - Hand you off to the Research Agent when you want to go deep

KEY NEW CONCEPT — Persistence:
-------------------------------
Unlike the Coding Agent (which forgets everything when you close the browser),
this agent SAVES your progress to a file: data/learning_profile.json

Every time you complete a topic, add a todo, or save a note, the JSON file
is updated. When you come back tomorrow, your progress is still there.

KEY NEW CONCEPT — Action Tokens:
---------------------------------
The LLM can't directly change a file. So we use a trick: we tell the AI
to write special "command lines" in its responses, like:
  ACTION: COMPLETE_TOPIC | Python fundamentals: functions, OOP, async/await

Our code then reads these lines and executes the commands.
It's like leaving a note that says "please do this" and having our code
act on the note automatically.
"""

import json
import time
from datetime import date, datetime, timezone
from pathlib import Path

from config.settings import MAX_HISTORY_TURNS
from config.prompts import CURRICULUM_TOPICS, build_learning_system_prompt
from config.syllabus import PHASES, get_task_key
from utils.claude_client import ClaudeClient
from utils.skills_loader import load_combined_skill


class LearningAgent:
    """
    A learning coach that tracks progress, manages to-dos, and helps
    the learner plan their AI learning journey.

    Usage:
        agent = LearningAgent()
        response, handoff = agent.chat("What should I study next?")
        print(response)
        if handoff:
            print(f"Hand off to: {handoff['agent']} for topic: {handoff['topic']}")
    """

    PROFILE_PATH = "data/learning_profile.json"

    def __init__(self):
        self.client = ClaudeClient()
        self.profile = self._load_profile()

        # Build conversation history with a fresh system message that
        # reflects the CURRENT state of the profile.
        system_text = build_learning_system_prompt(self.profile)
        system_text += "\n\n" + load_combined_skill("learning")
        self.conversation_history: list[dict] = [
            {"role": "system", "content": system_text}
        ]

        # Stores the most recently achieved goal for the UI to pick up
        self._last_achievement: dict | None = None

        # Restore previous conversation so the learner can pick up where
        # they left off after closing and reopening the browser.
        saved_history = self.profile.get("conversation_history", [])
        if saved_history and len(saved_history) > 1:
            # Skip index 0 (the saved system message) — we just built a
            # fresh one above with the latest profile state.
            self.conversation_history += saved_history[1:]

    # ── Profile I/O ───────────────────────────────────────────────────────────

    def _make_default_profile(self) -> dict:
        """
        Create a fresh learning profile with all 12 topics set to 'pending'.

        This runs the FIRST TIME the agent is used (no profile file exists yet).
        """
        now = datetime.now(timezone.utc).isoformat()
        return {
            "skill_level": "beginner",
            "created_at": now,
            "updated_at": now,
            "topics": {
                topic: {
                    "status": "pending",
                    "started_at": None,
                    "completed_at": None,
                    "notes": "",
                }
                for topic in CURRICULUM_TOPICS
            },
            "todos": [],
            "goals": [],
            "selected_roles": ["aipm", "evals", "context"],
            "syllabus_progress": {},
            "conversation_history": [],
        }

    def _load_profile(self) -> dict:
        """
        Load the profile from disk. Create it if it doesn't exist.

        The `Path.mkdir(parents=True, exist_ok=True)` call creates the
        'data/' folder automatically — you don't need to create it manually.
        """
        path = Path(self.PROFILE_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)

        if not path.exists():
            profile = self._make_default_profile()
            path.write_text(json.dumps(profile, indent=2))
            return profile

        try:
            profile = json.loads(path.read_text())
            # Migration guards — add fields missing from older profiles
            if "goals" not in profile:
                profile["goals"] = []
            if "selected_roles" not in profile:
                profile["selected_roles"] = ["aipm", "evals", "context"]
            if "syllabus_progress" not in profile:
                profile["syllabus_progress"] = {}
            return profile
        except (json.JSONDecodeError, Exception):
            # If the file is corrupted, start fresh rather than crashing.
            profile = self._make_default_profile()
            path.write_text(json.dumps(profile, indent=2))
            return profile

    def _save_profile(self) -> None:
        """
        Save the current profile (including conversation history) to disk.

        Called automatically after every chat() call and after any
        profile-changing action (add todo, complete topic, etc.).
        """
        # Recalculate goal health on every save (catches deadline transitions)
        for goal in self.profile.get("goals", []):
            if goal.get("status") not in ("achieved",):
                self._recalculate_health(goal)
        self.profile["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.profile["conversation_history"] = self.conversation_history
        Path(self.PROFILE_PATH).write_text(json.dumps(self.profile, indent=2))

    def _rebuild_system_message(self) -> None:
        """
        Replace the system message (history[0]) with a fresh one built
        from the current profile state.

        WHY: After completing a topic or adding a todo, we want the AI to
        immediately see the updated state on the NEXT turn — not the old one.
        Replacing history[0] is the correct way to update the system prompt.
        """
        system_text = build_learning_system_prompt(self.profile)
        system_text += "\n\n" + load_combined_skill("learning")
        self.conversation_history[0] = {
            "role": "system",
            "content": system_text,
        }

    # ── Action token parsing ───────────────────────────────────────────────────

    def _parse_actions(self, response: str) -> list[dict]:
        """
        Scan the LLM's response for embedded action tokens and parse them.

        WHY: The LLM can't directly edit our JSON file. Instead, we train
        it (via the system prompt) to write structured tokens like:
          ACTION: ADD_TODO | Practice httpx | Working with APIs

        This method finds those lines and converts them into structured dicts
        our code can act on.

        Args:
            response: The full text of the LLM's reply.

        Returns:
            A list of action dicts, e.g.:
            [{"type": "ADD_TODO", "args": ["Practice httpx", "Working with APIs"]}]
        """
        actions = []
        for line in response.splitlines():
            line = line.strip()
            if line.startswith("ACTION:") or line.startswith("HANDOFF:"):
                # Split on the first colon to get the type prefix
                prefix, _, rest = line.partition(":")
                parts = [p.strip() for p in rest.split("|")]
                if len(parts) >= 1:
                    action_type = parts[0].strip()
                    args = parts[1:] if len(parts) > 1 else []
                    actions.append({"type": action_type, "args": args})
        return actions

    def _apply_actions(self, actions: list[dict]) -> None:
        """
        Execute each parsed action by calling the appropriate method.

        After applying all non-handoff actions, saves the profile and
        rebuilds the system message so the next LLM call sees the update.

        Args:
            actions: The list returned by _parse_actions().
        """
        changed = False

        for action in actions:
            atype = action["type"]
            args = action["args"]

            if atype == "ADD_TODO" and len(args) >= 1:
                text = args[0]
                topic = args[1] if len(args) > 1 else "General"
                self.add_todo(text, topic)
                changed = True

            elif atype == "ADD_NOTE" and len(args) >= 2:
                self.add_note(args[0], args[1])
                changed = True

            elif atype == "COMPLETE_TOPIC" and len(args) >= 1:
                self.set_topic_status(args[0], "completed")
                changed = True

            elif atype == "COMPLETE_TODO" and len(args) >= 1:
                self.complete_todo(args[0])
                changed = True

            elif atype == "SET_GOAL" and len(args) >= 4:
                topics_list = [t.strip() for t in args[2].split(",") if t.strip()]
                ms_list     = [m.strip() for m in args[3].split(";") if m.strip()]
                deadline    = args[1].strip() if args[1].strip().lower() != "none" else None
                self.add_goal(args[0], deadline, topics_list, ms_list, raw_input=args[0])
                changed = True

            elif atype == "LOG_PROGRESS" and len(args) >= 3:
                try:
                    hours = float(args[1])
                except (ValueError, TypeError):
                    hours = 0.0
                self.log_progress(args[0], hours, args[2])
                changed = True

            elif atype == "ACHIEVE_GOAL" and len(args) >= 1:
                result = self.achieve_goal(args[0])
                if result:
                    self._last_achievement = result
                changed = True

            elif atype == "COMPLETE_MILESTONE" and len(args) >= 2:
                self.complete_milestone(args[0], args[1])
                changed = True

            elif atype == "ADD_MILESTONE" and len(args) >= 2:
                self.add_milestone(args[0], args[1])
                changed = True

            elif atype == "TASK_DONE" and len(args) >= 1:
                self.set_syllabus_task(args[0].strip(), "done")
                changed = True

            elif atype == "TASK_START" and len(args) >= 1:
                self.set_syllabus_task(args[0].strip(), "in_progress")
                changed = True

            # HANDOFF_RESEARCH is handled by detect_handoff(), not here.

        if changed:
            self._save_profile()
            self._rebuild_system_message()

    # ── Progress management ───────────────────────────────────────────────────

    def get_progress(self) -> dict:
        """
        Return a summary of the learner's topic progress.

        Returns:
            {
                "completed": [...topic names...],
                "in_progress": [...topic names...],
                "pending": [...topic names...],
                "total": 12,
                "pct": 33,   # percentage complete (0-100)
            }
        """
        topics = self.profile.get("topics", {})
        completed = [t for t, v in topics.items() if v.get("status") == "completed"]
        in_progress = [t for t, v in topics.items() if v.get("status") == "in_progress"]
        pending = [t for t, v in topics.items() if v.get("status") == "pending"]
        total = len(topics)
        pct = round(len(completed) / total * 100) if total > 0 else 0
        return {
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "total": total,
            "pct": pct,
        }

    def set_topic_status(self, topic: str, status: str) -> bool:
        """
        Change a topic's status to 'pending', 'in_progress', or 'completed'.

        Also records timestamps for when the topic was started and finished.

        Args:
            topic: Must match exactly one of the CURRICULUM_TOPICS strings.
            status: One of "pending", "in_progress", "completed".

        Returns:
            True if the update succeeded, False if the topic wasn't found.
        """
        topics = self.profile.get("topics", {})
        if topic not in topics:
            return False

        now = datetime.now(timezone.utc).isoformat()
        topics[topic]["status"] = status

        if status == "in_progress" and not topics[topic].get("started_at"):
            topics[topic]["started_at"] = now
        elif status == "completed":
            if not topics[topic].get("started_at"):
                topics[topic]["started_at"] = now
            topics[topic]["completed_at"] = now
        elif status == "pending":
            # Resetting — clear timestamps
            topics[topic]["started_at"] = None
            topics[topic]["completed_at"] = None

        self._save_profile()
        self._rebuild_system_message()
        return True

    def add_note(self, topic: str, note_text: str) -> bool:
        """
        Append a note to a topic.

        Notes are cumulative — each new note is added below the previous ones.

        Args:
            topic: Must match a CURRICULUM_TOPICS string.
            note_text: The note to save.

        Returns:
            True if saved, False if topic not found.
        """
        topics = self.profile.get("topics", {})
        if topic not in topics:
            return False

        existing = topics[topic].get("notes", "")
        if existing:
            topics[topic]["notes"] = existing + "\n" + note_text
        else:
            topics[topic]["notes"] = note_text

        self._save_profile()
        return True

    # ── To-do management ──────────────────────────────────────────────────────

    def add_todo(self, text: str, topic: str = "General") -> dict:
        """
        Add a new to-do item to the learner's list.

        The ID is based on the current timestamp so it's unique and sortable.

        Args:
            text: Description of the task.
            topic: Which curriculum topic this task relates to (optional).

        Returns:
            The new to-do dict so the UI can display it immediately.
        """
        now = datetime.now(timezone.utc).isoformat()
        todo = {
            "id": f"todo_{int(time.time())}",
            "text": text,
            "topic": topic,
            "status": "pending",
            "created_at": now,
            "completed_at": None,
        }
        self.profile["todos"].append(todo)
        self._save_profile()
        return todo

    def complete_todo(self, todo_id: str) -> bool:
        """
        Mark a to-do item as completed.

        Args:
            todo_id: The "id" field of the todo, e.g. "todo_1710374400".

        Returns:
            True if found and marked done, False if not found.
        """
        for todo in self.profile.get("todos", []):
            if todo["id"] == todo_id:
                todo["status"] = "completed"
                todo["completed_at"] = datetime.now(timezone.utc).isoformat()
                self._save_profile()
                return True
        return False

    def get_todos(self, status: str = "pending") -> list[dict]:
        """
        Return to-do items filtered by status.

        Args:
            status: "pending", "completed", or None (returns all todos).

        Returns:
            Filtered list of todo dicts.
        """
        todos = self.profile.get("todos", [])
        if status is None:
            return todos
        return [t for t in todos if t.get("status") == status]

    # ── Goal management ───────────────────────────────────────────────────────

    def _make_goal_id(self) -> str:
        return f"goal_{int(time.time())}"

    def _make_milestone_id(self) -> str:
        return f"ms_{int(time.time() * 1000) % 10_000_000}"

    def _get_goal_by_id(self, goal_id: str) -> dict | None:
        return next(
            (g for g in self.profile.get("goals", []) if g["id"] == goal_id),
            None,
        )

    def _recalculate_health(self, goal: dict) -> dict:
        """
        Mutate goal["health"], goal["health_score"], goal["updated_at"] in-place.

        Score starts at 50. Three independent factors:
          Milestones ratio  ± 30 pts  (0% → -30, 100% → +30)
          Time pressure     ± 25 pts  (ahead of schedule vs behind)
          Recent activity   ± 20 pts  (≤3 days → +20, 14+ days → -20)

        Labels: ≥60 → on_track | 35-59 → at_risk | <35 → stalled
        Terminal: achieved (score=100) | overdue (past deadline, score=0)
        """
        if goal.get("status") == "achieved":
            goal["health"] = "achieved"
            goal["health_score"] = 100
            return goal

        today = date.today()
        score = 50

        # Factor 1: milestone completion ratio (±30)
        milestones = goal.get("milestones", [])
        if milestones:
            ms_done = sum(1 for m in milestones if m.get("status") == "completed")
            ratio   = ms_done / len(milestones)
            score  += int((ratio - 0.5) * 60)

        # Factor 2: time pressure vs deadline (±25)
        deadline_str = goal.get("deadline")
        if deadline_str:
            try:
                deadline_d = date.fromisoformat(deadline_str)
                created_d  = date.fromisoformat(goal["created_at"][:10])
                total_days = max((deadline_d - created_d).days, 1)
                days_left  = (deadline_d - today).days

                if days_left < 0:
                    goal["status"]       = "overdue"
                    goal["health"]       = "overdue"
                    goal["health_score"] = 0
                    goal["updated_at"]   = datetime.now(timezone.utc).isoformat()
                    return goal

                time_used_ratio = 1 - (days_left / total_days)
                if milestones:
                    ms_ratio  = sum(1 for m in milestones if m["status"] == "completed") / len(milestones)
                    alignment = ms_ratio - time_used_ratio
                    score    += int(alignment * 25)
            except (ValueError, TypeError):
                pass

        # Factor 3: recent activity (±20)
        logs = goal.get("progress_logs", [])
        if logs:
            try:
                last_date  = date.fromisoformat(logs[-1]["logged_at"][:10])
                days_since = (today - last_date).days
                if days_since <= 3:
                    score += 20
                elif days_since <= 7:
                    score += 10
                elif days_since > 14:
                    score -= 20
            except (ValueError, TypeError):
                pass
        else:
            try:
                created_d = date.fromisoformat(goal["created_at"][:10])
                if (today - created_d).days > 7:
                    score -= 15
            except (ValueError, TypeError):
                pass

        score = max(0, min(100, score))
        goal["health_score"] = score
        if score >= 60:
            goal["health"] = "on_track"
        elif score >= 35:
            goal["health"] = "at_risk"
        else:
            goal["health"] = "stalled"

        goal["updated_at"] = datetime.now(timezone.utc).isoformat()
        return goal

    def add_goal(
        self,
        title: str,
        deadline: str | None,
        related_topics: list[str],
        milestones: list[str],
        raw_input: str = "",
    ) -> dict:
        """
        Create a new goal and append it to the profile.

        Args:
            title:          Short goal title.
            deadline:       "YYYY-MM-DD" or None.
            related_topics: List of curriculum topic strings.
            milestones:     Ordered list of milestone text strings.
            raw_input:      Original user utterance (preserved for AI context).

        Returns:
            The new goal dict.
        """
        now = datetime.now(timezone.utc).isoformat()
        goal: dict = {
            "id":                self._make_goal_id(),
            "title":             title,
            "raw_input":         raw_input or title,
            "related_topics":    related_topics,
            "deadline":          deadline,
            "status":            "active",
            "health":            "on_track",
            "health_score":      50,
            "xp_reward":         100,
            "created_at":        now,
            "updated_at":        now,
            "achieved_at":       None,
            "milestones":        [
                {
                    "id":           self._make_milestone_id(),
                    "text":         ms_text,
                    "status":       "pending",
                    "completed_at": None,
                }
                for ms_text in milestones
            ],
            "progress_logs":     [],
            "total_hours_logged": 0.0,
        }
        self._recalculate_health(goal)
        self.profile.setdefault("goals", []).append(goal)
        self._save_profile()
        return goal

    def log_progress(self, goal_id: str, hours: float, note: str) -> bool:
        """
        Append a progress log entry to a goal.

        Args:
            goal_id: The goal's id field.
            hours:   Hours worked (0.0 is valid).
            note:    Free-text description of progress.

        Returns:
            True if goal found and log appended, False otherwise.
        """
        goal = self._get_goal_by_id(goal_id)
        if goal is None:
            return False

        log = {
            "id":        f"log_{int(time.time())}",
            "note":      note,
            "hours":     max(0.0, hours),
            "logged_at": datetime.now(timezone.utc).isoformat(),
        }
        goal.setdefault("progress_logs", []).append(log)
        goal["total_hours_logged"] = round(
            goal.get("total_hours_logged", 0.0) + max(0.0, hours), 2
        )
        self._recalculate_health(goal)
        self._save_profile()
        return True

    def achieve_goal(self, goal_id: str) -> dict | None:
        """
        Mark a goal as fully achieved.

        Returns:
            {"goal": <goal dict>, "xp_earned": int} or None if not found.
        """
        goal = self._get_goal_by_id(goal_id)
        if goal is None:
            return None

        now = datetime.now(timezone.utc).isoformat()
        goal["status"]       = "achieved"
        goal["achieved_at"]  = now
        goal["health"]       = "achieved"
        goal["health_score"] = 100
        goal["updated_at"]   = now
        xp = goal.get("xp_reward", 100)
        self._save_profile()
        return {"goal": goal, "xp_earned": xp}

    def complete_milestone(self, goal_id: str, milestone_id: str) -> bool:
        """
        Mark a specific milestone as completed.

        Returns:
            True if both ids found and milestone updated, False otherwise.
        """
        goal = self._get_goal_by_id(goal_id)
        if goal is None:
            return False

        for ms in goal.get("milestones", []):
            if ms["id"] == milestone_id:
                ms["status"]       = "completed"
                ms["completed_at"] = datetime.now(timezone.utc).isoformat()
                self._recalculate_health(goal)
                self._save_profile()
                return True
        return False

    def add_milestone(self, goal_id: str, text: str) -> dict | None:
        """
        Add a new milestone to an existing goal.

        Returns:
            The new milestone dict, or None if goal not found.
        """
        goal = self._get_goal_by_id(goal_id)
        if goal is None:
            return None

        ms = {
            "id":           self._make_milestone_id(),
            "text":         text,
            "status":       "pending",
            "completed_at": None,
        }
        goal.setdefault("milestones", []).append(ms)
        self._recalculate_health(goal)
        self._save_profile()
        return ms

    def get_goals(self, status: str | None = "active") -> list[dict]:
        """
        Return goals filtered by status.

        Args:
            status: "active", "achieved", "overdue", "stalled", or None (all).

        Returns:
            Filtered list of goal dicts.
        """
        goals = self.profile.get("goals", [])
        if status is None:
            return goals
        return [g for g in goals if g.get("status") == status]

    # ── Syllabus task tracking ────────────────────────────────────────────────

    def set_syllabus_task(self, key: str, status: str) -> bool:
        """
        Update a syllabus task's status in the profile.

        Args:
            key:    Task key in format "<phase_id>-<track_idx>-<task_idx>"
            status: "todo" | "in_progress" | "done"

        Returns:
            True always (key is created if missing).
        """
        self.profile.setdefault("syllabus_progress", {})[key] = status
        self._save_profile()
        return True

    def get_syllabus_progress(self) -> dict:
        """Return the raw syllabus_progress dict."""
        return self.profile.get("syllabus_progress", {})

    def get_selected_roles(self) -> list[str]:
        """Return the learner's selected role tracks."""
        return self.profile.get("selected_roles", ["aipm", "evals", "context"])

    def set_selected_roles(self, roles: list[str]) -> None:
        """Update which role tracks the learner is targeting."""
        self.profile["selected_roles"] = [r for r in roles if r in ("aipm", "evals", "context")]
        self._save_profile()
        self._rebuild_system_message()

    def get_goal_feedback(self) -> str:
        """
        Generate intelligent coaching feedback on all active goals.

        Makes a one-shot Claude call (NOT added to conversation history).
        Builds a compact goals summary, sends with an analytical system prompt
        at temperature=0.3, and returns a markdown-formatted coaching string.

        Returns:
            Markdown string with Priority Order, Deadline Warnings, Next Actions.
            Returns a default message if no active/overdue goals exist.
        """
        goals = self.get_goals(status="active") + self.get_goals(status="overdue")
        if not goals:
            return (
                "You have no active goals yet. "
                "Tell me what you want to achieve and I'll help you set one up and track it."
            )

        today = date.today().isoformat()
        lines = [f"Today: {today}", f"Learner XP: {self.profile.get('xp', 0)}", ""]
        for g in goals:
            ms_total = len(g.get("milestones", []))
            ms_done  = sum(1 for m in g.get("milestones", []) if m.get("status") == "completed")
            hours    = g.get("total_hours_logged", 0.0)
            last_log = (
                g["progress_logs"][-1]["logged_at"][:10]
                if g.get("progress_logs") else "never"
            )
            lines.append(
                f"Goal: {g['title']} | health={g['health']} | "
                f"deadline={g.get('deadline') or 'none'} | "
                f"milestones={ms_done}/{ms_total} | hours={hours} | last_activity={last_log}"
            )
            for m in g.get("milestones", []):
                tick = "done" if m.get("status") == "completed" else "pending"
                lines.append(f"  - [{tick}] {m['text']}")
            lines.append("")

        goals_text = "\n".join(lines)
        system = (
            "You are a learning coach analysing a student's goal progress. "
            "Be direct, specific, and actionable. No filler praise. "
            "Respond in markdown with these sections: "
            "## Priority Order, ## Deadline Warnings (only if any deadline is within 14 days), "
            "## Momentum Issues (only if any goal is stalled/at_risk), ## Your Next Actions. "
            "Keep the full response under 300 words."
        )
        user_msg = (
            f"Here is the learner's current goal state:\n\n{goals_text}\n\n"
            "Analyse these goals and give prioritised coaching advice. "
            "Flag any goals needing immediate attention. "
            "Give one concrete next action per active goal."
        )
        return self.client.chat(
            messages=[{"role": "user", "content": user_msg}],
            system=system,
            temperature=0.3,
        )

    # ── Topic suggestions ─────────────────────────────────────────────────────

    def suggest_next_topic(self) -> str:
        """
        Suggest what the learner should study next — no API call needed.

        Logic:
        1. If any topic is 'in_progress', suggest resuming that one.
        2. Otherwise, suggest the first 'pending' topic (in curriculum order).
        3. If all done, congratulate!

        Returns:
            A short suggestion string shown in the sidebar.
        """
        topics = self.profile.get("topics", {})

        # Check in_progress first
        for topic in CURRICULUM_TOPICS:
            if topics.get(topic, {}).get("status") == "in_progress":
                return f"Resume: **{topic}**"

        # Then suggest the first pending topic
        for topic in CURRICULUM_TOPICS:
            if topics.get(topic, {}).get("status") == "pending":
                return f"Up next: **{topic}**"

        return "All topics complete! Consider building a capstone project."

    # ── Handoff detection ─────────────────────────────────────────────────────

    def detect_handoff(self, response: str) -> dict | None:
        """
        Check if the LLM's response contains a handoff signal.

        WHAT IS A HANDOFF?
        When the learner wants to deeply research a topic, we want to
        route them to the Research Agent (Step 3). The LLM signals this
        by writing: HANDOFF: RESEARCH | <topic name>

        The orchestrator (Step 6) will use this signal to switch agents.
        For now (Step 2), the UI shows a friendly "coming in Step 3" banner.

        Args:
            response: The full LLM reply text.

        Returns:
            {"agent": "research", "topic": "..."} or None if no handoff.
        """
        for line in response.splitlines():
            line = line.strip()
            if line.startswith("HANDOFF: RESEARCH"):
                parts = line.split("|", 1)
                topic = parts[1].strip() if len(parts) > 1 else "unknown topic"
                return {"agent": "research", "topic": topic}
        return None

    # ── Core interface ────────────────────────────────────────────────────────

    def chat(self, user_message: str) -> tuple[str, dict | None]:
        """
        Send a message to the Learning Coach and get a response.

        NOTE: This returns a TUPLE, not just a string like CodingAgent.chat().
        The second element is a handoff signal (or None).

        Why a tuple? The LearningAgent needs to pass extra information
        back to the UI — specifically, whether the user should be
        redirected to another agent. This is the cleanest way to do that
        without changing the method name.

        Args:
            user_message: What the learner typed.

        Returns:
            (response_text, handoff_dict_or_None)
        """
        # Step 1: Add user message
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
        })

        # Step 2: Call Claude
        system = self.conversation_history[0]["content"]
        messages = [m for m in self.conversation_history if m["role"] != "system"]
        reply = self.client.chat(messages=messages, system=system)

        # Step 3: Add reply to history
        self.conversation_history.append({
            "role": "assistant",
            "content": reply,
        })

        # Step 4: Trim history (same logic as CodingAgent)
        max_messages = 1 + (MAX_HISTORY_TURNS * 2)
        if len(self.conversation_history) > max_messages:
            self.conversation_history = (
                [self.conversation_history[0]]
                + self.conversation_history[3:]
            )

        # Step 5: Parse and apply any ACTION tokens in the response
        actions = self._parse_actions(reply)
        self._apply_actions(actions)  # also calls _save_profile() if anything changed

        # Step 6: Save (covers cases where no actions fired but history updated)
        self._save_profile()

        # Step 7: Detect handoff and return
        handoff = self.detect_handoff(reply)
        return reply, handoff

    def reset(self) -> None:
        """
        Clear the conversation history.

        IMPORTANT: This does NOT delete progress, todos, or notes.
        Only the chat is cleared. The learner's learning data is preserved.
        """
        system_text = build_learning_system_prompt(self.profile)
        system_text += "\n\n" + load_combined_skill("learning")
        self.conversation_history = [
            {"role": "system", "content": system_text}
        ]
        self._save_profile()

    def get_history(self) -> list[dict]:
        """Return the full conversation history (same interface as CodingAgent)."""
        return self.conversation_history

    def to_dict(self) -> dict:
        """
        Serialize the agent's state for the future orchestrator.

        When the orchestrator hands off TO this agent, it can also receive
        context from another agent via a matching `receive_context()` method
        (to be added in Step 6).
        """
        return {
            "agent": "learning",
            "skill_level": self.profile.get("skill_level", "beginner"),
            "history": self.conversation_history,
            "profile_summary": self.get_progress(),
        }
