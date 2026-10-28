# Publication note

Approved changes are merged into `main`, and the static interface is published on GitHub Pages: https://swopnab.github.io/Zabum-AI/. Only the static showcase is public. The document/chat API and personal storage stay local.

The review below records pre-publication validation and its remaining limits.

# Zabum AI — review build

Status: local review only. No push or deployment authorized yet. No real documents or profiles were used in testing.

## What changed

- Restored the missing persistence models using the existing unpublished persistence fix; retained conversation, message, memory, document, and chunk IDs.
- PDF ingestion chunks each page separately and stores nullable `page_number`. Legacy chunks retain unknown page locations; they are never guessed. New source records include document ID, chunk ID, name, page, and a full supporting passage. Clicking a source opens and highlights its stored chunk.
- Document mode is deliberately extractive. A conservative lexical gate requires meaningful query terms to occur in one passage, otherwise the response states insufficient evidence. The model is not asked to execute document instructions in this mode. General AI chat remains available, clearly labeled as not document-verified. Retrieved context in general chat is untrusted data; prompt instructions alone cannot guarantee injection resistance.
- Memory suggestions require approval. Existing add/edit/delete controls remain. A persisted preference disables memory retrieval and suggestions without deleting saved records. Deletion affects future context, not prior conversation text.
- Upload byte progress transitions to extraction/indexing, then ready or failed. Metadata/chunks/FTS updates commit together. Invalid PDFs, blank extraction, unavailable OCR, and indexing failures are not indexed as content. Failed requests do not claim to have saved a memory.
- Larger reading text, neutral/green surfaces, quieter navigation, accessible source disclosures, dialog focus containment/Escape, keyboard-accessible conversation entries, and a corrected mobile drawer.
- `/showcase/` serves a static project explanation with an actual fictional-data screenshot; it does not run a hosted AI service.

## Run

Use a virtual environment. From the repository root:

```sh
python -m venv .venv
.venv/bin/pip install -r backend/requirements-core.txt
AI_PROVIDER=mock ZABUM_STORAGE_DIR=/tmp/zabum-fictional-review .venv/bin/python backend/app.py
```

Open `http://127.0.0.1:5001/app`. Mock mode is labeled and performs no model inference. For normal local chat, use the existing Ollama configuration in `.env.example` and run Ollama locally with the configured models. Install `backend/requirements.txt` for optional Transformers/PyTorch TrOCR dependencies. Initial model downloads require internet and local disk space; no paid provider or new account was added. OCR quality is not claimed by the mocked tests.

The server binds to 127.0.0.1, accepts localhost hosts, and rejects foreign origins. A local machine is not a multi-user security boundary: do not expose the service through a proxy/tunnel. External model providers remain opt-in code extensions, not a hosted default.

## Storage, upgrades and recovery

SQLite stores metadata and source associations; uploads stay in the configured local storage directory. FTS5 provides the lexical shortlist and optional embeddings rerank candidates. There is no additional database or LangChain dependency.

Before adding `page_number` to an existing chunk table, startup writes a SQLite backup beside the database, named `*.before-sources-<UTC timestamp>.bak`. The migration is additive and tested for preserved IDs/content. Backups, databases, WAL files, credentials, and uploads are ignored by Git.

Before upgrading a real workspace, stop the server and make a separate copy of the complete storage directory. To recover, keep the current directory as evidence, restore the chosen SQLite backup as the configured database in a separate storage copy, retain its matching upload files, then restart and inspect it. A SQLite snapshot does not itself contain uploaded file bytes. Never restore over a running database. Historical chat quotations remain after document deletion; delete those conversations separately if required.

## Repeatable checks and measurements

```sh
cd backend
python -m unittest discover -s tests -v
python evaluate_evidence.py > ../evaluation/evidence-results.json
python evaluate.py --output ../evaluation/results.json
```

`evaluation/evidence-results.json` records the current small synthetic fixture: five short documents, five answerable questions, three unanswerable questions including related-but-unsupported facts, and 20 repetitions per question. Passage recall is the fraction of the five answerable questions returning their literal known passage. Abstention rate uses the three unanswerable questions as its denominator. Latencies include retrieval and lexical gating only, not generation, OCR, or real user interaction. They are machine-specific. The separate larger lexical evaluation retains its original meaning; it is not an LLM accuracy benchmark.

The gate misses paraphrases and can return a passage containing all query words without proving semantic support. Returned text is quoted evidence to inspect, not a hiring/medical/legal decision or a claim of verified generated answers. General chat output needs human review. Real Ollama inference was not verified because the local service was unavailable; physical OCR recognition was not measured. OCR route/failure behavior is tested with fixtures.

See `docs/screenshots/` and `tests/browser.cjs` for desktop/mobile evidence and browser reproduction instructions. No public deployment or GitHub CI run is claimed before approval.

## Interview explanation

“I kept the existing Flask/SQLite design, added stable source locations to ingestion, and separated an inspectable extractive mode from unverified generation. I used transactions to keep metadata and search chunks consistent, explicit memory approval for user control, and an additive migration with a recoverable snapshot. I can explain exactly what the lexical evaluation measures and why it does not establish general model accuracy.”

## Checks run for this review

15 isolated Python checks and 5 standalone browser scenarios passed. The eight-question synthetic evidence fixture returned 5/5 expected passages and abstained on 3/3 unsupported questions; retrieve-and-gate p50 0.207 ms, p95 0.238 ms on this machine, excluding model inference/OCR. The 1,000/10,000-chunk lexical comparison was also rerun; raw results are in `evaluation/results.json`. Static showcase asset loading passed.
