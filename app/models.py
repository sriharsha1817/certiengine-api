import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIALLY_FAILED = "PARTIALLY_FAILED"

class RecipientStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

def generate_uuid():
    return str(uuid.uuid4())

class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_name = Column(String(255), nullable=False)
    issuer_name = Column(String(255), nullable=False, default="Organization")
    issuer_title = Column(String(255), nullable=True, default="Authorized Issuer")
    template_style = Column(String(50), nullable=False, default="classic")
    issue_date = Column(String(50), nullable=True)
    
    status = Column(String(30), nullable=False, default=JobStatus.PENDING.value)
    total_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    recipients = relationship("RecipientCertificate", back_populates="job", cascade="all, delete-orphan")

class RecipientCertificate(Base):
    __tablename__ = "recipient_certificates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("generation_jobs.id"), nullable=False, index=True)
    
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    custom_attributes = Column(JSON, nullable=True)
    
    status = Column(String(30), nullable=False, default=RecipientStatus.PENDING.value)
    error_message = Column(Text, nullable=True)
    
    pdf_path = Column(String(512), nullable=True)
    png_path = Column(String(512), nullable=True)
    verification_hash = Column(String(64), nullable=True, index=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    generated_at = Column(DateTime, nullable=True)

    job = relationship("GenerationJob", back_populates="recipients")
