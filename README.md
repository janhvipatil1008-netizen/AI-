# AI² — AI for AI Builders

A personalised AI learning platform built with Streamlit and Claude. Learn how to build with AI APIs through an adaptive curriculum, hands-on coding, and a team of specialised AI agents.

## Agents

| Agent | Role |
|-------|------|
| **Atlas** | AI Learning Coach — guided lessons, curated research papers, progress tracking |
| **Forge** | Mini IDE — Ace editor, live code execution, integrated AI coding tutor |
| **Dojo** | Practice — quizzes, coding challenges, mock interviews with LLM-as-Judge scoring |
| **Spark** | Project Ideation — turns concepts into buildable project ideas |
| **Syllabus** | Adaptive career roadmap across AI PM and AI Builder tracks |

## Setup

1. Clone the repo
2. Copy `.env.example` to `.env` and add your API keys
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```

## Stack

- **Python** + **Streamlit** — UI and app framework
- **Anthropic Claude API** — all AI agents (Sonnet for teaching, Haiku for routing/curation)
- **OpenAI API** — optional integrations
- **arXiv API** — research paper search (free, no key required)
- **Ace Editor** (`streamlit-code-editor`) — syntax-highlighted code editor in Forge
