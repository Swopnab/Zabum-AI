"""
Memory API Route - User memory management and inspection
"""

from flask import Blueprint, request, jsonify
from models.memory import MemoryModel
from models.database import connection

memory_bp = Blueprint("memory", __name__)

def memory_enabled():
    with connection() as db:
        row = db.execute("SELECT value FROM preferences WHERE key='memory_enabled'").fetchone()
    return row is None or row[0] == 'true'

@memory_bp.route('/api/preferences', methods=['GET', 'PUT'])
def preferences():
    if request.method == 'PUT':
        value = (request.get_json(silent=True) or {}).get('memory_enabled')
        if not isinstance(value, bool):
            return jsonify({'error': 'memory_enabled must be a boolean'}), 400
        with connection() as db:
            db.execute("INSERT INTO preferences(key,value) VALUES('memory_enabled',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", ('true' if value else 'false',))
    return jsonify({'memory_enabled': memory_enabled()})

@memory_bp.route("/api/memories", methods=["GET"])
def list_memories():
    category = request.args.get("category")
    search = request.args.get("q")
    memories = MemoryModel.get_all(category=category, search=search)
    return jsonify({"memories": memories, "count": len(memories)})

@memory_bp.route("/api/memories", methods=["POST"])
def create_memory():
    data = request.get_json(silent=True) or {}
    content = data.get("content", "").strip()
    category = data.get("category", "general").strip()

    if not content:
        return jsonify({"error": "Memory content cannot be empty"}), 400

    mem = MemoryModel.create(content, category=category)
    return jsonify({"success": True, "memory": mem}), 201

@memory_bp.route("/api/memories/<int:mem_id>", methods=["PUT"])
def update_memory(mem_id):
    mem = MemoryModel.get_by_id(mem_id)
    if not mem:
        return jsonify({"error": "Memory not found"}), 404

    data = request.get_json(silent=True) or {}
    content = data.get("content", "").strip()
    category = data.get("category")

    if not content:
        return jsonify({"error": "Content cannot be empty"}), 400

    updated = MemoryModel.update(mem_id, content, category)
    return jsonify({"success": True, "memory": updated})

@memory_bp.route("/api/memories/<int:mem_id>", methods=["DELETE"])
def delete_memory(mem_id):
    mem = MemoryModel.get_by_id(mem_id)
    if not mem:
        return jsonify({"error": "Memory not found"}), 404

    MemoryModel.delete(mem_id)
    return jsonify({"success": True, "deleted_id": mem_id})
