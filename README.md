# Bulk Certificate Generator

A production-ready full-stack microservice and web application for bulk generating customizable participant PDF certificates. Built strategically with scalability, resilience, and clean architectural patterns, the platform combines a modern React + Vite frontend with an asynchronous FastAPI backend that transparently orchestrates PDF rendering with ReportLab, tracks batch progress in real time, handles individual recipient errors gracefully, and packages generated certificates into event-named bulk ZIP downloads.

---

## Key Features

- **Modern React + Vite Frontend**: Clean, responsive UI with CSV upload and preview, live batch progress tracking, and per-recipient certificate downloads.
- **Customizable Certificate Content**: Directly configure the Certificate Title, Introduction Text, Description Text, and Presented By Label from the UI or API with automatic text wrapping and font scaling.
- **Asynchronous Background Processing**: Generates batches of certificates asynchronously using FastAPI `BackgroundTasks`, polling job status without blocking requests.
- **Resilient Pipeline**: If one recipient fails during batch processing, the pipeline continues cleanly. Specific error messages are saved per certificate without failing the entire batch.
- **Event-Named Bulk ZIP Downloads**: Dynamically streams ZIP files named after the event (e.g., `Python_Workshop_2026_certificates.zip`), with filesystem-safe sanitization.
- **Unique Permanent Certificate IDs**: Generates predictable, tamper-resistant IDs formatted as `CERT-YYYY-XXXXX`.
- **Unified Full-Stack Deployment**: In production, FastAPI serves the compiled React application directly from `frontend/dist` with SPA fallback—enabling single-URL deployment without CORS overhead.
- **Deployable Natively or with Docker**: Ready for 1-click deployment as a native Python Web Service on Render (`render.yaml`) or containerized via Docker and Docker Compose.

---

## Technology Stack

### Backend
- **Python 3.11+**
- **FastAPI**: Asynchronous web framework and API orchestration.
- **SQLAlchemy & SQLite**: Relational ORM with idempotent database migration support.
- **Pydantic V2**: Strict request/response validation with field-level sanitization.
- **ReportLab**: High-fidelity PDF drafting and graphic vector canvas construction.
- **Pytest & HTTPX**: Comprehensive unit and integration test suite (29 tests).

### Frontend
- **React 19 & TypeScript**: Component-driven user interface.
- **Vite**: Ultra-fast build tool and development server with API proxying.
- **PapaParse**: Client-side CSV parsing and validation.
- **Lucide React**: Modern iconography.

---

## Architectural Decisions & Resiliency

* **BackgroundTasks Decoupling**: FastAPI `BackgroundTasks` processes batches asynchronously. For enterprise multi-worker production deployments, this can scale seamlessly to Celery with Redis. For single-node environments, `BackgroundTasks` keeps transaction durations short and minimizes infrastructure overhead.
* **Component Service Isolation**: API routers, database CRUD logic, generation orchestration (`generation_job_service.py`), and rendering (`certificate_service.py`) are strictly modular and decoupled.
* **Safe Resiliency Pipeline**: If `Recipient 4` encounters an error during a batch of 100, remaining certificates continue processing uninterrupted. Individual failure checkpoints preserve error flags independently.
* **Idempotent Database Migrations**: Uses database schema inspection at startup to safely apply missing columns to existing databases without breaking changes or duplicate errors.
* **Transient Test Environments**: Tests inject `TestingSessionLocal` to a scoped in-memory database to prevent test side-effects on local data.
* **Security & Path Traversal Protections**: Sanitizes all input strings, event names, and file identifiers to prevent directory traversal attacks during PDF storage and ZIP compression.

---

## Project Structure

```text
.
├── app/
│   ├── api/
│   │   ├── certificates.py    # Individual certificate download endpoint
│   │   └── jobs.py            # Job creation, polling, and bulk ZIP download
│   ├── database.py            # SQLite connection and idempotent migrations
│   ├── models.py              # SQLAlchemy database models
│   ├── schemas.py             # Pydantic request/response schemas
│   ├── crud.py                # Database transactions
│   ├── main.py                # FastAPI app & production static SPA serving
│   └── services/
│       ├── certificate_service.py     # ReportLab PDF drafting engine
│       └── generation_job_service.py  # Asynchronous batch processing
├── frontend/                  # React + Vite + TypeScript frontend
│   ├── src/
│   │   ├── App.tsx            # Main application UI and state
│   │   └── App.css            # Responsive styling
│   └── package.json
├── tests/                     # Pytest suite (29 automated tests)
│   ├── test_jobs.py
│   └── test_main.py
├── Dockerfile                 # Multi-stage production container build
├── docker-compose.yml         # Local container testing with persistent storage
├── render.yaml                # Native Render Python Web Service blueprint
├── DEPLOYMENT.md              # Complete deployment documentation
├── requirements.txt           # Python dependencies
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 1. Local Development (Separate Processes)

#### Backend
```powershell
# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server with hot reload
uvicorn app.main:app --reload --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

