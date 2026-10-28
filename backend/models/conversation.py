import json
from models.database import connection, get_one

class ConversationModel:
    @staticmethod
    def create(title='New Chat'):
        with connection() as db:
            row_id = db.execute('INSERT INTO conversations(title) VALUES(?)',(title,)).lastrowid
        return ConversationModel.get_by_id(row_id)
    @staticmethod
    def get_by_id(row_id): return get_one('conversations',row_id)
    @staticmethod
    def get_all():
        with connection() as db:
            return [dict(r) for r in db.execute('SELECT * FROM conversations ORDER BY updated_at DESC,id DESC')]
    @staticmethod
    def update_title(row_id,title):
        with connection() as db:
            db.execute("UPDATE conversations SET title=?,updated_at=datetime('now') WHERE id=?",(title,row_id))
        return ConversationModel.get_by_id(row_id)
    @staticmethod
    def delete(row_id):
        with connection() as db: db.execute('DELETE FROM conversations WHERE id=?',(row_id,))

class MessageModel:
    @staticmethod
    def create(conversation_id,role,content,sources=None):
        with connection() as db:
            row_id = db.execute('INSERT INTO messages(conversation_id,role,content,sources) VALUES(?,?,?,?)',
                (conversation_id,role,content,json.dumps(sources or []))).lastrowid
        row = get_one('messages',row_id); row['sources'] = json.loads(row['sources']); return row
    @staticmethod
    def get_by_conversation(conversation_id,limit=None):
        with connection() as db:
            if limit is None:
                rows = db.execute('SELECT * FROM messages WHERE conversation_id=? ORDER BY id',(conversation_id,)).fetchall()
            else:
                rows = list(reversed(db.execute('SELECT * FROM messages WHERE conversation_id=? ORDER BY id DESC LIMIT ?',
                    (conversation_id,max(0,int(limit)))).fetchall()))
        result = [dict(r) for r in rows]
        for row in result: row['sources'] = json.loads(row['sources'])
        return result
    @staticmethod
    def count_by_conversation(conversation_id):
        with connection() as db:
            return db.execute('SELECT count(*) FROM messages WHERE conversation_id=?',(conversation_id,)).fetchone()[0]
