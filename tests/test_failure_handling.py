import pytest
from fastapi import status
from app.models import GenerationJob, RecipientCertificate, JobStatus, RecipientStatus
from app.services.job_processor import JobProcessor

def test_individual_recipient_failure_isolation(db_session):
    """
    Tests that if 1 recipient in a batch of 3 fails (due to validation or error),
    the other 2 valid certificates generate successfully, and job completes as PARTIALLY_FAILED.
    """
    job = GenerationJob(
        event_name="Data Science Masterclass",
        issuer_name="Data Academy",
        template_style="classic",
        total_count=3,
        status=JobStatus.PENDING.value
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    # Recipient 1: Valid
    r1 = RecipientCertificate(job_id=job.id, recipient_name="Alice Good", recipient_email="alice@valid.com", status="PENDING")
    # Recipient 2: Invalid email format (will fail per-recipient processing)
    r2 = RecipientCertificate(job_id=job.id, recipient_name="Bad Email Recipient", recipient_email="invalid_email_no_at", status="PENDING")
    # Recipient 3: Valid
    r3 = RecipientCertificate(job_id=job.id, recipient_name="Carol Good", recipient_email="carol@valid.com", status="PENDING")

    db_session.add_all([r1, r2, r3])
    db_session.commit()

    # Process job
    processed_job = JobProcessor.process_job(job.id, db_session)

    assert processed_job.status == JobStatus.PARTIALLY_FAILED.value
    assert processed_job.total_count == 3
    assert processed_job.success_count == 2
    assert processed_job.failed_count == 1

    # Check recipient 1
    db_session.refresh(r1)
    assert r1.status == RecipientStatus.SUCCESS.value
    assert r1.pdf_path is not None

    # Check recipient 2 (Failed)
    db_session.refresh(r2)
    assert r2.status == RecipientStatus.FAILED.value
    assert r2.pdf_path is None
    assert "Invalid recipient email format" in r2.error_message

    # Check recipient 3
    db_session.refresh(r3)
    assert r3.status == RecipientStatus.SUCCESS.value
    assert r3.pdf_path is not None
