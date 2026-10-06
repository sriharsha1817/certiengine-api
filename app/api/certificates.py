import os
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models import RecipientCertificate, RecipientStatus
from app.schemas import RecipientResponse, CertificateVerificationResponse
from app.api.jobs import build_recipient_response

router = APIRouter(prefix="/certificates", tags=["Certificates"])

@router.get("/verify/{certificate_id}", response_model=CertificateVerificationResponse)
def verify_certificate(certificate_id: str, db: Session = Depends(get_db)):
    """
    Publicly verifies the authenticity of a certificate.
    """
    cert = db.query(RecipientCertificate).filter(RecipientCertificate.id == certificate_id).first()
    if not cert:
        return CertificateVerificationResponse(
            is_valid=False,
            certificate_id=certificate_id,
            recipient_name="Unknown",
            recipient_email="Unknown",
            event_name="Unknown",
            issuer_name="Unknown",
            status="NOT_FOUND"
        )
    
    if cert.status != RecipientStatus.SUCCESS.value:
        return CertificateVerificationResponse(
            is_valid=False,
            certificate_id=cert.id,
            recipient_name=cert.recipient_name,
            recipient_email=cert.recipient_email,
            event_name=cert.job.event_name if cert.job else "Unknown",
            issuer_name=cert.job.issuer_name if cert.job else "Unknown",
            status=cert.status
        )

    return CertificateVerificationResponse(
        is_valid=True,
        certificate_id=cert.id,
        recipient_name=cert.recipient_name,
        recipient_email=cert.recipient_email,
        event_name=cert.job.event_name if cert.job else "N/A",
        issuer_name=cert.job.issuer_name if cert.job else "N/A",
        issue_date=cert.job.issue_date if cert.job else None,
        verification_hash=cert.verification_hash,
        generated_at=cert.generated_at,
        status="VALID"
    )

@router.get("/{certificate_id}", response_model=RecipientResponse)
def get_certificate_details(certificate_id: str, db: Session = Depends(get_db)):
    """
    Retrieves metadata for a specific certificate.
    """
    cert = db.query(RecipientCertificate).filter(RecipientCertificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Certificate '{certificate_id}' not found.")
    
    return build_recipient_response(cert)

@router.get("/{certificate_id}/download")
def download_certificate(
    certificate_id: str,
    format: str = Query(default="pdf", pattern="^(pdf|png)$"),
    db: Session = Depends(get_db)
):
    """
    Downloads the generated certificate file (PDF or PNG format).
    """
    cert = db.query(RecipientCertificate).filter(RecipientCertificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Certificate '{certificate_id}' not found.")
    
    if cert.status != RecipientStatus.SUCCESS.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate '{certificate_id}' status is '{cert.status}'. Reason: {cert.error_message or 'Not generated'}"
        )

    file_path = cert.pdf_path if format.lower() == "pdf" else cert.png_path
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Certificate file for format '{format}' missing on server.")

    media_type = "application/pdf" if format.lower() == "pdf" else "image/png"
    safe_name = "".join(c for c in cert.recipient_name if c.isalnum() or c in (" ", "_", "-")).strip()
    download_filename = f"Certificate_{safe_name}_{cert.id[:8]}.{format.lower()}"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=download_filename
    )
