import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from parser import parse_log, analyze_findings
from rag_faiss import load_playbook_index, query_playbook
from gemini_client import generate_narrative
from db import init_db, save_analysis, get_all_analyses, get_analysis_by_id
import shutil
import ast

# Load environment variables from .env file
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(APP_ROOT, '.env'))

UPLOAD_DIR = os.path.join(APP_ROOT, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="SherlockLogs API", description="AI-powered Security Log Analysis")

# Get allowed origins from environment for production deployments
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 
    'http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001'
).split(',')

# Allow frontend (Next.js) to call this API - supports both local and production URLs
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS + ["*"],  # Allow all origins for flexibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db(os.path.join(APP_ROOT, 'data.db'))


@app.get('/', response_class=HTMLResponse)
def home():
    return "<h3>Log-to-Story FastAPI backend</h3><p>Use POST /analyze to upload logs.</p>"


@app.get('/health')
def health_check():
    """Health check endpoint for testing backend connectivity."""
    return {'status': 'healthy', 'service': 'SherlockLogs API'}


@app.post('/analyze')
async def analyze(logfile: UploadFile = File(...), playbook: UploadFile | None = None):
    # save uploaded logfile
    filepath = os.path.join(UPLOAD_DIR, logfile.filename)
    with open(filepath, 'wb') as f:
        shutil.copyfileobj(logfile.file, f)

    text = open(filepath, 'r', encoding='utf-8', errors='ignore').read()
    parsed = parse_log(text)
    analyze_findings(parsed)
    
    # Get pattern-based findings (brute force, post-failure success)
    pattern_findings = parsed.get('findings', [])
    
    # Build narrative from pattern findings
    narrative_parts = [f['description'] for f in pattern_findings]
    narrative_input = ' '.join(narrative_parts) if narrative_parts else "No significant security patterns detected."

    # Format events for frontend display (individual log events)
    formatted_events = []
    for event in parsed.get('events', []):
        formatted_events.append({
            'timestamp': event['ts'].strftime('%Y-%m-%d %H:%M:%S') if event.get('ts') else 'N/A',
            'user': event.get('user', 'unknown'),
            'ip': event.get('ip', 'N/A'),
            'status': 'Failed' if event.get('type') == 'failed' else 'Accepted',
            'raw': event.get('raw', '')
        })
    
    # Generate enhanced narrative with Gemini (or fallback)
    enriched = generate_narrative(narrative_input)

    # load or build playbook index
    if playbook:
        pb_path = os.path.join(UPLOAD_DIR, playbook.filename)
        with open(pb_path, 'wb') as f:
            shutil.copyfileobj(playbook.file, f)
        index = load_playbook_index(pb_path)
    else:
        default_pb = os.path.join(APP_ROOT, 'playbook.md')
        index = load_playbook_index(default_pb)

    recs = query_playbook(index, enriched or narrative_input, top_k=3)

    # save to DB and return JSON
    record_id = save_analysis(filepath, enriched or narrative_input, recs)

    return {
        'id': record_id, 
        'narrative': enriched or narrative_input, 
        'recs': recs, 
        'findings': formatted_events,  # Individual events for table display
        'threats': pattern_findings,    # Pattern-based detections
        'summary': {
            'total_events': len(formatted_events),
            'failed_attempts': len([e for e in formatted_events if e['status'] == 'Failed']),
            'successful_logins': len([e for e in formatted_events if e['status'] == 'Accepted']),
            'unique_ips': len(set(e['ip'] for e in formatted_events)),
            'unique_users': len(set(e['user'] for e in formatted_events)),
        }
    }


@app.get('/history')
async def get_history():
    """Get all past analyses."""
    analyses = get_all_analyses()
    # Parse the recs string back to list
    for a in analyses:
        try:
            a['recs'] = ast.literal_eval(a['recs']) if a['recs'] else []
        except:
            a['recs'] = []
    return {'analyses': analyses}


@app.get('/history/{analysis_id}')
async def get_history_item(analysis_id: int):
    """Get a specific analysis by ID."""
    analysis = get_analysis_by_id(analysis_id)
    if not analysis:
        return {'error': 'Analysis not found'}, 404
    try:
        analysis['recs'] = ast.literal_eval(analysis['recs']) if analysis['recs'] else []
    except:
        analysis['recs'] = []
    return analysis


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=True)
