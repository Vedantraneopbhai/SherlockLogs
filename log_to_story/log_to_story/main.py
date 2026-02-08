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
import re

# Load environment variables from .env file
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(APP_ROOT, '.env'))

UPLOAD_DIR = os.path.join(APP_ROOT, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

# Allow frontend (Next.js) running on localhost:3000 to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db(os.path.join(APP_ROOT, 'data.db'))


def build_narrative_story(parsed, formatted_events, pattern_findings):
    """Build a comprehensive narrative story from the analysis."""
    total_events = len(formatted_events)
    failed_events = [e for e in formatted_events if e['status'] == 'Failed']
    success_events = [e for e in formatted_events if e['status'] == 'Accepted']
    unique_ips = list(set(e['ip'] for e in formatted_events if e['ip'] != 'N/A'))
    unique_users = list(set(e['user'] for e in formatted_events if e['user'] != 'unknown'))
    
    # Build narrative sections
    narrative_parts = []
    
    # Executive Summary
    narrative_parts.append("**📋 EXECUTIVE SUMMARY**")
    if total_events == 0:
        narrative_parts.append("No authentication events were detected in the provided log file. This may indicate that the file format is incompatible or contains no SSH authentication entries.")
        return '\n\n'.join(narrative_parts)
    
    threat_level = "CRITICAL" if len(failed_events) > 50 else "HIGH" if len(failed_events) > 20 else "MEDIUM" if len(failed_events) > 5 else "LOW"
    narrative_parts.append(f"Threat Level: **{threat_level}** | Total Events: **{total_events}** | Failed Attempts: **{len(failed_events)}** | Successful Logins: **{len(success_events)}**")
    
    # Timeline Analysis
    narrative_parts.append("\n**⏱️ TIMELINE ANALYSIS**")
    if formatted_events:
        first_event = formatted_events[0]
        last_event = formatted_events[-1]
        narrative_parts.append(f"Analysis period: {first_event['timestamp']} to {last_event['timestamp']}")
        narrative_parts.append(f"Attack originated from **{len(unique_ips)}** unique IP address(es) targeting **{len(unique_users)}** user account(s).")
    
    # Threat Analysis
    narrative_parts.append("\n**🔍 THREAT ANALYSIS**")
    if pattern_findings:
        narrative_parts.append(f"**{len(pattern_findings)} security pattern(s) detected:**")
        for i, finding in enumerate(pattern_findings, 1):
            narrative_parts.append(f"{i}. {finding.get('description', 'Unknown pattern')}")
    else:
        if len(failed_events) > 0:
            narrative_parts.append(f"The log shows **{len(failed_events)} failed authentication attempts** scattered across multiple IPs and users, suggesting reconnaissance or distributed attack activity.")
        else:
            narrative_parts.append("No suspicious patterns detected. All authentication events appear to be legitimate.")
    
    # Attack Sources
    if unique_ips:
        narrative_parts.append("\n**🌐 ATTACK SOURCES**")
        ip_counts = {}
        for event in failed_events:
            ip = event['ip']
            ip_counts[ip] = ip_counts.get(ip, 0) + 1
        top_attackers = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        narrative_parts.append("Top attacking IP addresses:")
        for ip, count in top_attackers:
            narrative_parts.append(f"- **{ip}**: {count} failed attempt(s)")
    
    # Targeted Accounts
    if unique_users:
        narrative_parts.append("\n**👤 TARGETED ACCOUNTS**")
        user_counts = {}
        for event in failed_events:
            user = event['user']
            user_counts[user] = user_counts.get(user, 0) + 1
        top_targets = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        narrative_parts.append("Most targeted user accounts:")
        for user, count in top_targets:
            narrative_parts.append(f"- **{user}**: {count} failed attempt(s)")
    
    # Successful Compromises
    if success_events:
        narrative_parts.append("\n**⚠️ SUCCESSFUL AUTHENTICATIONS**")
        narrative_parts.append(f"**{len(success_events)} successful login(s) detected:**")
        for event in success_events[:5]:  # Show first 5
            narrative_parts.append(f"- User **{event['user']}** from **{event['ip']}** at {event['timestamp']}")
        if len(success_events) > 5:
            narrative_parts.append(f"... and {len(success_events) - 5} more")
    
    # Recommendations
    narrative_parts.append("\n**✅ RECOMMENDED ACTIONS**")
    if len(failed_events) > 20:
        narrative_parts.append("1. Implement rate limiting and IP blocking for repeated failed attempts")
        narrative_parts.append("2. Enable multi-factor authentication (MFA) for all accounts")
        narrative_parts.append("3. Review firewall rules to restrict SSH access to trusted networks")
    if success_events and failed_events:
        narrative_parts.append("4. Investigate successful logins that occurred after multiple failures")
        narrative_parts.append("5. Reset passwords for compromised accounts and enforce strong password policies")
    narrative_parts.append("6. Monitor logs continuously for similar attack patterns")
    narrative_parts.append("7. Consider implementing intrusion detection/prevention systems (IDS/IPS)")
    
    return '\n\n'.join(narrative_parts)


def extract_logs_from_python(content):
    """Extract SSH logs from a Python file.
    
    Finds lines with syslog format (Mon DD HH:MM:SS) and SSH keywords,
    extracting them from Python syntax (quotes, comments, assignments).
    """
    log_lines = []
    # Regex pattern for syslog timestamp
    syslog_pattern = re.compile(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}')
    
    for line in content.splitlines():
        # Check if line has both a timestamp and SSH keywords
        if syslog_pattern.search(line) and any(kw in line for kw in ['sshd', 'password', 'authentication', 'Failed', 'Accepted', 'Invalid']):
            # Extract from the timestamp onwards (skip Python syntax before it)
            match = syslog_pattern.search(line)
            if match:
                log_part = line[match.start():]
                log_lines.append(log_part)
    
    result = '\n'.join(log_lines)
    return result if result.strip() else content


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
    
    # If it's a Python file, extract logs from it
    if logfile.filename.endswith('.py'):
        text = extract_logs_from_python(text)
    
    parsed = parse_log(text)
    analyze_findings(parsed)
    
    # Get pattern-based findings (brute force, post-failure success)
    pattern_findings = parsed.get('findings', [])
    
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
    
    # Build comprehensive narrative story
    narrative = build_narrative_story(parsed, formatted_events, pattern_findings)
    
    # Optionally enhance with Gemini AI (if API key is available)
    ai_enhanced = generate_narrative('\n'.join([f['description'] for f in pattern_findings]) if pattern_findings else "Security log analysis")
    
    # Use AI-enhanced narrative if available, otherwise use our detailed story
    final_narrative = ai_enhanced if ai_enhanced and len(ai_enhanced) > 100 else narrative

    # load or build playbook index
    if playbook:
        pb_path = os.path.join(UPLOAD_DIR, playbook.filename)
        with open(pb_path, 'wb') as f:
            shutil.copyfileobj(playbook.file, f)
        index = load_playbook_index(pb_path)
    else:
        default_pb = os.path.join(APP_ROOT, 'playbook.md')
        index = load_playbook_index(default_pb)

    recs = query_playbook(index, final_narrative, top_k=3)

    # save to DB and return JSON
    record_id = save_analysis(filepath, final_narrative, recs)

    return {
        'id': record_id, 
        'narrative': final_narrative, 
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
