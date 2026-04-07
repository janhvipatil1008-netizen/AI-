"""
router.py — Legacy stub (NOT the real router).

⚠️  The real orchestrator is in agents/orchestrator.py (Orchestrator class).
    That file contains the full routing logic: classification via Haiku,
    handoff detection, agent caching, and a chat() method used by workspace.py.

This file is kept only so that old import paths don't break.
Do NOT add routing logic here — edit agents/orchestrator.py instead.

WHY THIS EXISTS NOW:
--------------------
We created this stub so the import structure was ready before the orchestrator
was built. The real implementation landed in agents/orchestrator.py.

WHAT IT WILL DO:
----------------
The orchestrator receives a message and decides which agent should handle it.

Example flow:
  User: "Can you quiz me on RAG?"
  Router: detects "quiz" intent → routes to PracticeAgent
  PracticeAgent: returns quiz questions

  User: "I want to research vector databases more"
  Router: detects "research" intent → routes to ResearchAgent
  ResearchAgent: searches web and returns summary

FUTURE INTERFACE:
-----------------
    from orchestrator.router import Router

    router = Router()
    response = router.route(user_message="What is a function?")

Each agent exposes:
  .chat(message: str) -> str          # get a response
  .to_dict() -> dict                  # serialize state for handoffs
"""


class Router:
    """Placeholder for the central orchestrator. Coming in Step 6."""

    def route(self, user_message: str, agent_name: str = "atlas") -> str:
        return (
            "The orchestrator is coming in Step 6. "
            "For now, use each agent directly."
        )
