# 📦 School in a Box

> **AI-Powered Adaptive Learning Platform with Multi-Agent RAG System**

An intelligent education platform that provides personalized learning experiences through AI-driven content explanation, adaptive quiz generation, and progress coaching.

---

## 🎯 Objective

Create an accessible, adaptive learning system that helps students master concepts at their own pace by:
- Ingesting educational materials from multiple sources (PDFs, text, images via OCR)
- Providing AI-powered explanations tailored to different learning levels
- Generating context-aware quizzes with retrieval-augmented generation (RAG)
- Offering personalized coaching based on performance analytics

---

## ⚠️ Problem Statement

Traditional learning platforms lack:
- **Personalization**: One-size-fits-all content doesn't adapt to individual learning needs
- **Context-Awareness**: Quiz questions are generic and don't align with studied material
- **Adaptive Feedback**: No intelligent coaching based on strengths and weaknesses
- **Multi-Format Support**: Limited ability to process diverse educational content (PDFs, images, text)

**School in a Box** solves these issues with a multi-agent RAG architecture that dynamically retrieves, analyzes, and responds to student needs.

---

## ✨ Key Features

### 📚 **Multi-Source Content Ingestion**
- Upload and process PDFs
- Paste text content directly
- OCR extraction from educational images
- Automatic chunking and embedding for retrieval

### 🧠 **AI-Powered Explainer Agent**
- Two modes: Raw text explanation or RAG-based retrieval
- Adjustable difficulty levels (simple, intermediate, advanced)
- Context-aware explanations using stored learning material

### 📝 **Adaptive Quiz Generator Agent**
- Generates MCQs based on retrieved content (RAG)
- Customizable difficulty and number of questions
- Stores quiz history for progress tracking

### 🎯 **Learning Coach Agent**
- Analyzes user performance across quizzes
- Identifies weak topics requiring revision
- Provides weekly study suggestions
- Tracks topic mastery with visual progress indicators

### 📊 **Progress Analytics Dashboard**
- Real-time performance metrics (accuracy, quizzes taken, questions attempted)
- Topic-wise mastery visualization
- Detailed review of quiz responses with explanations

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     STREAMLIT FRONTEND                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐    │
│  │   Learn    │  │    Quiz    │  │       Coach        │    │
│  │    Tab     │  │     Tab    │  │        Tab         │    │
│  └────────────┘  └────────────┘  └────────────────────┘    │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/REST API
┌───────────────────────────▼─────────────────────────────────┐
│                      FASTAPI BACKEND                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              LANGGRAPH ORCHESTRATION                 │   │
│  │  ┌────────────┐  ┌─────────────┐  ┌──────────────┐  │   │
│  │  │Quiz Graph  │  │Explain Graph│  │Coach Graph   │  │   │
│  │  └────────────┘  └─────────────┘  └──────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  SPECIALIZED AGENTS                  │   │
│  │  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐  │   │
│  │  │ Explainer   │ │Quiz Generator│ │Learning Coach│  │   │
│  │  │   Agent     │ │    Agent     │ │    Agent     │  │   │
│  │  └─────────────┘ └──────────────┘ └──────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────┬───────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼────────┐  ┌──────▼──────┐  ┌────────▼────────┐
│  FAISS Vector  │  │   MongoDB   │  │  OpenRouter API │
│     Store      │  │             │  │   (LLM Calls)   │
│  (Embeddings)  │  │ (User Data, │  │                 │
│                │  │  Quizzes,   │  │                 │
│                │  │  Progress)  │  │                 │
└────────────────┘  └─────────────┘  └─────────────────┘
```

---

## 🔄 Data Flow

### 1️⃣ **Content Ingestion Flow**
```
User uploads PDF/Text/Image
        ↓
OCR Processing (if image)
        ↓
Text Chunking (800 chars, 100 overlap)
        ↓
Embedding Generation (MiniLM-L6-v2)
        ↓
Storage in FAISS Vector Store
```

### 2️⃣ **Quiz Generation Flow (RAG Pipeline)**
```
User submits topic/question
        ↓
QUIZ GRAPH (LangGraph)
        ├─→ Generate MCQs Node
        │   ├─→ Retrieve relevant chunks (k=5)
        │   ├─→ LLM generates context-aware MCQs
        │   └─→ Return MCQ objects
        └─→ Save Quiz Node
            └─→ Store in MongoDB with user_id
        ↓
