"""
skills_loader.py — Loads SKILL.md files into agent system prompts

WHAT IS THIS?
--------------
A tiny utility that reads markdown files from the `skills/` folder and returns
their contents as a string to be appended to an agent's system prompt.

WHY DOES THIS EXIST?
---------------------
Without this: agent behavior = Python code. To change how an agent behaves,
you edit the agent file, re-test, redeploy.

With this: agent behavior = markdown file. To change how an agent behaves,
you edit the relevant skill file in any text editor. No code change.

This separation — "code does the work, markdown defines the behavior" — is how
real AI product teams iterate fast on agent quality without engineering cycles.

SIMPLE ANALOGY:
---------------
A chef (agent) follows a recipe book (SKILL.md). You can swap the recipe book
without hiring a new chef or rebuilding the kitchen.

USAGE:
------
  from utils.skills_loader import load_skill, load_global_skill

  # In an agent's __init__, append to the system prompt:
  system_prompt = build_learning_system_prompt(profile)
  system_prompt += "\\n\\n" + load_global_skill()
  system_prompt += "\\n\\n" + load_skill("learning")
"""

import os

# Skills directory — same level as this file's parent
SKILLS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "skills",
)

# Map agent identifiers → skill filenames
_SKILL_FILES = {
    "learning": "learning_manager_skill.md",
    "research": "research_agent_skill.md",
    "practice": "practice_agent_skill.md",
    "ideas":    "idea_agent_skill.md",
    "global":   "GLOBAL_SKILL.md",
}


def load_skill(agent_name: str) -> str:
    """
    Load the SKILL.md file for a named agent.

    Returns the full markdown content as a string.
    Returns an empty string (not an error) if the file doesn't exist —
    so agents work fine even before their skill file is written.

    Args:
        agent_name: One of "coding", "learning", "research", "practice", "ideas"

    Returns:
        The skill file content, or "" if not found.
    """
    filename = _SKILL_FILES.get(agent_name)
    if not filename:
        return ""

    path = os.path.join(SKILLS_DIR, filename)
    if not os.path.exists(path):
        return ""

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_global_skill() -> str:
    """
    Load the GLOBAL_SKILL.md — rules that apply to every agent.

    Returns the content or "" if the file doesn't exist.
    """
    return load_skill("global")


def load_combined_skill(agent_name: str) -> str:
    """
    Load global skill + agent-specific skill, combined.

    This is the recommended way to use skills. It prepends the global rules
    (things every agent must follow) before the agent-specific rules.

    Args:
        agent_name: The agent identifier.

    Returns:
        Combined skill text, or "" if neither file exists.
    """
    parts = []

    global_skill = load_global_skill()
    if global_skill:
        parts.append(global_skill)

    agent_skill = load_skill(agent_name)
    if agent_skill:
        parts.append(agent_skill)

    return "\n\n---\n\n".join(parts)
