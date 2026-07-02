# FinGuard AI — Start Guide

A step-by-step guide to running FinGuard AI locally.

---

## Prerequisites

Make sure you have these installed before starting:

| Tool | Minimum Version | Download |
|:---|:---|:---|
| **Python** | 3.11+ | https://python.org |
| **Node.js** | 18+ | https://nodejs.org |
| **Docker Desktop** | 4.0+ | https://docker.com/products/docker-desktop |
| **Git** | Any | https://git-scm.com |

---

## Option A — Docker (Recommended, Easiest)

Everything runs in containers. No manual Python or Node setup needed.

### Step 1 — Clone the project

```bash
git clone https://github.com/your-org/finguard-ai.git
cd finguard-ai
```

### Step 2 — Create your environment file

```bash
copy .env.example .env.development
```

Open `.env.development` and fill in your values:

```env
# Required — get your free key at https://aistudio.google.com
GEMINI_API_KEY=your-google-gemini-api-key-here

# Required — change this to any long random string
SECRET_KEY=change-this-to-a-long-random-secret-key-at-least-32-chars
```

Everything else can stay as-is for local development.

### Step 3 — Start all services

```bash
docker compose -f docker-compose.dev.yml --env-file .env.development up --build
```

Docker will start three containers:
- **MongoDB** database
- **FastAPI** backend
- **React** frontend

First build takes ~3–5 minutes. Subsequent starts are instant.

### Step 4 — Open the app

| Service | URL |
|:---|:---|
| **Dashboard (React UI)** | http://localhost:3000 |
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **API Health Check** | http://localhost:8000/api/v1/health |
| **MongoDB** | mongodb://localhost:27017 |

### Demo Login

```
Username:  admin
Password:  password123
```

### Stop the app

```bash
docker compose -f docker-compose.dev.yml down
```

---

## Option B — Manual (Without Docker)

Run the backend and frontend directly on your machine. You still need **MongoDB** running — either locally or via Docker.

### Step 1 — Start MongoDB (via Docker, simplest)

```bash
docker run -d -p 27017:27017 --name finguard-mongo mongo:6.0
```

Or install MongoDB Community locally: https://www.mongodb.com/try/download/community

---

### Step 2 — Set up the Backend

```bash
cd backend

# Create a Python virtual environment
python -m venv .venv

# Activate it
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Create a `.env.development` file in the **project root** (not inside `backend/`):

```bash
# From the project root:
copy .env.example .env.development
```

Edit `.env.development`:

```env
DATABASE_URL=mongodb://localhost:27017/finguard_dev
SECRET_KEY=change-this-to-a-long-random-secret-key
GEMINI_API_KEY=your-google-gemini-api-key-here
DEBUG=true
ENVIRONMENT=development
```

Start the backend server:

```bash
# From inside the backend/ directory
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO: Uvicorn running on http://0.0.0.0:8000
```

Confirm it works: http://localhost:8000/api/v1/health

---

### Step 3 — Set up the Frontend

Open a **new terminal**:

```bash
cd frontend

# Install Node dependencies
npm install

# Start the dev server
npm run dev
```

You should see:
```
VITE ready in 800ms
Local: http://localhost:5173/
```

> **Note:** When running manually, the frontend runs on port **5173** (Vite default).  
> When running via Docker, it runs on port **3000**.

---

## Option C — Production (Full Docker Build)

For a production-like environment on your machine:

```bash
# Create .env.production
copy .env.example .env.production
# Edit .env.production with real SECRET_KEY and GEMINI_API_KEY

# Start production containers
docker compose -f docker-compose.yml --env-file .env.production up -d --build
```

The React app is served via **Nginx** (port 80) instead of Vite dev server.

| Service | URL |
|:---|:---|
| **Dashboard** | http://localhost:80 |
| **API** | http://localhost:8000 |

---

## Running the ML Pipeline (Optional)

If you want to regenerate model artifacts or the SHAP background dataset:

```bash
cd ml_pipeline

# Install ML dependencies
pip install -r requirements.txt

# Generate SHAP background dataset
python explainability/background_generator.py

# Train models (requires creditcard.csv in ml_pipeline/data/processed/)
python run_training.py

# Run explainability pipeline
python run_explainability.py
```

---

## Running Tests

```bash
cd backend

# Activate virtual environment first if running manually
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # Mac/Linux

# Run the full test suite
pytest tests/test_prediction.py -v
```

Expected output: **28 passed**

---

## Common Issues

### Port already in use
```bash
# Find what is using port 8000
netstat -ano | findstr :8000   # Windows
lsof -i :8000                  # Mac/Linux

# Or change the port in docker-compose.dev.yml
ports:
  - "8001:8000"
```

### MongoDB connection refused
Make sure MongoDB is running:
```bash
docker ps | grep mongo
# If not running:
docker start finguard-mongo
```

### `GEMINI_API_KEY` errors
The app runs in offline demo mode if Gemini reports are disabled. Set `generate_reports=false` in prediction requests to skip Gemini calls entirely.

### Frontend shows blank page
Clear browser cache or open in an incognito window. If using Chrome, press `Ctrl+Shift+R`.

### Docker `permission denied` on Linux
```bash
sudo chmod 666 /var/run/docker.sock
```

---

## Environment Files Summary

| File | Purpose | Committed to Git? |
|:---|:---|:---|
| `.env.example` | Template — copy this first | Yes |
| `.env.development` | Local dev values | **No** (gitignored) |
| `.env.test` | Test runner values | **No** (gitignored) |
| `.env.production` | Production values | **No** (gitignored) |

---

## Project Layout (Quick Reference)

```
finguard-ai/
├── backend/        → FastAPI API server (port 8000)
├── frontend/       → React dashboard (port 3000 / 5173)
├── ml_pipeline/    → ML training, SHAP, Risk Engine, Gemini
├── docs/           → Architecture & deployment guides
├── .env.example    → Environment variable template
├── docker-compose.yml          → Production
├── docker-compose.dev.yml      → Development
└── start.md        → This file
```

---

## Next Steps

- **Deployment Guide:** [docs/deployment_guide.md](docs/deployment_guide.md)
- **Architecture Docs:** [docs/architecture.md](docs/architecture.md)
- **API Reference:** http://localhost:8000/docs (Swagger UI)
- **Full README:** [README.md](README.md)
