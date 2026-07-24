---
description: How to run the Actuarial Engine app (backend + frontend)
---

# Run Actuarial Engine

Requires **2 terminals** running simultaneously.

## Prerequisites
- Python 3.11+ with `.venv` already set up
- Node.js installed
- `.env` file exists (copy from `.env.example` if not)

// turbo-all

## Step 1: Start Backend (Terminal 1)

```bash
cd "d:\Web\Actuarial Engine"
.venv\Scripts\activate
uvicorn actuarial_engine.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir actuarial_engine
```

Backend runs at **http://localhost:8000**

## Step 2: Start Frontend (Terminal 2)

```bash
cd "d:\Web\Actuarial Engine\actuarial-dashboard"
npm run dev
```

Frontend runs at **http://localhost:3000**

## URLs

| URL | Fungsi |
|-----|--------|
| http://localhost:3000 | Dashboard (Web UI) |
| http://localhost:8000/api/v1/docs | API Docs (Swagger) |
| http://localhost:8000/health | Health check |

## Stop

Press `Ctrl+C` in each terminal.
