import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict

class RecipientInput(BaseModel):
    name: str = Field(..., description="Recipient full name", min_length=1, max_length=255)
    email: str = Field(..., description="Recipient email address")
    custom_attributes: Optional[Dict[str, Any]] = Field(default=None, description="Optional custom metadata like score, role, etc.")

    @field_validator("name")
    def name_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Recipient name cannot be empty or only whitespace")
        return v

    @field_validator("email")
    def validate_email_format(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Recipient email cannot be empty")
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid email format: '{v}'")
        return v

class BulkGenerationRequest(BaseModel):
    event_name: str = Field(..., description="Name of the course, event, or workshop", min_length=2, max_length=255)
    issuer_name: Optional[str] = Field(default="Global Academy", description="Name of issuing organization or individual")
    issuer_title: Optional[str] = Field(default="Authorized Signatory", description="Title of issuer")
    template_style: Optional[str] = Field(default="classic", description="Certificate design style: 'classic', 'modern', or 'elegant'")
    issue_date: Optional[str] = Field(default=None, description="Date of issuance (defaults to current date if omitted)")
    recipients: List[RecipientInput] = Field(..., min_length=1, description="List of certificate recipients")

    @field_validator("event_name")
    def event_name_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Event name cannot be empty")
        return v

    @field_validator("template_style")
    def validate_template_style(cls, v: Optional[str]) -> str:
        valid_styles = ["classic", "modern", "elegant"]
        style = (v or "classic").lower().strip()
        if style not in valid_styles:
            raise ValueError(f"Invalid template style '{v}'. Allowed styles: {', '.join(valid_styles)}")
        return style

class RecipientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    recipient_name: str
    recipient_email: str
    custom_attributes: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    pdf_download_url: Optional[str] = None
    png_download_url: Optional[str] = None
    verification_url: Optional[str] = None
    created_at: datetime
    generated_at: Optional[datetime] = None

class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_name: str
    issuer_name: str
    issuer_title: Optional[str] = None
    template_style: str
    issue_date: Optional[str] = None
    status: str
    progress_percentage: float = 0.0
    total_count: int
    success_count: int
    failed_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    recipients: List[RecipientResponse] = []

class JobStatusSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_name: str
    issuer_name: str
    template_style: str
    status: str
    progress_percentage: float
    total_count: int
    success_count: int
    failed_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None

class CertificateVerificationResponse(BaseModel):
    is_valid: bool
    certificate_id: str
    recipient_name: str
    recipient_email: str
    event_name: str
    issuer_name: str
    issue_date: Optional[str] = None
    verification_hash: Optional[str] = None
    generated_at: Optional[datetime] = None
    status: str
