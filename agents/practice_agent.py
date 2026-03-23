"""
practice_agent.py — The Practice Agent for the AI² platform (Step 4).

WHAT THIS AGENT DOES:
----------------------
Assesses the learner's knowledge through three modes:
  - Quiz:              Multiple-choice questions on a curriculum topic
  - Coding Challenge:  A small coding task with AI-powered code review
  - Mock Interview:    A realistic interview simulation for AI Builder or AI PM roles

KEY NEW CONCEPT — Structured Output (JSON mode):
-------------------------------------------------
For quiz mode, we tell OpenAI to return JSON instead of prose:

    response = client.chat.completions.create(
        model=...,
        messages=...,
        response_format={"type": "json_object"},   ← this is the new part
    )
    data = json.loads(response.choices[0].message.content)
    # Now data is a Python dict with "question", "options", "correct_answer", etc.

This makes the AI's output machine-readable so we can:
  - Parse the correct answer automatically
  - Track scores without any fragile text parsing
  - Display a nicely formatted question (not raw JSON)

JSON mode is only used in quiz mode. Challenge and interview use natural prose
because AI code review and interview feedback are better as free text.

KEY NEW CONCEPT — Multi-mode agent:
------------------------------------
One class, three completely different personalities.
All that changes is the system prompt passed to build_practice_system_prompt().
This is a core pattern in real AI products — "configuration as prompt".

KEY NEW CONCEPT — AI-as-evaluator:
------------------------------------
For challenge and interview modes, the AI grades free-text answers by
reasoning about them. It's not an exact-match check — it understands
"option B", "b", "the second option" all mean the same thing for a quiz,
and it can identify strengths and weaknesses in submitted code.
"""

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from config.settings import MAX_HISTORY_TURNS
from config.prompts import CURRICULUM_TOPICS, build_practice_system_prompt
from utils.claude_client import ClaudeClient
from utils.skills_loader import load_combined_skill


