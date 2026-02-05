import tempfile
import streamlit as st
import requests
import pandas as pd

from services.ingestion import ingest_pdf
from services.ocr import extract_text_from_image
from services.users import ensure_user, get_all_user_ids

BACKEND_URL = "http://localhost:8000"
# @st.cache_data(ttl=300)
@st.cache_data(ttl=60)
def fetch_coach_data(user_id):
    resp = requests.post(
        f"{BACKEND_URL}/coach/advice",
        json={"user_id": user_id},
        timeout=60,
    )
    return resp.json()

def fetch_progress(user_id: str):
    try:
        resp = requests.post(
            f"{BACKEND_URL}/coach/advice",
            json={"user_id": user_id},
            timeout=60,
        )
        data = resp.json()
        return data.get("progress", {})
    except Exception:
        return {}



# ---------- Session helpers ----------
def set_current_quiz(quiz_id: str, mcqs: list[dict]) -> None:
    st.session_state["current_quiz_id"] = quiz_id
    st.session_state["current_quiz_mcqs"] = mcqs
    st.session_state["quiz_submitted"] = False


def get_current_quiz():
    quiz_id = st.session_state.get("current_quiz_id")
    mcqs = st.session_state.get("current_quiz_mcqs")
    if not quiz_id or not mcqs:
        return None, None
    return quiz_id, mcqs


# ---------- Page Config ----------
st.set_page_config(page_title="School in a Box", layout="wide")

