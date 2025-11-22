import os
from textwrap import dedent

BASE_DIR = "school_in_a_box"

dirs = [
    BASE_DIR,
    os.path.join(BASE_DIR, "agents"),
    os.path.join(BASE_DIR, "services"),
    os.path.join(BASE_DIR, "models"),
    os.path.join(BASE_DIR, "data"),
    os.path.join(BASE_DIR, "data", "faiss_index"),
    os.path.join(BASE_DIR, "db"),
]

files_with_content = {
    os.path.join(BASE_DIR, "app.py"): dedent("""\
        import streamlit as st

        st.set_page_config(page_title="School in a Box", layout="wide")

        def main():
            st.title("School in a Box")
            tab_learn, tab_quiz, tab_coach = st.tabs(["Learn", "Quiz", "Coach"])
            with tab_learn:
                st.write("TODO: Learn tab UI")
            with tab_quiz:
                st.write("TODO: Quiz tab UI")
            with tab_coach:
                st.write("TODO: Coach tab UI")

        if __name__ == "__main__":
            main()
    """),

    os.path.join(BASE_DIR, "config.py"): dedent("""\
        # Global configuration for School in a Box

        OPENROUTER_API_KEY = ""  # set via env in real use
        MONGO_URI = "mongodb://localhost:27017"
        EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    """),

    os.path.join(BASE_DIR, "agents", "explainer.py"): dedent("""\
        # Content Explainer Agent

        def explain_content(text: str, level: str = "simple") -> str:
            \"\"\"Explain raw content for students (stub).\"\"\"
            return f"[EXPLAINER STUB] Level={level}\\n\\n{text}"
    """),

    os.path.join(BASE_DIR, "agents", "quiz_generator.py"): dedent("""\
        # Quiz Generator Agent

        def generate_quiz(text: str, num_questions: int = 5, difficulty: str = "medium") -> dict:
            \"\"\"Generate quiz questions from text (stub).\"\"\"
            return {
                "info": "[QUIZ GENERATOR STUB]",
                "difficulty": difficulty,
                "num_questions": num_questions,
            }
    """),

    os.path.join(BASE_DIR, "agents", "learning_coach.py"): dedent("""\
        # Learning Coach Agent

        def get_coaching_advice(progress_summary: str) -> str:
            \"\"\"Return coaching advice based on progress (stub).\"\"\"
            return f"[COACH STUB]\\n\\nProgress summary:\\n{progress_summary}"
    """),

    os.path.join(BASE_DIR, "services", "ingestion.py"): dedent("""\
        # PDF/image/text ingestion, chunking, tagging

        def ingest_text(text: str) -> list[str]:
            \"\"\"Very simple ingestion stub that returns one 'chunk'.\"\"\"
            return [text]
    """),

    os.path.join(BASE_DIR, "services", "vector_store.py"): dedent("""\
        # Qdrant/FAISS setup, similarity search

        class DummyVectorStore:
            def __init__(self):
                self.texts = []

            def add_texts(self, texts: list[str]):
                self.texts.extend(texts)

            def similarity_search(self, query: str, k: int = 5):
                # stub: just return stored texts
                return self.texts[:k]

        store = DummyVectorStore()
    """),

    os.path.join(BASE_DIR, "services", "quizzes.py"): dedent("""\
        # CRUD for quizzes/questions/responses (stub)

        def save_quiz(quiz: dict):
            pass

        def get_quizzes_for_user(user_id: str) -> list[dict]:
            return []
    """),

    os.path.join(BASE_DIR, "services", "progress.py"): dedent("""\
        # Stats + spaced repetition utilities (stub)

        def compute_progress(user_id: str) -> dict:
            return {"user_id": user_id, "progress": "stub"}

        def get_revision_schedule(user_id: str) -> list[dict]:
            return []
    """),

    os.path.join(BASE_DIR, "models", "llm_client.py"): dedent("""\
        # OpenRouter LLM client (stub)

        class LLMClient:
            def __init__(self, model_name: str):
                self.model_name = model_name

            def chat(self, messages: list[dict]) -> str:
                return "[LLM STUB RESPONSE]"
    """),

    os.path.join(BASE_DIR, "models", "embeddings.py"): dedent("""\
        # LocalEmbedder config (stub)

        def embed_texts(texts: list[str]):
            \"\"\"Return dummy embeddings (stub).\"\"\"
            return [[0.0] * 3 for _ in texts]
    """),

    os.path.join(BASE_DIR, "db", "models.py"): dedent("""\
        # DB models / helpers (stub)
        # Later: MongoDB collections, pydantic models, etc.

        def init_db():
            pass
    """),
}

def main():
    # create directories
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # create files with initial content (no overwrite if already exists)
    for path, content in files_with_content.items():
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

    print(f"Project scaffold created under ./{BASE_DIR}")

if __name__ == "__main__":
    main()
