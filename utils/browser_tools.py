"""
browser_tools.py — Playwright-powered browser tools for AI² agents.

SYNC ONLY: Uses playwright.sync_api exclusively. The async Playwright API
is incompatible with Streamlit's event loop and will raise RuntimeError.

HEADLESS ONLY: No GUI window. Required when running inside a Streamlit server.

FIRST-TIME SETUP (run once after pip install playwright):
    python -m playwright install chromium

All functions return plain strings — safe to pass directly as tool results
in the Claude ReAct loop.
"""

from __future__ import annotations

import json
import re

# ── Constants ──────────────────────────────────────────────────────────────────

_TIMEOUT_MS = 15_000          # 15 seconds per navigation
_MAX_CONTENT_CHARS = 6_000    # trim long pages to keep token count manageable
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

# ── Availability check (once at import time) ───────────────────────────────────
# Avoids repeated ModuleNotFoundError on every call if playwright isn't installed.

_PLAYWRIGHT_AVAILABLE: bool = False
_PLAYWRIGHT_ERROR: str = ""

try:
    from playwright.sync_api import sync_playwright as _sync_playwright  # noqa: F401
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    _PLAYWRIGHT_ERROR = (
        "Playwright is not installed. "
        "Run: pip install playwright && python -m playwright install chromium"
    )


# ── Internal helpers ───────────────────────────────────────────────────────────

def _get_browser():
    """
    Start a sync Playwright context and return (pw, browser).
    Caller is responsible for calling browser.close() and pw.stop().

    A fresh instance is created per-call (not a module-level singleton)
    because Playwright objects are not thread-safe and Streamlit may run
    each script rerun on a different thread.
    """
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    return pw, browser


def _extract_readable_text(page) -> str:
    """
    Extract human-readable text from a rendered page.
    Tries <article> → <main> → <body> to avoid nav/footer noise.
    Collapses excess whitespace and trims to _MAX_CONTENT_CHARS.
    """
    text = ""
    for selector in ["article", "main", "body"]:
        try:
            el = page.query_selector(selector)
            if el:
                t = el.inner_text()
                if t and len(t.strip()) > 100:
                    text = t
                    break
        except Exception:
            continue

    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) > _MAX_CONTENT_CHARS:
        text = text[:_MAX_CONTENT_CHARS] + f"\n\n[... content trimmed at {_MAX_CONTENT_CHARS} chars ...]"
    return text


# ── Public tool functions ──────────────────────────────────────────────────────

def browse_url(url: str, question: str = "") -> str:
    """
    Navigate to a URL and return its full readable text content.

    Args:
        url:      The full URL to visit (must include https:// or http://).
        question: Optional focus question. If provided, prefixes the result
                  so Claude knows what to look for in the page content.

    Returns:
        String with page title + readable body text, or an error message.
    """
    if not _PLAYWRIGHT_AVAILABLE:
        return f"[browser_tools unavailable]: {_PLAYWRIGHT_ERROR}"

    pw = browser = None
    try:
        pw, browser = _get_browser()
        page = browser.new_page(user_agent=_USER_AGENT)
        page.goto(url, timeout=_TIMEOUT_MS, wait_until="domcontentloaded")

        title = page.title()
        text = _extract_readable_text(page)

        result = f"# {title}\nURL: {url}\n\n{text}"
        if question:
            result = f"[Focus question: {question}]\n\n" + result
        return result

    except Exception as e:
        etype = type(e).__name__
        if "Timeout" in etype:
            return (
                f"[browse_url error]: Page at {url} did not load within "
                f"{_TIMEOUT_MS // 1000}s. The site may be slow or require JavaScript. "
                "Try a different URL or use web_search instead."
            )
        return f"[browse_url error]: {etype}: {e}"

    finally:
        if browser:
            browser.close()
        if pw:
            pw.stop()


