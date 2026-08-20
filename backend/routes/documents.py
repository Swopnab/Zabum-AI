"""
Documents API Route - Knowledge Base Ingestion and Management
Handles screenshot uploads, OCR processing, text file ingestion, and RAG chunk inspection.
"""

from flask import Blueprint, request, jsonify
import os
import uuid
from werkzeug.utils import secure_filename
from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS
from models.document import DocumentModel, DocumentChunkModel
from services.rag_service import get_rag_service

documents_bp = Blueprint("documents", __name__)

def is_allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@documents_bp.route("/api/documents/upload", methods=["POST"])
@documents_bp.route("/api/process", methods=["POST"])  # Backward compatibility
def upload_document():
    """
    Upload and index document or screenshot.
    Accepts: multipart/form-data with 'file' or 'image'
    """
    file = request.files.get("file") or request.files.get("image")
    if not file or file.filename == "":
        return jsonify({"error": "No file uploaded"}), 400

    if not is_allowed_file(file.filename):
        return jsonify({
            "error": f"Unsupported file type. Supported types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        }), 400

    try:
        orig_name = secure_filename(file.filename) or file.filename
        ext = orig_name.rsplit(".", 1)[-1].lower() if "." in orig_name else ""
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(str(UPLOAD_FOLDER), unique_name)
        
        file.save(filepath)

        # Process with RAG service (OCR if image, text extraction, chunking, embedding)
        rag_service = get_rag_service()
        doc = rag_service.process_file(filepath, orig_name)

        return jsonify({
            "success": True,
            "document": doc,
            # Legacy compatibility fields
            "id": doc["id"],
            "filename": doc["filename"],
            "extracted_text": doc["extracted_text"],
            "tags": doc["tags"],
            "summary": doc["summary"],
            "category": doc["category"],
            "created_at": doc["created_at"]
        }), 201

    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500


@documents_bp.route("/api/documents", methods=["GET"])
@documents_bp.route("/api/images", methods=["GET"])  # Legacy compatibility
def list_documents():
    file_type = request.args.get("type")
    docs = DocumentModel.get_all(file_type=file_type)
    return jsonify({
        "documents": docs,
        "images": docs,  # Legacy compatibility
        "count": len(docs)
    })


@documents_bp.route("/api/documents/<int:doc_id>", methods=["GET"])
def get_document(doc_id):
    doc = DocumentModel.get_by_id(doc_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404
    return jsonify({"document": doc})


@documents_bp.route("/api/documents/<int:doc_id>/chunks", methods=["GET"])
def get_document_chunks(doc_id):
    doc = DocumentModel.get_by_id(doc_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404
    chunks = DocumentChunkModel.get_by_document(doc_id)
    return jsonify({"document": doc, "chunks": chunks, "count": len(chunks)})


@documents_bp.route("/api/documents/<int:doc_id>", methods=["DELETE"])
def delete_document(doc_id):
    doc = DocumentModel.get_by_id(doc_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404

    # Remove file from disk if present
    try:
        fpath = os.path.join(str(UPLOAD_FOLDER), doc["filename"])
        if os.path.exists(fpath):
            os.remove(fpath)
    except Exception:
        pass

    DocumentModel.delete(doc_id)
    return jsonify({"success": True, "deleted_id": doc_id})
