"""
RAG Service - Retrieval-Augmented Generation for Personal Knowledge Base
Handles document processing, chunking, embedding generation, and hybrid similarity search.
"""

import os
import math
import re
from pathlib import Path
from config import CHUNK_SIZE, CHUNK_OVERLAP, MAX_RETRIEVED_CHUNKS, IMAGE_EXTENSIONS
from models.document import DocumentModel, DocumentChunkModel
from services.ai_provider import get_ai_provider
from services.ocr_service import get_ocr_service

class RAGService:
    """Service for managing personal knowledge base and RAG retrieval"""

    def __init__(self):
        self.ai_provider = get_ai_provider()
        self.ocr_service = get_ocr_service()

    def process_file(self, filepath: str, original_filename: str) -> dict:
        """
        Extract text from file, generate summary, chunk text, and index in database.
        
        Args:
            filepath: Absolute path to saved file
            original_filename: Original name of uploaded file
            
        Returns:
            dict: Created Document record
        """
        ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0

        # Step 1: Extract text
        file_type = "image" if ext in IMAGE_EXTENSIONS else ("pdf" if ext == "pdf" else "text")
        extracted_text = self._extract_text(filepath, ext)

        if not extracted_text or not extracted_text.strip():
            extracted_text = f"[Empty or unreadable content from {original_filename}]"

        # Step 2: Generate summary and tags
        summary, tags, category = self._analyze_content(extracted_text, original_filename, file_type)

        # Step 3: Save Document record
        doc = DocumentModel.create(
            filename=os.path.basename(filepath),
            original_name=original_filename,
            file_type=file_type,
            file_size=file_size,
            extracted_text=extracted_text,
            summary=summary,
            tags=tags,
            category=category
        )

        # Step 4: Chunk and Index
        chunks = self._chunk_text(extracted_text, CHUNK_SIZE, CHUNK_OVERLAP)
        for i, chunk in enumerate(chunks):
            # Try to get vector embedding from AI provider
            embedding = None
            try:
                embedding = self.ai_provider.get_embedding(chunk)
            except Exception:
                embedding = None
            
            DocumentChunkModel.create(
                document_id=doc["id"],
                chunk_index=i,
                content=chunk,
                embedding=embedding
            )

        return doc

    def _extract_text(self, filepath: str, ext: str) -> str:
        """Extract text depending on file extension"""
        if ext in IMAGE_EXTENSIONS:
            return self.ocr_service.extract_text(filepath)
        elif ext == "pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(filepath)
                text = "\n".join([page.extract_text() or "" for page in reader.pages])
                return text.strip()
            except Exception as e:
                return f"[PDF parsing error: {e}]"
        else:
            # Text / Code / Markdown
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    return f.read().strip()
            except Exception as e:
                return f"[File read error: {e}]"

    def _analyze_content(self, text: str, filename: str, file_type: str) -> tuple[str, list, str]:
        """Generate summary, tags, and category using AI provider or heuristics"""
        if len(text) < 15:
            return f"Uploaded file: {filename}", ["file", file_type], file_type

        prompt = f"""Analyze this content from file '{filename}' and respond ONLY with JSON:
{{"tags": ["3-5", "keywords"], "summary": "One sentence summary", "category": "document|code|screenshot|note|receipt|other"}}

Content excerpt:
{text[:1200]}

JSON:"""
        try:
            raw = self.ai_provider.generate(prompt, options={"temperature": 0.2})
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                import json
                data = json.loads(raw[start:end])
                tags = [str(t).lower().strip() for t in data.get("tags", [])][:5]
                summary = str(data.get("summary", "")).strip() or f"Content from {filename}"
                category = str(data.get("category", file_type)).strip()
                return summary, tags, category
        except Exception:
            pass

        # Heuristic fallback
        snippet = text[:150].replace("\n", " ")
        return f"Document: {filename} - {snippet}...", [file_type, "knowledge"], file_type

    def _chunk_text(self, text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
        """Split text into semantic/character chunks with overlap"""
        text = text.strip()
        if not text:
            return []
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            if end < len(text):
                # Try to break on newline or space
                break_point = text.rfind("\n", start + chunk_size // 2, end)
                if break_point == -1:
                    break_point = text.rfind(" ", start + chunk_size // 2, end)
                if break_point != -1:
                    end = break_point + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - overlap
            if start >= len(text) or end >= len(text):
                break

        return chunks

    def retrieve_relevant_chunks(self, query: str, top_k: int = MAX_RETRIEVED_CHUNKS) -> list[dict]:
        """
        Hybrid similarity search: Combines Cosine Vector Similarity (when embeddings exist)
        with BM25 / TF-IDF Keyword relevance scoring.
        """
        query = query.strip()
        if not query:
            return []

        all_chunks = DocumentChunkModel.get_all_chunks_with_doc_meta()
        if not all_chunks:
            return []

        # Get query embedding
        query_emb = None
        try:
            query_emb = self.ai_provider.get_embedding(query)
        except Exception:
            query_emb = None

        query_tokens = set(re.findall(r"\w+", query.lower()))

        scored_chunks = []
        for chunk in all_chunks:
            content = chunk.get("content", "")
            chunk_tokens = re.findall(r"\w+", content.lower())
            
            # 1. Vector similarity score
            vector_score = 0.0
            chunk_emb = chunk.get("embedding")
            if query_emb and chunk_emb and len(query_emb) == len(chunk_emb):
                vector_score = self._cosine_similarity(query_emb, chunk_emb)

            # 2. Keyword relevance score (token overlap & term frequency)
            keyword_score = 0.0
            if query_tokens and chunk_tokens:
                matches = sum(1 for t in chunk_tokens if t in query_tokens)
                keyword_score = matches / (math.sqrt(len(chunk_tokens)) + 1.0)

            # Hybrid combined score
            total_score = (vector_score * 0.7) + (keyword_score * 0.3) if vector_score > 0 else keyword_score

            if total_score > 0.08 or (matches if query_tokens and chunk_tokens else 0) > 0:
                scored_chunks.append({
                    "chunk_id": chunk["chunk_id"],
                    "document_id": chunk["document_id"],
                    "document_name": chunk["original_name"],
                    "file_type": chunk["file_type"],
                    "category": chunk["category"],
                    "content": content,
                    "score": round(total_score, 4)
                })

        # Sort by highest score descending
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]

    @staticmethod
    def _cosine_similarity(vec_a: list, vec_b: list) -> float:
        """Compute cosine similarity between two float vectors"""
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a, b in zip(vec_a, vec_b)))
        norm_b = math.sqrt(sum(b * b for a, b in zip(vec_a, vec_b)))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return max(0.0, min(1.0, dot / (norm_a * norm_b)))


_rag_service = None

def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
