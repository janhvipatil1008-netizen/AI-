"""
utils/paper_curator.py — AI-powered paper curation and explanation for AI².

Two public functions:

    curate_papers(topic, raw_papers, skill_level) -> list[dict]
        Takes raw arXiv results, uses Claude Haiku to filter to the 4-6 most
        relevant papers and enrich each with a plain-English summary, a
        "why it matters" line, and a difficulty level badge.

    explain_paper(title, tldr, skill_level) -> str
        Returns a 3-section Atlas explanation of a single paper, adapted to
        the learner's skill level.

Both use claude-haiku-4-5-20251001 for cost efficiency (~$0.0002-0.0003 per call).
"""

from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)

HAIKU_MODEL = "claude-haiku-4-5-20251001"


def _get_client():
    """Lazy-import ClaudeClient to avoid circular imports."""
    from utils.claude_client import ClaudeClient
    return ClaudeClient()


# ── curate_papers ─────────────────────────────────────────────────────────────

def curate_papers(
    topic: str,
    raw_papers: list[dict],
    skill_level: str = "intermediate",
) -> list[dict]:
    """
    Filter and enrich a list of raw arXiv papers for a given topic and learner.

    Args:
        topic:       The search topic the learner entered.
        raw_papers:  List of paper dicts from search_arxiv() —
                     each has: title, authors, summary, published, url
        skill_level: "beginner" | "intermediate" | "advanced"

    Returns:
        List of 4-6 enriched paper dicts, each with:
            title, authors, year, url, tldr, why_it_matters, level
        On failure: returns a best-effort fallback list from raw_papers.
    """
    if not raw_papers:
        return []

    level_guide = {
        "beginner":     "beginner and intermediate",
        "intermediate": "intermediate, with 1-2 beginner or advanced",
        "advanced":     "advanced and intermediate",
    }.get(skill_level, "intermediate")

    prompt = f"""You are a research paper curator for an AI learner (skill level: {skill_level}).
The learner searched for: "{topic}"

From the papers below, select the 4-6 most relevant and important ones.
For each selected paper, output a JSON object with these exact keys:
  title          — exact title from the input
  authors        — "First Author et al." format (max 30 chars)
  year           — 4-digit year string from the published date
  url            — exact URL from the input
  tldr           — ONE plain-English sentence, no jargon, max 15 words
  why_it_matters — ONE practical sentence for AI builders/PMs, max 20 words
  level          — exactly one of: "beginner", "intermediate", "advanced"

Selection rules:
- Prioritise: foundational papers, widely-cited work, recent high-impact results
- Include at least 1 beginner-accessible paper when available
- Skip: highly specialised narrow papers, pure theory with no practical application
- Level guide: beginner=accessible prose, intermediate=applied ML, advanced=novel theory/heavy math
- Favour {level_guide} papers for this learner

Return ONLY a valid JSON array — no markdown fences, no explanation, nothing else.

Papers to choose from:
{json.dumps(raw_papers, indent=2)}"""

    try:
        client = _get_client()
        response = client.chat(
            messages=[{"role": "user", "content": prompt}],
            system="You are a precise JSON-only API. Return valid JSON arrays only.",
            temperature=0.2,
            max_tokens=2048,
            model=HAIKU_MODEL,
        )

        # Strip accidental markdown fences if present
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
            clean = clean.strip()

        curated: list[dict] = json.loads(clean)

        # Validate structure — keep only dicts with required keys
        required = {"title", "url", "tldr", "why_it_matters", "level"}
        valid = [p for p in curated if isinstance(p, dict) and required.issubset(p)]

        # Ensure level is one of the valid values
        for p in valid:
            if p.get("level") not in ("beginner", "intermediate", "advanced"):
                p["level"] = "intermediate"

        return valid[:6] if valid else _fallback_curate(raw_papers)

    except Exception as exc:
        logger.warning("paper_curator.curate_papers failed: %s", exc)
        return _fallback_curate(raw_papers)


def _fallback_curate(raw_papers: list[dict]) -> list[dict]:
    """
    Best-effort fallback when the Haiku curation call fails.
    Returns up to 5 papers using the raw arXiv fields directly.
    """
    result = []
    for p in raw_papers[:5]:
        authors = p.get("authors", [])
        if isinstance(authors, list):
            authors_str = f"{authors[0]} et al." if authors else "Unknown"
        else:
            authors_str = str(authors)[:30]

        result.append({
            "title":          p.get("title", "Untitled"),
            "authors":        authors_str,
            "year":           p.get("published", "")[:4],
            "url":            p.get("url", ""),
            "tldr":           (p.get("summary") or "")[:120].rstrip() + "…",
            "why_it_matters": "",
            "level":          "intermediate",
        })
    return result


# ── explain_paper ─────────────────────────────────────────────────────────────

def explain_paper(
    title: str,
    tldr: str,
    skill_level: str = "intermediate",
) -> str:
    """
    Generate a 3-section Atlas explanation of a research paper.

    Args:
        title:       Paper title.
        tldr:        One-line summary (used as the abstract proxy).
        skill_level: "beginner" | "intermediate" | "advanced"

    Returns:
        Markdown string with three sections:
            **What it is** / **Why it matters** / **Key takeaway**
        Returns an error string on failure.
    """
    tone = {
        "beginner":     "Use simple analogies. Avoid all jargon. Assume no ML background.",
        "intermediate": "Use technical terms but briefly define non-obvious ones.",
        "advanced":     "Skip basics. Focus on architectural choices and trade-offs.",
    }.get(skill_level, "Use clear, accessible language.")

    prompt = f"""Explain this AI/ML research paper to a {skill_level}-level learner.

Title: {title}
Summary: {tldr}

Write exactly 3 short sections using this format:

**What it is**
2-3 sentences in plain English.

**Why it matters**
2-3 sentences on practical value for AI PMs and builders.

**Key takeaway**
1 memorable sentence they can recall weeks later.

Tone: {tone}
Keep the total response under 200 words."""

    try:
        client = _get_client()
        return client.chat(
            messages=[{"role": "user", "content": prompt}],
            system="You are Atlas, a friendly AI learning coach. Be concise and practical.",
            temperature=0.5,
            max_tokens=500,
            model=HAIKU_MODEL,
        )
    except Exception as exc:
        logger.warning("paper_curator.explain_paper failed: %s", exc)
        return (
            f"**What it is**\n{tldr}\n\n"
            "**Why it matters**\nThis is an important paper in the AI/ML field.\n\n"
            "**Key takeaway**\nRead the full paper on arXiv for details."
        )
