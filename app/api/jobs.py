from fastapi import APIRouter, Depends, status, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from .. import schemas, crud, models
from ..database import get_db
from ..services.generation_job_service import process_generation_job, generate_zip_for_job

router = APIRouter()

@router.post("", response_model=schemas.JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(job_in: schemas.JobCreateRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_job = crud.create_generation_job(db=db, job_in=job_in)
    
    # Delegate standard long-running operations to background task
    background_tasks.add_task(process_generation_job, db_job.id)
    
    return schemas.JobResponse(
        job_id=db_job.id,
        status=db_job.status,
        total_count=db_job.total_count,
        success_count=db_job.success_count,
        failed_count=db_job.failed_count,
        progress=0,
        certificates=[]
    )

@router.get("/{job_id}", response_model=schemas.JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.GenerationJob).filter(models.GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    progress = 0
    if job.total_count > 0:
        progress = int(((job.success_count + job.failed_count) / job.total_count) * 100)
    
    certificates = db.query(models.Certificate).filter(models.Certificate.job_id == job_id).all()
        
    return schemas.JobResponse(
        job_id=job.id,
        status=job.status,
        total_count=job.total_count,
        success_count=job.success_count,
        failed_count=job.failed_count,
        progress=progress,
        certificates=certificates
    )

@router.get("/{job_id}/download")
def download_certificates(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.GenerationJob).filter(models.GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    zip_buffer = generate_zip_for_job(job_id, db)
    if not zip_buffer:
        raise HTTPException(status_code=404, detail="No generated certificates found for this job")
        
    headers = {
        "Content-Disposition": f"attachment; filename=job_{job_id}_certificates.zip"
    }
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers=headers
    )
