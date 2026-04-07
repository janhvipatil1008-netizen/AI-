"""
research_agent.py — Research & Learning Agent (Step 3).

WHAT THIS AGENT DOES:
----------------------
This agent uses Claude (Anthropic) + two search tools to research AI topics.
The user asks a question, Claude decides which tools to call, we run them,
and Claude synthesises the results into a cited answer.

KEY NEW CONCEPT — Claude Tool Use (ReAct loop):
------------------------------------------------
Unlike the Coding Agent (which just sends a message and gets text back),
this agent runs a LOOP:

  1. Send message + tool definitions to Claude
  2. Claude either:
     a. Answers directly  → stop_reason = "end_turn"  → we're done
     b. Wants to use tools → stop_reason = "tool_use"  → we execute the tools
  3. If tools were called, add Claude's response AND the tool results to history
  4. Call Claude again — repeat until end_turn or max iterations

This is called the "ReAct" pattern: Reason → Act → Observe → Reason → ...

KEY NEW CONCEPT — Claude API vs OpenAI API:
--------------------------------------------
Claude's API has a few important differences:
  - System prompt is a separate `system=` parameter (NOT a {"role":"system"} message)
  - Tool use is signalled by `response.stop_reason == "tool_use"` (not message.tool_calls)
  - Response content is a LIST of blocks (TextBlock or ToolUseBlock)
  - Tool results go back as role="user" with type="tool_result" (not role="tool")
  - Tool definitions use "input_schema" (not "parameters")
"""

import json

from config.settings import MAX_HISTORY_TURNS
from config.prompts import build_research_system_prompt
from utils.search_tools import search_web, search_wikipedia, search_arxiv
from utils.browser_tools import browse_url, search_and_browse
from utils.claude_client import ClaudeClient
from utils.skills_loader import load_combined_skill


