"""
router.py — Central Orchestrator (Step 6, not yet built).

WHY THIS EXISTS NOW:
--------------------
We create this stub so the import structure is ready. When we build the
orchestrator in Step 6, we won't need to change any of the agent files —
we just fill in this file.

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

    def route(self, user_message: str, agent_name: str = "coding") -> str:
        return (
            "The orchestrator is coming in Step 6. "
            "For now, use each agent directly."
        )
