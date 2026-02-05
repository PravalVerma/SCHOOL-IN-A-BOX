"""""

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

from models.llm_client import LLMClient
from config import LLM_MODEL_COACH




_llm = LLMClient(model_name=LLM_MODEL_COACH)


def _build_coach_prompt(progress_summary: dict) -> str:
    return f"""
ROLE:
You are a Learning Coach Agent.

OBJECTIVE:
Help the student improve by analyzing performance data and recommending next steps.

INPUT DATA (authoritative):
{progress_summary}

ANALYSIS RULES:
- Base all guidance strictly on the provided data.
- Identify strengths, weaknesses, and trends.
- Do NOT assume motivation, effort, or external factors.

COACHING OUTPUT SHOULD INCLUDE:
1. What the student is doing well
2. Topics or skills that need improvement
3. Recommended next action (practice, revision, difficulty change)
4. A short, supportive message (1–2 lines, professional tone)

CONSTRAINTS:
- No generic advice.
- No motivational clichés.
- No new topics unless justified by data.

OUTPUT:
A concise coaching summary for the student.
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

    try:
        # Try LLM first
        return _llm.chat(messages)

    except Exception as e:
        # Fallback logic if rate limit or API failure occurs
        total_q = progress_summary.get("total_questions", 0)
        correct = progress_summary.get("correct_answers", 0)

        accuracy = 0
        if total_q > 0:
            accuracy = int((correct / total_q) * 100)

        topic_stats = progress_summary.get("topic_stats", {})

        weak_topics = []
        for topic, stats in topic_stats.items():
            total = stats.get("total", 0)
            correct_t = stats.get("correct", 0)

            if total > 0:
                mastery = correct_t / total
                if mastery < 0.6:
                    weak_topics.append(topic)

        advice = (
            "AI coaching is temporarily unavailable (rate limit reached).\n\n"
            f"Your current accuracy is {accuracy}%.\n"
        )

        if weak_topics:
            advice += (
                "You should focus on revising these topics:\n"
                + ", ".join(weak_topics)
                + ".\n"
            )
        else:
            advice += "Continue practicing regularly to improve retention.\n"

        advice += "\nTip: Practice weak topics first, then review strong ones after a few days."

        return advice
