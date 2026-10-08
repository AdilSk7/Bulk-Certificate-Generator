# Bulk Certificate Generator Backend

A robust microservice backend for bulk generating participant PDF certificates, built strategically with scalability and clean architectural patterns in mind. It receives generation requests via an API, transparently orchestrates background generation utilizing ReportLab, precisely manages individual transaction errors, and safely stores outputs for single ZIP bulk downloads.

## Technology Stack
- **Python 3.11+**
- **FastAPI**: Core API framework supporting asynchronous orchestration.
- **SQLAlchemy & SQLite**: ORM integration representing SQL relational boundaries effectively.
- **Pydantic V2**: Robust model structures guaranteeing immutable validation workflows.
- **ReportLab**: PDF drafting and graphic vector canvas construction.
- **Pytest**: Integration and unit testing frameworks mapping to full coverage objectives.

## Assignment Design Decisions & Architecture
* **BackgroundTasks Usage**: The application uses FastAPI `BackgroundTasks` for lightweight asynchronous bulk processing. For a production system requiring durable distributed job execution, scalable background workers, or a dedicated job queue, I would scale this up to Celery with Redis. For this single-node phase, Background Tasks efficiently decouples processing without introducing unnecessary infrastructure overhead securely keeping API transaction bounds short-lived while complying with architectural separation of concerns.
* **Component Service Isolation**: API definitions, database CRUD behaviors, and final rendering tools (Certificate Service) are deeply isolated. Generation processing (`generation_job_service.py`) glues the database models seamlessly to raw generation. 
* **Safe Resiliency Pipeline**: If `Certificate 4` fails during generation inside a batch of 10, the task continues cleanly. A transactional DB checkpoint preserves specific `failed` flags + error messages independently onto that certificate so debugging scales without bringing down the global pipeline success.
* **Transient Test Environments**: Implemented mocked test environments that inject `TestingSessionLocal` to a scoped memory DB for 100% data preservation and testing fidelity preventing side-effects globally against local data.
* **Security & Sandboxing**: Dynamically stripping inputs ensuring directory traversal protections prevents any malicious paths from overriding absolute paths natively resolved for storing or zipping assets.

## Application Setup

1. **Clone and create a virtual environment**
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the API Server**
   ```bash
   uvicorn app.main:app --reload
   ```

   _The API will be available at `http://127.0.0.1:8000`._

## Testing
Run the testing suite to execute 11 core architectural tests confirming full schema behaviors, transactional rollbacks, Background DB decoupling, zip creation, and PDF verification.
```bash
pytest -v
```

## API Documentation

FastAPI auto-generates interactive Swagger endpoints accessible via `http://127.0.0.1:8000/docs` while the server runs.

### 1. Create a Bulk Generation Job
`POST /api/v1/jobs`

Initiates async background tracking and bulk saves structural inputs into the database. Pydantic evaluates and enforces field lengths, types, and valid email formulations.

**Request Body**
```json
{
  "event_name": "Python Workshop",
  "event_date": "2026-10-08",
  "issuer_name": "ABC Organization",
  "recipients": [
    {
      "name": "Jane Smith",
      "email": "jane@example.com"
    }
  ]
}
```

### 2. Check Job Status
`GET /api/v1/jobs/{job_id}`

Dynamically polls job status enumerating successes against failures gracefully.

**Response**
```json
{
  "job_id": 1,
  "status": "COMPLETED",
  "total_count": 1,
  "success_count": 1,
  "failed_count": 0,
  "progress": 100,
  "certificates": [
    {
      "id": 1,
      "certificate_id": "CERT-2026-00001",
      "recipient_name": "Jane Smith",
      "status": "GENERATED",
      "error_message": null
    }
  ]
}
```

### 3. Bulk Download ZIP Certificates
`GET /api/v1/jobs/{job_id}/download`

Leverages dynamically constructed ZIP file extraction parsing exclusively successfully `GENERATED` certificates matching the underlying `job_id` relation directly streamable to end-users without saving ZIPs persistently to the filesystem. Files inside the ZIP are human-readable (e.g. `Jane_Smith.pdf`).

### 4. Individual Certificate Download
`GET /api/v1/certificates/download/{certificate_id}`

Download a standalone generated certificate securely via its permanent unique identifier (e.g., `CERT-2026-00001`). Prevents path traversal explicitly and streams the PDF rendering perfectly.