#### Frontend
```powershell
cd frontend
npm install
npm run dev
```
- Local UI: `http://localhost:5173`
- The Vite dev server proxies `/api/*` requests directly to `http://127.0.0.1:8000`.

---

### 2. Unified Production Run (Single Process)

FastAPI can serve the compiled React frontend directly:

```powershell
# 1. Build frontend
cd frontend
npm run build
cd ..

# 2. Run FastAPI
uvicorn app.main:app --port 8000
```
- Web Application & API: `http://localhost:8000/`

---

### 3. Optional Local Docker Run

```powershell
# Using Docker Compose with persistent SQLite and generated files:
docker compose up --build
```
- Web Application: `http://localhost:8000/`

---

## Testing

Run the full automated test suite covering job creation, validation, customizable text rendering, migration idempotency, event-name ZIP sanitization, and SPA routing:

```bash
pytest -v
```
All **29 tests** pass with 100% test fidelity.

---

## API Documentation

Interactive Swagger documentation is available at `http://localhost:8000/docs`.

### 1. Create a Bulk Generation Job
`POST /api/v1/jobs`

Initiates an asynchronous background job and saves batch inputs to the database.

**Request Body**
```json
{
  "event_name": "AI & Cloud Summit 2026",
  "event_date": "2026-11-20",
  "issuer_name": "Global Tech Institute",
  "certificate_title": "CERTIFICATE OF EXCELLENCE",
  "introduction_text": "This is proudly presented to",
  "description_text": "for active participation and outstanding performance in",
  "presented_by_label": "Presented by",
  "recipients": [
    {
      "name": "Jane Smith",
      "email": "jane@example.com"
    },
    {
      "name": "John Doe",
      "email": "john@example.com"
    }
  ]
}
```

### 2. Check Job Status & Progress
`GET /api/v1/jobs/{job_id}`

Polls generation status, progress percentage, and individual recipient certificate records.

**Response**
```json
{
  "job_id": 1,
  "status": "COMPLETED",
  "total_count": 2,
  "success_count": 2,
  "failed_count": 0,
  "progress": 100,
  "certificates": [
    {
      "id": 1,
      "certificate_id": "CERT-2026-00001",
      "recipient_name": "Jane Smith",
      "status": "GENERATED",
      "error_message": null
    },
    {
      "id": 2,
      "certificate_id": "CERT-2026-00002",
      "recipient_name": "John Doe",
      "status": "GENERATED",
      "error_message": null
    }
  ]
}
```

### 3. Bulk Download ZIP Certificates
`GET /api/v1/jobs/{job_id}/download`

Streams an in-memory ZIP archive containing all successfully generated certificates.
- **Filename**: Dynamically named based on the event name (e.g., `AI_&_Cloud_Summit_2026_certificates.zip`).
- **Internal Files**: Human-readable recipient names (e.g., `Jane_Smith.pdf`).

### 4. Individual Certificate Download
`GET /api/v1/certificates/download/{certificate_id}`

Downloads an individual certificate PDF by its unique identifier (e.g., `CERT-2026-00001`).

### 5. Health Check
`GET /health`

Lightweight endpoint returning `{"status": "ok"}` for deployment health checks and uptime monitoring.

---

## Production Deployment to Render

The repository is configured for native deployment to **Render** without requiring Docker.

1. Push your repository to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com/), create a **New Blueprint Instance** and select your repository (or create a **Web Service** using the settings below):
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt && cd frontend && npm ci && npm run build`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
   - **Environment Variable**: `PYTHON_VERSION` = `3.11.9`
3. Refer to [DEPLOYMENT.md](DEPLOYMENT.md) for full deployment details and storage persistence recommendations.
