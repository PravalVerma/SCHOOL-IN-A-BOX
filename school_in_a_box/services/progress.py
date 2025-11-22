# services/progress.py
"""
Progress & stats service.

Responsibilities:
- Read quizzes + responses from MongoDB.
- Compute per-topic and overall accuracy for a user.
- Shape a progress summary dict that the Learning Coach Agent understands.
- (Optionally) provide a helper to directly get a coaching message for a user.
"""

from __future__ import annotations

from typing import Dict, Any, List
from datetime import datetime

from bson import ObjectId

from school_in_a_box.db.models import quizzes_col, responses_col
from school_in_a_box.agents.learning_coach import get_coaching_advice



def compute_progress(user_id: str) -> Dict[str, Any]:
    """
    Compute progress metrics for a given user from quiz responses.

    Returns a dict like:

    {
        "user_id": "u123",
        "overall_accuracy": 0.72,
        "total_questions_answered": 50,
        "topics": [
            {
                "name": "Algebra",
                "accuracy": 0.55,
                "num_questions": 20,
                "last_answered_at": "...iso...",
            },
            ...
        ],
        "recent_sessions": [
            {
                "quiz_id": "....",
                "topic": "Algebra",
                "score": 0.6,
                "num_questions": 10,
                "completed_at": "...iso..."
            },
            ...
        ],
    }
    """

    # 1. Fetch all responses for this user
    resp_cursor = responses_col().find({"user_id": user_id})
    responses: List[Dict[str, Any]] = list(resp_cursor)

    if not responses:
        # No data yet – return an "empty" summary
        return {
            "user_id": user_id,
            "overall_accuracy": 0.0,
            "total_questions_answered": 0,
            "topics": [],
            "recent_sessions": [],
        }

    # 2. Collect quiz_ids and fetch quiz docs (for topics)
    quiz_ids = {r["quiz_id"] for r in responses if isinstance(r.get("quiz_id"), ObjectId)}
    quiz_docs = list(quizzes_col().find({"_id": {"$in": list(quiz_ids)}}))

    quiz_by_id: Dict[ObjectId, Dict[str, Any]] = {q["_id"]: q for q in quiz_docs}

    # 3. Aggregate per-topic and per-quiz stats
    topic_stats: Dict[str, Dict[str, Any]] = {}
    quiz_stats: Dict[ObjectId, Dict[str, Any]] = {}

    total_correct = 0
    total_answers = 0

    for r in responses:
        quiz_id = r.get("quiz_id")
        if not isinstance(quiz_id, ObjectId) or quiz_id not in quiz_by_id:
            continue

        quiz = quiz_by_id[quiz_id]
        topic = quiz.get("topic", "Unknown")

        is_correct = bool(r.get("is_correct", False))
        answered_at = r.get("answered_at", datetime.utcnow())

        # overall
        total_answers += 1
        if is_correct:
            total_correct += 1

        # per-topic
        if topic not in topic_stats:
            topic_stats[topic] = {
                "name": topic,
                "correct": 0,
                "total": 0,
                "last_answered_at": answered_at,
            }
        topic_stats[topic]["total"] += 1
        if is_correct:
            topic_stats[topic]["correct"] += 1

        # track latest answer timestamp
        if answered_at > topic_stats[topic]["last_answered_at"]:
            topic_stats[topic]["last_answered_at"] = answered_at

        # per-quiz
        if quiz_id not in quiz_stats:
            quiz_stats[quiz_id] = {
                "quiz_id": str(quiz_id),
                "topic": topic,
                "correct": 0,
                "total": 0,
                "completed_at": answered_at,
            }
        quiz_stats[quiz_id]["total"] += 1
        if is_correct:
            quiz_stats[quiz_id]["correct"] += 1

        # last answered per quiz (use latest timestamp)
        if answered_at > quiz_stats[quiz_id]["completed_at"]:
            quiz_stats[quiz_id]["completed_at"] = answered_at

    # 4. Build topics list with accuracy
    topics_list: List[Dict[str, Any]] = []
    for t in topic_stats.values():
        total = max(t["total"], 1)
        acc = t["correct"] / total
        topics_list.append(
            {
                "name": t["name"],
                "accuracy": acc,
                "num_questions": t["total"],
                "last_answered_at": t["last_answered_at"].isoformat(),
            }
        )

    # 5. Build recent_sessions list from quiz_stats
    recent_sessions: List[Dict[str, Any]] = []
    for qs in quiz_stats.values():
        total = max(qs["total"], 1)
        score = qs["correct"] / total
        recent_sessions.append(
            {
                "quiz_id": qs["quiz_id"],
                "topic": qs["topic"],
                "score": score,
                "num_questions": qs["total"],
                "completed_at": qs["completed_at"].isoformat(),
            }
        )

    # Sort sessions by completed_at (newest first)
    recent_sessions.sort(key=lambda s: s["completed_at"], reverse=True)

    # 6. Overall accuracy
    overall_accuracy = total_correct / max(total_answers, 1)

    return {
        "user_id": user_id,
        "overall_accuracy": overall_accuracy,
        "total_questions_answered": total_answers,
        "topics": topics_list,
        "recent_sessions": recent_sessions,
    }


def get_coaching_for_user(user_id: str) -> str:
    """
    Convenience helper:

    - Compute progress for the user
    - Call the Learning Coach agent
    - Return the coaching text
    """
    progress_summary = compute_progress(user_id)
    return get_coaching_advice(progress_summary)