def search_and_browse(query: str, max_pages: int = 2) -> str:
    """
    Search the web via Tavily and then browse the top result pages for
    full content (not just snippets).

    Args:
        query:     The search query.
        max_pages: Number of top results to open and read (default 2, max 5).

    Returns:
        Concatenated full-page content from each visited page.
    """
    if not _PLAYWRIGHT_AVAILABLE:
        return f"[browser_tools unavailable]: {_PLAYWRIGHT_ERROR}"

    import os
    from tavily import TavilyClient

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return json.dumps({"error": "TAVILY_API_KEY not set. search_and_browse requires Tavily for the URL list."})

    max_pages = min(max_pages, 5)

    # Step 1: Get URLs from Tavily
    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, max_results=max_pages, search_depth="basic")
        results = response.get("results", [])
    except Exception as e:
        return json.dumps({"error": f"Tavily search failed: {e}"})

    if not results:
        return "No search results found."

    # Step 2: Browse each URL and collect full content
    sections = []
    for i, r in enumerate(results[:max_pages], 1):
        url = r.get("url", "")
        title = r.get("title", "")
        snippet = r.get("content", "")[:300]

        if not url:
            continue

        page_content = browse_url(url)

        # Fall back to Tavily snippet if the page fails to load
        if page_content.startswith("[browse_url error]"):
            page_content = f"[Could not load full page — Tavily snippet:]\n{snippet}"

        sections.append(f"## Result {i}: {title}\nURL: {url}\n\n{page_content}")

    return "\n\n---\n\n".join(sections) if sections else "No pages could be loaded."


def scrape_github_repo(repo_url: str) -> str:
    """
    Visit a GitHub repository and extract description, topics, stars, and README.

    Args:
        repo_url: Full GitHub URL or short form 'owner/repo'.

    Returns:
        Structured text with repo metadata and README content.
    """
    if not _PLAYWRIGHT_AVAILABLE:
        return f"[browser_tools unavailable]: {_PLAYWRIGHT_ERROR}"

    # Normalise short "owner/repo" form
    if not repo_url.startswith("http"):
        repo_url = f"https://github.com/{repo_url.lstrip('/')}"

    pw = browser = None
    try:
        pw, browser = _get_browser()
        page = browser.new_page(user_agent=_USER_AGENT)
        page.goto(repo_url, timeout=_TIMEOUT_MS, wait_until="domcontentloaded")

        description = stars = ""
        topics: list[str] = []
        readme = ""

        try:
            el = (page.query_selector('[data-testid="repo-description-container"] p')
                  or page.query_selector(".f4.my-3"))
            if el:
                description = el.inner_text().strip()
        except Exception:
            pass

        try:
            els = (page.query_selector_all('[data-testid="topic-tag"]')
                   or page.query_selector_all(".topic-tag"))
            topics = [e.inner_text().strip() for e in els]
        except Exception:
            pass

        try:
            el = (page.query_selector('[data-testid="stargazers-count"]')
                  or page.query_selector("#repo-stars-counter-star"))
            if el:
                stars = el.inner_text().strip()
        except Exception:
            pass

        try:
            el = (page.query_selector('[data-testid="readme-container"]')
                  or page.query_selector("#readme article")
                  or page.query_selector("article.markdown-body"))
            if el:
                readme = el.inner_text().strip()
                if len(readme) > _MAX_CONTENT_CHARS:
                    readme = readme[:_MAX_CONTENT_CHARS] + "\n\n[README trimmed...]"
        except Exception:
            pass

        # Fallback: general page text if nothing specific extracted
        if not readme and not description:
            return browse_url(repo_url, question="What does this repository do?")

        return "\n".join([
            f"# GitHub Repository: {repo_url}",
            f"\n**Description:** {description or '(none)'}",
            f"**Stars:** {stars or '(unknown)'}",
            f"**Topics:** {', '.join(topics) if topics else '(none)'}",
            "\n## README\n",
            readme or "(No README found)",
        ])

    except Exception as e:
        return f"[scrape_github_repo error]: {type(e).__name__}: {e}"

    finally:
        if browser:
            browser.close()
        if pw:
            pw.stop()
