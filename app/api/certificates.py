from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
import os

router = APIRouter(prefix="/certificates", tags=["Certificates"])

@router.get("/download/{certificate_id}")
def download_individual_certificate(certificate_id: str, db: Session = Depends(get_db)):
    try:
        # Expected format: CERT-2026-00013
        parts = certificate_id.split("-")
        if len(parts) != 3 or parts[0] != "CERT":
            raise ValueError("Invalid format")
        cert_id = int(parts[2])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid certificate ID format")
        
    cert = db.query(models.Certificate).filter(models.Certificate.id == cert_id).first()
    
    if not cert or cert.certificate_id != certificate_id:
        raise HTTPException(status_code=404, detail="Certificate not found")
        
    if not cert.file_path or not os.path.exists(cert.file_path):
        raise HTTPException(status_code=404, detail="Certificate file missing")
        
    # Prevent path traversal implicitly mapping directly from the DB's absolute path
    abs_output_dir = os.path.abspath("generated/certificates")
    abs_filepath = os.path.abspath(cert.file_path)
    
    if not abs_filepath.startswith(abs_output_dir):
        raise HTTPException(status_code=400, detail="Invalid file path")
        
    return FileResponse(
        path=abs_filepath,
        filename=f"{certificate_id}.pdf",
        media_type="application/pdf"
    )
