import logging
import re
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import GenerationJob, RecipientCertificate, JobStatus, RecipientStatus
from app.services.generator import CertificateGenerator

logger = logging.getLogger(__name__)

class JobProcessor:
    """
    Handles bulk certificate generation processing with robust per-recipient error isolation.
    Ensures a single recipient failure does not prevent other valid certificates from being generated.
    """

    @staticmethod
    def process_job(job_id: str, db: Session) -> GenerationJob:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found for processing")
            return None

        job.status = JobStatus.PROCESSING.value
        db.commit()

        recipients = db.query(RecipientCertificate).filter(RecipientCertificate.job_id == job_id).all()
        
        success_count = 0
        failed_count = 0

        for recipient in recipients:
            try:
                # 1. Individual Recipient Validation
                validation_error = JobProcessor._validate_recipient(recipient)
                if validation_error:
                    recipient.status = RecipientStatus.FAILED.value
                    recipient.error_message = validation_error
                    failed_count += 1
                    db.commit()
                    continue

                # 2. Certificate Generation (PDF + PNG)
                issue_date_str = job.issue_date or datetime.now(timezone.utc).strftime("%B %d, %Y")
                
                pdf_path, png_path, verification_hash = CertificateGenerator.generate(
                    cert_id=recipient.id,
                    recipient_name=recipient.recipient_name,
                    recipient_email=recipient.recipient_email,
                    event_name=job.event_name,
                    issuer_name=job.issuer_name,
                    issuer_title=job.issuer_title or "Authorized Signatory",
                    issue_date=issue_date_str,
                    template_style=job.template_style,
                    custom_attributes=recipient.custom_attributes
                )

                # 3. Update Recipient Record on Success
                recipient.status = RecipientStatus.SUCCESS.value
                recipient.pdf_path = pdf_path
                recipient.png_path = png_path
                recipient.verification_hash = verification_hash
                recipient.generated_at = datetime.now(timezone.utc)
                recipient.error_message = None
                success_count += 1

            except Exception as e:
                logger.exception(f"Failed to generate certificate for recipient {recipient.id}")
                recipient.status = RecipientStatus.FAILED.value
                recipient.error_message = f"Generation error: {str(e)}"
                failed_count += 1

            # Commit per recipient to maintain real-time progress updates
            job.success_count = success_count
            job.failed_count = failed_count
            db.commit()

        # Update Job final state
        job.success_count = success_count
        job.failed_count = failed_count
        job.completed_at = datetime.now(timezone.utc)

        if failed_count == 0:
            job.status = JobStatus.COMPLETED.value
        elif success_count > 0:
            job.status = JobStatus.PARTIALLY_FAILED.value
        else:
            job.status = JobStatus.FAILED.value

        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def _validate_recipient(recipient: RecipientCertificate) -> str | None:
        if not recipient.recipient_name or not recipient.recipient_name.strip():
            return "Recipient name is missing or empty"
        
        email = (recipient.recipient_email or "").strip()
        if not email:
            return "Recipient email is missing or empty"
        
        # Simple email regex validation
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, email):
            return f"Invalid recipient email format: '{email}'"

        return None


def run_background_job(job_id: str):
    """
    FastAPI BackgroundTask worker entrypoint.
    """
    db = SessionLocal()
    try:
        JobProcessor.process_job(job_id, db)
    finally:
        db.close()