class ResearchAgent:
    """
    A research agent that uses Claude + web search + Wikipedia to answer
    deep questions about AI topics.

    Usage:
        agent = ResearchAgent()
        response = agent.chat("What is RAG and how does it work?")
        print(response)

    Handoff usage (from Learning Manager):
        agent = ResearchAgent()
        agent.receive_handoff("RAG systems and vector databases")
        response = agent.chat("Research and explain this topic")
    """

    def __init__(self):
        try:
            self.client = ClaudeClient()
        except EnvironmentError:
            raise EnvironmentError(
                "\n\n ERROR: ANTHROPIC_API_KEY is not set.\n"
                " Add this to your .env file:\n"
                "   ANTHROPIC_API_KEY=sk-ant-...your-key-here...\n"
                " Get a free key at: console.anthropic.com\n"
            )

        # Track the current handoff topic (set by receive_handoff())
        self._handoff_topic: str | None = None

        # Conversation history — system prompt stored at index 0, stripped
        # before API calls (Claude requires system as a separate parameter).
        system_text = build_research_system_prompt()
        system_text += "\n\n" + load_combined_skill("research")
        self.conversation_history: list[dict] = [
            {"role": "system", "content": system_text}
        ]

    # ── Handoff ───────────────────────────────────────────────────────────────

    def receive_handoff(self, topic: str) -> None:
        """
        Accept a handoff from the Learning Manager.

        Rebuilds the system prompt with the topic baked in — this tells
        Claude to proactively research the topic on the next turn instead
        of waiting for the user to ask.

        Args:
            topic: The topic name from the Learning Manager handoff signal.
        """
        self._handoff_topic = topic
        system_text = build_research_system_prompt(preloaded_topic=topic)
        system_text += "\n\n" + load_combined_skill("research")
        self.conversation_history[0] = {
            "role": "system",
            "content": system_text,
        }

    def get_handoff_topic(self) -> str | None:
        """Return the current handoff topic (or None if no handoff)."""
        return self._handoff_topic

    # ── Tool execution ────────────────────────────────────────────────────────

    def _execute_tool(self, name: str, args: dict) -> str:
        """
        Run a tool by name with the given arguments.

        This is called when Claude's response contains a tool_use block.
        We look at the tool name, call the right function, and return
        the result as a string (Claude expects string tool results).

        Args:
            name: Tool name — "web_search", "wiki_search", or "search_arxiv"
            args: The arguments Claude wants to pass (already parsed from JSON)

        Returns:
            String result to send back to Claude as a tool_result.
        """
        if name == "web_search":
            query = args.get("query", "")
            max_results = args.get("max_results", 5)
            return search_web(query, max_results)

        elif name == "wiki_search":
            topic = args.get("topic", "")
            return search_wikipedia(topic)

        elif name == "search_arxiv":
            query = args.get("query", "")
            max_results = args.get("max_results", 5)
            return search_arxiv(query, max_results)

        elif name == "browse_url":
            return browse_url(args.get("url", ""), args.get("question", ""))

        elif name == "search_and_browse":
            return search_and_browse(args.get("query", ""), args.get("max_pages", 2))

        else:
            return f"Unknown tool: {name}"

    # ── Claude ReAct loop ─────────────────────────────────────────────────────

    def _run_agentic_loop(self) -> str:
        """
        Run a Claude ReAct loop using the shared ClaudeClient wrapper.

        ClaudeClient.chat_with_tools() owns the loop logic (reason → tool call
        → observe → repeat). We pass `_execute_tool` as the executor so it calls
        the real search functions. The tool definitions come from TOOL_REGISTRY
        in ClaudeClient — no duplication here.

        Returns:
            The final text response from Claude.
        """
        system_content = self.conversation_history[0]["content"]
        messages = [m for m in self.conversation_history if m["role"] != "system"]

        return self.client.chat_with_tools(
            messages=messages,
            system=system_content,
            agent_name="research",
            tool_executor=self._execute_tool,
        )

    # ── Core interface ────────────────────────────────────────────────────────

    def chat(self, user_message: str) -> str:
        """
        Send a message to the Research Agent and get a cited answer.

        Same external interface as CodingAgent.chat() — returns a plain string.
        Internally, this runs the full ReAct loop (may call tools multiple times).

        Args:
            user_message: What the user typed (or the auto-generated handoff prompt).

        Returns:
            Claude's final answer, including a Sources section.
        """
        # Add the user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
        })

        # Run the agentic loop — this may take several API calls
        reply = self._run_agentic_loop()

        # Add Claude's final answer to history
        self.conversation_history.append({
            "role": "assistant",
            "content": reply,
        })

        # Trim history to avoid hitting token limits.
        # Keep system message [0] + the most recent N turns.
        # Each turn = 2 messages (user + assistant) but tool turns add more,
        # so we use a simpler count: keep at most MAX_HISTORY_TURNS * 4 messages
        # after the system message (the * 4 accounts for tool call messages).
        max_messages = 1 + (MAX_HISTORY_TURNS * 4)
        if len(self.conversation_history) > max_messages:
            self.conversation_history = (
                [self.conversation_history[0]]  # keep system message
                + self.conversation_history[-(MAX_HISTORY_TURNS * 4):]
            )

        return reply

    def reset(self) -> None:
        """
        Clear the conversation history and remove any handoff topic.
        Starts a fresh session while keeping the same agent instance.
        """
        self._handoff_topic = None
        system_text = build_research_system_prompt()
        system_text += "\n\n" + load_combined_skill("research")
        self.conversation_history = [
            {"role": "system", "content": system_text}
        ]

    def get_history(self) -> list[dict]:
        """Return the full conversation history (same interface as other agents)."""
        return self.conversation_history

    def to_dict(self) -> dict:
        """Serialize the agent state for the future orchestrator."""
        return {
            "agent": "research",
            "handoff_topic": self._handoff_topic,
            "history": self.conversation_history,
        }
