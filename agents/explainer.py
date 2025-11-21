# agents/explainer.py
"""
Content Explainer Agent.

Responsibilities:
- Explain raw text in a student-friendly way.
- (Optionally) use retrieved context from the vector store (RAG-style)
  based on a user question.

Image support (via vision model) will be added later.
"""

from typing import List

from ..models.llm_client import LLMClient
from ..config import LLM_MODEL_EXPLAINER
from ..services.vector_store import store as vector_store


# Single explainer LLM instance for this agent
_llm = LLMClient(model_name=LLM_MODEL_EXPLAINER)


def _build_explainer_prompt(content: str, level: str) -> str:
    """
    Build the prompt for explaining content.
    """
    return f"""
You are a friendly teaching assistant.

Explain the following content to a student.

- Use clear, simple language.
- Focus on understanding, not just definitions.
- Use short paragraphs and bullet points where helpful.
- Adjust the depth to this level: {level}

Content to explain:
\"\"\"{content}\"\"\"
""".strip()


def explain_raw_text(text: str, level: str = "simple") -> str:
    """
    Explain text directly (no retrieval).

    Used when the user pastes content or after ingestion of a specific chunk.
    """
    prompt = _build_explainer_prompt(text, level)
    messages = [
        {"role": "system", "content": "You explain concepts clearly for students."},
        {"role": "user", "content": prompt},
    ]
    return _llm.chat(messages)


def explain_with_retrieval(question: str, level: str = "simple", k: int = 5) -> str:
    """
    Explain a concept based on a student's question using stored material.

    Steps:
    - Retrieve top-k similar chunks from the vector store.
    - Ask the LLM to answer/explain using ONLY that context.
    """
    hits = vector_store.similarity_search(question, k=k)

    if not hits:
        # Fallback: just answer from prior + question (no context available)
        prompt = f"""
A student asked the following question:

\"\"\"{question}\"\"\"

There is no stored material available. 
Give the best explanation you can at this level: {level}.
"""
        messages = [
            {"role": "system", "content": "You explain concepts clearly for students."},
            {"role": "user", "content": prompt},
        ]
        return _llm.chat(messages)

    # Build context string
    context_parts: List[str] = []
    for i, (text, score) in enumerate(hits, start=1):
        context_parts.append(f"[Chunk {i}, score={score:.4f}]\n{text}")
    context_str = "\n\n".join(context_parts)

    prompt = f"""
You are a teaching assistant helping a student.

The student question:
\"\"\"{question}\"\"\"

You are given some context from their study material:

{context_str}

Instructions:
- Use the context above as your main source.
- If something is not in the context, say you are not sure instead of making it up.
- Explain at this level: {level}
- Use clear, structured explanation.

Now explain/answer the student's question.
""".strip()

    messages = [
        {"role": "system", "content": "You explain concepts clearly for students using given context."},
        {"role": "user", "content": prompt},
    ]
    return _llm.chat(messages)
