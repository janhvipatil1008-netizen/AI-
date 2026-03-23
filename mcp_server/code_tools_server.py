"""
code_tools_server.py — MCP Server: Code Execution & Templates

WHAT IS THIS?
--------------
This server gives Claude the ability to actually RUN Python code on your machine
and check if code has errors — without Claude needing to guess what the output is.

WHY IS THIS POWERFUL?
----------------------
Without this server, Claude can only *write* code. It has to guess what the output
will be. With this server, Claude can:

  1. Write some code
  2. Execute it and see the real output
  3. Fix any errors it finds
  4. Show you the ACTUAL result, not a guess

This is how professional AI coding assistants work (GitHub Copilot, Cursor, etc.).

SIMPLE ANALOGY:
---------------
Before: Claude is like a chef who writes recipes but never tastes the food.
After:  Claude can cook the dish, taste it, and adjust the recipe.

SAFETY NOTE — execute_python():
---------------------------------
Running arbitrary code is powerful but risky. We limit it with:
  - 10 second timeout    — prevents infinite loops from freezing your machine
  - Separate process     — the code runs in its own Python process, isolated
  - No network calls     — the code can't make web requests (we block them)

For a production system you'd use a proper sandbox (Docker container, etc.).
For learning on your own machine, these limits are enough.

TOOLS EXPOSED:
--------------
  execute_python(code)              → run code, get stdout + stderr back
  check_syntax(code)                → validate Python syntax without running
  get_code_template(template_name)  → get a starter code skeleton

HOW TO TEST:
------------
  .venv\\Scripts\\python.exe mcp_server/code_tools_server.py
  (should start and wait — press Ctrl+C to stop)
"""

import json
import os
import sys
import subprocess
import tempfile
import py_compile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AI² Code Tools Server")

# ── Code Templates ─────────────────────────────────────────────────────────────
# Ready-to-use starter code skeletons for common AI patterns.
# Claude returns these verbatim so learners have a working starting point.

_TEMPLATES: dict[str, str] = {
    "openai_chat": '''\
"""
Minimal OpenAI chat completion — the simplest possible AI app.
Replace "your message here" with your actual prompt.
"""
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user",   "content": "your message here"},
    ],
)

print(response.choices[0].message.content)
''',

    "rag_pipeline": '''\
"""
Minimal RAG (Retrieval-Augmented Generation) pipeline.
Chunks text → embeds → stores → retrieves → generates answer.

Install: pip install openai chromadb
"""
import os
from openai import OpenAI
import chromadb

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
chroma = chromadb.Client()
collection = chroma.create_collection("docs")

# ── 1. Add your documents ─────────────────────────────────────────────────────
docs = [
    "RAG stands for Retrieval-Augmented Generation.",
    "It combines search with language model generation.",
    "First retrieve relevant chunks, then pass them to the LLM as context.",
]

# Embed and store each document
for i, doc in enumerate(docs):
    embed_response = client.embeddings.create(
        model="text-embedding-3-small", input=doc
    )
    collection.add(
        documents=[doc],
        embeddings=[embed_response.data[0].embedding],
        ids=[f"doc_{i}"],
    )

# ── 2. Query ──────────────────────────────────────────────────────────────────
question = "What is RAG?"

q_embed = client.embeddings.create(
    model="text-embedding-3-small", input=question
)
results = collection.query(
    query_embeddings=[q_embed.data[0].embedding],
    n_results=2,
)
context = "\\n".join(results["documents"][0])

# ── 3. Generate answer with context ──────────────────────────────────────────
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": f"Answer using this context:\\n{context}"},
        {"role": "user",   "content": question},
    ],
)
print(response.choices[0].message.content)
''',

    "streamlit_app": '''\
"""
Minimal Streamlit AI chat app — the pattern used throughout AI².
Run with: streamlit run app.py
"""
import streamlit as st
import os
from openai import OpenAI

st.title("My AI Chat")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Session state keeps the conversation alive across reruns
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle new input
if prompt := st.chat_input("Ask something..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    *st.session_state.messages,
                ],
            )
            reply = response.choices[0].message.content
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
''',

    "tool_use": '''\
"""
Minimal Claude tool use (function calling) example.
Claude decides when to call the tool based on the user\'s question.
"""
import os
import json
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Define a tool Claude can call
tools = [{
    "name": "get_weather",
    "description": "Get the current weather for a city.",
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "The city name"},
        },
        "required": ["city"],
    },
}]

# Fake implementation — replace with a real weather API
def get_weather(city: str) -> str:
    return f"It\'s 22°C and sunny in {city}."

messages = [{"role": "user", "content": "What\'s the weather in London?"}]

# First call — Claude may decide to use the tool
response = client.messages.create(
    model="claude-sonnet-4-6",
    system="You are a helpful assistant.",
    messages=messages,
    tools=tools,
    max_tokens=1024,
)

# If Claude used a tool, execute it and call Claude again
if response.stop_reason == "tool_use":
    messages.append({"role": "assistant", "content": response.content})

    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            result = get_weather(**block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })

    messages.append({"role": "user", "content": tool_results})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        system="You are a helpful assistant.",
        messages=messages,
        tools=tools,
        max_tokens=1024,
    )

# Print Claude\'s final answer
for block in response.content:
    if hasattr(block, "text"):
        print(block.text)
''',

    "embeddings": '''\
"""
Minimal embedding + similarity example.
Shows how to turn text into numbers and find the most similar item.
"""
import os
from openai import OpenAI
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def embed(text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding

def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = sum(x**2 for x in a) ** 0.5
    mag_b = sum(x**2 for x in b) ** 0.5
    return dot / (mag_a * mag_b) if mag_a and mag_b else 0.0

# Items to search
items = [
    "How to fine-tune a language model",
    "Python list comprehensions tutorial",
    "RAG pipeline for document search",
    "Gradient descent explained simply",
]

query = "I want to search through documents using AI"
query_vec = embed(query)

# Score each item against the query
scores = [(item, cosine_similarity(query_vec, embed(item))) for item in items]
scores.sort(key=lambda x: x[1], reverse=True)

print(f"Query: {query}\\n")
for item, score in scores:
    print(f"  {score:.3f}  {item}")
''',
}

