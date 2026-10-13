from models.database import connection, get_one

class MemoryModel:
    @staticmethod
    def create(content,category='general'):
        with connection() as db:
            row_id = db.execute('INSERT INTO memories(content,category) VALUES(?,?)',(content,category)).lastrowid
        return MemoryModel.get_by_id(row_id)
    @staticmethod
    def get_by_id(row_id): return get_one('memories',row_id)
    @staticmethod
    def get_all(category=None,search=None):
        sql,values = 'SELECT * FROM memories WHERE 1=1',[]
        if category: sql += ' AND category=?'; values.append(category)
        if search:
            sql += " AND content LIKE ? ESCAPE '\\'"
            values.append('%'+search.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%')
        with connection() as db:
            return [dict(r) for r in db.execute(sql+' ORDER BY id DESC',values)]
    @staticmethod
    def update(row_id,content,category=None):
        with connection() as db:
            db.execute("UPDATE memories SET content=?,category=COALESCE(?,category),updated_at=datetime('now') WHERE id=?",(content,category,row_id))
        return MemoryModel.get_by_id(row_id)
    @staticmethod
    def exists_similar(content):
        with connection() as db:
            return db.execute('SELECT 1 FROM memories WHERE lower(trim(content))=lower(trim(?))',(content,)).fetchone() is not None
    @staticmethod
    def delete(row_id):
        with connection() as db: db.execute('DELETE FROM memories WHERE id=?',(row_id,))
