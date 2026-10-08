from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from .database import Base

class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    event_name = Column(String, nullable=False)
    event_date = Column(Date, nullable=False)
    issuer_name = Column(String, nullable=False)
    total_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    certificates = relationship("Certificate", back_populates="job")

class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("generation_jobs.id"))
    recipient_name = Column(String, index=True)
    recipient_email = Column(String, index=True)
    status = Column(String, default="pending")  # pending, generated, failed
    file_path = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("GenerationJob", back_populates="certificates")

    @property
    def certificate_id(self) -> str:
        if not self.id:
            return None
        year = self.created_at.year if self.created_at else datetime.utcnow().year
        return f"CERT-{year}-{self.id:05d}"