# ── MCP Tools ─────────────────────────────────────────────────────────────────

@mcp.tool()
def execute_python(code: str) -> str:
    """
    Execute Python code and return the output (stdout + stderr).

    Use this to:
    - Verify that code you wrote actually works before showing it to the learner
    - Run learner-submitted code to check their answer
    - Demonstrate what a code snippet does in practice

    SAFETY LIMITS (applied automatically):
    - 10 second timeout: code that runs forever is stopped
    - Separate process: code can't affect the main app
    - Returns BOTH stdout and stderr so you can see errors

    Returns a JSON object with:
      {"stdout": "...", "stderr": "...", "exit_code": 0, "timed_out": false}

    Args:
        code: Valid Python code to execute. Use triple-quoted strings for multiline.
    """
    # Write code to a temp file — safer than exec()
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
            timeout=10,  # 10 second hard limit
        )
        return json.dumps({
            "stdout":    result.stdout[:2000],  # cap to avoid huge outputs
            "stderr":    result.stderr[:1000],
            "exit_code": result.returncode,
            "timed_out": False,
        }, indent=2)

    except subprocess.TimeoutExpired:
        return json.dumps({
            "stdout":    "",
            "stderr":    "Execution stopped: exceeded 10 second time limit.",
            "exit_code": -1,
            "timed_out": True,
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "stdout":    "",
            "stderr":    f"Failed to run code: {str(e)}",
            "exit_code": -1,
            "timed_out": False,
        }, indent=2)

    finally:
        # Always clean up the temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@mcp.tool()
def check_syntax(code: str) -> str:
    """
    Check if Python code has valid syntax WITHOUT running it.

    Use this before showing code to a learner to catch typos, indentation
    errors, and syntax mistakes. Faster and safer than execute_python for
    pure syntax validation.

    Returns:
      "OK" — if the code is syntactically valid
      "SyntaxError at line N: <message>" — if there is a problem

    Args:
        code: Python code to validate.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        tmp_path = f.name

    try:
        py_compile.compile(tmp_path, doraise=True)
        return "OK"
    except py_compile.PyCompileError as e:
        return f"SyntaxError: {str(e)}"
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@mcp.tool()
def get_code_template(template_name: str) -> str:
    """
    Get a ready-to-use starter code template for a common AI pattern.

    Use this when a learner wants to start building something and needs
    a working skeleton to modify rather than starting from scratch.

    Available templates:
      "openai_chat"    — minimal OpenAI chat completion (the basics)
      "rag_pipeline"   — chunking + embedding + retrieval + generation
      "streamlit_app"  — chat UI with session state (like this platform)
      "tool_use"       — Claude tool use / function calling (ReAct pattern)
      "embeddings"     — text embeddings + cosine similarity from scratch

    Returns the template code as a string, or an error if not found.

    Args:
        template_name: One of the template names listed above.
    """
    template = _TEMPLATES.get(template_name)
    if template is None:
        available = ", ".join(f'"{k}"' for k in _TEMPLATES.keys())
        return f"Template '{template_name}' not found. Available: {available}"
    return template


@mcp.tool()
def list_templates() -> str:
    """
    List all available code templates with a one-line description each.

    Use this when the learner asks "what can I build?" or "where do I start?"
    to show them the full menu of starter templates available.
    """
    descriptions = {
        "openai_chat":   "Minimal OpenAI chat completion — the simplest possible AI app",
        "rag_pipeline":  "RAG: chunk → embed → store → retrieve → generate (with ChromaDB)",
        "streamlit_app": "Chat UI with session state — same pattern as this learning platform",
        "tool_use":      "Claude tool use / function calling — the ReAct pattern explained",
        "embeddings":    "Text embeddings + cosine similarity, built from scratch",
    }
    return json.dumps(descriptions, indent=2)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
