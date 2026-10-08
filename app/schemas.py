from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List

class CertificateBase(BaseModel):
    recipient_name: str
    recipient_email: str

class CertificateCreate(CertificateBase):
    pass

class Certificate(CertificateBase):
    id: int
    job_id: int
    status: str
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class GenerationJobBase(BaseModel):
    pass

class GenerationJobCreate(GenerationJobBase):
    pass

class GenerationJob(GenerationJobBase):
    id: int
    status: str
    event_name: str
    event_date: date
    issuer_name: str
    total_count: int
    success_count: int
    failed_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    certificates: List[Certificate] = []

    class Config:
        from_attributes = True

class Recipient(BaseModel):
    name: str = Field(..., min_length=1, strip_whitespace=True)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")

class JobCreateRequest(BaseModel):
    event_name: str = Field(..., min_length=1, strip_whitespace=True)
    event_date: date
    issuer_name: str = Field(..., min_length=1, strip_whitespace=True)
    recipients: List[Recipient] = Field(..., min_length=1)

class CertificateResponse(BaseModel):
    id: int
    certificate_id: Optional[str] = None
    recipient_name: str
    status: str
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class JobResponse(BaseModel):
    job_id: int
    status: str
    total_count: int
    success_count: int
    failed_count: int
    progress: int = 0
    certificates: List[CertificateResponse] = []

    class Config:
        from_attributes = True

class IndividualCertificateRequest(BaseModel):
    recipient_name: str
    course_name: str
    certificate_id: str
