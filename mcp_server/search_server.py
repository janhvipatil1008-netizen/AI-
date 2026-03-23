"""
search_server.py — MCP Server for the AI² Research Tools.

WHAT IS THIS FILE?
------------------
This is a standalone MCP (Model Context Protocol) server that exposes
our search tools (web search + Wikipedia) to ANY MCP-compatible client.

MCP is a standard protocol — like USB for AI tools. Once you run this
server, you can connect to it from:
  - Claude Desktop (add it to your config)
  - Any MCP client library
  - Our Research Agent (uses Claude's tool use API directly instead)

HOW TO RUN THIS STANDALONE:
-----------------------------
    # From the AI² folder:
    python mcp_server/search_server.py

    # The server starts in stdio mode — it waits for MCP clients to connect.
    # Press Ctrl+C to stop.

HOW TO ADD TO CLAUDE DESKTOP:
-------------------------------
Add this to your Claude Desktop config file
(usually at %APPDATA%\\Claude\\claude_desktop_config.json on Windows):

    {
      "mcpServers": {
        "ai2-search": {
          "command": "python",
          "args": ["C:\\\\path\\\\to\\\\AI²\\\\mcp_server\\\\search_server.py"]
        }
      }
    }

KEY CONCEPT — @mcp.tool() decorator:
--------------------------------------
Decorating a function with @mcp.tool() does three things:
  1. Registers the function as an MCP tool
  2. Uses the function's docstring as the tool description
  3. Uses the function's type hints to define the parameter schema

The MCP client (Claude Desktop, our agent, etc.) reads these descriptions
to understand WHAT the tool does and WHEN to use it.
"""

import sys
import os

# Make sure we can import from the parent AI² directory
# (needed when running as a subprocess or standalone)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from utils.search_tools import search_wikipedia, search_arxiv as _search_arxiv

# Create the MCP server with a name
# The name is shown to clients so they know what server they're connected to
mcp = FastMCP("AI² Search Server")


@mcp.tool()
def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web using DuckDuckGo for current information about AI topics.

    Use this tool for:
    - Recent developments, news, and updates (e.g., "latest GPT-4 features")
    - Tutorials and guides (e.g., "LangChain RAG tutorial")
    - Library documentation (e.g., "Anthropic SDK Python examples")
    - Practical implementation examples

    Returns a JSON string containing a list of results, each with:
    - title: The page title
    - url: The full URL
    - snippet: A short excerpt from the page
    """
    results = search_web(query, max_results)
    return json.dumps(results, indent=2)


@mcp.tool()
def wiki_search(topic: str) -> str:
    """
    Get an encyclopedic summary from Wikipedia for an AI/ML topic.

    Use this tool for:
    - Foundational concepts (e.g., "transformer neural network")
    - Definitions and background (e.g., "attention mechanism")
    - Historical context (e.g., "history of neural networks")
    - Mathematical foundations (e.g., "gradient descent")

    Returns a text summary of approximately 5 sentences from Wikipedia.
    """
    return search_wikipedia(topic)


@mcp.tool()
def search_arxiv(query: str, max_results: int = 5) -> str:
    """
    Search arXiv for recent AI/ML research papers. Free, no API key needed.

    Use this tool for:
    - Latest research on specific techniques (e.g., "RAG retrieval augmented generation")
    - Understanding what is state-of-the-art (e.g., "best LLM reasoning 2024")
    - Finding original papers for concepts (e.g., "attention is all you need transformer")
    - Academic context for any AI topic

    Returns a JSON list of papers, each with: title, authors, summary, published date, arxiv URL.

    Args:
        query:       The search query (be specific — e.g. "chain of thought prompting LLM")
        max_results: Number of papers to return (default: 5, max: 10)
    """
    return _search_arxiv(query, max_results)


if __name__ == "__main__":
    # Run the MCP server in stdio mode
    # stdio = communicate via standard input/output (the default for local servers)
    mcp.run()