# ---------- Styling ----------
st.markdown("""
<style>
.block-container {padding-top: 1rem;}
.stButton button {
    border-radius: 8px;
    padding: 0.5rem 1rem;
    font-weight: 600;
}
.metric-card {
    background-color: #111;
    padding: 12px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.title("📦 School in a Box")
st.caption("AI-Powered Adaptive Learning Dashboard")

# ---------- Session ----------
if "user_id" not in st.session_state:
    st.session_state["user_id"] = "demo-user"

# ---------- Sidebar ----------
st.sidebar.title("⚙️ Settings")

existing_users = get_all_user_ids()
default_user = st.session_state["user_id"]

selected_user = st.sidebar.selectbox(
    "Existing users",
    options=["(New user)"] + existing_users,
    index=1 if default_user in existing_users else 0,
)

new_user_input = st.sidebar.text_input("New user ID")

if st.sidebar.button("Switch User"):
    if new_user_input.strip():
        st.session_state["user_id"] = new_user_input.strip()
        ensure_user(st.session_state["user_id"])
        st.rerun()
    elif selected_user != "(New user)":
        st.session_state["user_id"] = selected_user
        ensure_user(st.session_state["user_id"])
        st.rerun()

st.sidebar.success(f"Active user: {st.session_state['user_id']}")
st.sidebar.divider()

# ---------- Dashboard Metrics ----------
progress = fetch_progress(st.session_state["user_id"])

quizzes_taken = progress.get("total_quizzes", 0)
total_questions = progress.get("total_questions", 0)
correct_answers = progress.get("correct_answers", 0)

accuracy = 0
if total_questions > 0:
    accuracy = int((correct_answers / total_questions) * 100)

colA, colB, colC = st.columns(3)

with colA:
    st.metric("Quizzes Taken", quizzes_taken)

with colB:
    st.metric("Questions Attempted", total_questions)

with colC:
    st.metric("Accuracy", f"{accuracy}%")


st.divider()



if total_questions > 0:
    st.markdown("### Performance Overview")

    chart_data = pd.DataFrame({
        "Metric": ["Correct", "Incorrect"],
        "Count": [
            correct_answers,
            total_questions - correct_answers
        ]
    })

    st.bar_chart(chart_data.set_index("Metric"))


if accuracy >= 80:
    st.success("Great performance! Keep it up.")
elif accuracy >= 50:
    st.info("You're improving. Focus on weak topics.")
elif total_questions > 0:
    st.warning("Consider revising key concepts before taking more quizzes.")


st.markdown("### Topic Mastery")

topic_stats = progress.get("topic_stats", {})

if topic_stats:
    for topic, stats in topic_stats.items():
        total = stats.get("total", 0)
        correct = stats.get("correct", 0)

        if total == 0:
            continue

        mastery = correct / total

        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{topic}**")
            st.progress(mastery)

            # 👇 Step 3 goes here
            if mastery >= 0.8:
                st.caption("Strong understanding")
            elif mastery >= 0.5:
                st.caption("Needs revision")
            else:
                st.caption("Weak topic — recommended for practice")

        with col2:
            st.write(f"{int(mastery*100)}%")
else:
    st.info("Topic mastery will appear after taking quizzes.")



# ---------- Tabs ----------
tab_learn, tab_quiz, tab_coach = st.tabs(["📘 Learn", "📝 Quiz", "🎯 Coach"])


# ================= LEARN TAB =================
with tab_learn:
    st.subheader("Add Study Material")

    col1, col2, col3 = st.columns(3)

    # TEXT INGEST
    with col1:
        st.markdown("#### ✍️ Paste Text")
        text_source_id = st.text_input("Source ID", "text_source_1")
        raw_text = st.text_area("Content", height=200)

        if st.button("Ingest Text"):
            if raw_text.strip():
                resp = requests.post(
                    f"{BACKEND_URL}/ingest/text",
                    json={"text": raw_text, "source_id": text_source_id},
                    timeout=60,
                )
                st.success("Text ingested.")

    # PDF INGEST
    with col2:
        st.markdown("#### 📄 Upload PDF")
        pdf_file = st.file_uploader("Upload PDF", type=["pdf"])
        pdf_source_id = st.text_input("PDF Source ID", "pdf_source_1")

        if st.button("Ingest PDF"):
            if pdf_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(pdf_file.read())
                    tmp_path = tmp.name
                chunks = ingest_pdf(tmp_path, source_id=pdf_source_id)
                st.success(f"{len(chunks)} chunks ingested.")

    # OCR INGEST
    with col3:
        st.markdown("#### 🖼 OCR Image")
        image_file = st.file_uploader("Upload Image", type=["png","jpg","jpeg"])
        image_source_id = st.text_input("Image Source ID", "image_source_1")

        if st.button("Run OCR"):
            if image_file:
                text = extract_text_from_image(image_file.read())
                st.text_area("Extracted Text", text, height=150, key="ocr_preview")

        if st.button("Ingest OCR Text"):
            ocr_text = st.session_state.get("ocr_preview", "")
            if ocr_text.strip():
                requests.post(
                    f"{BACKEND_URL}/ingest/text",
                    json={"text": ocr_text, "source_id": image_source_id},
                    timeout=60,
                )
                st.success("OCR text ingested.")

    st.divider()

    st.subheader("Explain Concepts")

    explain_mode = st.radio(
        "Mode",
        ["Explain pasted text", "Explain using stored material"]
    )

    level = st.selectbox("Level", ["simple", "intermediate", "advanced"])

    if explain_mode == "Explain pasted text":
        text = st.text_area("Text to explain")
        if st.button("Explain"):
            resp = requests.post(
                f"{BACKEND_URL}/explain/raw",
                json={"text": text, "level": level},
                timeout=120,
            )
            st.success("Explanation generated")
            st.write(resp.json().get("explanation",""))

    else:
        question = st.text_input("Ask a question")
        if st.button("Explain from material"):
            resp = requests.post(
                f"{BACKEND_URL}/explain/rag",
                json={"question": question, "level": level, "k": 5},
                timeout=120,
            )
            st.success("Explanation generated")
            st.write(resp.json().get("explanation",""))


# ================= QUIZ TAB =================
# ================= QUIZ TAB =================
with tab_quiz:
    st.subheader("Practice Quizzes")

    # ---------- Quiz Generation Form ----------
    with st.form("quiz_generation_form"):
        topic = st.text_input("Topic or Question")
        num_questions = st.slider("Number of Questions", 1, 10, 5)
        difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
        source_id = st.text_input("Source ID", "generic_source")

        generate_btn = st.form_submit_button("Generate Quiz")

    if generate_btn and topic.strip():
        with st.spinner("Generating quiz..."):
            resp = requests.post(
                f"{BACKEND_URL}/quiz/generate",
                json={
                    "user_id": st.session_state["user_id"],
                    "topic_or_question": topic,
                    "source_id": source_id,
                    "num_questions": num_questions,
                    "difficulty": difficulty,
                    "k": 5,
                },
            )
            data = resp.json()
            if data.get("quiz_id"):
                set_current_quiz(data["quiz_id"], data["mcqs"])
                st.session_state["quiz_submitted"] = False
                st.success("Quiz Ready!")

    # ---------- Display Quiz ----------
    quiz_id, mcqs = get_current_quiz()

    if quiz_id and mcqs:
        total = len(mcqs)

        with st.form("quiz_submit_form"):
            for i, mcq in enumerate(mcqs):
                st.markdown(f"### Q{i+1}")
                st.write(mcq["question"])

                st.radio(
                    "Select answer",
                    options=list(range(len(mcq["options"]))),
                    format_func=lambda idx, opts=mcq["options"]: f"{chr(65+idx)}. {opts[idx]}",
                    key=f"quiz_q_{i}",
                )

            submit_btn = st.form_submit_button("Submit Quiz")

        # ---------- Submission Logic ----------
        if submit_btn:
            with st.spinner("Evaluating quiz..."):
                correct_count = 0

                for i, mcq in enumerate(mcqs):
                    chosen = st.session_state.get(f"quiz_q_{i}", 0)
                    correct = mcq["correct_index"]

                    if chosen == correct:
                        correct_count += 1

                    # Save response to backend
                    requests.post(
                        f"{BACKEND_URL}/quiz/response",
                        json={
                            "user_id": st.session_state["user_id"],
                            "quiz_id": quiz_id,
                            "question_index": i,
                            "chosen_index": chosen,
                            "is_correct": chosen == correct,
                        },
                    )

                st.session_state["quiz_score"] = correct_count
                st.session_state["quiz_submitted"] = True

        # ---------- Results ----------
        if st.session_state.get("quiz_submitted"):
            correct_count = st.session_state.get("quiz_score", 0)
            percent = int((correct_count / total) * 100)

            st.success(f"Score: {correct_count}/{total} ({percent}%)")
            st.progress(percent / 100)

            st.markdown("### Review")

            for i, mcq in enumerate(mcqs):
                chosen = st.session_state.get(f"quiz_q_{i}", 0)
                correct = mcq["correct_index"]

                st.markdown(f"**Q{i+1}. {mcq['question']}**")

                for idx, option in enumerate(mcq["options"]):
                    if idx == correct:
                        st.write(f"✅ {chr(65+idx)}. {option}")
                    elif idx == chosen:
                        st.write(f"❌ {chr(65+idx)}. {option}")
                    else:
                        st.write(f"{chr(65+idx)}. {option}")

                if mcq.get("explanation"):
                    st.caption(f"Explanation: {mcq['explanation']}")

                st.markdown("---")



# ================= COACH TAB =================
with tab_coach:
    st.subheader("🎯 Learning Insights")
    st.caption("Personalized feedback based on your performance.")

    if st.button("Generate Coaching Report"):
        try:
            with st.spinner("Analyzing progress..."):
                data = fetch_coach_data(st.session_state["user_id"])

            advice = data.get("advice", "No advice available.")
            progress = data.get("progress", {})

            # Weekly suggestion
            st.markdown("### 📅 Weekly Study Suggestion")
            st.write(advice)

            # Summary metrics
            total_quizzes = progress.get("total_quizzes", 0)
            total_questions = progress.get("total_questions", 0)
            correct_answers = progress.get("correct_answers", 0)

            accuracy = 0
            if total_questions > 0:
                accuracy = int((correct_answers / total_questions) * 100)

            col1, col2, col3 = st.columns(3)
            col1.metric("Quizzes Taken", total_quizzes)
            col2.metric("Questions Attempted", total_questions)
            col3.metric("Accuracy", f"{accuracy}%")

            # Weak topics section
            topic_stats = progress.get("topic_stats", {})

            if topic_stats:
                st.markdown("### ⚠ Topics Needing Attention")

                weak_found = False

                for topic, stats in topic_stats.items():
                    total = stats.get("total", 0)
                    correct = stats.get("correct", 0)

                    if total == 0:
                        continue

                    mastery = correct / total

                    if mastery < 0.6:
                        weak_found = True
                        st.warning(
                            f"{topic} — {int(mastery*100)}% mastery (Recommended for revision)"
                        )

                if not weak_found:
                    st.success("No weak topics detected. Keep progressing!")

            # Detailed stats
            with st.expander("🔍 View Detailed Progress Data"):
                st.json(progress)

        except Exception as e:
            st.error(f"Error fetching coaching report: {e}")



st.divider()
st.caption("School in a Box • AI-Powered Adaptive Learning")
