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

- Python 3.9+
- Ollama installed and running

## Setup and Installation

1. Start Ollama and download the model:
```bash
ollama serve
ollama pull llama3.2
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
