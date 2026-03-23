"""
coding_agent.py — The AI Coding Agent for the AI² learning platform.

WHAT THIS FILE DOES (simple explanation):
-----------------------------------------
This file defines a "class" called CodingAgent. A class is like a blueprint
for an object that can remember things and do things.

Our CodingAgent remembers:
  - Your skill level (beginner / intermediate / advanced)
  - The full conversation history

Our CodingAgent can:
  - Chat with you about AI coding topics
  - Detect your skill level from your first message
  - Adjust its teaching style to match your level
  - Be imported and used by the future orchestrator

WHY A CLASS INSTEAD OF A FUNCTION?
-----------------------------------
A plain function forgets everything after it runs. A class instance
(an object) keeps its data alive as long as the program is running.
We need the agent to remember the conversation, so a class is the
right tool here.
"""

from config.settings import MAX_HISTORY_TURNS, DEFAULT_SKILL_LEVEL
from config.prompts import build_system_prompt
from utils.claude_client import ClaudeClient
from utils.skills_loader import load_combined_skill


class CodingAgent:
    """
    An AI tutor that teaches AI-related coding and adapts to the
    learner's skill level.

    Usage:
        agent = CodingAgent(skill_level="beginner")
        response = agent.chat("What is a function in Python?")
        print(response)
    """

    def __init__(self, skill_level: str = DEFAULT_SKILL_LEVEL):
        """
        Set up the agent with a skill level and an empty conversation.

        Args:
            skill_level: Starting level — "beginner", "intermediate", or "advanced"
        """
        self.skill_level = skill_level
        self.client = ClaudeClient()
        # Stores execute_python results from the most recent chat_and_run() call.
        # Each entry: {"code": str, "output": str}
        self.last_tool_outputs: list[dict] = []

        # conversation_history is the list of messages we send to OpenAI.
        # It always starts with a "system" message — the secret instruction
        # that tells the AI how to behave.
        #
        # Format OpenAI expects:
        #   [
        #     {"role": "system",    "content": "You are a tutor..."},
        #     {"role": "user",      "content": "What is a function?"},
        #     {"role": "assistant", "content": "A function is..."},
        #     ...
        #   ]
        system_text = build_system_prompt(self.skill_level)
        system_text += "\n\n" + load_combined_skill("coding")
        self.conversation_history: list[dict] = [
            {"role": "system", "content": system_text}
        ]

    # ── Skill level management ────────────────────────────────────────────────

    def detect_skill_level(self, user_message: str) -> str:
        """
        Guess the learner's skill level from their first message.

        This is a simple keyword check — no API call needed.
        It won't be perfect, but it gives a good starting point.

        Args:
            user_message: The first message the learner typed.

        Returns:
            "beginner", "intermediate", or "advanced"
        """
        message_lower = user_message.lower()

        # Words that suggest the person is just starting out
        beginner_signals = [
            "what is", "what are", "how do i", "how to", "explain",
            "i don't understand", "i dont understand", "new to", "never",
            "first time", "basics", "start", "beginner", "confused",
            "help me understand", "simple", "easy",
        ]

        # Words that suggest an experienced developer
        advanced_signals = [
            "optimize", "optimization", "architecture", "trade-off", "tradeoff",
            "production", "async", "concurrency", "type hint", "benchmark",
            "performance", "latency", "throughput", "design pattern",
            "best practice", "scalab", "deploy", "fine-tun", "embedding",
            "vector store", "orchestrat", "agentic", "function calling",
        ]

        for signal in advanced_signals:
            if signal in message_lower:
                return "advanced"

        for signal in beginner_signals:
            if signal in message_lower:
                return "beginner"

        return "intermediate"

    def set_skill_level(self, skill_level: str) -> None:
        """
        Change the skill level and update the system prompt.

        IMPORTANT: We replace the system message at index 0 rather than
        adding a new one. OpenAI works best with a single system message.
        The rest of the conversation history is kept intact.

        Args:
            skill_level: "beginner", "intermediate", or "advanced"
        """
        self.skill_level = skill_level
        system_text = build_system_prompt(self.skill_level)
        system_text += "\n\n" + load_combined_skill("coding")
        self.conversation_history[0] = {
            "role": "system",
            "content": system_text,
        }

    # ── Core chat method ──────────────────────────────────────────────────────

    def chat(self, user_message: str) -> str:
        """
        Send a message to the agent and get a response.

        What happens step by step:
        1. Add the user's message to the conversation history
        2. Send the full history to OpenAI
        3. Get the response back
        4. Add the response to the history (so future messages have context)
        5. Trim old messages if the history gets too long
        6. Return the response text

        Args:
            user_message: What the learner typed.

        Returns:
            The agent's reply as a string.
        """
        # Step 1: Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
        })

        # Step 2 & 3: Call Claude
        # Claude requires the system prompt as a separate parameter,
        # so we strip it from the messages list before sending.
        system = self.conversation_history[0]["content"]
        messages = [m for m in self.conversation_history if m["role"] != "system"]
        assistant_reply = self.client.chat(messages=messages, system=system)

        # Step 4: Add the assistant's reply to history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_reply,
        })

        # Step 5: Trim history if it's getting too long
        # We keep: 1 system message + up to MAX_HISTORY_TURNS * 2 other messages
        # Each "turn" = 1 user message + 1 assistant reply = 2 messages
        max_messages = 1 + (MAX_HISTORY_TURNS * 2)
        if len(self.conversation_history) > max_messages:
            # Keep the system message (index 0), drop the oldest user+assistant pair
            # history[1] and history[2] are the oldest user+assistant pair
            self.conversation_history = (
                [self.conversation_history[0]]  # system message
                + self.conversation_history[3:]  # everything after the oldest pair
            )

        # Step 6: Return the reply
        return assistant_reply

    # ── Tool-enabled chat (Idea B — live code execution) ──────────────────────

    def chat_and_run(self, user_message: str) -> str:
        """
        Like chat(), but gives Forge access to execute_python and other coding
        tools so it can run code examples and show real output.

        How it works:
        1. A capturing closure wraps tool_executor so any execute_python calls
           are stored in self.last_tool_outputs for the UI to display.
        2. We call client.chat_with_tools() instead of client.chat() — this
           drives the ReAct loop where Claude can request tools and see results.
        3. The final text reply is added to history exactly like chat() does.

        The UI should read agent.last_tool_outputs after this call and render
        expandable ▶ Output blocks for each item.
        """
        from utils.code_runner import tool_executor as _base_executor

        # Reset tool outputs for this turn
        self.last_tool_outputs = []

        # Capturing closure — intercepts execute_python calls so we can display
        # the code + output in the UI without changing the tool_executor signature
        def _capturing_executor(tool_name: str, tool_args: dict) -> str:
            result = _base_executor(tool_name, tool_args)
            if tool_name == "execute_python":
                self.last_tool_outputs.append({
                    "code":   tool_args.get("code", ""),
                    "output": result,
                })
            return result

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
        })

        system = self.conversation_history[0]["content"]
        messages = [m for m in self.conversation_history if m["role"] != "system"]

        assistant_reply = self.client.chat_with_tools(
            messages=messages,
            system=system,
            agent_name="coding",
            tool_executor=_capturing_executor,
        )

        # Add reply to history and trim if needed
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_reply,
        })
        max_messages = 1 + (MAX_HISTORY_TURNS * 2)
        if len(self.conversation_history) > max_messages:
            self.conversation_history = (
                [self.conversation_history[0]]
                + self.conversation_history[3:]
            )

        return assistant_reply

    # ── Utility methods ───────────────────────────────────────────────────────

    def reset(self) -> None:
        """
        Clear the conversation and start fresh.

        Keeps the current skill level and its system prompt.
        Called when the user clicks "New Chat" in the UI.
        """
        system_text = build_system_prompt(self.skill_level)
        system_text += "\n\n" + load_combined_skill("coding")
        self.conversation_history = [
            {"role": "system", "content": system_text}
        ]

    def get_history(self) -> list[dict]:
        """
        Return the full conversation history.

        Returns the raw list including the system message.
        The UI filters out the system message before displaying.
        """
        return self.conversation_history

    def to_dict(self) -> dict:
        """
        Serialize the agent's state to a dictionary.

        WHY THIS EXISTS:
        The future orchestrator needs to pass context between agents.
        For example, when handing off from the Coding Agent to the
        Practice Agent, it can pass this dict so the Practice Agent
        knows what topics were just discussed.

        Returns:
            {"skill_level": "beginner", "history": [...messages...]}
        """
        return {
            "skill_level": self.skill_level,
            "history": self.conversation_history,
        }
