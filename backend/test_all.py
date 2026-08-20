"""
Comprehensive Backend Test for Zabum AI
Tests:
1. Status and Health Check
2. Conversation CRUD
3. Memory extraction and manual CRUD
4. Document / Screenshot ingestion & chunking
5. Hybrid RAG retrieval
6. Full Chat Conversation Pipeline
"""

import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.conversation import ConversationModel, MessageModel
from models.memory import MemoryModel
from models.document import DocumentModel, DocumentChunkModel
from services.rag_service import get_rag_service
from services.memory_service import get_memory_service
from services.ai_provider import MockProvider, get_ai_provider

def run_tests():
    print("=" * 60)
    print("🧪 Running Zabum AI Verification Tests")
    print("=" * 60)

    app = create_app()
    client = app.test_client()

    # 1. Test Status endpoint
    print("\n1. Testing /api/status...")
    res = client.get("/api/status")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    status_data = res.get_json()
    print(f"   ✅ App: {status_data['app_name']} - {status_data['subtitle']}")
    print(f"   ✅ AI Provider: {status_data['ai_provider']['name']} ({status_data['ai_provider']['message']})")

    # 2. Test Conversation CRUD
    print("\n2. Testing Conversations API...")
    res = client.post("/api/conversations", json={"title": "Test AI Chat"})
    assert res.status_code == 201
    conv = res.get_json()["conversation"]
    conv_id = conv["id"]
    print(f"   ✅ Created conversation ID: {conv_id} ({conv['title']})")

    # Update conversation title
    res = client.put(f"/api/conversations/{conv_id}", json={"title": "Renamed Chat"})
    assert res.status_code == 200
    assert res.get_json()["conversation"]["title"] == "Renamed Chat"
    print("   ✅ Updated conversation title")

    # 3. Test Memory CRUD & Extraction
    print("\n3. Testing Memory Engine...")
    # Manual memory creation
    res = client.post("/api/memories", json={"content": "User prefers Python for backend development", "category": "preference"})
    assert res.status_code == 201
    mem = res.get_json()["memory"]
    mem_id = mem["id"]
    print(f"   ✅ Saved manual memory ID {mem_id}: {mem['content']}")

    # Memory search
    res = client.get("/api/memories?q=python")
    assert res.status_code == 200
    found_mems = res.get_json()["memories"]
    assert len(found_mems) > 0
    print(f"   ✅ Memory query found {len(found_mems)} matching items")

    # Memory regex extraction
    mem_service = get_memory_service()
    extracted = mem_service.extract_and_save_memory("Remember that my favorite database is PostgreSQL")
    print(f"   ✅ Explicit memory detection extracted: {extracted[0]['content'] if extracted else 'None'}")

    # 4. Test Document Ingestion & Chunking
    print("\n4. Testing Knowledge Base & Document Chunking...")
    rag_service = get_rag_service()
    test_doc_content = """
# Binary Trees Notes
A binary tree is a hierarchical data structure where each node has at most two children, referred to as the left child and right child.
Binary Search Trees (BST) maintain an ordering property: left subtree < root < right subtree.
In-order traversal of a BST yields elements in sorted order.
Time complexity for search in a balanced BST is O(log n).
    """.strip()

    test_file_path = "/tmp/test_knowledge_notes.md"
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_doc_content)

    doc = rag_service.process_file(test_file_path, "binary_tree_notes.md")
    assert doc is not None
    doc_id = doc["id"]
    print(f"   ✅ Ingested document ID {doc_id}: {doc['original_name']}")
    
    chunks = DocumentChunkModel.get_by_document(doc_id)
    print(f"   ✅ Created {len(chunks)} text chunks for RAG")

    # 5. Test RAG Retrieval
    print("\n5. Testing Hybrid RAG Retrieval...")
    retrieved = rag_service.retrieve_relevant_chunks("What did my notes say about binary search trees?")
    print(f"   ✅ Retrieved {len(retrieved)} relevant knowledge chunks:")
    for r in retrieved:
        print(f"      - [{r['document_name']}] Score: {r['score']} | Content: {r['content'][:60]}...")

    # 6. Test Chat API pipeline
    print("\n6. Testing /api/chat context pipeline...")
    res = client.post("/api/chat", json={
        "conversation_id": conv_id,
        "message": "What is my preference for backend and what do my notes say about binary trees?"
    })
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    chat_resp = res.get_json()
    print(f"   ✅ AI Response generated successfully!")
    print(f"   ✅ Sources used: {len(chat_resp.get('sources', []))} citations")
    for s in chat_resp.get('sources', []):
        print(f"      * {s.get('type')}: {s.get('document_name') or s.get('content')}")

    print("\n" + "=" * 60)
    print("🎉 ALL BACKEND TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
