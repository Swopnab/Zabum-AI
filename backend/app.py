"""
Zabum AI - Personal AI Assistant Backend
Local-first, privacy-focused conversational AI with persistent memory and RAG knowledge retrieval.
"""

import os
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from config import UPLOAD_FOLDER, THUMBNAIL_FOLDER, MAX_CONTENT_LENGTH
from models.database import init_db
from routes.chat import chat_bp
from routes.conversations import conversations_bp
from routes.memory import memory_bp
from routes.documents import documents_bp
from routes.status import status_bp

# Define frontend path
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

def create_app():
    """Application factory for Zabum AI Flask backend"""
    app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
    CORS(app)

    # Configuration
    app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
    app.config["THUMBNAIL_FOLDER"] = str(THUMBNAIL_FOLDER)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

    # Initialize Database Schema
    init_db()

    # Register Blueprints
    app.register_blueprint(status_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(conversations_bp)
    app.register_blueprint(memory_bp)
    app.register_blueprint(documents_bp)

    # Serve Frontend Single Page App
    @app.route("/app")
    @app.route("/chat")
    def serve_frontend():
        return send_from_directory(str(FRONTEND_DIR), "index.html")

    # Serve uploaded files if requested
    @app.route("/storage/uploads/<path:filename>")
    def serve_upload(filename):
        return send_from_directory(str(UPLOAD_FOLDER), filename)

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found_error(e):
        return jsonify({"error": "Endpoint or resource not found", "status_code": 404}), 404

    @app.errorhandler(413)
    def file_too_large_error(e):
        return jsonify({"error": "File size exceeds the 32MB maximum limit", "status_code": 413}), 413

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error occurred", "details": str(e), "status_code": 500}), 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    print("=" * 60)
    print("🧠 Zabum AI - Personal AI Assistant Backend")
    print(f"🚀 Server running on http://localhost:{port}")
    print(f"🌐 Chat App available at http://localhost:{port}/app")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=port)
