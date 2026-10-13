import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Isolate even the module-level default application's storage from personal data.
_boot_storage = tempfile.TemporaryDirectory()
os.environ['ZABUM_STORAGE_DIR'] = _boot_storage.name
os.environ['AI_PROVIDER'] = 'mock'
from app import create_app
from models.database import connection, init_db
from models.conversation import ConversationModel, MessageModel
from models.document import DocumentModel, DocumentChunkModel, create_indexed_document
from services.ocr_service import OCRService
from services.rag_service import RAGService

class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app({'TESTING':True,'DB_PATH':str(Path(self.temp.name)/'test.db')})
        self.client = self.app.test_client()
    def tearDown(self): self.temp.cleanup()
    def upload(self,text,name='notes.txt'):
        return self.client.post('/api/documents/upload',data={'file':(io.BytesIO(text),name)})
    def test_existing_chunks_are_indexed_when_search_schema_is_added(self):
        self.upload(b'Existing CyberSteer keyboard documentation.')
        with self.app.app_context():
            with connection() as db:
                db.executescript('DROP TRIGGER chunks_insert; DROP TRIGGER chunks_delete; DROP TRIGGER chunks_update; DROP TABLE chunks_fts;')
            init_db()
            self.assertEqual(len(DocumentChunkModel.search_candidates('CyberSteer')), 1)
            init_db()
            self.assertEqual(len(DocumentChunkModel.search_candidates('CyberSteer')), 1)
    def test_clean_start_and_mock_chat_persistence(self):
        status = self.client.get('/api/status').get_json()
        self.assertEqual(status['stats'],{'conversations':0,'memories':0,'documents':0})
        self.assertEqual(status['ai_provider']['name'],'MockProvider')
        first = self.client.post('/api/chat',json={'message':'Remember that I prefer Python'}).get_json()
        self.assertEqual(len(first['memories_created']),1)
        conv = first['conversation_id']
        self.client.post('/api/chat',json={'conversation_id':conv,'message':'What do I prefer?'})
        restarted = create_app({'TESTING':True,'DB_PATH':self.app.config['DB_PATH']}).test_client()
        history = restarted.get(f'/api/conversations/{conv}').get_json()
        self.assertEqual(history['message_count'],4)
        self.assertEqual([m['role'] for m in history['messages']],['user','assistant','user','assistant'])
        self.assertEqual(self.client.post('/api/chat',json={'message':'   '}).status_code,400)
    def test_conversation_rename_and_delete_cascade(self):
        conv = self.client.post('/api/conversations',json={'title':'A'}).get_json()['conversation']['id']
        with self.app.app_context(): MessageModel.create(conv,'user','hello')
        self.assertEqual(self.client.put(f'/api/conversations/{conv}',json={'title':'B'}).get_json()['conversation']['title'],'B')
        self.assertEqual(self.client.delete(f'/api/conversations/{conv}').status_code,200)
        self.assertEqual(self.client.get(f'/api/conversations/{conv}').status_code,404)
        with self.app.app_context(): self.assertEqual(MessageModel.count_by_conversation(conv),0)
    def test_recent_history_is_chronological_and_foreign_keys_are_enforced(self):
        with self.app.app_context():
            conv = ConversationModel.create('History')
            for i in range(6): MessageModel.create(conv['id'],'user',str(i),sources=[{'document_name':'source'}])
            self.assertEqual([m['content'] for m in MessageModel.get_by_conversation(conv['id'],limit=3)],['3','4','5'])
            self.assertEqual(MessageModel.get_by_conversation(conv['id'],limit=0),[])
            with self.assertRaises(Exception): MessageModel.create(9999,'user','orphan')
    def test_memory_crud_and_literal_search(self):
        memory = self.client.post('/api/memories',json={'content':'use variable_a','category':'code'}).get_json()['memory']
        self.assertEqual(self.client.get('/api/memories?q=variable_').get_json()['count'],1)
        self.assertEqual(self.client.get('/api/memories?q=%25').get_json()['count'],0)
        self.assertEqual(self.client.put(f"/api/memories/{memory['id']}",json={'content':'updated'}).status_code,200)
        self.assertEqual(self.client.delete(f"/api/memories/{memory['id']}").status_code,200)
        self.assertEqual(self.client.get('/api/memories').get_json()['count'],0)
    def test_document_retrieval_sources_and_delete_remove_fts_records(self):
        uploaded = self.upload(b'CyberSteer controls use keyboard arrows and hand tracking.').get_json()['document']
        self.assertIsInstance(uploaded['tags'],list)
        with self.app.app_context():
            chunks = RAGService().retrieve_relevant_chunks('CyberSteer keyboard')
            self.assertEqual(chunks[0]['document_name'],'notes.txt')
            self.assertEqual(chunks[0]['document_id'],uploaded['id'])
            self.assertEqual(DocumentChunkModel.search_candidates('" OR * --'),[])
        chat = self.client.post('/api/chat',json={'message':'CyberSteer controls'}).get_json()
        self.assertEqual(chat['sources'][0]['document_name'],'notes.txt')
        self.assertEqual(self.client.delete(f"/api/documents/{uploaded['id']}").status_code,200)
        with self.app.app_context():
            self.assertEqual(DocumentChunkModel.search_candidates('CyberSteer'),[])
            self.assertEqual(DocumentChunkModel.get_by_document(uploaded['id']),[])
    def test_failed_ocr_and_empty_or_invalid_documents_are_not_indexed(self):
        failing = OCRService(); failing._load_error = 'Unavailable during test'
        with patch('services.rag_service.get_ocr_service',return_value=failing), patch('routes.documents.get_rag_service',side_effect=RAGService):
            response = self.upload(b'not a real image','screen.png')
        self.assertEqual(response.status_code,503)
        self.assertNotIn('OCR Processed',response.get_data(as_text=True))
        self.assertEqual(self.upload(b'  ').status_code,422)
        self.assertEqual(self.upload(b'not PDF','bad.pdf').status_code,422)
        self.assertEqual(self.upload(b'executable','bad.exe').status_code,400)
        self.assertEqual(self.client.get('/api/documents').get_json()['count'],0)
    def test_indexing_transaction_rolls_back_metadata_when_a_chunk_fails(self):
        with self.app.app_context():
            fields={'filename':'x.txt','original_name':'x.txt','file_type':'text','file_size':1,'extracted_text':'x','summary':'x','tags':[],'category':'text'}
            # A second chunk violates the existing non-null constraint.
            with self.assertRaises(Exception): create_indexed_document(fields,[('valid',None),(None,None)])
            self.assertEqual(DocumentModel.get_all(),[])
            self.assertEqual(DocumentChunkModel.search_candidates('valid'),[])
    def test_candidate_budget_and_chunking_rejects_nonprogressing_overlap(self):
        with self.app.app_context():
            doc = DocumentModel.create('x.txt','x.txt','text',100,'shared')
            for i in range(125): DocumentChunkModel.create(doc['id'],i,f'shared topic {i}')
            self.assertEqual(len(DocumentChunkModel.search_candidates('shared')),100)
        with self.assertRaises(ValueError): RAGService()._chunk_text('long text',4,4)
        self.assertEqual(RAGService().retrieve_relevant_chunks('   '),[])

if __name__ == '__main__': unittest.main()
