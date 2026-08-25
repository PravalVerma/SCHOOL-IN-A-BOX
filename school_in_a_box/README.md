# 📦 School in a Box

**AI-Powered Adaptive Learning Platform**

School in a Box helps students learn smarter by turning their own study material into an interactive learning loop:

- **Ingest** study material (raw text, PDFs, or photos of notes via OCR)
- **Learn** with RAG-based explanations grounded strictly in that material
- **Practice** with auto-generated multiple-choice quizzes
- **Improve** with an AI Learning Coach that analyzes performance and recommends what to revise

The system is built as two cooperating processes: a **Streamlit dashboard** (frontend) and a **FastAPI backend** whose AI workflows are orchestrated with **LangGraph**.

---

## 🏗 Architecture

```
┌─────────────────────────┐         ┌──────────────────────────────┐
│   Streamlit UI          │  HTTP   │   FastAPI Backend (:8001)    │
│   app.py                │ ──────► │   backend/main.py            │
│                         │         │                              │
│  • Dashboard metrics    │         │  LangGraph workflows:        │
│  • Learn tab            │         │   • explain_graph (RAG)      │
│    - text / PDF / OCR   │         │   • quiz_graph               │
│  • Quiz tab             │         │   • coach_graph              │
│  • Coach tab            │         │                              │
└─────────────────────────┘         └──────┬───────────┬───────────┘
                                           │           │
                            ┌──────────────▼───┐   ┌───▼────────────────────┐
                            │ MongoDB (Atlas/  │   │ OpenRouter LLM API     │
                            │ local)           │   │ (OpenAI-compatible)    │
                            │ users, content,  │   │ Explainer / Quiz /     │
                            │ quizzes,         │   │ Coach agents           │
                            │ responses,       │   └───┬────────────────────┘
                            │ progress         │       │
                            └──────────────────┘   ┌───▼────────────────────┐
                                                   │ FAISS vector store +   │
                                                   │ all-MiniLM-L6-v2       │
                                                   │ embeddings             │
                                                   │ (data/faiss_index/)    │
                                                   └────────────────────────┘
```

### Tech stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit, pandas, requests |
| Backend API | FastAPI, Pydantic, Uvicorn |
| AI orchestration | LangGraph (`StateGraph`) |
| LLM | OpenRouter via the OpenAI Python SDK |
| Embeddings / RAG | `sentence-transformers/all-MiniLM-L6-v2` + FAISS |
| Database | MongoDB (Atlas or local) via PyMongo |
| OCR | Tesseract (`pytesseract`) + Pillow |

---

## ✨ Features

### 📘 Learn tab
- **Paste text** — ingested through the backend, chunked, embedded, and stored in FAISS.
- **Upload PDF** — loaded with `PyPDFLoader`, split into overlapping chunks, and indexed.
- **OCR image** — extract text from photos of notes/handouts using Tesseract.
- **Ask a question** — RAG explanation: top-k relevant chunks are retrieved from FAISS and the LLM explains the answer grounded in that context.

### 📝 Quiz tab
- Generate MCQs on any topic/question, choosing count (1–10) and difficulty (easy/medium/hard).
- Questions are generated **from retrieved study material** when available; otherwise from the raw topic text.
- Take quizzes in-form, get instant scoring and a per-question review with explanations.
- Every answer is recorded to MongoDB for progress tracking.

### 🎯 Coach tab
- Generates a personalized coaching report from your quiz history:
  - Overall accuracy metrics
  - Weekly study suggestion written by the LLM
  - Weak-topic detection (< 60% mastery flagged for revision)
- Includes a rule-based fallback if the LLM/rate limit is unavailable.

### 📊 Dashboard
- Quizzes taken, questions attempted, accuracy
- Correct vs. incorrect bar chart
- Per-topic mastery progress bars with recommendations

---

## 📁 Project Structure

