"""
openai_client.py — Shared OpenAI client for the entire AI² platform.

WHY a shared client?
--------------------
Every agent needs to call the OpenAI API. If each agent created its own
`openai.OpenAI()` object, we'd have multiple connections to the same API,
and we'd have to pass the API key around everywhere.

Instead, we create ONE client here and every agent imports it. This is
called a "singleton" pattern — there's only ever one instance.

Think of it like a single phone line to OpenAI that everyone in the office
shares, rather than giving each person their own phone.
"""

import openai
from config.settings import OPENAI_API_KEY

# Create the client once when this file is first imported.
# All agents call get_client() to use this same instance.
_client = openai.OpenAI(api_key=OPENAI_API_KEY)


def get_client() -> openai.OpenAI:
    """Return the shared OpenAI client instance."""
    return _client
