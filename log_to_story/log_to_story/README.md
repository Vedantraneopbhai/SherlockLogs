# SherlockLogs — Incident Response Assistant

Transform cryptic security logs into clear, actionable intelligence with AI-powered analysis.

## Overview

Upload a raw auth/syslog file (e.g., `auth.log`) and this tool will:
- Parse SSH authentication events
- Detect suspicious patterns (brute force, success after failures)
- Generate a human-readable narrative explaining what happened
- Provide matching incident response recommendations from your playbook

## Quick Start

### 1. Backend Setup (FastAPI)

```powershell
# Navigate to the project directory
cd log_to_story

# Create and activate virtual environment (optional but recommended)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# (Optional) Configure Gemini AI - copy .env.example to .env and add your API key
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY if you want AI-enhanced narratives

# Start the backend server
python main.py
```

The backend API will be available at `http://127.0.0.1:8000`

### 2. Frontend Setup (Next.js)

```powershell
# In a new terminal, navigate to frontend directory
cd log_to_story/frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

Open `http://localhost:3000` in your browser to use the application.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API status page |
| `/health` | GET | Health check endpoint |
| `/analyze` | POST | Upload and analyze a log file (multipart form-data) |
| `/history` | GET | Get all past analyses |
| `/history/{id}` | GET | Get a specific analysis by ID |

## Features

- **Log Parsing**: Automatically extracts SSH authentication events from syslog format
- **Threat Detection**: Identifies brute force attacks and suspicious login patterns
- **AI Narratives**: Optional integration with Google Gemini for enhanced incident stories
- **Playbook RAG**: Matches findings against your incident response playbook using semantic search
- **History**: Stores and retrieves past analyses

## Files

- `main.py` — FastAPI app and API endpoints
- `parser.py` — Event extraction and pattern analysis
- `rag_faiss.py` — Playbook indexing with FAISS for semantic search
- `gemini_client.py` — Google Gemini AI integration for narrative generation
- `db.py` — SQLite database for storing analyses
- `playbook.md` — Example incident response playbook
- `.env.example` — Environment configuration template

## Configuration

Copy `.env.example` to `.env` and configure:

```env
# Optional: Get from https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_key_here

# Model to use (default: gemini-1.5-flash)
GEMINI_MODEL=gemini-1.5-flash
```

The app works without an API key - it will use fallback narrative generation instead.

## Tech Stack

- **Backend**: FastAPI, Python, FAISS, sentence-transformers
- **Frontend**: Next.js, React, Axios
- **AI**: Google Gemini (optional)
- **Database**: SQLite
