import os
import zipfile
import io
import datetime
import re
from sqlalchemy.orm import Session
from app import models
from app.database import SessionLocal
from app.services.certificate_service import generate_certificate
from typing import Optional, Union

OUTPUT_BASE_DIR = "generated/certificates"

def process_generation_job(job_id: int):
    db = SessionLocal()
    try:
        job = db.query(models.GenerationJob).filter(models.GenerationJob.id == job_id).first()
        if not job:
            return
            
        job.status = "PROCESSING"
        db.commit()
        
        certificates = db.query(models.Certificate).filter(models.Certificate.job_id == job_id).all()
        
        for cert in certificates:
            if cert.status != "PENDING":
                continue
                
            try:
                file_path = generate_certificate(
                    recipient_name=cert.recipient_name,
                    event_name=job.event_name,
                    event_date=str(job.event_date.strftime("%Y-%m-%d")),
                    issuer_name=job.issuer_name,
                    output_dir=OUTPUT_BASE_DIR,
                    unique_id=cert.id,
                    filename_override=f"{cert.certificate_id}.pdf",
                    certificate_title=job.certificate_title or "CERTIFICATE OF PARTICIPATION",
                    introduction_text=job.introduction_text or "This certificate is proudly presented to",
                    description_text=job.description_text or "for successfully participating in",
                    presented_by_label=job.presented_by_label or "Presented by"
                )
                cert.status = "GENERATED"
                cert.file_path = file_path
                job.success_count += 1
            except Exception as e:
                cert.status = "FAILED"
                cert.error_message = str(e)
                job.failed_count += 1
                
            db.commit()
            
        job.status = "COMPLETED"
        if job.failed_count == job.total_count and job.total_count > 0:
            job.status = "FAILED"
            
        job.completed_at = datetime.datetime.utcnow()
        db.commit()
    finally:
        db.close()

def generate_zip_for_job(job_id: int, db: Session) -> Optional[io.BytesIO]:
    certificates = db.query(models.Certificate).filter(
        models.Certificate.job_id == job_id,
        models.Certificate.status == "GENERATED"
    ).all()
    
    if not certificates:
        return None
        
    zip_buffer = io.BytesIO()
    abs_output_dir = os.path.abspath(OUTPUT_BASE_DIR)
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for cert in certificates:
            if cert.file_path and os.path.exists(cert.file_path):
                abs_cert_path = os.path.abspath(cert.file_path)
                # Prevent path traversal vulnerabilities by enforcing output constraints
                if abs_cert_path.startswith(abs_output_dir):
                    safe_name = re.sub(r'[^A-Za-z0-9_-]', '_', cert.recipient_name)
                    zip_file.write(abs_cert_path, arcname=f"{safe_name}.pdf")
                    
    zip_buffer.seek(0)
    return zip_buffer
