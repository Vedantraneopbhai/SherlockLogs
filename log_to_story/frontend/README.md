Frontend — Next.js

Quick start (from `log_to_story` folder)

```powershell
cd log_to_story\frontend
npm install
npm run dev
# Open http://localhost:3000
```

This frontend calls the FastAPI backend at `http://127.0.0.1:8000/analyze`.
Ensure the backend is running and CORS is enabled (done in `main.py`).
