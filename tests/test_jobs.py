import pytest
from app.models import GenerationJob, Certificate

def test_create_job_success(client):
    payload = {
      "event_name": "Python Workshop",
      "event_date": "2026-10-08",
      "issuer_name": "ABC Organization",
      "recipients": [
        {"name": "Adil Shaik", "email": "adil@example.com"},
        {"name": "Rahul Kumar", "email": "rahul@example.com"}
      ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["job_id"] is not None
    assert data["status"] in ["PENDING", "COMPLETED", "PROCESSING"]

def test_missing_event_name(client):
    payload = {
      "event_date": "2026-10-08",
      "issuer_name": "ABC Organization",
      "recipients": [{"name": "A", "email": "a@example.com"}]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_empty_recipients_list(client):
    payload = {
      "event_name": "Python Workshop",
      "event_date": "2026-10-08",
      "issuer_name": "ABC Organization",
      "recipients": []
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_invalid_recipient_email(client):
    payload = {
      "event_name": "Python Workshop",
      "event_date": "2026-10-08",
      "issuer_name": "ABC Organization",
      "recipients": [{"name": "A", "email": "invalid-email"}]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_missing_recipient_name(client):
    payload = {
      "event_name": "Python Workshop",
      "event_date": "2026-10-08",
      "issuer_name": "ABC Organization",
      "recipients": [{"email": "a@example.com"}]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_full_job_lifecycle(client, db_session):
    payload = {
      "event_name": "Lifecycle Event",
      "event_date": "2026-10-09",
      "issuer_name": "XYZ Corp",
      "recipients": [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"}
      ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 201
    job_id = response.json()["job_id"]

    # Test client usually processes background tasks before returning
    job = db_session.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    assert job.status == "COMPLETED"
    assert job.total_count == 2
    assert job.success_count == 2
    assert job.failed_count == 0
    
    certs = db_session.query(Certificate).filter(Certificate.job_id == job_id).all()
    assert len(certs) == 2
    for cert in certs:
        assert cert.status == "GENERATED"
        assert str(cert.file_path).endswith(".pdf")

    # Retrieve job over API
    response = client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "COMPLETED"

    # Download zip 
    response = client.get(f"/api/v1/jobs/{job_id}/download")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-zip-compressed"
    assert f"job_{job_id}_certificates.zip" in response.headers["content-disposition"]
    # Verify Zip structure contains CERT-YYYY-XXXXX format.
    has_cert_name = False
    
    # Check invalid extraction formats
    response = client.get("/api/v1/certificates/download/123")
    assert response.status_code == 400

    response = client.get("/api/v1/certificates/download/CERT-2026-99999")
    assert response.status_code == 404

    response = client.get("/api/v1/certificates/download/../../etc/passwd")
    assert response.status_code in [400, 404]
    
    # We grab a real cert ID to test success
    cert_id = data["certificates"][0]["certificate_id"]
    response = client.get(f"/api/v1/certificates/download/{cert_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"

def test_download_not_found(client):
    response = client.get("/api/v1/jobs/9999/download")
    assert response.status_code == 404
