"""
claude_client.py — Shared Claude (Anthropic) API Wrapper

WHAT IS THIS?
--------------
A shared wrapper around the Anthropic SDK so every agent that uses Claude
doesn't have to re-implement the same patterns (tool use loop, error handling,
rate limits, token management).

Before this file: Each agent that uses Claude copies the same ReAct loop code.
After this file:  Agents call `ClaudeClient().chat(...)` and get an answer.
                  The complexity is here, hidden once, used everywhere.

SIMPLE ANALOGY:
---------------
Imagine every department in a company has to write their own email system.
This file is the company's shared email server. Everyone sends mail the same way.

KEY CONCEPT — Tool Registry:
-----------------------------
The `TOOL_REGISTRY` dictionary maps each agent name to the MCP tool definitions
it is ALLOWED to use. The orchestrator (and agents) pass the agent name, and
ClaudeClient only gives Claude the tools that agent is permitted to call.

Why this matters:
  - The Coding Agent doesn't get access to the Ideas library (irrelevant noise)
  - The Ideas Agent doesn't get access to code execution (safety)
  - Each agent's context window stays lean and focused
  - Access control is in one place — easy to audit and change

This is called "least privilege" — give each component only what it needs.

USAGE:
------
  from utils.claude_client import ClaudeClient

  client = ClaudeClient()

  # Simple chat (no tools)
  reply = client.chat(
      messages=[{"role": "user", "content": "What is RAG?"}],
      system="You are a helpful AI tutor.",
  )

  # Chat with tools (ReAct loop handled for you)
  reply = client.chat_with_tools(
      messages=[{"role": "user", "content": "Research transformer architecture"}],
      system="You are a research agent.",
      agent_name="research",    # controls which tools Claude can see
  )
"""

import json
from typing import Optional
import anthropic

from config.settings import ANTHROPIC_API_KEY

# ── Tool definitions for each MCP server ──────────────────────────────────────
# These are the "menus" Claude reads to understand what tools exist.
# Organised by server, then assembled per-agent in TOOL_REGISTRY below.

_LEARNER_STATE_TOOLS = [
    {
        "name": "get_learner_profile",
        "description": "Get the full learner profile: skill level, goals, study history.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "update_skill_level",
        "description": "Update the learner's skill level (beginner/intermediate/advanced).",
        "input_schema": {
            "type": "object",
            "properties": {
                "level": {"type": "string", "description": "beginner, intermediate, or advanced"},
            },
            "required": ["level"],
        },
    },
    {
        "name": "log_topic_studied",
        "description": "Record that the learner studied a topic in this session.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic":   {"type": "string"},
                "agent":   {"type": "string"},
                "summary": {"type": "string"},
            },
            "required": ["topic", "agent"],
        },
    },
    {
        "name": "get_recent_topics",
        "description": "Get the most recently studied topics (newest first).",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of topics (default 5)"},
            },
            "required": [],
        },
    },
    {
        "name": "set_learning_goal",
        "description": "Save the learner's current stated learning goal.",
        "input_schema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string"},
            },
            "required": ["goal"],
        },
    },
    {
        "name": "get_progress_summary",
        "description": "Get a plain-English summary of the learner's overall progress.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]

_SEARCH_TOOLS = [
    {
        "name": "web_search",
        "description": (
            "Search the web using Tavily for current, real-world information. "
            "Use for recent news, tutorials, library docs, product pages, and anything "
            "that requires up-to-date web results."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query":       {"type": "string", "description": "The search query."},
                "max_results": {"type": "integer", "description": "Number of results (default 5)."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "wiki_search",
        "description": "Get a Wikipedia summary for an AI/ML concept or topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
            },
            "required": ["topic"],
        },
    },
    {
        "name": "search_arxiv",
        "description": "Search arXiv for recent AI/ML research papers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query":       {"type": "string"},
                "max_results": {"type": "integer"},
            },
            "required": ["query"],
        },
    },
]

