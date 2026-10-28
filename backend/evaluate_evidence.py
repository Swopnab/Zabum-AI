"""Offline, deterministic passage/abstention evaluation. No LLM or OCR accuracy claim."""
import json, os, tempfile, statistics
from pathlib import Path
from time import perf_counter
root=Path(__file__).resolve().parents[1]
fixture=json.loads((root/'evaluation/retrieval_cases.json').read_text())
# Known supported passages are literal fixture document text; negative questions ask absent facts.
queries=fixture['queries']+[{'query':'library director phone number','expected':None},{'query':'parking permit costs','expected':None}]
with tempfile.TemporaryDirectory() as folder:
    os.environ['ZABUM_STORAGE_DIR']=folder;os.environ['AI_PROVIDER']='mock'
    from app import create_app
    from services.rag_service import RAGService
    from services.evidence import supported_passages
    app=create_app({'DB_PATH':str(Path(folder)/'evaluation.db')})
    client=app.test_client()
    import io
    for doc in fixture['documents']:
        client.post('/api/documents/upload',data={'file':(io.BytesIO(doc['text'].encode()),doc['name'])})
    times=[];rows=[]
    with app.app_context():
        for case in queries:
            selected=[]
            for _ in range(20):
                start=perf_counter();selected=supported_passages(case['query'],RAGService().retrieve_relevant_chunks(case['query']));times.append((perf_counter()-start)*1000)
            names=[s['document_name'] for s in selected]
            expected=case['expected']
            passage=next((d['text'] for d in fixture['documents'] if d['name']==expected),None)
            rows.append({**case,'known_supporting_passage':passage,'selected_documents':names,'abstained':not selected,'known_passage_found':bool(passage and any(s['content']==passage for s in selected))})
    positive=[r for r in rows if r['expected']];negative=[r for r in rows if not r['expected']];times.sort()
    report={'fixture':'5 short fictional text documents, 5 answerable and 3 unanswerable questions; mock provider; lexical gate; no paraphrase/semantic entailment, LLM quality, or OCR evaluation','repetitions_per_question':20,'answerable_passage_recall':sum(r['known_passage_found'] for r in positive)/len(positive),'unanswerable_abstention_rate':sum(r['abstained'] for r in negative)/len(negative),'p50_retrieve_and_gate_ms':statistics.median(times),'p95_retrieve_and_gate_ms':times[int(.95*(len(times)-1))],'cases':rows}
print(json.dumps(report,indent=2))
