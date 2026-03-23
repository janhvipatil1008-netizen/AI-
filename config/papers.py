"""
config/papers.py — Curated landmark research papers for AI² Research Papers feature.

20 hand-picked papers every AI PM / AI Builder should know.
Each paper has pre-written TL;DR and why_it_matters so no API call is needed
to display the landmark library.

Structure:
    LANDMARK_PAPERS  — list[dict] with keys:
        title, authors, year, url, category, level, tldr, why_it_matters

    CATEGORIES — ordered list of category names for the browse filter
"""

CATEGORIES = [
    "All",
    "Transformers & LLMs",
    "Prompt Engineering",
    "RAG & Retrieval",
    "AI Agents & Tools",
    "Evals & Safety",
    "Scaling & Systems",
]

LANDMARK_PAPERS: list[dict] = [
    # ── Transformers & LLMs ───────────────────────────────────────────────────
    {
        "title":          "Attention Is All You Need",
        "authors":        "Vaswani et al.",
        "year":           "2017",
        "url":            "https://arxiv.org/abs/1706.03762",
        "category":       "Transformers & LLMs",
        "level":          "advanced",
        "tldr":           "Replaces recurrence with self-attention; every modern LLM is built on this architecture.",
        "why_it_matters": "You cannot understand GPT, Claude, or BERT without knowing this paper.",
    },
    {
        "title":          "Language Models are Few-Shot Learners (GPT-3)",
        "authors":        "Brown et al.",
        "year":           "2020",
        "url":            "https://arxiv.org/abs/2005.14165",
        "category":       "Transformers & LLMs",
        "level":          "intermediate",
        "tldr":           "A 175B-parameter model learns new tasks from just a few examples in the prompt.",
        "why_it_matters": "First proof that scale unlocks emergent capabilities without task-specific training.",
    },
    {
        "title":          "Training Language Models to Follow Instructions with Human Feedback (InstructGPT)",
        "authors":        "Ouyang et al.",
        "year":           "2022",
        "url":            "https://arxiv.org/abs/2203.02155",
        "category":       "Transformers & LLMs",
        "level":          "intermediate",
        "tldr":           "Uses human feedback (RLHF) to make GPT-3 helpful, harmless, and honest.",
        "why_it_matters": "The alignment technique behind ChatGPT and Claude — essential reading for AI PMs.",
    },
    {
        "title":          "Constitutional AI: Harmlessness from AI Feedback",
        "authors":        "Bai et al. (Anthropic)",
        "year":           "2022",
        "url":            "https://arxiv.org/abs/2212.08073",
        "category":       "Transformers & LLMs",
        "level":          "intermediate",
        "tldr":           "Trains an AI to be safe using a written constitution instead of expensive human labels.",
        "why_it_matters": "Anthropic's method for building Claude; key read for AI safety and product teams.",
    },

    # ── Prompt Engineering ────────────────────────────────────────────────────
    {
        "title":          "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
        "authors":        "Wei et al.",
        "year":           "2022",
        "url":            "https://arxiv.org/abs/2201.11903",
        "category":       "Prompt Engineering",
        "level":          "beginner",
        "tldr":           "Adding 'think step by step' dramatically improves LLM accuracy on hard problems.",
        "why_it_matters": "The most important prompting technique; used in nearly every production AI system.",
    },
    {
        "title":          "Large Language Models Are Zero-Shot Reasoners",
        "authors":        "Kojima et al.",
        "year":           "2022",
        "url":            "https://arxiv.org/abs/2205.11916",
        "category":       "Prompt Engineering",
        "level":          "beginner",
        "tldr":           "'Let's think step by step' (no examples needed) works almost as well as few-shot CoT.",
        "why_it_matters": "The simplest way to unlock reasoning in any LLM with a single phrase.",
    },
    {
        "title":          "The Prompt Report: A Systematic Survey of Prompting Techniques",
        "authors":        "Schulhoff et al.",
        "year":           "2024",
        "url":            "https://arxiv.org/abs/2406.06608",
        "category":       "Prompt Engineering",
        "level":          "beginner",
        "tldr":           "Catalogues 58 prompting techniques with when and how to use each.",
        "why_it_matters": "The definitive reference guide for prompt engineering — bookmark this one.",
    },
    {
        "title":          "Lost in the Middle: How Language Models Use Long Contexts",
        "authors":        "Liu et al.",
        "year":           "2023",
        "url":            "https://arxiv.org/abs/2307.03172",
        "category":       "Prompt Engineering",
        "level":          "beginner",
        "tldr":           "LLMs perform worse when key information is buried in the middle of a long prompt.",
        "why_it_matters": "Critical for building RAG systems — put your most important context first or last.",
    },

    # ── RAG & Retrieval ───────────────────────────────────────────────────────
    {
        "title":          "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "authors":        "Lewis et al.",
        "year":           "2020",
        "url":            "https://arxiv.org/abs/2005.11401",
        "category":       "RAG & Retrieval",
        "level":          "intermediate",
        "tldr":           "Combines a document retriever with a generative model to produce grounded, factual answers.",
        "why_it_matters": "The original RAG paper; foundation of every knowledge-grounded AI product.",
    },
    {
        "title":          "Dense Passage Retrieval for Open-Domain Question Answering",
        "authors":        "Karpukhin et al.",
        "year":           "2020",
        "url":            "https://arxiv.org/abs/2004.04906",
        "category":       "RAG & Retrieval",
        "level":          "intermediate",
        "tldr":           "Dense vector search beats keyword search for finding relevant documents.",
        "why_it_matters": "Explains why every RAG system uses embeddings + vector databases instead of plain text search.",
    },
    {
        "title":          "In-Context Retrieval-Augmented Language Models",
        "authors":        "Ram et al.",
        "year":           "2023",
        "url":            "https://arxiv.org/abs/2302.00083",
        "category":       "RAG & Retrieval",
        "level":          "intermediate",
        "tldr":           "Inserting retrieved documents directly into the prompt works without any fine-tuning.",
        "why_it_matters": "Explains why simple RAG patterns work well with off-the-shelf LLM APIs like Claude.",
    },

    # ── AI Agents & Tools ─────────────────────────────────────────────────────
    {
        "title":          "ReAct: Synergizing Reasoning and Acting in Language Models",
        "authors":        "Yao et al.",
        "year":           "2022",
        "url":            "https://arxiv.org/abs/2210.03629",
        "category":       "AI Agents & Tools",
        "level":          "intermediate",
        "tldr":           "LLMs alternate between reasoning traces and tool actions in a loop until the task is done.",
        "why_it_matters": "The architectural pattern behind every AI agent, including the one running this app.",
    },
    {
        "title":          "Toolformer: Language Models Can Teach Themselves to Use Tools",
        "authors":        "Schick et al.",
        "year":           "2023",
        "url":            "https://arxiv.org/abs/2302.04761",
        "category":       "AI Agents & Tools",
        "level":          "intermediate",
        "tldr":           "An LLM learns when and how to call APIs by generating and filtering its own training examples.",
        "why_it_matters": "Shows that tool use can be learned, not just hardcoded — key for scalable agent design.",
    },
    {
        "title":          "Gorilla: Large Language Model Connected with Massive APIs",
        "authors":        "Patil et al.",
        "year":           "2023",
        "url":            "https://arxiv.org/abs/2305.15334",
        "category":       "AI Agents & Tools",
        "level":          "intermediate",
        "tldr":           "Fine-tuned LLM that accurately calls real ML APIs (PyTorch, HuggingFace, TensorFlow).",
        "why_it_matters": "Practical reference for building systems where LLMs call real-world production APIs.",
    },
    {
        "title":          "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation",
        "authors":        "Wu et al.",
        "year":           "2023",
        "url":            "https://arxiv.org/abs/2308.08155",
        "category":       "AI Agents & Tools",
        "level":          "intermediate",
        "tldr":           "Networks of specialised AI agents converse with each other to solve complex tasks.",
        "why_it_matters": "The multi-agent orchestration pattern this app is built on — multiple agents + a router.",
    },
    {
        "title":          "Generative Agents: Interactive Simulacra of Human Behavior",
        "authors":        "Park et al.",
        "year":           "2023",
        "url":            "https://arxiv.org/abs/2304.03442",
        "category":       "AI Agents & Tools",
        "level":          "beginner",
        "tldr":           "AI agents with memory, planning, and reflection behave like believable people in a simulation.",
        "why_it_matters": "Demonstrates the memory + reflection patterns every serious agent system needs.",
    },

    # ── Evals & Safety ────────────────────────────────────────────────────────
    {
        "title":          "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena",
        "authors":        "Zheng et al.",
        "year":           "2023",
        "url":            "https://arxiv.org/abs/2306.05685",
        "category":       "Evals & Safety",
        "level":          "intermediate",
        "tldr":           "Using a strong LLM (GPT-4) as an automated evaluator correlates well with human judgment.",
        "why_it_matters": "The foundation of the LLM-as-Judge eval pattern used in every serious AI product team.",
    },
    {
        "title":          "HELM: Holistic Evaluation of Language Models",
        "authors":        "Liang et al.",
        "year":           "2022",
        "url":            "https://arxiv.org/abs/2211.09110",
        "category":       "Evals & Safety",
        "level":          "intermediate",
        "tldr":           "Evaluates LLMs across 42 scenarios and 7 dimensions including accuracy, fairness, and robustness.",
        "why_it_matters": "Reference framework for building comprehensive eval harnesses for AI products.",
    },

    # ── Scaling & Systems ─────────────────────────────────────────────────────
    {
        "title":          "Scaling Laws for Neural Language Models",
        "authors":        "Kaplan et al.",
        "year":           "2020",
        "url":            "https://arxiv.org/abs/2001.08361",
        "category":       "Scaling & Systems",
        "level":          "advanced",
        "tldr":           "Model performance scales predictably with compute, parameters, and data size.",
        "why_it_matters": "The empirical foundation for why bigger models work better, and precisely by how much.",
    },
    {
        "title":          "Training Compute-Optimal Large Language Models (Chinchilla)",
        "authors":        "Hoffmann et al.",
        "year":           "2022",
        "url":            "https://arxiv.org/abs/2203.15556",
        "category":       "Scaling & Systems",
        "level":          "advanced",
        "tldr":           "For a fixed compute budget, train a smaller model on more data than GPT-3 era wisdom suggested.",
        "why_it_matters": "Overturned GPT-3-era scaling assumptions; influences every modern LLM training decision.",
    },
]
