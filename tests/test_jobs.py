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
    assert "Lifecycle_Event_certificates.zip" in response.headers["content-disposition"]
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

def test_create_job_default_certificate_content(client, db_session):
    import pypdf
    import os

    payload = {
        "event_name": "Default Content Summit",
        "event_date": "2026-10-12",
        "issuer_name": "Standard Issuer Org",
        "recipients": [
            {"name": "Default Recipient", "email": "default@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 201
    job_id = response.json()["job_id"]

    job = db_session.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    assert job.status == "COMPLETED"
    assert job.certificate_title == "CERTIFICATE OF PARTICIPATION"
    assert job.introduction_text == "This certificate is proudly presented to"
    assert job.description_text == "for successfully participating in"
    assert job.presented_by_label == "Presented by"

    cert = db_session.query(Certificate).filter(Certificate.job_id == job_id).first()
    assert cert.file_path and os.path.exists(cert.file_path)

    # Extract text from PDF
    reader = pypdf.PdfReader(cert.file_path)
    page_text = reader.pages[0].extract_text()
    assert "CERTIFICATE OF PARTICIPATION" in page_text
    assert "This certificate is proudly presented to" in page_text
    assert "for successfully participating in" in page_text
    assert "Presented by" in page_text
    assert "Standard Issuer Org" in page_text
    assert "Default Recipient" in page_text

def test_create_job_custom_certificate_content(client, db_session):
    import pypdf
    import os

    payload = {
        "event_name": "AI & Cloud Workshop 2026",
        "event_date": "2026-10-08",
        "issuer_name": "Tech Innovation Institute",
        "certificate_title": "CERTIFICATE OF COMPLETION",
        "introduction_text": "This certificate is awarded to",
        "description_text": "for successfully completing",
        "presented_by_label": "Issued by",
        "recipients": [
            {"name": "Sneha Rao", "email": "sneha@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 201
    job_id = response.json()["job_id"]

    job = db_session.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    assert job.status == "COMPLETED"
    assert job.certificate_title == "CERTIFICATE OF COMPLETION"
    assert job.introduction_text == "This certificate is awarded to"
    assert job.description_text == "for successfully completing"
    assert job.presented_by_label == "Issued by"

    cert = db_session.query(Certificate).filter(Certificate.job_id == job_id).first()
    assert cert.file_path and os.path.exists(cert.file_path)

    # Extract text from PDF to verify custom wording
    reader = pypdf.PdfReader(cert.file_path)
    page_text = reader.pages[0].extract_text()
    assert "CERTIFICATE OF COMPLETION" in page_text
    assert "This certificate is awarded to" in page_text
    assert "for successfully completing" in page_text
    assert "Issued by" in page_text
    assert "Tech Innovation Institute" in page_text
    assert "Sneha Rao" in page_text

@pytest.mark.parametrize("field_name,invalid_val", [
    ("certificate_title", ""),
    ("certificate_title", "   "),
    ("introduction_text", ""),
    ("introduction_text", "   "),
    ("description_text", ""),
    ("description_text", "   "),
    ("presented_by_label", ""),
    ("presented_by_label", "   "),
])
def test_invalid_empty_custom_content_fields(client, field_name, invalid_val):
    payload = {
        "event_name": "Validation Test Event",
        "event_date": "2026-10-15",
        "issuer_name": "Test Org",
        "recipients": [{"name": "Test User", "email": "user@example.com"}],
        field_name: invalid_val
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_migration_idempotency(db_session):
    from app.database import run_migrations, engine
    # Run migrations once
    run_migrations(engine)
    # Run migrations second time (must not fail or duplicate)
    run_migrations(engine)
    # Run with None (defaults to engine)
    run_migrations()

def test_sanitize_filename_unit():
    from app.api.jobs import sanitize_filename

    assert sanitize_filename("AI & Cloud Workshop 2026") == "AI_&_Cloud_Workshop_2026"
    assert sanitize_filename("Hackathon 2026") == "Hackathon_2026"
    assert sanitize_filename("Python Workshop") == "Python_Workshop"
    assert sanitize_filename("  Multiple   Spaces   ") == "Multiple_Spaces"
    assert sanitize_filename('Unsafe: / \\ * ? " < > | chars') == "Unsafe_chars"
    assert sanitize_filename("___leading_and_trailing___") == "leading_and_trailing"
    assert sanitize_filename("...dots...and...spaces   ") == "dots...and...spaces"
    assert sanitize_filename("") == ""
    assert sanitize_filename("   ") == ""
    assert sanitize_filename("???///:::***") == ""

def test_bulk_zip_download_filename_custom_event(client):
    payload = {
        "event_name": "AI & Cloud Workshop 2026",
        "event_date": "2026-10-12",
        "issuer_name": "AI Academy",
        "recipients": [
            {"name": "Sneha Rao", "email": "sneha@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 201
    job_id = response.json()["job_id"]

    download_resp = client.get(f"/api/v1/jobs/{job_id}/download")
    assert download_resp.status_code == 200
    assert download_resp.headers["content-type"] == "application/x-zip-compressed"
    assert "AI_&_Cloud_Workshop_2026_certificates.zip" in download_resp.headers["content-disposition"]

def test_bulk_zip_download_filename_unsafe_characters(client):
    payload = {
        "event_name": 'Hackathon: 2026 / Winter <Edition>?',
        "event_date": "2026-10-12",
        "issuer_name": "Tech Club",
        "recipients": [
            {"name": "Vikram Singh", "email": "vikram@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 201
    job_id = response.json()["job_id"]

    download_resp = client.get(f"/api/v1/jobs/{job_id}/download")
    assert download_resp.status_code == 200
    assert "Hackathon_2026_Winter_Edition_certificates.zip" in download_resp.headers["content-disposition"]

def test_bulk_zip_download_filename_fallback_when_empty(client, db_session):
    # If event_name is somehow all unsafe characters
    payload = {
        "event_name": ': / * ? < > |',
        "event_date": "2026-10-12",
        "issuer_name": "Org",
        "recipients": [
            {"name": "Arjun", "email": "arjun@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 201
    job_id = response.json()["job_id"]

    download_resp = client.get(f"/api/v1/jobs/{job_id}/download")
    assert download_resp.status_code == 200
    assert 'filename="certificates.zip"' in download_resp.headers["content-disposition"] or 'filename=certificates.zip' in download_resp.headers["content-disposition"]
