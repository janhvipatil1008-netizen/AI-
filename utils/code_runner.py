"""
code_runner.py — Tool executor for CodingAgent's live code execution.

Implements every tool in TOOL_REGISTRY["coding"]:
  execute_python    → run code in a subprocess with a 10-second timeout
  check_syntax      → compile()-check without running
  get_code_template → starter code templates for common AI patterns
  list_templates    → list available template names
  get_learner_profile / update_skill_level / log_topic_studied /
  get_recent_topics / set_learning_goal / get_progress_summary
    → read/write data/learning_profile.json
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

PROFILE_PATH = Path("data/learning_profile.json")

# ── Starter templates ──────────────────────────────────────────────────────────

_TEMPLATES: dict[str, str] = {
    "openai_chat": '''\
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user",   "content": "What is RAG?"},
    ],
)
print(response.choices[0].message.content)
''',

    "rag_pipeline": '''\
import os
from anthropic import Anthropic
import chromadb

# 1. Embed documents
client    = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
chroma    = chromadb.Client()
collection = chroma.create_collection("docs")

documents = ["RAG stands for Retrieval-Augmented Generation.",
             "It combines a retrieval step with a generative model."]

# Simple embed via Claude (production: use a real embedding model)
collection.add(documents=documents, ids=["doc1", "doc2"])

# 2. Retrieve
query   = "What is RAG?"
results = collection.query(query_texts=[query], n_results=2)
context = " ".join(results["documents"][0])

# 3. Generate
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=512,
    messages=[{"role": "user", "content": f"Context: {context}\\n\\nQuestion: {query}"}],
)
print(response.content[0].text)
''',

    "streamlit_app": '''\
import os
import streamlit as st
from anthropic import Anthropic

st.set_page_config(page_title="AI Chat", layout="centered")
st.title("💬 Claude Chat")

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=st.session_state.messages,
            )
            reply = response.content[0].text
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
''',

    "tool_use": '''\
import os
import json
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
            },
            "required": ["city"],
        },
    }
]

def get_weather(city: str) -> str:
    # Mock — replace with a real API call
    return json.dumps({"city": city, "temp_c": 22, "condition": "Sunny"})

messages = [{"role": "user", "content": "What\'s the weather in London?"}]

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=tools,
    messages=messages,
)

# ReAct loop
while response.stop_reason == "tool_use":
    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            result = get_weather(**block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })
    messages.append({"role": "assistant", "content": response.content})
    messages.append({"role": "user", "content": tool_results})
    response = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=1024, tools=tools, messages=messages
    )

for block in response.content:
    if block.type == "text":
        print(block.text)
''',

    "embeddings": '''\
import os
import numpy as np
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def embed(text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding

def cosine_similarity(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

docs = [
    "RAG combines retrieval with generation.",
    "Fine-tuning updates model weights on new data.",
    "Prompt engineering crafts inputs to guide LLM outputs.",
]

query = "How do I improve LLM output quality?"
q_emb = embed(query)

scores = [(doc, cosine_similarity(q_emb, embed(doc))) for doc in docs]
scores.sort(key=lambda x: x[1], reverse=True)

print(f"Query: {query}\\n")
for doc, score in scores:
    print(f"  [{score:.3f}] {doc}")
''',
}


# ── Tool implementations ───────────────────────────────────────────────────────

def execute_python(code: str, stdin: str = "") -> str:
    """Run Python code in a subprocess with a 10-second timeout.

    Args:
        code:  Python source code to execute.
        stdin: Optional string to pipe to the process as standard input.
               Each line corresponds to one input() call in the program.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        tmp_path = f.name
    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=10,
            input=stdin or None,   # None = no stdin pipe (original behaviour)
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        if stdout and stderr:
            return f"{stdout}\n\n[stderr]:\n{stderr}"
        if stderr:
            return f"[stderr]:\n{stderr}"
        return stdout or "(no output)"
    except subprocess.TimeoutExpired:
        return "[Error]: Code timed out after 10 seconds."
    except Exception as e:
        return f"[Error]: {e}"
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def check_syntax(code: str) -> str:
    """Check Python syntax without executing."""
    try:
        compile(code, "<string>", "exec")
        return "✅ No syntax errors found."
    except SyntaxError as e:
        return f"❌ Syntax error on line {e.lineno}: {e.msg}"


