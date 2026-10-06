from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.config import settings
from app.models import GenerationJob, RecipientCertificate, JobStatus
from app.schemas import BulkGenerationRequest, JobResponse, JobStatusSummary, RecipientResponse
from app.services.job_processor import JobProcessor, run_background_job
from app.services.zip_service import ZipService

router = APIRouter(prefix="/jobs", tags=["Generation Jobs"])

def build_recipient_response(recipient: RecipientCertificate) -> RecipientResponse:
    resp = RecipientResponse.model_validate(recipient)
    if recipient.status == "SUCCESS":
        resp.pdf_download_url = f"{settings.BASE_URL}/api/v1/certificates/{recipient.id}/download?format=pdf"
        resp.png_download_url = f"{settings.BASE_URL}/api/v1/certificates/{recipient.id}/download?format=png"
        resp.verification_url = f"{settings.BASE_URL}/api/v1/certificates/verify/{recipient.id}"
    return resp

def build_job_response(job: GenerationJob) -> JobResponse:
    progress = 0.0
    if job.total_count > 0:
        processed = job.success_count + job.failed_count
        progress = round((processed / job.total_count) * 100, 2)

    recipients_resp = [build_recipient_response(r) for r in job.recipients]
    
    resp = JobResponse(
        id=job.id,
        event_name=job.event_name,
        issuer_name=job.issuer_name,
        issuer_title=job.issuer_title,
        template_style=job.template_style,
        issue_date=job.issue_date,
        status=job.status,
        progress_percentage=progress,
        total_count=job.total_count,
        success_count=job.success_count,
        failed_count=job.failed_count,
        created_at=job.created_at,
        completed_at=job.completed_at,
        recipients=recipients_resp
    )
    return resp

@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_bulk_generation_job(
    request: BulkGenerationRequest,
    background_tasks: BackgroundTasks,
    async_process: bool = Query(default=True, description="Process in background task if True, synchronously if False"),
    db: Session = Depends(get_db)
):
    """
    Submits a bulk certificate generation request.
    Validates recipient list size and saves initial job metadata.
    """
    if len(request.recipients) > settings.MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch size limit exceeded. Maximum allowed recipients per job is {settings.MAX_BATCH_SIZE}."
        )

    # Create GenerationJob
    job = GenerationJob(
        event_name=request.event_name,
        issuer_name=request.issuer_name or "Organization",
        issuer_title=request.issuer_title or "Authorized Signatory",
        template_style=request.template_style or "classic",
        issue_date=request.issue_date,
        status=JobStatus.PENDING.value,
        total_count=len(request.recipients),
        success_count=0,
        failed_count=0
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Insert RecipientCertificate placeholders
    recipient_objects = []
    for r in request.recipients:
        rec_obj = RecipientCertificate(
            job_id=job.id,
            recipient_name=r.name,
            recipient_email=r.email,
            custom_attributes=r.custom_attributes,
            status="PENDING"
        )
        recipient_objects.append(rec_obj)
    
    db.bulk_save_objects(recipient_objects)
    db.commit()
    db.refresh(job)

    if async_process:
        background_tasks.add_task(run_background_job, job.id)
    else:
        JobProcessor.process_job(job.id, db)
        db.refresh(job)

    return build_job_response(job)

@router.get("", response_model=List[JobStatusSummary])
def list_generation_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of all certificate generation jobs.
    """
    jobs = db.query(GenerationJob).order_by(desc(GenerationJob.created_at)).offset(skip).limit(limit).all()
    
    results = []
    for job in jobs:
        progress = 0.0
        if job.total_count > 0:
            processed = job.success_count + job.failed_count
            progress = round((processed / job.total_count) * 100, 2)
            
        summary = JobStatusSummary(
            id=job.id,
            event_name=job.event_name,
            issuer_name=job.issuer_name,
            template_style=job.template_style,
            status=job.status,
            progress_percentage=progress,
            total_count=job.total_count,
            success_count=job.success_count,
            failed_count=job.failed_count,
            created_at=job.created_at,
            completed_at=job.completed_at
        )
        results.append(summary)
    return results

@router.get("/{job_id}", response_model=JobResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the current status, progress, and detailed results of a generation job.
    """
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with ID '{job_id}' not found.")
    
    return build_job_response(job)

@router.get("/{job_id}/download-all")
def download_all_certificates_zip(
    job_id: str,
    format: str = Query(default="pdf", pattern="^(pdf|png)$"),
    db: Session = Depends(get_db)
):
    """
    Downloads a ZIP file containing all successfully generated certificates for a job.
    """
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with ID '{job_id}' not found.")

    zip_buffer, zip_filename = ZipService.create_job_zip(job_id=job_id, db=db, file_format=format)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
    )
