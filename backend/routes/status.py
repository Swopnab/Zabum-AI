"""
Status & Health API Route
"""

from flask import Blueprint, jsonify, current_app
import os
import tempfile
from pathlib import Path
from datetime import datetime
from services.ai_provider import get_ai_provider
from models.conversation import ConversationModel
from models.memory import MemoryModel
from models.document import DocumentModel

status_bp = Blueprint("status", __name__)

@status_bp.route("/api/status", methods=["GET"])
@status_bp.route("/", methods=["GET"])
def system_status():
    provider = get_ai_provider()
    is_avail, provider_msg = provider.is_available()

    conv_count = len(ConversationModel.get_all())
    mem_count = len(MemoryModel.get_all())
    doc_count = len(DocumentModel.get_all())

    return jsonify({
        "status": "online",
        "review_fixture": os.getenv("ZABUM_REVIEW_FIXTURE") == "1" and provider.__class__.__name__ == "MockProvider" and any(Path(current_app.config["DB_PATH"]).resolve().is_relative_to(root.resolve()) for root in (Path("/tmp"), Path(tempfile.gettempdir()))),
        "app_name": "Zabum AI",
        "subtitle": "Personal AI Assistant",
        "version": "1.0.0",
        "ai_provider": {
            "name": provider.__class__.__name__,
            "available": is_avail,
            "message": provider_msg
        },
        "stats": {
            "conversations": conv_count,
            "memories": mem_count,
            "documents": doc_count
        },
        "timestamp": datetime.now().isoformat()
    })
