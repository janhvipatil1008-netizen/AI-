<div align="center">

# AI² — AI for AI Builders

**A personalised, multi-agent learning platform that teaches you to build with AI — by building with AI.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Claude](https://img.shields.io/badge/Claude-Sonnet%20%2B%20Haiku-D97706?style=flat)](https://anthropic.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-22C55E?style=flat)](LICENSE)

</div>

---

## What is AI²?

AI² is a **team of five specialised AI agents** that collaborate to give you an adaptive, hands-on learning experience for building AI products. Rather than watching videos or reading docs, you learn by doing — writing and running real code, getting quizzed by an AI examiner, and tracking a personalised roadmap.

It targets two tracks:
- **AI Product Managers** — understand AI systems deeply enough to define and ship them
- **AI Builders** — get hands-on with modern AI APIs, RAG, agents, and evals

Everything is tied together by a **persistent learner profile** that every agent reads and writes to — so the platform always knows where you stand.

---

## The Five Agents

| Agent | Role | Personality |
|-------|------|-------------|
| 💻 **Forge** | Mini IDE + AI coding tutor | Practical, code-first. Writes code with you, debugs your errors, generates challenges. |
| 🧭 **Atlas** | Learning coach + research papers | Strategic. Tracks your goals, recommends next steps, curates arXiv papers. |
| 🎯 **Dojo** | Practice arena | Honest examiner. Quizzes, coding challenges, and mock interviews with AI scoring. |
| 💡 **Spark** | Project ideation | Creative. Turns concepts into buildable project ideas with full briefs. |
| 📋 **Syllabus** | Career roadmap | Organised. A 6-phase, 13-week adaptive roadmap across 3 role tracks. |

---

## Feature Highlights

### 🗺️ Mission Control — Unified Chat
Type anything in one chat box. The Orchestrator automatically classifies your message and routes it to the right agent — no clicking around required.

```
You: "Quiz me on RAG"          → Dojo handles it
You: "Explain embeddings"      → Atlas or Forge
You: "Help me debug this code" → Forge
You: "I want to build an idea" → Spark
```

### 💻 Forge — Mini IDE
A full code-writing environment inside the browser.
- **Ace Editor** with syntax highlighting, VSCode shortcuts, dark theme
- **5 built-in templates**: OpenAI chat, RAG pipeline, Streamlit chatbot, Claude tool use, embeddings
- **4 quick actions**: Explain, Fix Error, Improve, Challenge
- **Auto-debug**: When your code errors, Forge automatically explains the problem and shows the fix
- **Live execution** with stdout/stderr console (10s timeout)

### 🧭 Atlas — Learning Coach + Research Papers
Atlas knows your full state — goals, syllabus progress, topics completed — and injects it all into every response.

**Coach tab:**
- Sets and tracks multi-step goals with milestones, deadlines, and health scoring
- Monitors goal health: `ON TRACK` / `AT RISK` / `STALLED` / `OVERDUE` / `ACHIEVED`
- Manages a per-topic todo list
- Suggests what to study next based on your roadmap

**Papers tab:**
- 20 hand-picked landmark papers (zero API cost) across Transformers, RAG, Agents, Evals, and more
- Dynamic arXiv search — type any topic, Haiku filters 15 results to the 4–6 most relevant
- 4-layer reading experience: Card → TL;DR → Atlas explanation → original paper

### 🎯 Dojo — Practice Arena
Three modes, all scored by Claude (LLM-as-Judge — no hardcoded answer keys):

| Mode | Format | Scoring |
|------|--------|---------|
| 🎯 Quiz | 5 multiple-choice questions | Correct/Incorrect with explanation |
| 💻 Coding Challenge | Open-ended task, AI code review | 0–10 rubric score |
| 🤝 Mock Interview | Conversational, role-based | 0–5 per question |

### 💡 Spark — Project Ideation
Three modes with different temperatures for different creative needs:
- **Brainstorm (temp 1.0)** — 3–5 varied project ideas from a topic
- **Project Brief (temp 0.3)** — full structured plan: stack, steps, time estimate, risks
- **Idea Feedback (temp 0.5)** — honest feasibility scoring on your idea

### 📋 Syllabus — Adaptive Roadmap
A 6-phase, 13-week roadmap with 3 specialisation tracks:

| Phase | Weeks | Focus |
|-------|-------|-------|
| 🧠 AI Foundations | 1–2 | LLMs, transformers, eval foundations |
| ⚡ APIs & Prompts | 3–4 | API usage, prompt engineering, context |
| 🌾 MVP Build | 5–7 | End-to-end RAG + agent app |
| 📊 Evals Mastery | 8 | Evals, LLM-as-Judge, metrics |
| 🤖 Multi-Agent Systems | 9–11 | Design + build AI² itself |
| 🎯 Portfolio & Prep | 12–13 | Demo, resume, case studies |

**3 Role Tracks:** AI Product Manager · AI Evals Specialist · Context Engineer

### 🏅 XP & Progression
Every meaningful action earns XP — chat, run code, fix bugs, complete quizzes, save ideas. Progress is stored persistently across sessions.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     STREAMLIT UI                         │
│            app.py → workspace.py → agent_view.py        │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                 ORCHESTRATION LAYER                      │
│   Haiku classifier (temp=0) → routes to the right agent │
└──────┬──────────┬──────────┬──────────┬─────────────────┘
       │          │          │          │
    Forge      Atlas       Dojo       Spark
  (coding)   (learning) (practice) (ideation)
       │          │
       └──────────┴──→  ClaudeClient
                         ├── chat()             simple Q&A
                         └── chat_with_tools()  ReAct loop (≤5 iterations)
                                    │
                             TOOL REGISTRY  (least-privilege per agent)
                             ├── coding:   execute_python, check_syntax, templates
                             ├── research: web_search, wiki_search, search_arxiv
                             ├── practice: save_score, get_weak_topics
                             ├── learning: assessment + learner state tools
                             └── ideas:    save_idea, get_ideas
                                    │
                              DATA LAYER  (local JSON, no database)
                              ├── data/learning_profile.json  ← single source of truth
                              ├── data/ideas.json
                              └── data/practice_history.json
```

---

## AI Concepts Built In

This platform *is* an AI system — using it teaches you the patterns behind production AI:

| Concept | Where it's used |
|---------|----------------|
| **Multi-agent orchestration** | Haiku routes every message to a specialised sub-agent |
| **ReAct (Reason + Act) loop** | Research Agent and Forge chain tool calls up to 5 iterations |
| **Tool use / function calling** | Each agent has a least-privilege tool registry |
| **LLM-as-Judge** | Dojo uses Claude to score open-ended quiz and interview answers |
| **System prompt engineering** | Atlas injects full learner state into every system prompt |
| **Prompt adaptation by skill level** | All agents adjust tone, depth, and terminology |
| **Temperature as a design lever** | Spark uses 1.0 for brainstorm, 0.3 for structured briefs |
| **Action tokens** | Atlas emits structured tokens; app code executes the side effects |
| **Skill injection** | Agent behaviour defined in markdown files, not Python |
| **Inter-agent handoff** | Agents pass context to each other via hidden HANDOFF tokens |
| **RAG-adjacent curation** | arXiv fetch → Haiku filter → Haiku enrichment → Sonnet explanation |

---

## Tech Stack

| Technology | Role |
|------------|------|
| **Python 3.11+** | Primary language |
| **Streamlit** | UI framework (multi-page) |
| **Anthropic SDK** | Claude Sonnet (agents) + Haiku (routing, curation) |
| **OpenAI SDK** | Research agent cross-reference (optional) |
| **streamlit-code-editor** | Ace editor component in Forge |
| **Tavily** | Web search API |
| **arXiv API** | Research paper search (free, no key) |
| **Wikipedia** | Encyclopedic search |
| **MCP** | Claude Desktop integration (bonus layer) |

**Models used:**
- `claude-sonnet-4-6` — all five teaching agents (best reasoning quality)
- `claude-haiku-4-5-20251001` — routing classifier, paper curation, paper explanation (fast + cheap)
- `gpt-4o-mini` — Research Agent second opinion (optional)

---

## Project Structure

```
AI²/
├── app.py                       Entry point — loads profile, boots workspace
├── pages/
│   ├── workspace.py             Mission Control hub + stats dashboard
│   └── agent_view.py            All 5 agent views
├── agents/
│   ├── orchestrator.py          Multi-agent router + handoff logic
│   ├── coding_agent.py          Forge
│   ├── learning_agent.py        Atlas
│   ├── practice_agent.py        Dojo
│   ├── idea_agent.py            Spark
│   └── research_agent.py        Research sub-agent (used inside Atlas)
├── config/
│   ├── prompts.py               System prompt builders
│   ├── syllabus.py              6-phase roadmap, 3 role tracks, progress logic
│   ├── settings.py              API keys, model names, constants
│   └── python_curriculum.py     Curriculum topic definitions
├── utils/
│   ├── claude_client.py         Anthropic API wrapper + ReAct loop + tool registry
│   ├── code_runner.py           execute_python, check_syntax, 5 code templates
│   ├── paper_curator.py         Haiku-powered arXiv curation
│   ├── search_tools.py          web_search, wiki_search, search_arxiv
│   └── ui_theme.py              Glassmorphism CSS, Catppuccin Mocha palette
├── skills/                      Agent behaviour as markdown (skill injection)
│   ├── GLOBAL_SKILL.md
│   ├── coding_agent_skill.md
│   ├── learning_manager_skill.md
│   ├── practice_agent_skill.md
│   ├── idea_agent_skill.md
│   └── research_agent_skill.md
├── mcp_server/                  MCP servers for Claude Desktop integration
│   ├── search_server.py
│   ├── code_tools_server.py
│   ├── learner_state_server.py
│   ├── assessment_server.py
│   └── ideas_server.py
└── data/                        Local JSON — all learner state (gitignored)
    ├── learning_profile.json
    ├── ideas.json
    └── practice_history.json
```

---

## Setup

**Prerequisites:** Python 3.11+, an Anthropic API key (required), Tavily API key (optional, for web search)

```bash
# 1. Clone the repo
git clone https://github.com/janhvipatil1008-netizen/AI-.git
cd AI-

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your API keys
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY, TAVILY_API_KEY (optional), OPENAI_API_KEY (optional)

# 5. Run
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## Data & Privacy

All your learning data is stored **locally** in the `data/` folder — no database, no backend server, no sign-in. The `data/` directory is gitignored so your progress never gets committed.

| File | Contents |
|------|----------|
| `data/learning_profile.json` | Progress, goals, XP, syllabus completion, conversation history |
| `data/practice_history.json` | Quiz scores, challenge results, interview sessions |
| `data/ideas.json` | Project ideas saved through Spark |

---

## Design Philosophy

> *"The best way to learn how to build AI systems is to use one that teaches you while demonstrating every pattern you need to know."*

AI² is intentionally transparent — every AI concept it uses is one it teaches:
- The routing classifier is the same pattern you'd build in a production agent
- The ReAct loop in the Research Agent is the same one covered in the curriculum
- The LLM-as-Judge scoring in Dojo is the same pattern used in evals pipelines

You're not just learning *about* these things. You're learning *inside* a working implementation of them.

---

<div align="center">

Built with Claude · Streamlit · Python

*AI² v1.0 — March 2026*

</div>
