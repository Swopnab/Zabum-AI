# Zabum AI — Personal AI Assistant with Memory and Knowledge Retrieval

Zabum AI is a local-first personal AI assistant built with Flask, SQLite, Ollama (Llama 3.2), Microsoft TrOCR, and Vanilla JavaScript. It provides multi-turn conversational chat, persistent user memory, and retrieval-augmented generation (RAG) across uploaded screenshots, text files, and documents.

## Features

- Multi-turn conversation interface with chat history management (create, rename, delete).
- Persistent user memory for storing and recalling user preferences and facts across conversations.
- Screenshot OCR using Microsoft TrOCR (`microsoft/trocr-base-printed`) to extract text from images.
- Knowledge Base / RAG pipeline that chunks documents and retrieves relevant context for queries.
- Local inference via Ollama with an extensible provider abstraction.
- SQLite database for persistent storage of conversations, messages, memories, documents, and chunks.

## Architecture

```text
zabum-ai/
├── backend/
│   ├── app.py                 # Flask application and static file serving
│   ├── config.py              # Configuration settings and system prompt
│   ├── requirements.txt       # Python dependencies
│   ├── models/                # SQLite models (conversation, message, memory, document)
│   ├── services/              # AI provider, OCR, RAG, and memory services
│   └── routes/                # Flask blueprints (chat, conversations, memory, documents, status)
├── frontend/
│   ├── index.html             # Chat UI layout
│   ├── styles.css             # CSS styling
│   └── app.js                 # Frontend state and API interactions
└── storage/
    ├── zabum.db               # SQLite database
    └── uploads/               # Uploaded files and screenshots
```

## Tech Stack

- Backend: Python 3, Flask, Flask-CORS, Werkzeug
- Frontend: HTML5, CSS3, JavaScript (ES6+)
- Database: SQLite 3
- LLM Inference: Ollama (`llama3.2`)
- OCR: Hugging Face Transformers (`microsoft/trocr-base-printed`), PyTorch, Pillow

## Prerequisites

- Python 3.11+
- Ollama installed and running

## Setup and Installation

1. Start Ollama and download the model:
```bash
ollama serve
ollama pull llama3.2
ollama pull nomic-embed-text
```

2. Set up the Python environment:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Start the application:
```bash
python app.py
```

4. Open the chat interface in your browser:
`http://localhost:5001/app`

## API Endpoints

- `POST /api/chat`: Send message and receive AI response with context retrieval.
- `GET /api/conversations`: List conversation sessions.
- `POST /api/conversations`: Create a new conversation.
- `PUT /api/conversations/<id>`: Rename a conversation.
- `DELETE /api/conversations/<id>`: Delete a conversation and its messages.
- `GET /api/memories`: Retrieve saved memories (supports `?q=` and `?category=`).
- `POST /api/memories`: Manually add a memory.
- `PUT /api/memories/<id>`: Edit a memory.
- `DELETE /api/memories/<id>`: Delete a memory.
- `POST /api/documents/upload`: Upload and index a screenshot or document.
- `GET /api/documents`: List indexed documents.
- `GET /api/documents/<id>/chunks`: View chunks for a document.
- `DELETE /api/documents/<id>`: Delete a document and its chunks.
- `GET /api/status`: Health check and Ollama connectivity status.

## Run without downloading models

For a lightweight, free local demo and regression tests:

```sh
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-core.txt
AI_PROVIDER=mock python app.py
python -m unittest discover -s tests -v
python evaluate.py --output ../evaluation/results.json
```

Mock mode labels its responses as demonstrations. It verifies application behavior without pretending to generate intelligent answers. Full chat uses the two Ollama models above; installing the original `requirements.txt` also enables TrOCR dependencies. OCR weights load only on the first image upload. If they cannot load, image upload returns an explicit 503 and creates no indexed document. Empty/unreadable files return 422. Text uploads work without OCR.

## Persistence and retrieval

Application SQLite models are checked in under `backend/models/`; the ignore rule now excludes only `/model-weights/`. Conversations/messages, memories, documents, and chunks survive restarts. Foreign keys cascade deletions. Document metadata, chunks, and FTS updates commit together, so a chunk failure rolls the ingestion back.

SQLite FTS5/BM25 selects at most 100 lexical candidates for token-overlap/optional-vector reranking. This bounds Python ranking work, but synonym-only semantic matches outside the lexical shortlist can be missed. The previous exhaustive keyword scan is retained only as an evaluation baseline. No separate vector database or paid API is required.

The checked-in synthetic evaluation compares recall@4, reciprocal rank, unrelated-query results, and p50/p95 retrieval time at 1,000 and 10,000 chunks. These simple fixtures do not establish answer grounding or OCR accuracy. For a meaningful next evaluation, use held-out real documents/questions and manually verified screenshot transcriptions; report answer support and OCR word error rate separately.

The server binds to localhost with debug disabled by default. Storage defaults to `storage/`; `ZABUM_STORAGE_DIR` selects another local directory. This remains a single-user local application. Back up an existing database before changing schemas. Tests use isolated temporary storage and require no running Ollama instance.

## Review release

See [setup, architecture, data recovery, evaluation definitions, and limitations](docs/RELEASE_REVIEW.md) and [UI provenance](docs/UI_REUSE.md). The local app now offers document passages with clickable source locations and general AI chat as separate modes. Suggested memories require approval. The working service remains localhost-only; the static showcase is available at `/showcase/`.

## Published interface — October 28, 2026

[Open the website](https://swopnab.github.io/Zabum-AI/). Only the static showcase is public. The document/chat API and personal storage stay local. See GitHub Actions for release checks and deployment status.
