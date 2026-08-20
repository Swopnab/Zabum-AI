"""
Memory Service - Personal Memory Engine for Zabum AI
Handles persistent memory extraction, relevance scoring, and contextual injection.
"""

import re
from config import MAX_RETRIEVED_MEMORIES
from models.memory import MemoryModel
from services.ai_provider import get_ai_provider

class MemoryService:
    """Service for managing personal assistant memories"""

    def __init__(self):
        self.ai_provider = get_ai_provider()

    def get_relevant_memories(self, query: str, limit: int = MAX_RETRIEVED_MEMORIES) -> list[dict]:
        """
        Find user memories most relevant to the current conversation query.
        Returns top matches or recent general preferences.
        """
        all_memories = MemoryModel.get_all()
        if not all_memories:
            return []

        query_tokens = set(re.findall(r"\w+", query.lower()))
        # Remove common stop words for matching
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "what", "how", "why", "to", "in", "of", "and", "or", "for", "me", "my", "i", "do", "you"}
        meaningful_tokens = query_tokens - stop_words

        scored = []
        for mem in all_memories:
            content = mem["content"].lower()
            mem_tokens = set(re.findall(r"\w+", content))
            
            matches = len(meaningful_tokens.intersection(mem_tokens)) if meaningful_tokens else 0
            category_boost = 1 if mem.get("category") in ["preference", "profile", "identity"] else 0
            
            score = matches * 2 + category_boost
            scored.append({
                "id": mem["id"],
                "content": mem["content"],
                "category": mem["category"],
                "score": score
            })

        # Sort by score descending
        scored.sort(key=lambda x: x["score"], reverse=True)
        # Return top matches with positive score, or top general preferences if no specific match
        top = [m for m in scored if m["score"] > 0]
        if not top:
            top = scored[:limit]
        return top[:limit]

    def extract_and_save_memory(self, user_message: str) -> list[dict]:
        """
        Detects if the user is asking the assistant to remember something,
        extracts the persistent statement, and stores it in SQLite.
        """
        text = user_message.strip()
        saved = []

        # 1. Regex pattern detection for explicit memory requests
        explicit_patterns = [
            (r"(?:please\s+)?remember\s+that\s+(.*)", "preference"),
            (r"(?:please\s+)?remember[:\s]+(.*)", "preference"),
            (r"(?:keep\s+in\s+mind\s+that\s+)(.*)", "preference"),
            (r"(?:note\s+that\s+)(.*)", "fact"),
            (r"(?:don'?t\s+forget\s+that\s+)(.*)", "preference"),
            (r"^(?:my\s+name\s+is\s+)(.*)", "identity"),
            (r"^(?:i\s+prefer\s+)(.*)", "preference"),
        ]

        matched_content = None
        category = "general"

        for pattern, cat in explicit_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                matched_content = match.group(1).strip().rstrip(".!?,")
                category = cat
                break

        if matched_content and len(matched_content) > 3:
            # Format clean memory statement
            if not matched_content.lower().startswith("user") and not matched_content.lower().startswith("i "):
                clean_content = f"User preference: {matched_content}"
            elif matched_content.lower().startswith("i "):
                clean_content = f"User {matched_content[2:]}"
            else:
                clean_content = matched_content

            if not MemoryModel.exists_similar(clean_content):
                mem = MemoryModel.create(clean_content, category=category)
                saved.append(mem)
                return saved

        return saved


_memory_service = None

def get_memory_service() -> MemoryService:
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
