from pydantic import BaseModel, Field, field_validator
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
    certificate_title: Optional[str] = "CERTIFICATE OF PARTICIPATION"
    introduction_text: Optional[str] = "This certificate is proudly presented to"
    description_text: Optional[str] = "for successfully participating in"
    presented_by_label: Optional[str] = "Presented by"
    total_count: int
    success_count: int
    failed_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    certificates: List[Certificate] = []

    class Config:
        from_attributes = True

class Recipient(BaseModel):
    name: str = Field(..., min_length=1)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name cannot be empty or blank")
        return v.strip()

class JobCreateRequest(BaseModel):
    event_name: str = Field(..., min_length=1)
    event_date: date
    issuer_name: str = Field(..., min_length=1)
    certificate_title: str = Field(default="CERTIFICATE OF PARTICIPATION", min_length=1)
    introduction_text: str = Field(default="This certificate is proudly presented to", min_length=1)
    description_text: str = Field(default="for successfully participating in", min_length=1)
    presented_by_label: str = Field(default="Presented by", min_length=1)
    recipients: List[Recipient] = Field(..., min_length=1)

    @field_validator("event_name", "issuer_name", "certificate_title", "introduction_text", "description_text", "presented_by_label")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or blank")
        return v.strip()

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
