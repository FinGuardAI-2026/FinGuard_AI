# FinGuard AI — Production Deployment Guide

This guide provides comprehensive, step-by-step instructions for deploying the **FinGuard AI** enterprise fraud detection workspace into production environments using Docker, Docker Compose, Kubernetes, or cloud platforms (AWS, GCP, Azure).

---

## Architecture Overview

FinGuard AI consists of three core containerized services:
1. **Frontend UI** (`finguard-frontend`): High-performance React 19 SPA served via Nginx with automated caching & OWASP security headers.
2. **Backend Engine** (`finguard-backend`): FastAPI ASGI server orchestrating the 7-stage ML inference pipeline (`champion_model.joblib`), SHAP explainability, Risk Engine, and Gemini report generator.
3. **Database** (`finguard-mongodb`): MongoDB database storing transaction ledgers, audit trails, and user profiles.

---

## Environment Configuration

Copy `.env.example` to `.env.production` before launching containers:

```bash
cp .env.example .env.production
```

### Critical Environment Variables

| Variable | Description | Recommended Production Value |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Runtime environment mode | `production` |
| `DEBUG` | FastAPI debug logging flag | `false` |
| `SECRET_KEY` | JWT signing secret | 64-character random hex string |
| `DATABASE_URL` | MongoDB connection string | `mongodb://mongodb:27017/finguard_prod` |
| `GEMINI_API_KEY` | Google Gemini API Key | Enterprise API key string |
| `VITE_API_BASE_URL` | API endpoint for frontend | `https://api.finguard.ai` |

---

## Production Deployment via Docker Compose

### 1. Launch Production Stack
Run the following command on the host server:

```bash
docker compose -f docker-compose.yml --env-file .env.production up -d --build
```

### 2. Verify Container Liveness Probe & Health Checks
Check the health status of running services:

```bash
docker compose ps
```

Expected output:
```
NAME               IMAGE               COMMAND                  SERVICE             STATUS
finguard-backend   finguard-backend    "uvicorn app.main:ap…"   backend             running (healthy)
finguard-frontend  finguard-frontend   "/docker-entrypoint.…"   frontend            running (healthy)
finguard-mongodb   mongo:6.0           "docker-entrypoint.s…"   mongodb             running (healthy)
```

---

## Development & Testing Workflows

### Running Local Development Stack (Hot Reloading)
```bash
docker compose -f docker-compose.dev.yml --env-file .env.development up
```

### Running Automated Test Suite in Isolated Containers
```bash
docker compose -f docker-compose.test.yml --env-file .env.test up --exit-code-from backend-test
```

---

## Security & Hardening Best Practices

1. **SSL/TLS Termination**: Deploy an ingress controller or reverse proxy (e.g., Traefik, Nginx Proxy Manager, AWS ALB) in front of the frontend container to enforce HTTPS with TLS 1.3.
2. **Database Authentication**: Enable MongoDB RBAC authentication (`MONGO_INITDB_ROOT_USERNAME` / `MONGO_INITDB_ROOT_PASSWORD`) when deploying outside private VPCs.
3. **Secrets Management**: Inject `SECRET_KEY` and `GEMINI_API_KEY` using Docker Secrets, AWS Secrets Manager, or HashiCorp Vault rather than plain text files.
4. **Network Isolation**: Restrict MongoDB port `27017` access strictly to internal container networks.

---

## Continuous Integration & Deployment (CI/CD)

The repository includes a GitHub Actions pipeline configured at `.github/workflows/ci.yml`. It automatically executes on pushes or pull requests to `main` and `develop` branches:

- **Stage 1**: Backend unit testing via `pytest` & linting with `flake8`.
- **Stage 2**: Frontend production build verification via Vite.
- **Stage 3**: Multi-stage Docker build check.

---

## Backup & Recovery Protocols

### Database Backup (MongoDB)
Execute a database dump inside the running MongoDB container:

```bash
docker exec -t finguard-mongodb mongodump --out /data/db/dumps/$(date +%F)
```

### Restoring Database Dump
```bash
docker exec -t finguard-mongodb mongorestore /data/db/dumps/2026-06-28
```
