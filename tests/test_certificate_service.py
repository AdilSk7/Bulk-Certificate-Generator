import os
import tempfile
import pytest
from app.services.certificate_service import generate_certificate, get_safe_filename
from pypdf import PdfReader

def test_get_safe_filename():
    assert get_safe_filename("Adil Shaik") == "Adil_Shaik"
    assert ".." not in get_safe_filename("../../etc/passwd")

def test_generate_certificate_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = generate_certificate(
            recipient_name="John Doe",
            event_name="Test Event",
            event_date="2026-01-01",
            issuer_name="Test Org",
            output_dir=tmpdir,
            unique_id=1
        )
        assert os.path.exists(output_path)
        assert output_path.endswith("John_Doe_1.pdf")
        
        # Verify text via pypdf
        reader = PdfReader(output_path)
        assert len(reader.pages) == 1
        page_text = reader.pages[0].extract_text()
        
        assert "CERTIFICATE OF PARTICIPATION" in page_text
        assert "John Doe" in page_text
        assert "Test Event" in page_text

def test_invalid_path_handling():
    with pytest.raises(RuntimeError):
        generate_certificate(
            recipient_name="John Doe",
            event_name="Test Event",
            event_date="2026-01-01",
            issuer_name="Test Org",
            output_dir="Z:\\this_drive_definitely_does_not_exist_xyz123",
            unique_id=1
        )
