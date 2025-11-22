# agents/learning_coach.py
"""
Learning Coach Agent.

Responsibilities:
- Take a summary of learner performance (from Mongo / progress service).
- Generate:
  - What the learner is doing well
  - What needs improvement
  - Suggested next topics / difficulty
  - A short revision plan (spaced over days)

This agent itself does NOT talk to Mongo or FAISS directly.
It only consumes a structured summary that other services compute.
"""

from __future__ import annotations

from typing import Dict, Any

from school_in_a_box.models.llm_client import LLMClient
from school_in_a_box.config import LLM_MODEL_COACH



_llm = LLMClient(model_name=LLM_MODEL_COACH)


def _build_coach_prompt(progress: Dict[str, Any]) -> str:
    """
    Build a prompt from a structured progress summary.

    Expected structure (example):
    {
        "user_id": "123",
        "overall_accuracy": 0.72,
        "topics": [
            {"name": "Algebra", "accuracy": 0.55, "recent_activity_days": 1},
            {"name": "Kinematics", "accuracy": 0.82, "recent_activity_days": 5},
        ],
        "recent_sessions": [
            {"topic": "Algebra", "score": 0.6, "num_questions": 10},
            ...
        ]
    }

    The progress service will be responsible for creating such a dict.
    """
    # We intentionally keep this as plain text JSON-style.
    # The service that calls this agent will pass a Python dict.
    return f"""
You are a supportive learning coach helping a student improve.

You will be given a JSON-like progress summary for the student.
Use it to:

1. Briefly summarize how the student is doing overall.
2. List strengths (topics doing well in).
3. List weaknesses (topics that need work).
4. Recommend:
   - Which topics to focus on next.
   - What difficulty level to use next (easy / medium / hard).
5. Propose a short revision schedule for the next 7 days.
   - Mention topics per day in simple language.

Important:
- Be encouraging and specific.
- Do NOT invent topics that are not in the summary.

Student progress summary:
{progress}
""".strip()


def get_coaching_advice(progress_summary: Dict[str, Any]) -> str:
    """
    Main entry point for the Learning Coach.

    Input:
        progress_summary: dict built by services.progress.compute_progress()

    Output:
        A natural language coaching message for the student.
    """
    prompt = _build_coach_prompt(progress_summary)
    messages = [
        {"role": "system", "content": "You are a kind and practical learning coach."},
        {"role": "user", "content": prompt},
    ]
    return _llm.chat(messages)
