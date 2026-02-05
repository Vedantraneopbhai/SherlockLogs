import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from parser import parse_log, analyze_findings
from rag_faiss import load_playbook_index, query_playbook
from gemini_client import generate_narrative
from db import init_db, save_analysis
import shutil

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(APP_ROOT, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

# Allow frontend (Next.js) running on localhost:3000 to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db(os.path.join(APP_ROOT, 'data.db'))


@app.get('/', response_class=HTMLResponse)
def home():
    return "<h3>Log-to-Story FastAPI backend</h3><p>Use POST /analyze to upload logs.</p>"


@app.post('/analyze')
async def analyze(logfile: UploadFile = File(...), playbook: UploadFile | None = None):
    # save uploaded logfile
    filepath = os.path.join(UPLOAD_DIR, logfile.filename)
    with open(filepath, 'wb') as f:
        shutil.copyfileobj(logfile.file, f)

    text = open(filepath, 'r', encoding='utf-8', errors='ignore').read()
    parsed = parse_log(text)
    findings = analyze_findings(parsed)
    narrative = ' '.join([f['description'] for f in parsed.get('findings', [])])

    # optional: enrich narrative with Gemini
    enriched = generate_narrative(narrative)

    # load or build playbook index
    if playbook:
        pb_path = os.path.join(UPLOAD_DIR, playbook.filename)
        with open(pb_path, 'wb') as f:
            shutil.copyfileobj(playbook.file, f)
        index = load_playbook_index(pb_path)
    else:
        default_pb = os.path.join(APP_ROOT, 'playbook.md')
        index = load_playbook_index(default_pb)

    recs = query_playbook(index, enriched or narrative, top_k=3)

    # save to DB and return JSON
    record_id = save_analysis(filepath, enriched or narrative, recs)

    return {'id': record_id, 'narrative': enriched or narrative, 'recs': recs, 'findings': parsed.get('findings', [])}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=True)
