# Zabum AI — Personal AI Assistant with Memory and Knowledge Retrieval

**Zabum AI** is a privacy-first, local personal AI assistant built with Python Flask, SQLite, Ollama (Llama 3.2), Microsoft TrOCR, and Vanilla JavaScript.

It combines multi-turn conversational AI with persistent user memory and Retrieval-Augmented Generation (RAG) across uploaded screenshots, documents, code files, and notes.

---

## 🌟 Key Capabilities

* **🧠 Multi-Turn Conversational Assistant**: Clean, responsive chat interface supporting explanations, code generation, summarization, and brainstorming.
* **💾 Persistent Personal Memory**: Remembers user preferences, tech stacks, facts, and identity across sessions (both automatically via natural conversation and manually via the Memory Manager).
* **📸 Screenshot Intelligence (TrOCR)**: Extracts text from uploaded screenshots using Microsoft TrOCR and indexes them into the personal knowledge base.
* **📚 Retrieval-Augmented Generation (RAG)**: Automatically chunks documents and retrieves the most relevant semantic segments to answer user queries with source attribution.
* **🔒 100% Local & Privacy-First**: Runs on your local machine using Ollama and local storage. No external APIs or recurring subscription costs required.
* **🔌 Pluggable AI Provider Architecture**: Clean abstraction layer supporting Ollama (default), mock offline mode, and future cloud or local AI providers.

---

## 🏗️ Architecture Overview

```text
zabum-ai/
├── backend/
│   ├── app.py                     # Flask application entry point & static file server
│   ├── config.py                  # Central configuration & system persona prompt
│   ├── requirements.txt           # Python dependencies
│   ├── models/
│   │   ├── database.py            # SQLite connection manager & schema migrations
│   │   ├── conversation.py        # Conversations & Messages CRUD
│   │   ├── memory.py              # Persistent user memories model
│   │   └── document.py            # Documents & Document Chunks (RAG) model
│   ├── services/
│   │   ├── ai_provider.py         # AI provider interface (Ollama / Mock)
│   │   ├── memory_service.py      # Memory extraction & contextual retrieval
│   │   ├── rag_service.py         # Chunking, embeddings & hybrid search
│   │   └── ocr_service.py         # Hugging Face TrOCR text extraction
│   └── routes/
│       ├── chat.py                # POST /api/chat context assembly & turn handler
│       ├── conversations.py       # Conversation management endpoints
│       ├── memory.py              # Memory CRUD endpoints
│       ├── documents.py           # Document upload, OCR, and chunk inspection
│       └── status.py              # Health check & Ollama connectivity
├── frontend/
│   ├── index.html                 # Modern chat UI (Sidebar, Chat Feed, Modals)
│   ├── styles.css                 # Dark-mode glassmorphic design system
│   └── app.js                     # State management, markdown/code rendering & API client
└── storage/
    ├── zabum.db                   # SQLite database
    ├── uploads/                   # Uploaded images & documents
    └── thumbnails/                # Generated previews
```

---

## 🛠️ Technology Stack

| Layer | Technologies Used |
|---|---|
| **Frontend** | Vanilla HTML5, Vanilla CSS3 (Custom Glassmorphic Design System), Vanilla JavaScript (ES6+) |
| **Backend API** | Python 3.9+, Flask, Flask-CORS, Werkzeug |
| **Database** | SQLite 3 (WAL mode, relational schema with cascade deletes) |
| **Local LLM** | Ollama running `llama3.2` |
| **OCR Pipeline** | Hugging Face Transformers (`microsoft/trocr-base-printed`), PyTorch, Pillow |
| **RAG / Vector Retrieval** | SQLite chunk store, Ollama embeddings / Hybrid cosine & keyword ranking |

---

## ⚙️ Context Assembly Pipeline

Every time a message is sent to `POST /api/chat`, Zabum AI constructs context in modular stages:

```text
┌────────────────────────────────────────────────────────┐
│ 1. Central System Persona & Behavioral Instructions    │
├────────────────────────────────────────────────────────┤
│ 2. Contextually Relevant User Memories & Preferences   │
├────────────────────────────────────────────────────────┤
│ 3. Retrieved Knowledge Base / Screenshot OCR Chunks    │
├────────────────────────────────────────────────────────┤
│ 4. Recent Conversation History (Sliding Window)        │
├────────────────────────────────────────────────────────┤
│ 5. Current User Message                                │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 Getting Started

### 1. Prerequisites

* Python 3.9+
* [Ollama](https://ollama.com/) installed on your machine
* At least 4GB of RAM (for running local 1B/3B LLM and OCR)

### 2. Install Ollama & Pull the Model

```bash
# Start Ollama service
ollama serve

# In a separate terminal, pull the Llama 3.2 model
ollama pull llama3.2
```

*(Optional: For fast vector embeddings, run `ollama pull nomic-embed-text`)*

### 3. Clone & Setup Backend

```bash
# Clone the repository
git clone https://github.com/yourusername/Zabum-AI.git
cd Zabum-AI/backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

Open your browser and navigate to:
```
http://localhost:5001/app
```

---

## 💡 Usage Examples

### 1. Natural Conversation
* *"Explain recursion with a Python code example."*
* *"How do I structure a modular Flask application?"*

### 2. Persistent Memory
* **User**: `"Remember that I prefer Python and PostgreSQL for backend development."`
* **Zabum AI**: Stores the preference in persistent memory.
* Later in any conversation:
* **User**: `"What tech stack should I choose for my new web service?"`
* **Zabum AI**: Recalls your preference for Python and PostgreSQL and tailors recommendations accordingly.

### 3. Screenshot & Document Intelligence
* Click the paperclip attachment button or drag and drop a screenshot of programming notes into the chat window.
* TrOCR extracts the text and splits it into searchable RAG chunks.
* Ask: `"What did my uploaded screenshot say about binary search trees?"`
* Zabum AI retrieves the exact chunk, answers your question, and cites the source document.

---

## 📄 License

This project is licensed under the MIT License.
