"""Short-lived, transactional SQLite connections with foreign-key enforcement."""
import sqlite3
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path
from flask import current_app, has_app_context
from config import DB_PATH

@contextmanager
def connection():
    path = Path(current_app.config.get('DB_PATH', DB_PATH) if has_app_context() else DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        with db:
            yield db
    finally:
        db.close()

def init_db():
    with connection() as db:
        existing = {r[1] for r in db.execute('PRAGMA table_info(document_chunks)')}
        if existing and 'page_number' not in existing:
            # Snapshot before the additive migration; IDs and old chunks stay intact.
            path = db.execute('PRAGMA database_list').fetchone()[2]
            backup = sqlite3.connect(path + '.before-sources-' + datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f') + '.bak')
            try:
                db.backup(backup)
            finally:
                backup.close()
            db.execute('ALTER TABLE document_chunks ADD COLUMN page_number INTEGER')
        had_search_index = db.execute("SELECT 1 FROM sqlite_master WHERE name='chunks_fts'").fetchone() is not None
        db.executescript('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY, title TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY, conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            role TEXT NOT NULL CHECK(role IN ('user','assistant','system')), content TEXT NOT NULL,
            sources TEXT NOT NULL DEFAULT '[]', created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id,id);
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY, content TEXT NOT NULL, category TEXT NOT NULL DEFAULT 'general',
            created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY, filename TEXT NOT NULL, original_name TEXT NOT NULL,
            file_type TEXT NOT NULL, file_size INTEGER NOT NULL, extracted_text TEXT NOT NULL,
            summary TEXT NOT NULL DEFAULT '', tags TEXT NOT NULL DEFAULT '[]', category TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS document_chunks (
            id INTEGER PRIMARY KEY, document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL, content TEXT NOT NULL, embedding TEXT,
            UNIQUE(document_id,chunk_index)
        );
        CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks(document_id,chunk_index);
        CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(content,content='document_chunks',content_rowid='id');
        CREATE TRIGGER IF NOT EXISTS chunks_insert AFTER INSERT ON document_chunks BEGIN
            INSERT INTO chunks_fts(rowid,content) VALUES(new.id,new.content);
        END;
        CREATE TRIGGER IF NOT EXISTS chunks_delete AFTER DELETE ON document_chunks BEGIN
            INSERT INTO chunks_fts(chunks_fts,rowid,content) VALUES('delete',old.id,old.content);
        END;
        CREATE TRIGGER IF NOT EXISTS chunks_update AFTER UPDATE OF content ON document_chunks BEGIN
            INSERT INTO chunks_fts(chunks_fts,rowid,content) VALUES('delete',old.id,old.content);
            INSERT INTO chunks_fts(rowid,content) VALUES(new.id,new.content);
        END;
        ''')
        if not had_search_index:
            # Index documents already present when upgrading an existing database.
            db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
        if not existing:
            db.execute('ALTER TABLE document_chunks ADD COLUMN page_number INTEGER')

def get_one(table, row_id):
    # Only fixed internal table names call this helper.
    with connection() as db:
        row = db.execute(f'SELECT * FROM {table} WHERE id=?',(row_id,)).fetchone()
        return dict(row) if row else None
