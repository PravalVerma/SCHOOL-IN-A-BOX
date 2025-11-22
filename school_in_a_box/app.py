import tempfile
from pathlib import Path

import streamlit as st

from db.models import init_indexes
from services.ingestion import ingest_text, ingest_pdf
from agents.explainer import explain_raw_text, explain_with_retrieval
from agents.quiz_generator import generate_mcqs_with_retrieval, MCQ
from services.quizzes import save_quiz, save_response, get_quiz_by_id
from services.progress import compute_progress, get_coaching_for_user


# ---------- One-time init ----------

# Create indexes (safe to call multiple times)
try:
    init_indexes()
except Exception as e:
    # Don't crash UI if Mongo isn't up yet; just show a warning
    st.sidebar.warning(f"MongoDB index init failed: {e}")


# ---------- Session helpers ----------

def get_user_id() -> str:
    """Return the current user_id from session_state."""
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = "demo-user"
    return st.session_state["user_id"]


def set_current_quiz(quiz_id: str, mcqs: list[MCQ]) -> None:
    """Store current quiz info in session_state for answering."""
    st.session_state["current_quiz_id"] = quiz_id
    # Store a serializable version of MCQs
    st.session_state["current_quiz_mcqs"] = [
        {
            "question": m.question,
            "options": m.options,
            "correct_index": m.correct_index,
            "explanation": m.explanation,
            "difficulty": m.difficulty,
        }
        for m in mcqs
    ]
    st.session_state["quiz_submitted"] = False


def get_current_quiz():
    """Return (quiz_id, mcq_dict_list) or (None, None) if no quiz."""
    quiz_id = st.session_state.get("current_quiz_id")
    mcqs = st.session_state.get("current_quiz_mcqs")
    if not quiz_id or not mcqs:
        return None, None
    return quiz_id, mcqs


# ---------- Streamlit UI ----------

st.set_page_config(page_title="School in a Box", layout="wide")
st.title("📦 School in a Box")

# Sidebar: user id
user_id = get_user_id()
st.sidebar.text_input("User ID", value=user_id, key="user_id")

tab_learn, tab_quiz, tab_coach = st.tabs(["📘 Learn", "📝 Quiz", "🎯 Coach"])


# ---------- LEARN TAB ----------

with tab_learn:
    st.header("Learn")

    st.subheader("Ingest Content")

    col1, col2 = st.columns(2)

    # --- Text ingestion ---
    with col1:
        st.markdown("**Paste Text**")
        text_source_id = st.text_input(
            "Text Source ID (e.g., 'physics_ch1_notes')",
            value="text_source_1",
            key="text_source_id",
        )
        raw_text = st.text_area(
            "Content to ingest",
            height=200,
            key="learn_raw_text",
        )
        if st.button("Ingest Text", key="btn_ingest_text") and raw_text.strip():
            chunks = ingest_text(raw_text, source_id=text_source_id)
            st.success(f"Ingested {len(chunks)} chunks from text.")

    # --- PDF ingestion ---
    with col2:
        st.markdown("**Upload PDF**")
        pdf_file = st.file_uploader(
            "Upload a PDF",
            type=["pdf"],
            key="learn_pdf_file",
        )
        pdf_source_id = st.text_input(
            "PDF Source ID (e.g., 'physics_ch1_pdf')",
            value="pdf_source_1",
            key="pdf_source_id",
        )

        if st.button("Ingest PDF", key="btn_ingest_pdf") and pdf_file is not None:
            # Save uploaded file to a temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(pdf_file.read())
                tmp_path = tmp.name

            chunks = ingest_pdf(tmp_path, source_id=pdf_source_id)
            st.success(f"Ingested {len(chunks)} chunks from PDF: {pdf_file.name}")

    st.markdown("---")
    st.subheader("Explain Content")

    explain_mode = st.radio(
        "Explanation mode",
        ["Explain pasted text", "Explain using stored material (RAG)"],
        key="explain_mode",
    )

    explain_level = st.selectbox(
        "Explanation level",
        ["simple", "intermediate", "advanced"],
        index=0,
        key="explain_level",
    )

    if explain_mode == "Explain pasted text":
        explain_text = st.text_area(
            "Text to explain",
            height=180,
            key="explain_raw_text_area",
        )
        if st.button("Explain Text", key="btn_explain_text") and explain_text.strip():
            with st.spinner("Generating explanation..."):
                explanation = explain_raw_text(explain_text, level=explain_level)
            st.markdown("### Explanation")
            st.write(explanation)

    else:
        question = st.text_input(
            "Ask a question based on your ingested material",
            key="explain_question",
        )
        if st.button("Explain from Stored Material", key="btn_explain_rag") and question.strip():
            with st.spinner("Retrieving and explaining..."):
                explanation = explain_with_retrieval(question, level=explain_level, k=5)
            st.markdown("### Explanation from Stored Material")
            st.write(explanation)