def get_code_template(template_name: str) -> str:
    t = _TEMPLATES.get(template_name.lower().replace("-", "_"))
    if t:
        return t
    available = ", ".join(_TEMPLATES.keys())
    return f"Template '{template_name}' not found. Available: {available}"


def list_templates() -> str:
    descriptions = {
        "openai_chat":    "Basic OpenAI chat completion call",
        "rag_pipeline":   "Retrieval-Augmented Generation with Chroma",
        "streamlit_app":  "Streamlit chatbot interface with Claude",
        "tool_use":       "Claude tool use / function calling ReAct loop",
        "embeddings":     "OpenAI text embeddings + cosine similarity",
    }
    return "\n".join(f"- **{k}**: {v}" for k, v in descriptions.items())


# ── Learner state helpers ──────────────────────────────────────────────────────

def _load_profile() -> dict:
    if PROFILE_PATH.exists():
        try:
            return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_profile(p: dict) -> None:
    PROFILE_PATH.parent.mkdir(exist_ok=True)
    PROFILE_PATH.write_text(json.dumps(p, indent=2, default=str), encoding="utf-8")


# ── Dispatcher ────────────────────────────────────────────────────────────────

def tool_executor(tool_name: str, tool_args: dict) -> str:
    """
    Route a tool call from the ReAct loop to the correct implementation.

    Called by ClaudeClient.chat_with_tools() every time Claude requests a tool.
    Must return a string — the tool result Claude reads next.
    """
    if tool_name == "execute_python":
        return execute_python(tool_args.get("code", ""), stdin=tool_args.get("stdin", ""))

    if tool_name == "check_syntax":
        return check_syntax(tool_args.get("code", ""))

    if tool_name == "get_code_template":
        return get_code_template(tool_args.get("template_name", ""))

    if tool_name == "list_templates":
        return list_templates()

    # ── Learner state tools ────────────────────────────────────────────────────
    if tool_name == "get_learner_profile":
        p = _load_profile()
        return json.dumps({
            "user_name":   p.get("user_name", "Learner"),
            "skill_level": p.get("skill_level", "beginner"),
            "xp":          p.get("xp", 0),
            "streak":      p.get("streak", 1),
        }, indent=2)

    if tool_name == "update_skill_level":
        p = _load_profile()
        p["skill_level"] = tool_args.get("level", p.get("skill_level", "beginner"))
        _save_profile(p)
        return json.dumps({"status": "ok", "skill_level": p["skill_level"]})

    if tool_name == "log_topic_studied":
        p = _load_profile()
        topic = tool_args.get("topic", "")
        p.setdefault("topics", {})[topic] = {
            "status":       "in_progress",
            "last_studied": str(__import__("datetime").date.today()),
            "agent":        tool_args.get("agent", "coding"),
            "summary":      tool_args.get("summary", ""),
        }
        _save_profile(p)
        return json.dumps({"status": "ok", "topic": topic})

    if tool_name == "get_recent_topics":
        p = _load_profile()
        topics = sorted(
            p.get("topics", {}).items(),
            key=lambda x: x[1].get("last_studied", ""),
            reverse=True,
        )
        limit = tool_args.get("limit", 5)
        return "\n".join(f"- {name}" for name, _ in topics[:limit]) or "No topics studied yet."

    if tool_name == "set_learning_goal":
        p = _load_profile()
        p["current_goal"] = tool_args.get("goal", "")
        _save_profile(p)
        return json.dumps({"status": "ok"})

    if tool_name == "get_progress_summary":
        p = _load_profile()
        topics    = p.get("topics", {})
        completed = sum(1 for t in topics.values() if t.get("status") == "completed")
        return (
            f"{p.get('user_name', 'Learner')} · {p.get('skill_level', 'beginner')} · "
            f"{completed}/{len(topics)} topics complete · {p.get('xp', 0)} XP"
        )

    return json.dumps({"error": f"Unknown tool: {tool_name}"})