```
school_in_a_box/
├── app.py                    # Streamlit dashboard (UI entry point)
├── backend/
│   ├── main.py               # FastAPI app — all REST endpoints
│   └── graphs.py             # LangGraph definitions (quiz, coach, explain)
├── agents/
│   ├── explainer.py          # Content Explainer agent (prompts + RAG explain)
│   ├── quiz_generator.py     # Quiz Generator agent (MCQ dataclass, JSON parsing)
│   └── learning_coach.py     # Learning Coach agent (+ rule-based fallback)
├── models/
│   ├── llm_client.py         # OpenRouter chat-completion wrapper
│   └── embeddings.py         # SentenceTransformer embedder (lazy singleton)
├── services/
│   ├── ingestion.py          # Text/PDF loading, chunking, vector-store push
│   ├── ocr.py                # Tesseract OCR utilities
│   ├── vector_store.py       # FAISS wrapper (persisted index + metadata)
│   ├── quizzes.py            # Quiz/response persistence (Mongo CRUD)
│   ├── progress.py           # Progress aggregation (per-topic/per-quiz stats)
│   └── users.py              # User upsert & listing
├── db/
│   └── models.py             # Mongo client, collection helpers, indexes
├── config.py                 # Central configuration (env vars, models, paths)
├── data/faiss_index/         # Persisted FAISS index + chunk metadata
├── scratch/                  # Ad-hoc test/debug scripts
├── requirements.txt
├── packages.txt              # System packages (tesseract, poppler) for cloud deploys
├── Dockerfile                # (see Known Limitations — currently stale)
└── .env                      # Secrets — never commit
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- A **MongoDB** instance — either [MongoDB Atlas](https://www.mongodb.com/atlas) (free tier works) or a local `mongod`
- An **[OpenRouter](https://openrouter.ai/)** API key
- **Tesseract OCR** (only needed for the OCR feature):
  - Windows: install from the [UB-Mannheim Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki) to the default path `C:\Program Files\Tesseract-OCR\` (auto-detected by `services/ocr.py`)
  - Linux/Debian: `sudo apt install tesseract-ocr tesseract-ocr-eng poppler-utils`

### 1. Clone and install dependencies

```bash
cd school_in_a_box
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install fastapi uvicorn langgraph pymongo python-dotenv pytesseract Pillow \
    streamlit requests pandas numpy openai \
    langchain-community langchain-text-splitters \
    sentence-transformers faiss-cpu pydantic typing_extensions
```

> ⚠️ Note: `requirements.txt` currently lists only a subset of these packages (see [Known Limitations](#known-limitations)). The command above reflects what the code actually imports.

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
MONGO_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/
MONGO_DB_NAME=school_in_a_box
```

All values are loaded by `config.py` at startup. An optional extra setting is also supported:

```env
VECTOR_STORE_TYPE=faiss
```

### 3. Run the backend (port 8001)

```bash
uvicorn backend.main:app --reload --port 8001
```

On startup the app creates Mongo indexes automatically. Verify it's healthy:

```bash
curl http://localhost:8001/health
# {"status":"ok"}
```

### 4. Run the frontend (new terminal)

```bash
streamlit run app.py
```

The UI opens at `http://localhost:8501` and calls the backend at `http://localhost:8001` (hard-coded in `app.py` as `BACKEND_URL`).

---

## 🔌 API Reference

Base URL: `http://localhost:8001`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/ingest/text` | Chunk + embed raw text into the vector store |
| POST | `/explain/raw` | Explain provided text directly (no retrieval) |
| POST | `/explain/rag` | RAG explanation for a question from stored material |
| POST | `/quiz/generate` | Generate MCQs (RAG-grounded), save quiz, return quiz_id |
| POST | `/quiz/response` | Record a single answer |
| GET | `/quiz/{quiz_id}` | Fetch a saved quiz by id |
| POST | `/coach/advice` | Compute progress + generate coaching advice |

Interactive docs are available at [`/docs`](http://localhost:8001/docs) (Swagger UI).

### Example requests

```bash
# Ingest study material
curl -X POST http://localhost:8001/ingest/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Photosynthesis is the process by which plants...", "source_id": "bio_ch1"}'

# Ask a question (RAG explanation)
curl -X POST http://localhost:8001/explain/rag \
  -H "Content-Type: application/json" \
  -d '{"question": "How does photosynthesis work?", "level": "simple", "k": 5}'

# Generate a quiz
curl -X POST http://localhost:8001/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo-user", "topic_or_question": "photosynthesis",
       "source_id": "bio_ch1", "num_questions": 5, "difficulty": "medium"}'

# Record an answer
curl -X POST http://localhost:8001/quiz/response \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo-user", "quiz_id": "<quiz_id>",
       "question_index": 0, "chosen_index": 2, "is_correct": false}'

