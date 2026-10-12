from sqlalchemy.orm import Session
from . import models, schemas
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

def create_generation_job(db: Session, job_in: schemas.JobCreateRequest) -> models.GenerationJob:
    db_job = models.GenerationJob(
        status="PENDING",
        event_name=job_in.event_name,
        event_date=job_in.event_date,
        issuer_name=job_in.issuer_name,
        certificate_title=job_in.certificate_title,
        introduction_text=job_in.introduction_text,
        description_text=job_in.description_text,
        presented_by_label=job_in.presented_by_label,
        total_count=len(job_in.recipients),
        success_count=0,
        failed_count=0
    )
    db.add(db_job)
    
    try:
        db.flush()  # Gets the db_job.id without committing the transaction
        
        for recipient in job_in.recipients:
            cert = models.Certificate(
                job_id=db_job.id,
                recipient_name=recipient.name,
                recipient_email=recipient.email,
                status="PENDING"
            )
            db.add(cert)
            
        db.commit()
        db.refresh(db_job)
        return db_job
    except Exception as e:
        db.rollback()
        raise e
