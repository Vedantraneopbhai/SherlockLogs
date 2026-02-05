Log-to-Story — Incident Response Assistant

Overview
--------
Upload a raw auth/syslog file (e.g., `auth.log`) and this tool will parse SSH authentication events, detect suspicious patterns (brute force, success after failures), and generate a short human-readable narrative. Optionally upload your incident response playbook to receive matching recommended actions.

Quick start (PowerShell)
-------------------------
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
# Open http://127.0.0.1:5000
```

Files
- `app.py` — Flask app and narrative generator
- `parser.py` — event extraction + analysis
- `rag.py` — simple playbook loader + keyword matching
- `playbook.md` — example incident response playbook
- `sample.log` — small sample log for testing

Next steps
- Improve parser to handle more log vendors and formats
- Replace keyword matching with embeddings for robust RAG
- Add tests and Dockerfile for reproducible runs