_CODE_TOOLS = [
    {
        "name": "execute_python",
        "description": "Execute Python code and return stdout + stderr. 10s timeout.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
            },
            "required": ["code"],
        },
    },
    {
        "name": "check_syntax",
        "description": "Check Python code for syntax errors without running it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
            },
            "required": ["code"],
        },
    },
    {
        "name": "get_code_template",
        "description": "Get a starter code template. Options: claude_chat, rag_pipeline, streamlit_app, tool_use, embeddings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "template_name": {"type": "string"},
            },
            "required": ["template_name"],
        },
    },
    {
        "name": "list_templates",
        "description": "List all available code templates with descriptions.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]

_ASSESSMENT_TOOLS = [
    {
        "name": "save_score",
        "description": "Record a practice session score.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic":     {"type": "string"},
                "mode":      {"type": "string", "description": "quiz, challenge, or interview"},
                "score":     {"type": "integer"},
                "max_score": {"type": "integer"},
                "notes":     {"type": "string"},
            },
            "required": ["topic", "mode", "score", "max_score"],
        },
    },
    {
        "name": "get_weak_topics",
        "description": "Get topics where the learner's average score is below a threshold.",
        "input_schema": {
            "type": "object",
            "properties": {
                "threshold": {"type": "number", "description": "0.0–1.0, default 0.6"},
            },
            "required": [],
        },
    },
    {
        "name": "get_stats_summary",
        "description": "Get a plain-English summary of the learner's practice history.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]

_IDEAS_TOOLS = [
    {
        "name": "save_idea",
        "description": "Save a project idea to the learner's library.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":       {"type": "string"},
                "description": {"type": "string"},
                "topic":       {"type": "string"},
                "mode":        {"type": "string"},
            },
            "required": ["title", "description", "topic"],
        },
    },
    {
        "name": "get_ideas",
        "description": "Get the learner's saved project ideas, newest first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer"},
            },
            "required": [],
        },
    },
    {
        "name": "search_ideas",
        "description": "Search saved ideas by keyword.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
            },
            "required": ["query"],
        },
    },
]


# ── Tool Registry ─────────────────────────────────────────────────────────────
# Maps each agent name → the tools it is allowed to use.
# This is the "least privilege" access control list.
#
# Key design decisions:
#   - ALL agents get learner_state — it's the shared backbone
#   - Research gets search tools — that's its whole job
#   - Coding gets code execution — so it can verify its own answers
#   - Practice gets assessment — to save/read scores
#   - Learning Manager gets assessment + learner_state — to plan next steps
#   - Ideas gets ideas tools — to save/retrieve project ideas

TOOL_REGISTRY: dict[str, list[dict]] = {
    "coding":   _CODE_TOOLS + _LEARNER_STATE_TOOLS,
    "research": _SEARCH_TOOLS + _LEARNER_STATE_TOOLS,
    "practice": _ASSESSMENT_TOOLS + _LEARNER_STATE_TOOLS,
    "learning": _ASSESSMENT_TOOLS + _LEARNER_STATE_TOOLS,
    "ideas":    _IDEAS_TOOLS + _LEARNER_STATE_TOOLS,
}


# ── ClaudeClient ──────────────────────────────────────────────────────────────

