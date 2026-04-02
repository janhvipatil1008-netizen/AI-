"""
search_tools.py — Reusable search utilities for the AI² platform.

WHAT THIS FILE DOES:
These two functions are the actual "tools" our Research Agent uses.
They are pure Python — no AI, no Streamlit. Any agent can import them.

They are also used by the MCP server (mcp_server/search_server.py),
which exposes them to Claude Desktop or any MCP-compatible client.

WHY KEEP TOOLS SEPARATE FROM THE AGENT?
One implementation, two ways to use it:
  1. Direct call from research_agent.py (used in our Streamlit app)
  2. Wrapped in MCP server for Claude Desktop / Claude.ai integration
"""

import json
import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

import wikipedia
from tavily import TavilyClient


def search_web(query: str, max_results: int = 5) -> str:
    """
    Search the web using Tavily — an AI-native search API built for agents.

    Tavily returns clean, structured results (no HTML scraping) specifically
    designed for LLM consumption. Free tier: 1000 searches/month.

    REQUIRES: TAVILY_API_KEY in your .env file.
    Get a free key at: https://app.tavily.com

    Args:
        query:       The search query.
        max_results: Number of results to return (default: 5, max: 10).

    Returns:
        JSON string with a list of results, each with title, url, content.
        Returns an error message if the API key is missing or call fails.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return json.dumps({
            "error": "TAVILY_API_KEY not set in .env. Get a free key at app.tavily.com"
        })

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            max_results=min(max_results, 10),
            search_depth="basic",
        )
        results = [
            {
                "title":   r.get("title", ""),
                "url":     r.get("url", ""),
                "content": r.get("content", "")[:500],  # trim long snippets
            }
            for r in response.get("results", [])
        ]
        return json.dumps(results, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Tavily search failed: {str(e)}"})


def search_wikipedia(topic: str) -> str:
    """
    Get a Wikipedia summary for a topic.

    Wikipedia is excellent for foundational AI/ML concepts that have
    stable, encyclopedic definitions (e.g., "transformer neural network",
    "attention mechanism", "gradient descent").

    Args:
        topic: The topic to look up. Examples:
               "Retrieval-Augmented Generation"
               "transformer architecture"
               "reinforcement learning from human feedback"

    Returns:
        A string with the Wikipedia summary (opening ~5 sentences).
        Returns an error message string if the topic isn't found or is
        ambiguous — never raises so the agent loop stays safe.

    Example:
        text = search_wikipedia("vector database")
        print(text[:200])
    """
    try:
        wikipedia.set_lang("en")
        return wikipedia.summary(topic, sentences=5, auto_suggest=True)

    except wikipedia.exceptions.DisambiguationError as e:
        # "Python" could mean the language or the snake.
        # Retry with the first suggested option.
        try:
            return wikipedia.summary(e.options[0], sentences=5)
        except Exception:
            return (
                f"Wikipedia: '{topic}' is ambiguous. "
                f"Try being more specific. Options include: {', '.join(e.options[:3])}"
            )

    except wikipedia.exceptions.PageError:
        return f"Wikipedia: No article found for '{topic}'. Try a different search term."

    except Exception as ex:
        return f"Wikipedia: Search failed — {str(ex)}"


def search_arxiv(query: str, max_results: int = 5) -> str:
    """
    Search arXiv for recent AI/ML research papers. Free, no API key needed.

    Args:
        query:       Search query (e.g. "chain of thought prompting LLM")
        max_results: Number of papers to return (default: 5, max: 10)

    Returns:
        JSON string with a list of papers (title, authors, summary, published, url).
    """
    max_results = min(max_results, 10)
    base_url = "http://export.arxiv.org/api/query"
    params = urllib.parse.urlencode({
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    })

    try:
        with urllib.request.urlopen(f"{base_url}?{params}", timeout=10) as resp:
            xml_data = resp.read().decode("utf-8")
    except Exception as e:
        return json.dumps({"error": f"arXiv request failed: {str(e)}"})

    try:
        root = ET.fromstring(xml_data)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        papers = []
        for entry in root.findall("atom:entry", ns):
            title_el   = entry.find("atom:title", ns)
            summary_el = entry.find("atom:summary", ns)
            pub_el     = entry.find("atom:published", ns)
            id_el      = entry.find("atom:id", ns)
            authors    = [
                a.find("atom:name", ns).text
                for a in entry.findall("atom:author", ns)
                if a.find("atom:name", ns) is not None
            ]
            papers.append({
                "title":     title_el.text.strip() if title_el is not None else "Unknown",
                "authors":   authors[:3],
                "summary":   summary_el.text.strip()[:400] if summary_el is not None else "",
                "published": pub_el.text[:10] if pub_el is not None else "",
                "url":       id_el.text.strip() if id_el is not None else "",
            })
        return json.dumps(papers, indent=2)
    except ET.ParseError as e:
        return json.dumps({"error": f"Failed to parse arXiv response: {str(e)}"})
