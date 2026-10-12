# Production Deployment Guide: Bulk Certificate Generator

This document provides complete instructions for deploying the Bulk Certificate Generator directly to **Render** as a **native Python Web Service** without requiring Docker.

> [!TIP]
> **Docker is NOT required for Render deployment.**
> The application builds and runs natively using Render's standard Python 3.11 environment with Node.js pre-installed to compile the React frontend.
> (The `Dockerfile` and `docker-compose.yml` remain in the repository strictly for optional local container testing if desired).

---

## Architecture Overview

In production on Render:
1. **Frontend**: React + Vite + TypeScript built into static production assets (`frontend/dist`).
2. **Backend**: FastAPI + Uvicorn serving both the API endpoints (`/api/v1/*`) and the React frontend (`/` and SPA fallback).
3. **Unified Single Service**: Both frontend and backend run on a single Render URL with zero CORS configuration required.

---

## 1. Deploying to Render (Native Python Web Service)

Deploying to [Render](https://render.com) is free and takes just a few clicks.

### Option A: Using the Render Blueprint (`render.yaml`) — Recommended
1. Commit and push your code to GitHub:
   ```powershell
   git add .
   git commit -m "Configure native Python Render deployment"
   git push origin main
   ```
2. Log in to your [Render Dashboard](https://dashboard.render.com/).
3. Click **Blueprints** → **New Blueprint Instance**.
4. Select your repository (`AdilSk7/Bulk-Certificate-Generator`).
5. Render will detect `render.yaml` and configure the settings automatically.
6. Click **Apply**.

---

### Option B: Manual Web Service Setup on Render
1. Log in to [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** → **Web Service**.
3. Choose **Build and deploy from a Git repository** and connect your GitHub repository.
4. Fill in the service settings:
   - **Name**: `bulk-certificate-generator`
   - **Language / Runtime**: **Python**
   - **Region**: Choose your closest region (e.g., Oregon, Frankfurt, Singapore)
   - **Branch**: `main`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && cd frontend && npm ci && npm run build
     ```
   - **Start Command**:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan**: **Free**
5. Expand **Advanced**:
   - **Health Check Path**: `/health`
   - **Environment Variables**:
     - `PYTHON_VERSION`: `3.11.9`
6. Click **Create Web Service**.

---

## 2. Deployment Settings Summary

| Setting | Value |
|---|---|
| **Runtime** | `Python` (Docker is NOT required) |
| **Plan** | `Free` |
| **Build Command** | `pip install -r requirements.txt && cd frontend && npm ci && npm run build` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Health Check Path** | `/health` |

### Environment Variables

| Variable | Default Value | Description |
|---|---|---|
| `PORT` | Auto-set by Render (usually `10000`) | Port that Uvicorn binds to dynamically. |
| `PYTHON_VERSION` | `3.11.9` | Python version for Render runtime. |
| `DATABASE_URL` | `sqlite:///./certificates.db` | Database URL. Defaults to SQLite in project directory. |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Allowed CORS origins for external clients (optional since frontend is served same-origin). |

---

## 3. Health Check

FastAPI provides an automated health check at:
```http
GET /health
```
**Response (200 OK)**:
```json
{"status": "ok"}
```
Render checks this endpoint during every deployment to verify that the application has started and is ready for live traffic.

---

## 4. Testing the Deployed Application

Once the Render service is **Live**:
1. Open your assigned URL: `https://<your-service-name>.onrender.com/`
2. Verify that the React application loads at `/`.
3. Test the complete certificate generation flow:
   - Enter **Event Name** (e.g., `AI & Cloud Summit 2026`).
   - Enter **Event Date** (e.g., `2026-11-20`).
   - Enter **Issuer Name** (e.g., `Global Tech Institute`).
   - Customize **Certificate Content** (Title, Intro Text, Description, Presented By).
   - Upload a CSV of recipients (e.g., `test_recipients.csv`).
   - Click **Generate Certificates**.
   - Watch the progress bar advance to 100%.
   - Download an individual recipient's PDF to verify custom content and certificate ID.
   - Click **Download All (ZIP)** and verify that the downloaded filename uses the event name:
     `AI_&_Cloud_Summit_2026_certificates.zip`.

---

## 5. Local Normal Development

For active development with hot reload:

### Backend (Terminal 1)
```powershell
.\venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

### Frontend (Terminal 2)
```powershell
cd frontend
npm install
npm run dev
```
- Local UI: [http://localhost:5173](http://localhost:5173)
- Vite proxy automatically forwards `/api/*` to `http://127.0.0.1:8000`.

---

## 6. Optional Local Docker Testing

If you ever want to test the multi-stage Docker build locally:
```powershell
# Build and run with Docker Compose
docker compose up --build

# Or build and run standalone Docker image
docker build -t bulk-certificate-generator .
docker run -p 8000:8000 -e PORT=8000 bulk-certificate-generator
```

---

## Storage & Persistence Considerations

> [!IMPORTANT]
> **Ephemeral Storage on Render Free Tier**:
> - The free tier on Render uses an **ephemeral filesystem** and spins down after 15 minutes of inactivity.
> - When restarted, local SQLite records (`certificates.db`) and files saved in `generated/certificates/` reset.
> - This setup is completely suitable for demonstration, portfolio, and take-home review purposes because generated certificates and ZIP downloads stream instantly upon job completion.

### Recommended Future Upgrades for Permanent Commercial Use:
1. **Managed Database**: Connect to a managed PostgreSQL database (e.g., Supabase, Neon, or Render PostgreSQL) by updating the `DATABASE_URL` environment variable.
2. **Cloud Object Storage**: Stream generated certificate PDFs to AWS S3, Cloudflare R2, or Google Cloud Storage, or attach a Render Persistent Disk.