class ClaudeClient:
    """
    Shared wrapper around the Anthropic SDK.

    Provides two methods:
      chat()            — simple one-turn call (no tools)
      chat_with_tools() — full ReAct loop with tool use

    Both accept the same message format as the raw Anthropic SDK.
    """

    DEFAULT_MODEL = "claude-sonnet-4-6"
    MAX_TOOL_ITERATIONS = 5

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or ANTHROPIC_API_KEY
        if not key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY is not set. "
                "Add it to your .env file: ANTHROPIC_API_KEY=sk-ant-..."
            )
        self.client = anthropic.Anthropic(api_key=key)

    # ── Simple chat (no tool use) ──────────────────────────────────────────────

    def chat(
        self,
        messages: list[dict],
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model: Optional[str] = None,
    ) -> str:
        """
        Send messages to Claude and get a text reply. No tools.

        Use this for straightforward questions where Claude doesn't need
        to call any external tools.

        Args:
            messages:    List of {"role": "user"/"assistant", "content": "..."}
            system:      System prompt (Claude's instructions / personality)
            temperature: 0.0 = focused, 1.0 = creative (default 0.7)
            max_tokens:  Max reply length (default 4096)
            model:       Override model name (default: claude-sonnet-4-6)

        Returns:
            Claude's text reply as a string.
        """
        try:
            response = self.client.messages.create(
                model=model or self.DEFAULT_MODEL,
                system=system,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except anthropic.AuthenticationError:
            return "[Error]: Invalid API key. Check ANTHROPIC_API_KEY in your .env file."
        except anthropic.RateLimitError:
            return "[Error]: Rate limit reached. Please wait a moment and try again."
        except anthropic.APIConnectionError:
            return "[Error]: Could not reach the Anthropic API. Check your internet connection."
        except anthropic.APIError as e:
            return f"[Error]: Anthropic API error — {e}"
        for block in response.content:
            if block.type == "text":
                return block.text
        return ""

    # ── ReAct loop (with tool use) ─────────────────────────────────────────────

    def chat_with_tools(
        self,
        messages: list[dict],
        system: str = "",
        agent_name: str = "",
        tools: Optional[list[dict]] = None,
        tool_executor=None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model: Optional[str] = None,
    ) -> str:
        """
        Run a full Claude ReAct loop with tool use.

        Claude will reason, call tools as needed, observe results, and repeat
        until it gives a final answer or hits MAX_TOOL_ITERATIONS.

        How it works (the ReAct pattern):
          1. Send messages + tools to Claude
          2. If Claude wants a tool → run it → send result back → repeat
          3. When Claude says stop_reason="end_turn" → return the text

        Args:
            messages:      Conversation history (user/assistant only, no system)
            system:        System prompt string
            agent_name:    Agent identifier — picks tools from TOOL_REGISTRY.
                           Ignored if `tools` is provided directly.
            tools:         Override: pass tool definitions directly instead of
                           using the registry. Optional.
            tool_executor: A callable(tool_name, tool_args) → str that runs the
                           actual tool logic. If None, tools return a placeholder.
            temperature:   Creativity (default 0.7)
            max_tokens:    Max tokens per Claude call (default 4096)
            model:         Model override

        Returns:
            Claude's final text answer as a string.
        """
        # Resolve tools from registry if not provided directly
        active_tools = tools or TOOL_REGISTRY.get(agent_name, [])

        working_messages = list(messages)  # don't mutate the caller's list

        for _ in range(self.MAX_TOOL_ITERATIONS):
            try:
                response = self.client.messages.create(
                    model=model or self.DEFAULT_MODEL,
                    system=system,
                    messages=working_messages,
                    tools=active_tools,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except anthropic.AuthenticationError:
                return "[Error]: Invalid API key. Check ANTHROPIC_API_KEY in your .env file."
            except anthropic.RateLimitError:
                return "[Error]: Rate limit reached. Please wait a moment and try again."
            except anthropic.APIConnectionError:
                return "[Error]: Could not reach the Anthropic API. Check your internet connection."
            except anthropic.APIError as e:
                return f"[Error]: Anthropic API error — {e}"

            # ── Claude is done ────────────────────────────────────────────────
            if response.stop_reason == "end_turn":
                for block in response.content:
                    if block.type == "text":
                        return block.text
                return ""

            # ── Claude wants tools ────────────────────────────────────────────
            if response.stop_reason == "tool_use":
                # Add Claude's full response (with tool_use blocks) to history
                working_messages.append({
                    "role": "assistant",
                    "content": response.content,
                })

                # Execute each requested tool and collect results
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        if tool_executor:
                            result = tool_executor(block.name, block.input)
                        else:
                            result = json.dumps({
                                "note": f"Tool '{block.name}' was called with args: {block.input}. "
                                        "No executor provided — this is a dry run."
                            })

                        tool_results.append({
                            "type":        "tool_result",
                            "tool_use_id": block.id,
                            "content":     str(result),
                        })

                # Send tool results back to Claude
                working_messages.append({
                    "role": "user",
                    "content": tool_results,
                })
                continue

            # Unexpected stop_reason — return whatever text we have
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        # Hit max iterations — return last text seen
        if hasattr(response, "content"):
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
        return "I reached the maximum number of steps. Please try a more specific question."

    def get_tools_for_agent(self, agent_name: str) -> list[dict]:
        """
        Return the list of tool definitions for a named agent.

        Useful when you want to inspect which tools an agent has access to,
        or when building a custom tool list for a new agent type.

        Args:
            agent_name: One of "coding", "research", "practice", "learning", "ideas"

        Returns:
            List of tool definition dicts (empty list if agent_name not found).
        """
        return TOOL_REGISTRY.get(agent_name, [])
