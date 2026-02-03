# Zabum AI

**Local-First AI Screenshot Knowledge Management System**

Transform your unorganized screenshots into a searchable, tagged knowledge base using AI—100% locally, zero cost.

---

## 🎯 What is Zabum AI?

Zabum AI automatically:

- **Extracts text** from screenshots using Microsoft TrOCR
- **Generates smart tags** using local LLMs (Ollama + Llama 3.2)
- **Creates searchable gallery** of all your visual content
- **Exports to Markdown** for notes and documentation

**Privacy-First**: All processing happens on your machine. No cloud uploads, no API costs.

---

## 🏗️ Project Structure

```
zabum-ai/
├── backend/           # Python Flask API
│   ├── app.py        # Main Flask application
│   ├── services/     # OCR and LLM services
│   ├── models/       # Database models
│   └── requirements.txt
├── frontend/         # Web interface
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── storage/          # Local file storage
    ├── uploads/      # Original images
    └── thumbnails/   # Generated thumbnails
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Ollama installed
- ~2GB free disk space

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/zabum-ai.git
cd zabum-ai

# 2. Set up backend
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Install Ollama and pull model
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:1b

# 4. Run the app
python app.py
```

Visit `http://localhost:5000` in your browser!

---

## 📖 Development Timeline

**Week 1**: OCR Pipeline ✅  
**Week 2**: LLM Tagging  
**Week 3**: Frontend UI  
**Week 4**: Export & Deployment  

See [one_month_roadmap.md](docs/one_month_roadmap.md) for detailed timeline.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **OCR** | TrOCR (Hugging Face Transformers) |
| **LLM** | Llama 3.2 (via Ollama) |
| **Backend** | Flask + SQLite |
| **Frontend** | Vanilla JS + CSS |
| **Deployment** | GitHub Pages (frontend) + Local runner |

---

## 📝 Documentation

- [Market Research](docs/market_research.md)
- [Project Proposal](docs/project_proposal.md)
- [Development Roadmap](docs/one_month_roadmap.md)
- [Your Preparation Tasks](docs/YOUR_PREPARATION_TASKS.md)

---

## 🎓 Portfolio Value

This project demonstrates:

- ✅ Full-stack development (frontend + backend + AI)
- ✅ Modern AI integration (transformers, local LLMs)
- ✅ System architecture (local vs cloud tradeoffs)
- ✅ Privacy-first design
- ✅ Real product (not a toy demo)

Perfect for 2025 software engineering interviews!

---

## 📄 License

MIT License - Feel free to use for your portfolio!

---

## 🤝 Contributing

This is a portfolio project, but contributions are welcome! Open an issue or PR.

---

**Built with ❤️ as a portfolio project**