Return quiz to frontend
        ↓
User submits answers
        ↓
Evaluate & Save responses to MongoDB
```

### 3️⃣ **Explanation Flow (RAG Pipeline)**
```
User asks question
        ↓
EXPLAIN GRAPH (LangGraph)
        ├─→ Retrieve Context Node
        │   └─→ Similarity search in FAISS (k=5)
        └─→ Generate Explanation Node
            └─→ LLM explains with context + difficulty level
        ↓
Return explanation to user
```

### 4️⃣ **Coaching Flow**
```
User requests coaching report
        ↓
COACH GRAPH (LangGraph)
        ├─→ Compute Progress Node
        │   ├─→ Aggregate quiz responses from MongoDB
        │   ├─→ Calculate accuracy, topic mastery
        │   └─→ Identify weak areas
        └─→ Coaching Node
            └─→ LLM generates personalized advice
        ↓
Display insights & recommendations
```

---

## 🛠️ Tech Stack

### **Frontend**
- **Streamlit** - Interactive web interface
- **Pandas** - Data visualization for progress charts
- **Requests** - HTTP client for API calls

### **Backend**
- **FastAPI** - RESTful API server
- **Uvicorn** - ASGI web server
- **LangGraph** - Multi-agent workflow orchestration
- **Pydantic** - Data validation and serialization

### **AI & ML**
- **OpenRouter API** - LLM provider (Trinity-Large model)
- **Sentence Transformers** - Text embeddings (all-MiniLM-L6-v2)
- **FAISS** - Vector similarity search
- **PyTesseract** - OCR for image text extraction
- **Pillow** - Image processing

### **Database**
- **MongoDB** - Document store for users, quizzes, responses, progress
- **PyMongo** - MongoDB Python driver

### **Utilities**
- **python-dotenv** - Environment variable management

---

## 📁 Project Structure

```
school_in_a_box/
├── app.py                    # Streamlit frontend
├── backend/
│   ├── main.py               # FastAPI routes
│   └── graphs.py             # LangGraph workflow definitions
├── agents/
│   ├── explainer.py          # Content explanation agent
│   ├── quiz_generator.py    # Quiz generation agent
│   └── learning_coach.py    # Progress coaching agent
├── services/
│   ├── ingestion.py          # Document processing & chunking
│   ├── vector_store.py       # FAISS wrapper
│   ├── ocr.py                # Image text extraction
│   ├── quizzes.py            # Quiz CRUD operations
│   ├── users.py              # User management
│   └── progress.py           # Analytics computation
├── models/
│   ├── embeddings.py         # Text embedding generation
│   └── llm_client.py         # OpenRouter LLM client
├── db/
│   └── models.py             # MongoDB collections & indexes
├── data/
│   └── faiss_index/          # Persistent vector store
├── config.py                 # Centralized configuration
├── requirements.txt          # Python dependencies
└── Dockerfile                # Container deployment config
```

---

## 🚀 Getting Started

### Prerequisites
```bash
# Install MongoDB
# Install Tesseract OCR

# Python 3.11+
pip install -r requirements.txt
```

### Environment Setup
Create a `.env` file:
```env
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=School In a Box
```

### Run Backend
```bash
cd school_in_a_box
uvicorn backend.main:app --reload --port 8000
```

### Run Frontend
```bash
streamlit run app.py
```

Access the app at `http://localhost:8501`

---

## 📊 RAG Pipeline Details

### **Vector Store Architecture**
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- **Index Type**: FAISS Flat L2 (exact nearest neighbor search)
- **Chunking Strategy**: 800 characters with 100-character overlap
- **Retrieval**: Top-k similarity search (k=5 default)

### **LangGraph Workflows**
1. **Quiz Graph**: `generate_mcqs → save_quiz → END`
2. **Explain Graph**: `retrieve_context → generate_explanation → END`
3. **Coach Graph**: `compute_progress → coaching → END`

---

## 📈 Future Enhancements

- [ ] Integration with Qdrant for cloud-based vector storage
- [ ] Support for video content transcription
- [ ] Real-time collaborative learning sessions
- [ ] Advanced analytics with learning path recommendations
- [ ] Multi-language support

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ using AI and modern Python frameworks**
