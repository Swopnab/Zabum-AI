"""
Chat API Route - Core Conversation Context Pipeline for Zabum AI
"""

from flask import Blueprint, request, jsonify
from config import SYSTEM_PROMPT, MAX_RECENT_MESSAGES
from models.conversation import ConversationModel, MessageModel
from services.ai_provider import get_ai_provider
from services.memory_service import get_memory_service
from services.rag_service import get_rag_service

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    """
    Main Chat Endpoint
    Request: { "conversation_id": 1 (optional), "message": "..." }
    """
    data = request.get_json(silent=True) or {}
    user_text = data.get("message", "").strip()
    conv_id = data.get("conversation_id")

    if not user_text:
        return jsonify({"error": "Message cannot be empty"}), 400

    # 1. Get or create conversation
    if not conv_id:
        conv = ConversationModel.create("New Chat")
        conv_id = conv["id"]
        is_new_conv = True
    else:
        conv = ConversationModel.get_by_id(conv_id)
        if not conv:
            conv = ConversationModel.create("New Chat")
            conv_id = conv["id"]
            is_new_conv = True
        else:
            is_new_conv = MessageModel.count_by_conversation(conv_id) == 0

    # 2. Extract explicit memories from user message
    memory_service = get_memory_service()
    newly_saved_memories = memory_service.extract_and_save_memory(user_text)

    # 3. Retrieve relevant personal memories
    relevant_memories = memory_service.get_relevant_memories(user_text)

    # 4. Retrieve relevant knowledge base chunks (RAG)
    rag_service = get_rag_service()
    relevant_chunks = rag_service.retrieve_relevant_chunks(user_text)

    # 5. Build System / Context Instructions
    context_sections = [SYSTEM_PROMPT]

    # Add memories section if present
    if relevant_memories:
        mem_lines = ["\n[SAVED USER MEMORIES & PREFERENCES]:"]
        for m in relevant_memories:
            mem_lines.append(f"- ({m.get('category', 'general')}) {m['content']}")
        context_sections.append("\n".join(mem_lines))

    # Add knowledge base chunks section if present
    sources_for_response = []
    if relevant_chunks:
        chunk_lines = ["\n[RETRIEVED PERSONAL KNOWLEDGE & SCREENSHOTS]:"]
        for c in relevant_chunks:
            source_tag = f"File: {c['document_name']}"
            chunk_lines.append(f"--- Document Source: {source_tag} ---\n{c['content']}")
            sources_for_response.append({
                "type": "document",
                "document_name": c["document_name"],
                "file_type": c.get("file_type", "document"),
                "content_preview": c["content"][:160] + "..." if len(c["content"]) > 160 else c["content"],
                "score": c["score"]
            })
        context_sections.append("\n".join(chunk_lines))

    if newly_saved_memories:
        for m in newly_saved_memories:
            sources_for_response.append({
                "type": "new_memory",
                "content": m["content"]
            })

    # Assemble messages array for LLM
    final_system_instruction = "\n\n".join(context_sections)

    # 6. Retrieve recent conversation turns
    recent_history = MessageModel.get_by_conversation(conv_id, limit=MAX_RECENT_MESSAGES)

    llm_messages = [{"role": "system", "content": final_system_instruction}]
    for msg in recent_history:
        llm_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    # Add current user message
    llm_messages.append({"role": "user", "content": user_text})

    # Save user message to database
    user_msg_record = MessageModel.create(conv_id, "user", user_text)

    # 7. Generate response from AI provider
    ai_provider = get_ai_provider()
    try:
        assistant_reply = ai_provider.chat(llm_messages)
    except Exception as e:
        error_msg = str(e)
        assistant_reply = f"⚠️ **Zabum AI encountered an issue:**\n\n{error_msg}\n\n*If Ollama is not running, start it with `ollama serve` and ensure model `llama3.2` is pulled.*"

    # 8. Save assistant reply to database
    assistant_msg_record = MessageModel.create(
        conv_id,
        "assistant",
        assistant_reply,
        sources=sources_for_response
    )

    # 9. Auto-generate title if this is a new conversation
    current_conv = ConversationModel.get_by_id(conv_id)
    if is_new_conv or current_conv.get("title") == "New Chat":
        try:
            title_prompt = f"Summarize this initial user message into a concise 3 to 5 word title for a chat conversation. Do not use quotes or punctuation.\n\nMessage: {user_text}\n\nTitle:"
            gen_title = ai_provider.generate(title_prompt, options={"temperature": 0.2})
            clean_title = gen_title.strip().strip('"\'').split("\n")[0][:40].strip()
            if clean_title and len(clean_title) > 2:
                ConversationModel.update_title(conv_id, clean_title)
                current_conv["title"] = clean_title
        except Exception:
            # Fallback title from user message
            clean_title = user_text[:30] + ("..." if len(user_text) > 30 else "")
            ConversationModel.update_title(conv_id, clean_title)
            current_conv["title"] = clean_title

    return jsonify({
        "conversation_id": conv_id,
        "conversation_title": current_conv.get("title", "New Chat"),
        "user_message": user_msg_record,
        "assistant_message": assistant_msg_record,
        "sources": sources_for_response,
        "memories_created": newly_saved_memories
    })