class PracticeAgent:
    """
    A practice coach that tests the learner through quizzes, coding challenges,
    and mock interviews — and tracks scores across sessions.

    Usage:
        agent = PracticeAgent()
        agent.set_mode("quiz")
        agent.set_topic("Prompt engineering and LLM best practices")
        opening = agent.start_session()   # returns the first question

        reply, result = agent.chat("B")   # answer a quiz question
        if result:
            print(result["correct"])      # True or False
            if result["session_complete"]:
                print(agent.get_stats())
    """

    HISTORY_PATH = "data/practice_history.json"

    def __init__(self) -> None:
        self.client = ClaudeClient()

        # Current session configuration — changed via setters
        self.mode: str = "quiz"
        self.topic: str = CURRICULUM_TOPICS[0]
        self.role: str = "AI Builder"

        # Session state
        self.session_active: bool = False
        self.current_session: dict = {}  # accumulates question results during a session

        # Persistent history (scores across all sessions)
        self.history = self._load_history()

        # Conversation history for the current session.
        # Starts EMPTY — start_session() initialises it with a fresh system prompt.
        # This is different from LearningAgent which restores history across page loads.
        # Practice sessions are always fresh — there's no value in resuming a quiz.
        self.conversation_history: list[dict] = []

    # ── Setters ───────────────────────────────────────────────────────────────

    def set_mode(self, mode: str) -> None:
        """Set mode to 'quiz', 'challenge', or 'interview'."""
        self.mode = mode

    def set_topic(self, topic: str) -> None:
        """Set the curriculum topic for quiz and challenge modes."""
        self.topic = topic

    def set_role(self, role: str) -> None:
        """Set the target role for interview mode: 'AI Builder' or 'AI PM'."""
        self.role = role

    # ── Session lifecycle ─────────────────────────────────────────────────────

    def start_session(self) -> str:
        """
        Begin a new practice session in the current mode/topic/role.

        Builds a fresh system prompt, sends a "Start" trigger to OpenAI,
        and returns the AI's opening message (first question or challenge).

        WHY we send "Start":
        The system prompt sets up the AI's role and format rules, but doesn't
        produce the first question automatically. Sending a "Start" user message
        triggers the AI to produce the opening output.

        Returns:
            The AI's opening message, formatted for display.
        """
        # Build fresh system prompt for this session
        prompt = build_practice_system_prompt(
            mode=self.mode,
            topic=self.topic,
            role=self.role,
        )
        prompt += "\n\n" + load_combined_skill("practice")

        # Initialise conversation with system + trigger message
        self.conversation_history = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Start"},
        ]

        # Call Claude — system prompt already instructs JSON output for quiz mode
        system = self.conversation_history[0]["content"]
        messages = [m for m in self.conversation_history if m["role"] != "system"]
        raw_reply = self.client.chat(messages=messages, system=system)

        # Add to history
        self.conversation_history.append({"role": "assistant", "content": raw_reply})

        # Format the reply for display
        formatted = self._format_reply(raw_reply)

        # Initialise the current session record
        now = datetime.now(timezone.utc).isoformat()
        self.current_session = {
            "id": f"session_{int(time.time())}",
            "mode": self.mode,
            "topic": self.topic if self.mode != "interview" else None,
            "role": self.role if self.mode == "interview" else None,
            "started_at": now,
            "ended_at": None,
            "results": [],
            "score": 0,
            "max_score": 0,
        }
        self.session_active = True

        return formatted

    def end_session(self) -> None:
        """
        Close the current session, compute final score, and save to history.

        Called automatically when the AI signals session_complete=True
        (quiz) or after the interview closing summary.
        """
        self.current_session["ended_at"] = datetime.now(timezone.utc).isoformat()

        # Compute totals from individual results
        results = self.current_session.get("results", [])
        if self.mode == "quiz":
            correct = sum(1 for r in results if r.get("correct"))
            self.current_session["score"] = correct
            self.current_session["max_score"] = len(results)
        else:
            total = sum(r.get("score", 0) for r in results)
            max_total = sum(r.get("max_score", 0) for r in results)
            self.current_session["score"] = total
            self.current_session["max_score"] = max_total

        self.history["sessions"].append(self.current_session)
        self._save_history()
        self.session_active = False

    # ── Core chat ─────────────────────────────────────────────────────────────

    def chat(self, user_message: str) -> tuple[str, dict | None]:
        """
        Send a learner response and get back the AI's reply.

        Returns a tuple — same pattern as LearningAgent.chat():
            (reply_text, result_dict_or_None)

        result_dict is non-None when the AI has evaluated an answer:
            {
                "correct":          True | False   (quiz only),
                "score":            int,            (challenge/interview),
                "max_score":        int,
                "session_complete": bool,
            }

        When session_complete=True, end_session() is called automatically
        so the history file is updated before the page re-renders.

        WHY a tuple:
        The page needs to know immediately when an answer was graded so it
        can show the correct/incorrect callout and update the stats panel.
        Returning the result alongside the text is the cleanest way to do this.

        Args:
            user_message: What the learner typed.

        Returns:
            (formatted_reply, result_dict_or_None)
        """
        # Step 1: Add user message
        self.conversation_history.append({"role": "user", "content": user_message})

        # Step 2: Call Claude — system prompt instructs JSON output for quiz mode
        system = self.conversation_history[0]["content"]
        messages = [m for m in self.conversation_history if m["role"] != "system"]
        raw_reply = self.client.chat(messages=messages, system=system)

        # Step 3: Add to history
        self.conversation_history.append({"role": "assistant", "content": raw_reply})

        # Step 4: Trim history to avoid token bloat
        max_messages = 1 + (MAX_HISTORY_TURNS * 2)
        if len(self.conversation_history) > max_messages:
            self.conversation_history = (
                [self.conversation_history[0]]
                + self.conversation_history[-(MAX_HISTORY_TURNS * 2):]
            )

        # Step 5: Parse the reply
        data = self._parse_json_response(raw_reply)
        formatted = self._format_reply(raw_reply, data)
        result = self._extract_result(raw_reply, data)

        # Step 6: Record the result and end session if complete
        if result:
            self.current_session["results"].append(result)
            if result.get("session_complete"):
                self.end_session()

        return formatted, result

    # ── Reply formatting ──────────────────────────────────────────────────────

    def _format_reply(self, raw_reply: str, data: dict | None = None) -> str:
        """
        Convert the AI's raw output into readable Markdown for display.

        WHY this exists:
        In quiz mode the AI returns JSON — which is great for our code but
        terrible for users to read. This method converts the JSON into
        nicely formatted Markdown. The user never sees raw JSON.

        For challenge and interview modes the AI already returns Markdown,
        so we just return it as-is.

        Args:
            raw_reply: The raw string from OpenAI.
            data:      Pre-parsed JSON dict (or None).

        Returns:
            A Markdown string for display.
        """
        if self.mode != "quiz":
            return raw_reply

        # Parse JSON if not already done
        if data is None:
            data = self._parse_json_response(raw_reply)

        if data is None:
            # JSON parsing failed — return raw text as a fallback
            return raw_reply

        msg_type = data.get("type", "")

        if msg_type == "question":
            # Format: question number + question text + A/B/C/D options
            qn = data.get("question_number", "?")
            q = data.get("question", "")
            opts = data.get("options", {})
            lines = [f"**Question {qn}**", "", q, ""]
            for letter in ["A", "B", "C", "D"]:
                if letter in opts:
                    lines.append(f"{letter}) {opts[letter]}")
            return "\n".join(lines)

        elif msg_type == "grade":
            # Format: correct/incorrect marker + feedback
            correct = data.get("correct", False)
            feedback = data.get("feedback", "")
            marker = "Correct!" if correct else "Incorrect."
            return f"**{marker}**\n\n{feedback}"

        # Unknown JSON type — return raw
        return raw_reply

    # ── JSON and score parsing helpers ────────────────────────────────────────

    def _parse_json_response(self, text: str) -> dict | None:
        """
        Try to parse the AI's response as JSON.

        WHY two attempts:
        Even with JSON mode enabled, the AI sometimes wraps its output in
        markdown code fences like ```json ... ```. We strip those and retry.

        Args:
            text: The raw response string from OpenAI.

        Returns:
            A Python dict if parsing succeeds, None otherwise.
        """
        # Attempt 1: parse directly
        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            pass

        # Attempt 2: strip markdown fences and retry
        stripped = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
        stripped = re.sub(r"\s*```$", "", stripped.strip(), flags=re.MULTILINE)
        try:
            return json.loads(stripped.strip())
        except (json.JSONDecodeError, ValueError):
            return None

    def _extract_result(self, reply: str, data: dict | None) -> dict | None:
        """
        Extract a structured result dict from the AI's response.

        Quiz:      reads "correct" and "session_complete" from parsed JSON.
        Challenge: parses "SCORE: X/10" from free-text reply using regex.
        Interview: parses "SCORE: X/5" from free-text reply using regex.

        WHY regex for challenge/interview:
        The AI returns prose for these modes, but we asked it to include a
        structured "SCORE: X/Y" line. A simple regex is more robust than
        asking the AI to produce full JSON when it's already in "prose mode".

        Args:
            reply: Raw reply string.
            data:  Parsed JSON dict (or None).

        Returns:
            Result dict or None if no gradeable event in this turn.
        """
        if self.mode == "quiz":
            if data is None:
                return None
            if data.get("type") != "grade":
                return None

            return {
                "question_number": data.get("question_number", 0),
                "correct": bool(data.get("correct", False)),
                "score": 1 if data.get("correct") else 0,
                "max_score": 1,
                "session_complete": bool(data.get("session_complete", False)),
            }

        else:
            # Challenge: SCORE: X/10 | Interview: SCORE: X/5
            match = re.search(r"SCORE:\s*(\d+)/(\d+)", reply, re.IGNORECASE)
            if not match:
                return None

            score = int(match.group(1))
            max_score = int(match.group(2))

            # Interview session is complete after the closing summary
            # which appears after the last SCORE line and contains
            # "strengths" or "overall" (part of the closing summary format).
            session_complete = False
            if self.mode == "interview":
                lower = reply.lower()
                if "strengths" in lower or "overall" in lower:
                    session_complete = True
            elif self.mode == "challenge":
                # One task per session — always complete after grading
                session_complete = True

            return {
                "score": score,
                "max_score": max_score,
                "session_complete": session_complete,
            }

    # ── Stats ─────────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """
        Compute aggregate stats across all completed sessions.

        Returns:
            {
                "quiz": {sessions, total_questions, correct, accuracy_pct, by_topic},
                "challenge": {sessions, avg_score, by_topic},
                "interview": {sessions, by_role: {AI Builder: {...}, AI PM: {...}}}
            }
        """
        sessions = self.history.get("sessions", [])

        # ── Quiz stats ────────────────────────────────────────────────────────
        quiz_sessions = [s for s in sessions if s["mode"] == "quiz"]
        quiz_total = sum(s.get("max_score", 0) for s in quiz_sessions)
        quiz_correct = sum(s.get("score", 0) for s in quiz_sessions)

        quiz_by_topic: dict = {}
        for s in quiz_sessions:
            t = s.get("topic", "Unknown")
            if t not in quiz_by_topic:
                quiz_by_topic[t] = {"questions": 0, "correct": 0, "accuracy_pct": 0}
            quiz_by_topic[t]["questions"] += s.get("max_score", 0)
            quiz_by_topic[t]["correct"] += s.get("score", 0)
        for t in quiz_by_topic:
            q = quiz_by_topic[t]["questions"]
            c = quiz_by_topic[t]["correct"]
            quiz_by_topic[t]["accuracy_pct"] = round(c / q * 100) if q > 0 else 0

        # ── Challenge stats ───────────────────────────────────────────────────
        challenge_sessions = [s for s in sessions if s["mode"] == "challenge"]
        challenge_scores = [
            s["score"] / s["max_score"] * 10
            for s in challenge_sessions
            if s.get("max_score", 0) > 0
        ]
        challenge_avg = round(sum(challenge_scores) / len(challenge_scores), 1) if challenge_scores else 0.0

        challenge_by_topic: dict = {}
        for s in challenge_sessions:
            t = s.get("topic", "Unknown")
            raw = s["score"] / s["max_score"] * 10 if s.get("max_score", 0) > 0 else 0
            if t not in challenge_by_topic:
                challenge_by_topic[t] = {"sessions": 0, "avg_score": 0.0, "_scores": []}
            challenge_by_topic[t]["sessions"] += 1
            challenge_by_topic[t]["_scores"].append(raw)
        for t in challenge_by_topic:
            sc = challenge_by_topic[t].pop("_scores")
            challenge_by_topic[t]["avg_score"] = round(sum(sc) / len(sc), 1) if sc else 0.0

        # ── Interview stats ───────────────────────────────────────────────────
        interview_sessions = [s for s in sessions if s["mode"] == "interview"]
        interview_by_role: dict = {
            "AI Builder": {"sessions": 0, "avg_score": 0.0, "_scores": []},
            "AI PM": {"sessions": 0, "avg_score": 0.0, "_scores": []},
        }
        for s in interview_sessions:
            r = s.get("role", "AI Builder")
            if r not in interview_by_role:
                interview_by_role[r] = {"sessions": 0, "avg_score": 0.0, "_scores": []}
            interview_by_role[r]["sessions"] += 1
            mx = s.get("max_score", 0)
            pct = round(s["score"] / mx * 5, 1) if mx > 0 else 0
            interview_by_role[r]["_scores"].append(pct)
        for r in interview_by_role:
            sc = interview_by_role[r].pop("_scores")
            interview_by_role[r]["avg_score"] = round(sum(sc) / len(sc), 1) if sc else 0.0

        return {
            "quiz": {
                "sessions": len(quiz_sessions),
                "total_questions": quiz_total,
                "correct": quiz_correct,
                "accuracy_pct": round(quiz_correct / quiz_total * 100) if quiz_total > 0 else 0,
                "by_topic": quiz_by_topic,
            },
            "challenge": {
                "sessions": len(challenge_sessions),
                "avg_score": challenge_avg,
                "by_topic": challenge_by_topic,
            },
            "interview": {
                "sessions": len(interview_sessions),
                "by_role": interview_by_role,
            },
        }

    # ── Persistence ───────────────────────────────────────────────────────────

    def _make_default_history(self) -> dict:
        """Create an empty history file structure."""
        now = datetime.now(timezone.utc).isoformat()
        return {"created_at": now, "updated_at": now, "sessions": []}

    def _load_history(self) -> dict:
        """Load practice history from disk. Create it if it doesn't exist."""
        path = Path(self.HISTORY_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)

        if not path.exists():
            history = self._make_default_history()
            path.write_text(json.dumps(history, indent=2))
            return history

        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, Exception):
            history = self._make_default_history()
            path.write_text(json.dumps(history, indent=2))
            return history

    def _save_history(self) -> None:
        """Save practice history to disk."""
        self.history["updated_at"] = datetime.now(timezone.utc).isoformat()
        Path(self.HISTORY_PATH).write_text(json.dumps(self.history, indent=2))

    # ── Standard interface ────────────────────────────────────────────────────

    def reset(self) -> None:
        """Clear the current conversation and session state."""
        self.conversation_history = []
        self.session_active = False
        self.current_session = {}

    def get_history(self) -> list[dict]:
        """Return the current conversation history."""
        return self.conversation_history

    def to_dict(self) -> dict:
        """Serialize agent state for the future orchestrator."""
        return {
            "agent": "practice",
            "mode": self.mode,
            "topic": self.topic,
            "role": self.role,
            "session_active": self.session_active,
            "history": self.conversation_history,
            "stats": self.get_stats(),
        }
