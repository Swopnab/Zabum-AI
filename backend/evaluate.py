"""Compare indexed retrieval with the previous full-scan keyword baseline."""
import argparse
import json
import math
import os
import platform
import re
import statistics
import tempfile
from pathlib import Path
from time import perf_counter

def evaluate(size=1000,iterations=20):
    root=Path(__file__).resolve().parents[1]
    fixture=json.loads((root/'evaluation/retrieval_cases.json').read_text())
    with tempfile.TemporaryDirectory() as folder:
        os.environ['ZABUM_STORAGE_DIR']=folder;os.environ['AI_PROVIDER']='mock'
        from app import create_app
        from models.document import create_indexed_document,DocumentChunkModel
        from services.rag_service import RAGService
        app=create_app({'DB_PATH':str(Path(folder)/'evaluation.db')})
        with app.app_context():
            for doc in fixture['documents']:
                create_indexed_document({'filename':doc['name'],'original_name':doc['name'],'file_type':'text','file_size':len(doc['text']),
                    'extracted_text':doc['text'],'summary':'fixture','tags':[],'category':'text'},[(doc['text'],None)])
            create_indexed_document({'filename':'distractors.txt','original_name':'distractors.txt','file_type':'text','file_size':size,
                'extracted_text':'neutral distractors','summary':'fixture','tags':[],'category':'text'},
                [(f'Neutral item record identifier {i} example unrelated material',None) for i in range(size-len(fixture['documents']))])
            rag=RAGService()
            def baseline(query):
                tokens=set(re.findall(r'\w+',query.lower()));ranked=[]
                for chunk in DocumentChunkModel.get_all_chunks_with_doc_meta():
                    words=re.findall(r'\w+',chunk['content'].lower());matches=sum(word in tokens for word in words)
                    score=matches/(math.sqrt(len(words))+1)
                    if score>0:ranked.append((score,chunk['original_name']))
                return [name for _,name in sorted(ranked,reverse=True)[:4]]
            timings={'fts5':[],'full_scan':[]};predictions=[]
            for case in fixture['queries']:
                found={}
                for mode,search in [('fts5',lambda q:[row['document_name'] for row in rag.retrieve_relevant_chunks(q)]),('full_scan',baseline)]:
                    for _ in range(iterations):
                        start=perf_counter();found[mode]=search(case['query']);timings[mode].append((perf_counter()-start)*1000)
                predictions.append({'query':case['query'],'expected':case['expected'],'results':found})
            metrics={}
            positives=[row for row in predictions if row['expected']]
            for mode,samples in timings.items():
                samples.sort()
                metrics[mode]={'recall_at_4':round(sum(row['expected'] in row['results'][mode] for row in positives)/len(positives),3),
                    'mrr_at_4':round(sum(1/(row['results'][mode].index(row['expected'])+1) if row['expected'] in row['results'][mode] else 0 for row in positives)/len(positives),3),
                    'unrelated_queries_with_results':sum(bool(row['results'][mode]) for row in predictions if row['expected'] is None),
                    'p50_ms':round(statistics.median(samples),3),'p95_ms':round(samples[int(.95*(len(samples)-1))],3)}
            return {'chunks':size,'iterations_per_query':iterations,'metrics':metrics,'predictions':predictions}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);parser.add_argument('--iterations',type=int,default=20)
    args=parser.parse_args()
    if args.iterations<1:parser.error('iterations must be positive')
    report={'fixture':'synthetic lexical retrieval; offline mock provider; not LLM/OCR quality','python':platform.python_version(),'platform':platform.platform(),
        'runs':[evaluate(size,args.iterations) for size in [1000,10000]]}
    text=json.dumps(report,indent=2)+'\n'
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text)
    else:print(text)
