# AI² — Product Documentation

**AI for AI Builders** | A personalised multi-agent learning platform built with Streamlit and Claude.

---

## Table of Contents

1. [High-Level System Overview](#1-high-level-system-overview)
2. [Architecture & Components](#2-architecture--components)
3. [Core Features & Workflows](#3-core-features--workflows)
4. [Technologies Used](#4-technologies-used)
5. [AI Concepts Implemented](#5-ai-concepts-implemented)
6. [Design Decisions & Trade-offs](#6-design-decisions--trade-offs)

---

## 1. High-Level System Overview

### What Is AI²?

AI² is a personalised AI learning platform designed for people who want to build AI products. It targets two audiences: **AI Product Managers** who need to understand AI systems deeply enough to define and ship them, and **AI Builders** who want hands-on coding experience with modern AI APIs.

Rather than a static course, AI² is a team of five specialised AI agents — each an expert in one aspect of learning — that collaborate to give the learner an adaptive, interactive experience.

### The Five Agents at a Glance

| Agent | Icon | Role | Personality |
|-------|------|------|-------------|
| **Forge** | 💻 | Mini IDE + AI coding tutor | Practical, code-first |
| **Atlas** | 🧭 | Learning coach + research papers | Strategic, structured |
| **Dojo** | 🎯 | Practice arena (quiz, challenge, interview) | Honest examiner |
| **Spark** | 💡 | Project ideation | Creative, opinionated |
| **Syllabus** | 📋 | Adaptive career roadmap | Organised, goal-oriented |

### What a Learner Does Each Session

```
Open app → Mission Control (orchestrated chat) or pick an agent directly
     │
     ├── Ask a question → Orchestrator routes to the right agent automatically
     ├── Write and run code in Forge's mini IDE
     ├── Read curated research papers in Atlas
     ├── Take a quiz or mock interview in Dojo
     ├── Brainstorm a project in Spark
     └── Track roadmap progress in Syllabus
```

Everything is tied together by a persistent **learner profile** (`data/learning_profile.json`) that stores progress, goals, XP, and history — so every agent always knows where the learner stands.

---

## 2. Architecture & Components

### 2.1 Overall System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     STREAMLIT UI                         │
│  app.py → workspace.py → agent_view.py                  │
└──────────────┬──────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────┐
│               ORCHESTRATION LAYER                        │
│  agents/orchestrator.py                                  │
│  • Haiku classifier (temp=0, max_tokens=10)             │
│  • Agent cache (lazy-load + persist conversation)        │
│  • Handoff detection + pre-routing                       │
└──┬──────┬──────┬──────┬──────────────────────────────────┘
   │      │      │      │
   ▼      ▼      ▼      ▼
Forge   Atlas   Dojo   Spark        ← 5 specialised agents
               (+ Research sub-agent inside Atlas)
   │
   ▼
ClaudeClient (utils/claude_client.py)
• chat()           — simple Q&A
• chat_with_tools() — ReAct loop (up to 5 iterations)
   │
   ▼
TOOL_REGISTRY  — least-privilege per agent
   │
   ├── coding:   execute_python, check_syntax, get_code_template
   ├── research: web_search, wiki_search, search_arxiv, ask_chatgpt
   ├── practice: save_score, get_weak_topics, get_stats_summary
   ├── learning: assessment tools + learner state tools
   └── ideas:    save_idea, get_ideas, search_ideas
   │
   ▼
DATA LAYER
   data/learning_profile.json  ← single source of truth
   data/ideas.json
   data/practice_history.json
```

### 2.2 File Structure

```
AI²/
├── app.py                    Entry point — loads profile, routes to workspace
├── pages/
│   ├── workspace.py          Hub: Mission Control chat + agent nav + stats
│   └── agent_view.py         Individual agent views (all 5 agents rendered here)
├── agents/
│   ├── orchestrator.py       Multi-agent router + handoff logic
│   ├── coding_agent.py       Forge — CodingAgent class
│   ├── learning_agent.py     Atlas — LearningAgent class
│   ├── practice_agent.py     Dojo — PracticeAgent class
│   ├── idea_agent.py         Spark — IdeaAgent class
│   └── research_agent.py     Research sub-agent (used by Atlas)
├── config/
│   ├── prompts.py            System prompt builders + CURRICULUM_TOPICS
│   ├── syllabus.py           6-phase roadmap, 3 role tracks, progress calc
│   ├── papers.py             20 landmark papers with pre-written TL;DRs
│   └── settings.py           API keys, model names, constants
├── utils/
│   ├── claude_client.py      Anthropic API wrapper + ReAct loop + TOOL_REGISTRY
│   ├── code_runner.py        execute_python, check_syntax, 5 code templates
│   ├── paper_curator.py      Haiku-powered arXiv curation + paper explanation
│   ├── search_tools.py       web_search, wiki_search, search_arxiv
│   ├── skills_loader.py      Loads skill markdown files into system prompts
│   └── ui_theme.py           Glassmorphism CSS, Catppuccin Mocha palette
├── skills/
│   ├── GLOBAL_SKILL.md       Rules applying to all agents
│   ├── coding_agent_skill.md Forge's teaching philosophy + IDE context
│   ├── learning_manager_skill.md Atlas's coaching approach + action tokens
│   ├── practice_agent_skill.md Dojo's examiner rules + scoring formats
│   ├── idea_agent_skill.md   Spark's 3-mode ideation framework
│   └── research_agent_skill.md Research agent's search strategy
├── mcp_server/               MCP servers (Claude Desktop integration)
│   ├── search_server.py      web_search, wiki_search, search_arxiv
│   ├── code_tools_server.py  execute_python, check_syntax, templates
│   ├── learner_state_server.py profile read/write
│   ├── assessment_server.py  scoring tools
│   └── ideas_server.py       idea management
└── data/
    ├── learning_profile.json Learner state (progress, goals, XP, history)
    ├── ideas.json            Saved project ideas
    └── practice_history.json Quiz/challenge/interview scores
```

### 2.3 The Learner Profile — Single Source of Truth

Every agent reads and writes to `data/learning_profile.json`. Its structure:

```json
{
  "skill_level": "beginner | intermediate | advanced",
  "xp": 245,
  "streak": 7,
  "last_login": "2026-03-24",
  "selected_roles": ["aipm", "evals", "context"],

  "topics": {
    "Python fundamentals: functions, OOP, async/await": {
      "status": "pending | in_progress | completed",
      "started_at": "2026-03-17T...",
      "completed_at": null,
      "notes": "..."
    }
    // 11 more curriculum topics
  },

  "todos": [
    { "id": "todo_123", "text": "Practice httpx", "topic": "APIs", "status": "pending" }
  ],

  "goals": [
    {
      "id": "goal_123",
      "title": "Build a RAG pipeline",
      "deadline": "2026-04-15",
      "health": "on_track | at_risk | stalled | overdue | achieved",
      "health_score": 72,
      "milestones": [...],
      "progress_logs": [...],
      "xp_reward": 100
    }
  ],

  "syllabus_progress": {
    "foundation-0-0": "todo | in_progress | done"
  },

  "papers_read": [
    { "title": "ReAct: Synergizing...", "url": "...", "level": "intermediate", "xp_earned": 5 }
  ],

  "conversation_history": [...]  // Atlas only — persisted across sessions
}
```

---

## 3. Core Features & Workflows

### 3.1 Mission Control — Orchestrated Chat (workspace.py)

The home screen has a unified chat box where the learner types freely. The Orchestrator classifies each message and routes it to the right agent — no clicking required.

**How routing works:**
1. Learner types: *"Quiz me on RAG"*
2. Haiku classifier (temp=0, max_tokens=10) outputs: `dojo`
3. Orchestrator fetches cached Dojo agent → calls `agent.chat(message)`
4. Response shown with agent badge: 🎯 **Dojo**

**Agent badges and colours:**
- Forge → 💻 blue `#4A9EFF`
- Atlas → 🧭 purple `#A78BFA`
- Dojo → 🎯 gold `#FBBF24`
- Spark → 💡 pink `#F472B6`

**Stats dashboard (4 tiles):**
- Topics Complete (cyan)
- Curriculum Done % (purple)
- XP Earned (gold)
- Ideas Saved (pink)

---

### 3.2 Forge — Mini IDE with AI Tutor

Forge is a full code-writing environment embedded inside the app.

**Layout:**
```
[Toolbar: 🐍 Python | Template ▼ | Skill ▼ | 🗑 New Chat]
[AI Tutor panel (2/5)] | [Code Editor (3/5)]
                        | [▶ Run] [🔍 Check Syntax] [🗑 Clear]
                        | [Output Console]
```

**AI Tutor Panel (left):**
- 4 quick-action buttons:
  - 📖 **Explain** — Forge explains the current code line by line
  - 🐛 **Fix Error** — Forge explains the stderr and shows the fix
  - ✨ **Improve** — Forge suggests 2–3 concrete improvements
  - 🎯 **Challenge** — Forge generates a 5–15 min coding challenge
- Scrollable chat history
- Chat input: *"Ask Forge anything..."*

**IDE Panel (right):**
- **Ace Editor** — syntax highlighted Python, VSCode shortcuts, dark theme, line numbers
- **5 code templates** available from the toolbar dropdown:
  - `openai_chat` — basic OpenAI chat completion
  - `rag_pipeline` — RAG with ChromaDB
  - `streamlit_app` — Streamlit chatbot with Claude
  - `tool_use` — Claude tool use / function calling loop
  - `embeddings` — OpenAI text embeddings + cosine similarity
- **Run button** — executes code in a subprocess (10-second timeout)
- **Output console** — green for stdout, red for stderr

**Auto-debug flow:**
When code produces an error, Forge automatically sends the error to the AI tutor — no button click needed. The AI explains the error in plain English, identifies the specific line, and shows a minimal fix.

**XP Awards in Forge:**

| Action | XP |
|--------|----|
| Chat message / quick action | +5 |
| Code runs cleanly | +5 |
| Fixed an error (prev run had error, now clean) | +10 |
| Challenge complete | +15 |

---

### 3.3 Atlas — Learning Coach + Research Papers

Atlas has two tabs:

#### Tab 1: Learning Coach

Atlas knows the learner's full state — topics completed, active goals, syllabus progress — and injects it all into the system prompt on every message. This lets Atlas give advice like:

> *"You're 58% through the curriculum. Your RAG pipeline goal is AT RISK — you haven't logged any progress in 9 days. I'd recommend 2 hours on chunking strategies this week."*

**What Atlas does:**
- Recommends what to study next based on goals and roadmap
- Sets and tracks multi-step goals with milestones and deadlines
- Manages a todo list (per topic)
- Monitors goal health (ON TRACK / AT RISK / STALLED / OVERDUE / ACHIEVED)
- Routes to other agents via HANDOFF tokens

**Goal health scoring:**
- Milestone completion ratio: ±30 points
- Time pressure (ahead/behind schedule): ±25 points
- Recent activity (last logged): ±20 points
- Thresholds: ≥60 = on track, 35–59 = at risk, <35 = stalled

**Mid-conversation paper suggestions:**
When Atlas explains a concept in depth, it embeds a hidden tag:
```html
<!-- SUGGEST_PAPERS: RAG retrieval augmented generation -->
```
The UI strips the tag and shows a chip below the message:
> 📄 See papers on "RAG retrieval augmented generation" →

Clicking pre-fills the Papers tab search with that keyword.

#### Tab 2: Research Papers

**Two sources of papers:**

**Static landmark papers (zero API cost):**
20 hand-picked papers across 6 categories with pre-written TL;DRs:
- Transformers & LLMs (4 papers)
- Prompt Engineering (4 papers)
- RAG & Retrieval (3 papers)
- AI Agents & Tools (5 papers)
- Evals & Safety (2 papers)
- Scaling & Systems (2 papers)

**Dynamic arXiv search (Haiku-curated):**
Type any topic → 15 arXiv results fetched → Claude Haiku filters to 4–6 best papers → enriched with TL;DR, why_it_matters, and difficulty level badge.

**4-layer reading experience:**

| Layer | What it shows | API cost |
|-------|--------------|----------|
| Card | Title, authors, year, level badge | $0 |
| TL;DR expand | One-line summary + why it matters | $0 |
| Atlas explains | 3-section breakdown (What / Why / Takeaway) | ~$0.0002 Haiku |
| arXiv link | Opens original paper in new tab | $0 |

**Difficulty levels:** 🟢 Beginner · 🟡 Intermediate · 🔴 Advanced

**XP Awards in Atlas:**

| Action | XP |
|--------|----|
| Coach chat message | +5 |
| Research chat message | +15 |
| Ask Atlas to explain a paper | +5 |
| Paper → Build in Spark | +10 |

---

### 3.4 Dojo — Practice Arena

Three practice modes:

| Mode | Format | Scoring | Placeholder |
|------|--------|---------|-------------|
| 🎯 **Quiz** | 5 multiple-choice questions | Correct / Incorrect per question | "Type A, B, C, or D..." |
| 💻 **Coding Challenge** | Open-ended task, AI code review | 0–10 score with feedback | "Paste your code solution here..." |
| 🤝 **Mock Interview** | Conversational, role-based | 0–5 per question | "Type your answer..." |

**LLM-as-Judge approach:**
Dojo does not hardcode correct answers. It uses Claude (Sonnet) to evaluate responses against rubric dimensions:
- Quiz: Correctness of answer + explanation of why
- Challenge: Code correctness (40%), completeness (25%), clarity (20%), best practices (15%)
- Interview: Relevance, depth, structure, role-fit

**Stats tracked (per mode):**
- Quiz: total sessions, accuracy %
- Challenge: average score / 10
- Interview: sessions per role, average score / 5

**Session completion:**
When a session ends, confetti balloons appear, stats update, and the learner can start another session immediately.

**XP Awards in Dojo:**

| Action | XP |
|--------|----|
| Quiz correct answer | +15 |
| Any other response (wrong/challenge/interview) | +10 |
| Session complete | +50 |

---

### 3.5 Spark — Project Ideation

Three modes with different temperatures:

| Mode | Temperature | Purpose |
|------|-------------|---------|
| 🧠 **Brainstorm** | 1.0 | Generate 3–5 varied project ideas |
| 📋 **Project Brief** | 0.3 | Turn rough idea into structured plan |
| 🔍 **Idea Feedback** | 0.5 | Honest feasibility scoring |

**Brainstorm output format:**
```
### [Title]
Topic: [AI/ML area]
Difficulty: Beginner / Intermediate / Advanced
What it does: [2–3 sentences]
Why it's interesting: [1 sentence learning value]
```

**Project Brief format:**
```
## [Project Title]
Problem: [1–2 sentences]
Tech Stack: [tool → why this choice]
Implementation Steps: [with time estimates]
Estimated time: [MVP range]
Learning outcomes: [3 bullet points]
Risks: [2–3 risks + mitigation]
```

**Idea Feedback rubric (each 1–5):**
- Feasibility — can they build it now?
- Scope — right size?
- Learning Value — new skills?
- Real-world Usefulness — would someone use it?

**Paper → Spark integration:**
From the Atlas Research Papers tab, clicking "Explore ideas from this paper" injects the paper's title and key technique into Spark, which generates project ideas based on the research.

**XP Awards in Spark:**

| Action | XP |
|--------|----|
| Idea saved | +20 |
| Chat message (no save) | +5 |

---

### 3.6 Syllabus — Career Roadmap

A 6-phase, 13-week adaptive roadmap with 3 specialisation tracks.

**6 Phases:**

| Phase | Icon | Weeks | Focus |
|-------|------|-------|-------|
| AI Foundations & PM Core | 🧠 | 1–2 | LLMs, transformers, eval foundations |
| APIs, Prompts & Core Techniques | ⚡ | 3–4 | API usage, prompt engineering, context engineering |
| MVP Build (Agri-Saathi) | 🌾 | 5–7 | End-to-end RAG + agent app |
| Evaluation & Metrics Mastery | 📊 | 8 | Evals, LLM-as-Judge, metrics |
| AI² Multi-Agent System | 🤖 | 9–11 | Design + build the platform itself |
| Portfolio & Interview Prep | 🎯 | 12–13 | Demo, resume, case studies |

**3 Role Tracks:**
- 📦 **AI Product Manager** (AIPM) — cyan
- 🔬 **AI Evals Specialist** (EVALS) — orange
- 🧩 **Context Engineer** (CONTEXT) — green

Task keys follow the format `phase_id-track_idx-task_idx` (e.g., `foundation-0-2`). Status is `todo | in_progress | done`, stored in the learner profile.

---

### 3.7 XP & Progression System

XP is awarded for every meaningful action and persists in the learner profile.

| Action | XP | Agent |
|--------|----|-------|
| Any chat message | +5 | All |
| Code runs cleanly | +5 | Forge |
| Fixed an error | +10 | Forge |
| Challenge complete | +15 | Forge |
| Research session | +15 | Atlas |
| Paper explained by Atlas | +5 | Atlas |
| Quiz correct answer | +15 | Dojo |
| Session complete | +50 | Dojo |
| Idea saved | +20 | Spark |
| Goal achieved | Variable | Atlas |

---

### 3.8 Inter-Agent Handoff System

Agents cooperate by emitting HANDOFF tokens in their responses:

```
HANDOFF: DOJO | RAG systems
HANDOFF: RESEARCH | retrieval-augmented generation
HANDOFF: SPARK | tool use patterns
HANDOFF: FORGE | async Python
```

**How it works:**
1. Agent includes a `HANDOFF: TARGET | topic` line in its response
2. Orchestrator detects it, strips it from display, sets `_pre_route = "dojo"`
3. The learner's **next message** goes directly to Dojo — no classification needed
4. Learner experiences a seamless context switch

**Example:**
> Atlas: *"You've covered enough theory on RAG. Time to test yourself."*
> *(HANDOFF: DOJO | RAG systems — hidden from user)*
> Learner: *"Ok, quiz me"* → goes directly to Dojo

---

### 3.9 Action Token System

Atlas (and Spark) can modify the learner profile by emitting structured tokens:

```
ACTION: COMPLETE_TOPIC | Python fundamentals: functions, OOP, async/await
ACTION: ADD_TODO | Practice httpx | Working with APIs
ACTION: SET_GOAL | Build RAG pipeline | 2026-04-15 | RAG systems, APIs | Week 1: Study concepts ; Week 2: Code
ACTION: LOG_PROGRESS | goal_123 | 2.5 | Got embedding working
ACTION: ACHIEVE_GOAL | goal_123
ACTION: TASK_DONE | foundation-0-1
```

**Full list of Atlas action tokens (12 types):**
`ADD_TODO`, `ADD_NOTE`, `COMPLETE_TOPIC`, `COMPLETE_TODO`, `SET_GOAL`, `LOG_PROGRESS`, `COMPLETE_MILESTONE`, `ACHIEVE_GOAL`, `ADD_MILESTONE`, `TASK_DONE`, `TASK_START`, `SAVE_IDEA`

The LLM can't write to disk directly. Action tokens let it express intent — our code executes the change, saves the profile, and rebuilds the system prompt with fresh state.

---

## 4. Technologies Used

### Core Stack

| Technology | Role | Version |
|------------|------|---------|
| **Python** | Primary language | 3.11+ |
| **Streamlit** | UI framework (multi-page) | ≥1.35 |
| **Anthropic SDK** | Claude API client | ≥0.40 |
| **OpenAI SDK** | OpenAI API client (Research agent) | ≥1.30 |
| **streamlit-code-editor** | Ace editor component (Forge) | ≥0.1.20 |
| **Tavily** | Web search API | ≥0.3.0 |
| **Wikipedia** | Encyclopedic search | ≥1.4.0 |
| **arXiv API** | Research paper search (free, no key) | HTTP/XML |
| **python-dotenv** | Environment variable loading | ≥1.0.0 |
| **MCP** | Model Context Protocol (Claude Desktop) | ≥1.0.0 |

### Models Used

| Model | Where | Why |
|-------|-------|-----|
| `claude-sonnet-4-6` | All 5 teaching agents | Best reasoning, quality responses |
| `claude-haiku-4-5-20251001` | Routing classifier, paper curation, paper explanation | Fast + cheap for high-frequency tasks |
| `gpt-4o-mini` | Research Agent cross-reference | Second AI opinion |

### Cost Profile

| Operation | Model | Est. Cost |
|-----------|-------|-----------|
| Route a message | Haiku | ~$0.0001 |
| Curate 15 arXiv papers → 4–6 | Haiku | ~$0.0003 |
| Explain one paper | Haiku | ~$0.0002 |
| Full teaching conversation turn | Sonnet | ~$0.003–0.01 |
| Landmark papers display | None | $0 |

### Data Storage

All data is local JSON files — no database, no backend server, no auth layer. This makes the app portable and easy to run locally. The trade-off is single-user only (no multi-tenancy).

---

## 5. AI Concepts Implemented

### 5.1 Multi-Agent Orchestration

The app is a functioning multi-agent system. A lightweight orchestrator (Haiku, temp=0) classifies each message and routes it to one of four specialised sub-agents. Each agent has its own:
- System prompt and personality
- Conversation history (persistent within a session)
- Tool access (least-privilege)
- Return type (str or tuple)

**Why it matters:** This is the same architectural pattern used in production AI systems. Learning about it by using it makes the concept concrete.

### 5.2 ReAct (Reason + Act) Loop

The Research Agent and Forge both use the ReAct pattern: the LLM reasons about what to do, takes an action (tool call), observes the result, then reasons again — up to 5 iterations.

```
User message
    → Claude thinks: "I need to search arXiv for this"
    → Calls search_arxiv(query)
    → Observes results
    → Claude thinks: "Let me also check Wikipedia for background"
    → Calls wiki_search(topic)
    → Observes results
    → Claude thinks: "I have enough to answer"
    → Returns synthesis
```

Implemented in `utils/claude_client.py → chat_with_tools()`.

### 5.3 Tool Use / Function Calling

Each agent declares a set of tools (JSON schema). Claude decides *when* to call them. The app executes the tool and sends the result back. Agents cannot access tools outside their registry — the **least-privilege principle**.

**Tool registries:**
```python
TOOL_REGISTRY = {
    "coding":   [execute_python, check_syntax, get_code_template] + learner_state_tools,
    "research": [web_search, wiki_search, search_arxiv, ask_chatgpt] + learner_state_tools,
    "practice": [save_score, get_weak_topics] + learner_state_tools,
    "learning": [assessment_tools] + learner_state_tools,
    "ideas":    [save_idea, get_ideas] + learner_state_tools,
}
```

### 5.4 System Prompt Engineering

The entire learner state is injected into Atlas's system prompt on every call:

```
You are the Learning Manager...

Current progress: 7/12 topics complete (58%)
In progress: RAG systems
Pending: 5 topics

Active goals:
[AT RISK] Build RAG pipeline — deadline 2026-04-15 (1/3 milestones done, 0 hours this week)

Next syllabus tasks:
[ACTIVE] foundation-0-2: Read the Attention Is All You Need paper
[TODO]   foundation-0-3: Watch Andrej Karpathy's neural nets video

Papers read: 3 (ReAct, Chain-of-Thought, RAG original)
```

The LLM has "zero memory" between calls but this prompt gives it complete context. This is the standard production pattern for stateful AI systems.

### 5.5 LLM-as-Judge

Dojo uses Claude to evaluate open-ended answers — no hardcoded answer keys. The evaluator scores on a rubric and provides structured feedback. This is the same pattern used in production AI evaluation pipelines (like MT-Bench and Chatbot Arena, which are in the landmark papers library).

### 5.6 Prompt Adaptation by Skill Level

Every agent adjusts its tone and depth based on `skill_level`:

| Level | Beginner | Intermediate | Advanced |
|-------|---------|-------------|---------|
| Analogies | Always | When helpful | Rarely |
| Comments | Line by line | Key lines only | Minimal |
| Terminology | Simplified | Proper | Assumed |
| Style | Ask "make sense?" | Explain trade-offs | Treat as peer |

### 5.7 Temperature as a Design Lever

Spark uses three different temperatures for its three modes:

- **Brainstorm (1.0):** High temperature = more varied, creative, unexpected ideas
- **Project Brief (0.3):** Low temperature = structured, consistent, reliable output
- **Idea Feedback (0.5):** Mid temperature = balanced directness

### 5.8 RAG-Adjacent: arXiv + Haiku Curation

The Research Papers feature implements a simplified RAG-like pattern:
1. **Retrieve** — arXiv API returns 15 candidate papers
2. **Filter** — Claude Haiku selects 4–6 most relevant for the learner's query and level
3. **Augment** — Haiku enriches each paper with a TL;DR, why_it_matters, and difficulty level
4. **Generate** — Full Atlas explanation (3-section breakdown) on demand

### 5.9 Skill Files as Behaviour Configuration

Agent behaviour is defined in markdown files (`skills/`), not hardcoded in Python. Each file contains the agent's:
- Core philosophy
- Adaptive rules by skill level
- Output formats (with worked examples)
- Handoff conditions

To change how Forge teaches, you edit a markdown file. No redeploy of Python logic needed. This is the **skill injection** pattern — a clean separation between LLM behaviour and application code.

### 5.10 Action Tokens for Side Effects

LLMs can't call Python functions directly. Action tokens solve this:

```
Atlas says:  ACTION: COMPLETE_TOPIC | RAG systems
Our code:    profile["topics"]["RAG systems"]["status"] = "completed"
             profile.save()
             rebuild_system_prompt(profile)
```

This is a form of **structured output** — the LLM speaks a mini language, and the application interprets it. It's similar to function calling but without requiring the model to emit valid JSON tool calls.

---

## 6. Design Decisions & Trade-offs

### Decision 1: Local JSON Over a Database

**Choice:** All learner state stored in `data/learning_profile.json`.

**Why:**
- Zero setup — no Postgres, no Supabase, no auth tokens
- Portable — clone repo, run `streamlit run app.py`, everything works
- Readable — JSON is inspectable and editable by hand

**Trade-off:**
- Single-user only — no multi-tenancy
- No concurrent writes — fine for one learner, would break with multiple users
- No versioning or migration — profile schema changes require manual migration

---

### Decision 2: Skill Files as Markdown, Not Code

**Choice:** Agent behaviour defined in `skills/*.md` files loaded into system prompts.

**Why:**
- Non-engineers can edit agent personality without touching Python
- Rapid iteration — change the skill file, restart the app, new behaviour
- Clear separation of concerns: Python handles state and UI; markdown handles LLM behaviour

**Trade-off:**
- Behaviour changes are invisible to the type checker — no linting, no tests
- Long skill files make system prompts large (more tokens = higher cost)
- Race between skill file update and system prompt rebuild could cause inconsistency in long sessions

---

### Decision 3: Haiku for Routing and Curation

**Choice:** Claude Haiku (not Sonnet) for message classification, paper curation, and paper explanation.

**Why:**
- Routing is called on **every user message** — Sonnet would be 10–15× more expensive
- Classification needs only 1 word output — Haiku is more than capable
- Paper curation needs structured JSON — Haiku at temp=0.2 is reliable

**Trade-off:**
- Haiku occasionally misclassifies ambiguous messages (e.g., "I want to test RAG" could be Forge or Dojo)
- Haiku paper explanations are slightly shallower than Sonnet

---

### Decision 4: Agent Conversation Persistence Strategy

**Choice:** Atlas saves conversation history to disk; other agents keep history in memory only.

**Why:**
- Atlas is the long-term coach — continuity across sessions is essential
- Forge conversations are tactical (per-coding-session) — no need to persist
- Dojo sessions are self-contained (start → quiz → end)
- Spark conversations are mode-scoped (brainstorm mode history isn't useful in brief mode)

**Trade-off:**
- Atlas's saved history can grow very large over many sessions
- History trim (`MAX_HISTORY_TURNS = 20`) may lose context in very long conversations
- Other agents lose all context on browser refresh — learner must re-explain context

---

### Decision 5: ReAct Loop Max 5 Iterations

**Choice:** `chat_with_tools()` runs a maximum of 5 tool iterations before returning.

**Why:**
- Prevents infinite loops on unexpected tool failures
- Caps latency — 5 tool calls × ~1s each = max ~5s added latency
- Cost ceiling — limits token spend on runaway tool chains

**Trade-off:**
- Complex research (web + wiki + arXiv + ChatGPT = 4 tools) fits comfortably in 5 iterations
- If tools fail or return empty results, Claude may use all 5 iterations trying alternatives
- A task requiring 6+ tool calls will return a partial answer

---

### Decision 6: Streamlit for the UI

**Choice:** Streamlit instead of React/Next.js.

**Why:**
- Pure Python — no context switch to JavaScript
- Built-in state management (`st.session_state`)
- Rich component library (chat_message, expander, tabs, columns)
- Fast to iterate — save file → hot reload

**Trade-off:**
- Streamlit reruns the entire script on every interaction — state management requires care
- Tabs cannot be switched programmatically — workaround: `papers_preload` session state key pre-fills search, simulating "open this tab with data"
- Custom UI requires HTML injection via `st.markdown(unsafe_allow_html=True)` — harder to maintain
- Not production-grade for high concurrency

---

### Decision 7: MCP Servers as a Bonus Layer

**Choice:** All tools are also exposed as MCP servers for Claude Desktop.

**Why:**
- Same tool implementations, zero duplication — MCP wraps the existing functions
- Lets power users interact with their learning data from Claude Desktop
- Demonstrates the MCP pattern to learners using the platform

**Trade-off:**
- MCP servers must be started separately — not integrated into the Streamlit boot process
- Increases surface area for bugs in tool implementations
- MCP is relatively new — API stability not guaranteed

---

### Decision 8: Glassmorphism Dark Theme

**Choice:** Catppuccin Mocha palette with frosted glass components, injected as custom CSS.

**Why:**
- Immediately distinctive — looks professional and modern
- Dark theme is standard for developer tools
- Glassmorphism suits an "AI platform" aesthetic
- Catppuccin is a popular, well-designed palette with good contrast ratios

**Trade-off:**
- Heavy CSS injection (`st.markdown(unsafe_allow_html=True)`) is fragile — Streamlit internals could change and break selectors
- Backdrop blur (`backdrop-filter`) has no effect on some elements due to Streamlit's iframe architecture
- Custom theme overrides Streamlit's built-in theme — accessibility features (high contrast mode) may not work

---

*Documentation generated from source code analysis — March 2026.*
*Platform: AI² v1.0 | Stack: Python · Streamlit · Claude API · OpenAI API*
