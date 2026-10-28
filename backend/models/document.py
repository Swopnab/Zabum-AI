import json
import re
from models.database import connection, get_one

def decode(row):
    if row is None: return None
    row = dict(row)
    for key in ('tags','embedding'):
        if key in row: row[key] = json.loads(row[key]) if row[key] else None
    return row

class DocumentModel:
    @staticmethod
    def create(filename,original_name,file_type,file_size,extracted_text,summary='',tags=None,category='document'):
        with connection() as db:
            row_id = db.execute('''INSERT INTO documents(filename,original_name,file_type,file_size,extracted_text,summary,tags,category)
                VALUES(?,?,?,?,?,?,?,?)''',(filename,original_name,file_type,file_size,extracted_text,summary,json.dumps(tags or []),category)).lastrowid
        return DocumentModel.get_by_id(row_id)
    @staticmethod
    def get_by_id(row_id): return decode(get_one('documents',row_id))
    @staticmethod
    def get_all(file_type=None):
        with connection() as db:
            rows = db.execute('SELECT * FROM documents WHERE file_type=? ORDER BY id DESC',(file_type,)) if file_type else db.execute('SELECT * FROM documents ORDER BY id DESC')
            return [decode(r) for r in rows]
    @staticmethod
    def delete(row_id):
        with connection() as db: db.execute('DELETE FROM documents WHERE id=?',(row_id,))

class DocumentChunkModel:
    @staticmethod
    def create(document_id,chunk_index,content,embedding=None):
        with connection() as db:
            row_id = db.execute('INSERT INTO document_chunks(document_id,chunk_index,content,embedding) VALUES(?,?,?,?)',
                (document_id,chunk_index,content,json.dumps(embedding) if embedding else None)).lastrowid
        return decode(get_one('document_chunks',row_id))
    @staticmethod
    def get_by_document(document_id):
        with connection() as db:
            return [decode(r) for r in db.execute('SELECT * FROM document_chunks WHERE document_id=? ORDER BY chunk_index',(document_id,))]
    @staticmethod
    def get_all_chunks_with_doc_meta():
        with connection() as db:
            return [decode(r) for r in db.execute('''SELECT c.id AS chunk_id,c.*,d.original_name,d.file_type,d.category
                FROM document_chunks c JOIN documents d ON d.id=c.document_id''')]
    @staticmethod
    def search_candidates(query,limit=100):
        tokens = list(dict.fromkeys(re.findall(r'\w+',query.lower())))[:32]
        if not tokens: return []
        expression = ' OR '.join('"'+token+'"' for token in tokens)
        with connection() as db:
            rows = db.execute('''SELECT c.id AS chunk_id,c.*,d.original_name,d.file_type,d.category
                FROM chunks_fts JOIN document_chunks c ON c.id=chunks_fts.rowid
                JOIN documents d ON d.id=c.document_id
                WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts),c.id LIMIT ?''',
                (expression,min(500,max(1,int(limit)))))
            return [decode(r) for r in rows]

def create_indexed_document(fields,chunks):
    """Commit metadata, chunks and FTS updates together, or roll everything back."""
    with connection() as db:
        document_id = db.execute('''INSERT INTO documents(filename,original_name,file_type,file_size,extracted_text,summary,tags,category)
            VALUES(?,?,?,?,?,?,?,?)''',tuple(fields[key] for key in ('filename','original_name','file_type','file_size','extracted_text','summary'))+
            (json.dumps(fields['tags']),fields['category'])).lastrowid
        db.executemany('INSERT INTO document_chunks(document_id,chunk_index,content,embedding,page_number) VALUES(?,?,?,?,?)',
            [(document_id,index,chunk[0],json.dumps(chunk[1]) if chunk[1] else None,chunk[2] if len(chunk)>2 else None) for index,chunk in enumerate(chunks)])
    return DocumentModel.get_by_id(document_id)