# ---------- QUIZ TAB ----------

with tab_quiz:
    st.header("Quiz")

    st.subheader("Generate a Quiz")

    topic_or_question = st.text_input(
        "Topic or question to generate quiz from (will use stored material if available)",
        key="quiz_topic",
    )
    num_questions = st.number_input(
        "Number of questions",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
        key="quiz_num_questions",
    )
    difficulty = st.selectbox(
        "Difficulty",
        ["easy", "medium", "hard"],
        index=1,
        key="quiz_difficulty",
    )
    source_id_for_quiz = st.text_input(
        "Source ID for this quiz (e.g., 'physics_ch1_pdf')",
        value="generic_source",
        key="quiz_source_id",
    )

    if st.button("Generate Quiz", key="btn_generate_quiz") and topic_or_question.strip():
        with st.spinner("Generating MCQs..."):
            mcqs = generate_mcqs_with_retrieval(
                topic_or_question=topic_or_question,
                num_questions=int(num_questions),
                difficulty=difficulty,
                k=5,
            )

        if not mcqs:
            st.error("Failed to generate quiz questions. Try again or adjust the input.")
        else:
            quiz_id = save_quiz(
                user_id=st.session_state["user_id"],
                topic=topic_or_question,
                source_id=source_id_for_quiz,
                mcqs=mcqs,
            )
            set_current_quiz(quiz_id, mcqs)
            st.success(f"Quiz generated and saved. Quiz ID: {quiz_id}")

    st.markdown("---")
    st.subheader("Answer Current Quiz")

    quiz_id, mcq_dicts = get_current_quiz()

    if not quiz_id or not mcq_dicts:
        st.info("No current quiz. Generate a quiz above to start.")
    else:
        st.write(f"**Current Quiz ID:** `{quiz_id}`")

        # Render questions with options
        for i, mcq in enumerate(mcq_dicts):
            st.markdown(f"**Q{i+1}. {mcq['question']}**")
            selected = st.radio(
                "Select an option",
                options=list(range(len(mcq["options"]))),
                format_func=lambda idx, opts=mcq["options"]: f"{chr(65+idx)}. {opts[idx]}",
                key=f"quiz_q_{i}_choice",
            )
            st.markdown("---")

        if st.button("Submit Answers", key="btn_submit_quiz"):
            total = len(mcq_dicts)
            correct_count = 0

            for i, mcq in enumerate(mcq_dicts):
                chosen_index = st.session_state.get(f"quiz_q_{i}_choice", 0)
                correct_index = mcq["correct_index"]
                is_correct = (chosen_index == correct_index)

                if is_correct:
                    correct_count += 1

                save_response(
                    user_id=st.session_state["user_id"],
                    quiz_id=quiz_id,
                    question_index=i,
                    chosen_index=int(chosen_index),
                    is_correct=is_correct,
                )

            st.session_state["quiz_submitted"] = True
            st.success(f"You scored {correct_count} / {total}")

            # Optionally reveal correct answers
            with st.expander("Show Correct Answers & Explanations"):
                for i, mcq in enumerate(mcq_dicts):
                    st.markdown(f"**Q{i+1}. {mcq['question']}**")
                    st.write("Options:")
                    for idx, opt in enumerate(mcq["options"]):
                        prefix = "✅" if idx == mcq["correct_index"] else "  "
                        st.write(f"{prefix} {chr(65+idx)}. {opt}")
                    if mcq.get("explanation"):
                        st.write(f"_Explanation:_ {mcq['explanation']}")
                    st.markdown("---")


# ---------- COACH TAB ----------

with tab_coach:
    st.header("Learning Coach")

    if st.button("Compute Progress & Show Raw Stats", key="btn_compute_progress"):
        with st.spinner("Computing progress..."):
            stats = compute_progress(st.session_state["user_id"])
        st.markdown("### Progress Summary (Raw Data)")
        st.json(stats)

    if st.button("Get Coaching Advice", key="btn_get_coaching"):
        with st.spinner("Talking to your learning coach..."):
            advice = get_coaching_for_user(st.session_state["user_id"])
        st.markdown("### Coaching Advice")
        st.write(advice)
