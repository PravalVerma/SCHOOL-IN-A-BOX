

from __future__ import annotations

from typing import List, Dict, Any
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END

from agents.quiz_generator import MCQ, generate_mcqs_with_retrieval
from services.quizzes import save_quiz
from services.progress import compute_progress
from agents.learning_coach import get_coaching_advice
from services.vector_store import store as vector_store
from agents.explainer import explain_from_context


# ---------- QUIZ GRAPH ----------

class QuizState(TypedDict, total=False):
    # input fields
    user_id: str
    topic_or_question: str
    source_id: str
    num_questions: int
    difficulty: str
    k: int

    # output fields
    mcqs: List[MCQ]
    quiz_id: str | None


def generate_mcqs_node(state: QuizState) -> QuizState:
    mcqs = generate_mcqs_with_retrieval(
        topic_or_question=state["topic_or_question"],
        num_questions=state.get("num_questions", 5),
        difficulty=state.get("difficulty", "medium"),
        k=state.get("k", 5),
    )
    return {"mcqs": mcqs}


def save_quiz_node(state: QuizState) -> QuizState:
    mcqs = state.get("mcqs") or []
    if not mcqs:
        return {"quiz_id": None}

    quiz_id = save_quiz(
        user_id=state["user_id"],
        topic=state["topic_or_question"],
        source_id=state["source_id"],
        mcqs=mcqs,
    )
    return {"quiz_id": quiz_id}


quiz_builder = StateGraph(QuizState)
quiz_builder.add_node("generate_mcqs", generate_mcqs_node)
quiz_builder.add_node("save_quiz", save_quiz_node)

quiz_builder.add_edge(START, "generate_mcqs")
quiz_builder.add_edge("generate_mcqs", "save_quiz")
quiz_builder.add_edge("save_quiz", END)

quiz_graph = quiz_builder.compile()


# ---------- COACH GRAPH ----------

class CoachState(TypedDict, total=False):
    user_id: str
    progress: Dict[str, Any]
    advice: str


def compute_progress_node(state: CoachState) -> CoachState:
    progress = compute_progress(state["user_id"])
    return {"progress": progress}


def coaching_node(state: CoachState) -> CoachState:
    progress = state.get("progress", {})
    advice = get_coaching_advice(progress)
    return {"advice": advice}


coach_builder = StateGraph(CoachState)
coach_builder.add_node("compute_progress", compute_progress_node)
coach_builder.add_node("coaching", coaching_node)

coach_builder.add_edge(START, "compute_progress")
coach_builder.add_edge("compute_progress", "coaching")
coach_builder.add_edge("coaching", END)

coach_graph = coach_builder.compile()


# ---------- EXPLAIN GRAPH (RAG) ----------

class ExplainState(TypedDict, total=False):
    # input
    question: str
    level: str
    k: int

    # intermediate / output
    context_chunks: List[str]
    explanation: str


def retrieve_context_node(state: ExplainState) -> ExplainState:
    hits = vector_store.similarity_search(state["question"], k=state.get("k", 5))
    context_chunks = [text for (text, _score) in hits]
    return {"context_chunks": context_chunks}


def generate_explanation_node(state: ExplainState) -> ExplainState:
    question = state["question"]
    level = state.get("level", "simple")
    context_chunks = state.get("context_chunks", [])
    explanation = explain_from_context(question, level, context_chunks)
    return {"explanation": explanation}


explain_builder = StateGraph(ExplainState)
explain_builder.add_node("retrieve_context", retrieve_context_node)
explain_builder.add_node("generate_explanation", generate_explanation_node)

explain_builder.add_edge(START, "retrieve_context")
explain_builder.add_edge("retrieve_context", "generate_explanation")
explain_builder.add_edge("generate_explanation", END)

explain_graph = explain_builder.compile()