# Get coaching advice
curl -X POST http://localhost:8001/coach/advice \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo-user"}'
```

---

## 🔄 LangGraph Workflows

All AI flows live in `backend/graphs.py` as compiled `StateGraph`s:

**Explain (RAG):**
```
START → retrieve_context → generate_explanation → END
```

**Quiz:**
```
START → generate_mcqs → save_quiz → END
```

**Coach:**
```
START → compute_progress → coaching → END
```

Agents themselves (`agents/*`) only build prompts and call the LLM; retrieval, persistence, and stats are handled by `services/*`.

---

## 🗄 Data Model (MongoDB)

| Collection | Purpose | Key fields |
|---|---|---|
| `users` | Known user ids | `user_id`, `created_at`, `last_active_at` |
| `content` | Ingested material metadata | `user_id`, `source_id`, `source_type`, `title` |
| `quizzes` | Quiz definitions with embedded MCQs | `user_id`, `topic`, `source_id`, `mcqs[]`, `created_at` |
| `responses` | Individual answers | `user_id`, `quiz_id`, `question_index`, `chosen_index`, `is_correct`, `answered_at` |
| `progress` | Aggregated/snapshot progress | `user_id`, `overall_accuracy`, `topics[]` |

Indexes on `user_id`, `source_id`, `topic`, and `quiz_id` are created at backend startup via `init_indexes()`.

Chunk texts and embeddings live outside Mongo, persisted on disk under `data/faiss_index/` (`index.faiss` + `metadata.pkl`).

---

## ⚙️ Configuration Reference (`config.py`)

| Setting | Default | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | env var | Required. OpenRouter API key |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter endpoint |
| `MONGO_URI` | `mongodb://localhost:27017/` | MongoDB connection string |
| `MONGO_DB_NAME` | `School In a Box` | Database name (recommended: `school_in_a_box`) |
| `EMBEDDING_MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `LLM_MODEL_EXPLAINER` / `_QUIZ` / `_COACH` | `arcee-ai/trinity-large-preview:free` | Model per agent (swap freely) |
| `VECTOR_STORE_TYPE` | `faiss` | Vector store selection (`qdrant` planned) |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `800` / `100` | Text-splitter settings |
| `DEFAULT_NUM_QUESTIONS` | `5` | Quiz size default |

---

## 🧪 Testing

Ad-hoc scripts for exercising the LLM, RAG pipeline, and endpoints live in `scratch/` (e.g., `test_llm_direct.py`, `test_rag.py`, `test_endpoints.py`). Run them directly with Python while both services are up:

```bash
python scratch/test_rag.py
```

---

## ☁️ Deployment Notes

- `packages.txt` lists system packages (`tesseract-ocr`, `poppler-utils`) in the format used by Hugging Face Spaces / similar platforms that install them alongside `requirements.txt`.
- The included `Dockerfile` is **not yet aligned** with the current app (see below) — use it only as a starting point.

## ⚠️ Known Limitations

1. **`requirements.txt` is incomplete** — it omits several packages the code imports (`streamlit`, `requests`, `pandas`, `openai`, `langchain-community`, `langchain-text-splitters`, `sentence-transformers`, `faiss-cpu`, `numpy`). Install manually or update the file before deploying.
2. **Stale `Dockerfile`** — installs `awscli`, runs a nonexistent `main.py`, uses Python 3.9, and doesn't install Tesseract/poppler. Needs rewriting to run uvicorn + streamlit.
3. **Hard-coded backend URL** — the Streamlit app targets `http://localhost:8001`; make it configurable via env for remote deployments.
4. **Mixed ingestion paths** — text ingest goes through the backend API, while PDF ingest runs in the Streamlit process directly. Unifying on the backend would be cleaner.
5. **No authentication** — user identity is a plain string chosen in the sidebar; fine for demos, not multi-tenant production.
6. **Strict MCQ parsing** — quiz generation expects valid JSON with exactly 4 options per question; malformed LLM output yields fewer/no questions.

## 🗺 Roadmap Ideas

- Qdrant vector-store support (config hook already exists)
- Spaced-repetition revision scheduling (`get_revision_schedule`)
- Image ingestion wired into the vector store (OCR text is currently preview-only)
- Proper test suite replacing `scratch/` scripts

---

## 📄 License

See [LICENSE](LICENSE).


