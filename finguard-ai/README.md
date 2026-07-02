# FinGuard AI

**Enterprise-Grade Financial Fraud Detection & AI Intelligence Platform**

[![CI/CD Pipeline](https://github.com/your-org/finguard-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/finguard-ai/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![React 18](https://img.shields.io/badge/react-18.2-61DAFB.svg)](https://reactjs.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What Is FinGuard AI?

FinGuard AI is a production-ready monorepo that combines a multi-stage machine learning inference pipeline, SHAP explainability, a calibrated risk scoring engine, and Google Gemini LLM report generation — all served through a FastAPI backend and a dark-mode React dashboard.

Every transaction submitted to the system passes through **7 automated stages**:

```
Incoming Transaction
        │
  [1] Schema Validation
        │
  [2] FraudPreprocessor  (Imputation → Capping → Scaling)
        │
  [3] XGBoost Inference  (predict_proba → fraud_probability)
        │
  [4] SHAP Explainer     (positive/negative attribution drivers)
        │
  [5] Risk Engine        (ML × SHAP × Business Rules → 0–100 score)
        │
  [6] Top Feature Extraction
        │
  [7] Gemini AI Reports  (4 report types, optional)
        │
  PredictionResponse
```

---

## Repository Structure

```
finguard-ai/
├── backend/                  ← FastAPI ASGI engine
│   ├── app/
│   │   ├── core/             ← Config, logging, security
│   │   ├── middleware/       ← Request context, security headers
│   │   ├── routers/          ← REST endpoint definitions
│   │   ├── schemas/          ← Pydantic request/response models
│   │   ├── services/         ← Prediction orchestration
│   │   └── dependencies/     ← DI model registry
│   ├── tests/                ← Pytest unit test suite (28 passing)
│   ├── Dockerfile            ← Production multi-stage Docker image
│   ├── requirements.txt      ← Python dependency pinning
│   └── setup.cfg             ← Flake8 + Pytest configuration
│
├── frontend/                 ← React 18 + Vite dashboard
│   ├── src/
│   │   ├── components/       ← 20+ reusable UI components
│   │   ├── pages/            ← 8 pages + Admin Panel
│   │   ├── services/         ← Axios API layer
│   │   └── context/          ← AuthContext provider
│   ├── Dockerfile            ← Multi-stage Node build → Nginx serve
│   └── nginx.conf            ← Production Nginx with security headers
│
├── ml_pipeline/              ← Model training & evaluation
│   ├── preprocessing/        ← FraudPreprocessor scikit-learn pipeline
│   ├── models/               ← Trained model artifacts (.joblib / .pkl)
│   ├── explainability/       ← FinGuardSHAPExplainer
│   ├── risk_engine/          ← RiskEngine + BusinessRuleEvaluator
│   └── gemini/               ← Gemini client, prompts, report generator
│
├── docs/                     ← Architecture and deployment documentation
├── .github/workflows/        ← GitHub Actions CI/CD pipeline
├── docker-compose.yml        ← Production orchestration
├── docker-compose.dev.yml    ← Development with hot reload
├── docker-compose.test.yml   ← Isolated test environment
├── .env.example              ← Environment variable template
├── .env.development          ← Development environment values
├── .env.test                 ← Testing environment values
└── .env.production           ← Production environment values
```

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker + Docker Compose

### 1. Clone & Configure Environment

```bash
git clone https://github.com/your-org/finguard-ai.git
cd finguard-ai

# Copy environment template
cp .env.example .env.development
# Edit GEMINI_API_KEY and SECRET_KEY with your values
```

### 2. Start All Services (Docker)

```bash
docker compose -f docker-compose.dev.yml --env-file .env.development up --build
```

| Service | URL |
| :--- | :--- |
| **React Dashboard** | http://localhost:3000 |
| **FastAPI Docs (Swagger)** | http://localhost:8000/docs |
| **API Health Check** | http://localhost:8000/api/v1/health |
| **MongoDB** | mongodb://localhost:27017 |

### 3. Demo Login Credentials

Open http://localhost:3000 and use:
- **Username:** `admin` or `analyst`  
- **Password:** `password123`

*(The UI operates in offline demo mode if the backend is unavailable.)*

---

## Running Without Docker (Native Python + Node)

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## Running Tests

### Backend Unit Tests (28 passing)
```bash
cd backend
pytest tests/test_prediction.py -v
```

### Frontend Build Verification
```bash
cd frontend
npm run build
```

---

## Production Deployment

See the full deployment guide at [docs/deployment_guide.md](docs/deployment_guide.md).

### One-Command Production Start

```bash
docker compose -f docker-compose.yml --env-file .env.production up -d --build
```

---

## CI/CD Pipeline (GitHub Actions)

Every push to `main` or `develop` triggers:

| Stage | What Runs |
| :--- | :--- |
| **Backend Test** | `flake8` lint + `pytest` unit tests |
| **Frontend Build** | `vite build` production bundle |
| **Docker Build** | Backend + Frontend image build verification |

---

## API Reference

The FastAPI backend auto-generates interactive docs at `/docs` (Swagger UI) and `/redoc`.

### Core Endpoint

```
POST /api/v1/predict
```

**Request body** (key fields):
```json
{
  "amount": 1250.75,
  "V1": -1.359, "V14": -0.311,
  "merchant_name": "Amazon Prime",
  "country": "USA",
  "generate_reports": false
}
```

**Response includes:**
- `prediction` — `"FRAUD"` or `"GENUINE"`
- `fraud_probability` — percentage 0–100
- `confidence_score` — percentage 0–100
- `risk_assessment` — score, level, triggered rules, breakdown
- `shap_explanation` — positive/negative attribution drivers
- `top_features` — ranked feature attribution matrix
- `gemini_reports` — 4 Gemini AI report types (if requested)
- `processing_time_ms` — end-to-end pipeline latency

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| **ML Framework** | Scikit-Learn, XGBoost, LightGBM |
| **Explainability** | SHAP (TreeExplainer) |
| **LLM / GenAI** | Google Gemini API |
| **Backend API** | FastAPI 0.110+, Uvicorn, Pydantic v2 |
| **Database** | MongoDB (Motor async driver) |
| **Frontend** | React 18, Vite, Tailwind CSS, Recharts |
| **API Client** | Axios |
| **Routing** | React Router v6 |
| **Infrastructure** | Docker, Docker Compose, Nginx |
| **CI/CD** | GitHub Actions |

---

## Security

- **OWASP Security Headers**: `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, `Content-Security-Policy` applied via `SecurityHeadersMiddleware`.
- **JWT Authentication**: All protected routes require `Authorization: Bearer <token>`.
- **Input Validation**: All request payloads are validated by Pydantic schemas before reaching business logic.
- **CORS**: Configurable via `allow_origins` in `setup_middleware()`.

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
