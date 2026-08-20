"""
Conversations API Route - Manage chat sessions and history
"""

from flask import Blueprint, request, jsonify
from models.conversation import ConversationModel, MessageModel

conversations_bp = Blueprint("conversations", __name__)

@conversations_bp.route("/api/conversations", methods=["GET"])
def list_conversations():
    convs = ConversationModel.get_all()
    return jsonify({"conversations": convs, "count": len(convs)})

@conversations_bp.route("/api/conversations", methods=["POST"])
def create_conversation():
    data = request.get_json(silent=True) or {}
    title = data.get("title", "New Chat").strip() or "New Chat"
    conv = ConversationModel.create(title)
    return jsonify({"success": True, "conversation": conv}), 201

@conversations_bp.route("/api/conversations/<int:conv_id>", methods=["GET"])
def get_conversation(conv_id):
    conv = ConversationModel.get_by_id(conv_id)
    if not conv:
        return jsonify({"error": "Conversation not found"}), 404
    messages = MessageModel.get_by_conversation(conv_id)
    return jsonify({
        "conversation": conv,
        "messages": messages,
        "message_count": len(messages)
    })

@conversations_bp.route("/api/conversations/<int:conv_id>", methods=["PUT"])
def update_conversation(conv_id):
    conv = ConversationModel.get_by_id(conv_id)
    if not conv:
        return jsonify({"error": "Conversation not found"}), 404
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "Title cannot be empty"}), 400
    updated = ConversationModel.update_title(conv_id, title)
    return jsonify({"success": True, "conversation": updated})

@conversations_bp.route("/api/conversations/<int:conv_id>", methods=["DELETE"])
def delete_conversation(conv_id):
    conv = ConversationModel.get_by_id(conv_id)
    if not conv:
        return jsonify({"error": "Conversation not found"}), 404
    ConversationModel.delete(conv_id)
    return jsonify({"success": True, "deleted_id": conv_id})
