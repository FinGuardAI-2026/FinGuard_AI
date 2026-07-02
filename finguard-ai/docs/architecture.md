# FinGuard AI — Architecture Reference

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   PRODUCTION TOPOLOGY                    │
│                                                         │
│  ┌─────────────┐    HTTP    ┌──────────────────────┐    │
│  │   Browser   │ ──────────▶│  Nginx (port 80)     │    │
│  └─────────────┘            │  React SPA Bundle    │    │
│                             │  + Security Headers  │    │
│                             └──────────┬───────────┘    │
│                                        │ /api/* proxy   │
│                             ┌──────────▼───────────┐    │
│                             │  FastAPI Backend      │    │
│                             │  (Uvicorn, port 8000) │    │
│                             │                       │    │
│                             │  ┌─────────────────┐ │    │
│                             │  │  7-Stage         │ │    │
│                             │  │  Prediction      │ │    │
│                             │  │  Pipeline        │ │    │
│                             │  └────────┬────────┘ │    │
│                             └───────────┼───────────┘   │
│                                         │               │
│           ┌─────────────────────────────┼──────────┐    │
│           │                             │          │    │
│  ┌────────▼──────┐  ┌──────────┐  ┌────▼──────┐   │    │
│  │   MongoDB      │  │  XGBoost │  │  Gemini   │   │    │
│  │   (port 27017) │  │  .joblib │  │  API      │   │    │
│  └───────────────┘  └──────────┘  └───────────┘   │    │
└─────────────────────────────────────────────────────────┘
```

## Prediction Pipeline Stages

| Stage | Component | Input → Output |
| :--- | :--- | :--- |
| 1 | **Schema Validation** | Raw JSON → Pydantic `PredictionRequest` |
| 2 | **FraudPreprocessor** | Feature DataFrame → Scaled/Imputed array |
| 3 | **XGBoost Inference** | Feature array → `[fraud_prob, genuine_prob]` |
| 4 | **SHAP Explainer** | Feature array → TreeExplainer SHAP values |
| 5 | **Risk Engine** | ML prob + SHAP + Rules → Risk Score (0–100) |
| 6 | **Top Feature Extraction** | SHAP values → Ranked feature list |
| 7 | **Gemini Report Gen** | `FraudContext` → 4 Markdown reports |

## Environment Separation

| Environment | Docker Compose | .env File | DB |
| :--- | :--- | :--- | :--- |
| Development | `docker-compose.dev.yml` | `.env.development` | `finguard_dev` |
| Testing | `docker-compose.test.yml` | `.env.test` | `finguard_test` |
| Production | `docker-compose.yml` | `.env.production` | `finguard_prod` |

## Security Architecture

```
Request Chain:
  Client
    │
    ├─ TLS Termination (reverse proxy / ALB)
    │
    ├─ CORS Policy (fastapi CORSMiddleware)
    │
    ├─ SecurityHeadersMiddleware
    │    ├─ X-Frame-Options: DENY
    │    ├─ X-Content-Type-Options: nosniff
    │    ├─ Strict-Transport-Security
    │    └─ Content-Security-Policy
    │
    ├─ JWT Authentication (Bearer token)
    │
    ├─ Pydantic Schema Validation
    │
    └─ Business Logic
```
