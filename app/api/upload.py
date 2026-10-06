import csv
import io
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models import GenerationJob, RecipientCertificate, JobStatus
from app.schemas import JobResponse
from app.api.jobs import build_job_response
from app.services.job_processor import JobProcessor, run_background_job

router = APIRouter(prefix="/jobs/upload-csv", tags=["CSV Upload"])

@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_csv_and_create_job(
    file: UploadFile = File(..., description="CSV file containing recipient details ('name','email', optional extra columns)"),
    event_name: str = Form(..., min_length=2, max_length=255),
    issuer_name: str = Form(default="Global Academy"),
    issuer_title: str = Form(default="Authorized Signatory"),
    template_style: str = Form(default="classic"),
    issue_date: Optional[str] = Form(default=None),
    async_process: bool = Form(default=True),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Parses an uploaded CSV file of recipients and submits a bulk certificate generation job.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a valid CSV file ending with .csv"
        )

    content = await file.read()
    try:
        text_content = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text_content = content.decode("latin-1")

    csv_reader = csv.DictReader(io.StringIO(text_content))
    if not csv_reader.fieldnames:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded CSV file is empty or missing headers.")

    # Normalize column header names
    headers_map = {h.strip().lower(): h for h in csv_reader.fieldnames if h}
    
    name_col = headers_map.get("name") or headers_map.get("recipient_name") or headers_map.get("full_name")
    email_col = headers_map.get("email") or headers_map.get("recipient_email") or headers_map.get("email_address")

    if not name_col or not email_col:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file must contain 'name' (or 'recipient_name') and 'email' (or 'recipient_email') header columns."
        )

    recipient_rows = []
    for row in csv_reader:
        r_name = row.get(name_col, "").strip()
        r_email = row.get(email_col, "").strip()
        if not r_name and not r_email:
            continue # Skip blank rows
        
        # Extra columns become custom attributes
        custom_attrs = {}
        for original_col in csv_reader.fieldnames:
            norm = original_col.strip().lower()
            if norm not in [name_col.strip().lower(), email_col.strip().lower()] and row.get(original_col):
                custom_attrs[original_col.strip()] = row[original_col].strip()
        
        recipient_rows.append((r_name, r_email, custom_attrs if custom_attrs else None))

    if not recipient_rows:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No recipient records found in CSV file.")

    if len(recipient_rows) > settings.MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV row limit exceeded ({len(recipient_rows)}). Max batch size is {settings.MAX_BATCH_SIZE}."
        )

    # Save GenerationJob
    job = GenerationJob(
        event_name=event_name,
        issuer_name=issuer_name,
        issuer_title=issuer_title,
        template_style=template_style.lower(),
        issue_date=issue_date,
        status=JobStatus.PENDING.value,
        total_count=len(recipient_rows),
        success_count=0,
        failed_count=0
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Insert RecipientCertificate placeholders
    recipient_objs = []
    for name, email, custom_attrs in recipient_rows:
        rec_obj = RecipientCertificate(
            job_id=job.id,
            recipient_name=name,
            recipient_email=email,
            custom_attributes=custom_attrs,
            status="PENDING"
        )
        recipient_objs.append(rec_obj)

    db.bulk_save_objects(recipient_objs)
    db.commit()
    db.refresh(job)

    if async_process and background_tasks:
        background_tasks.add_task(run_background_job, job.id)
    else:
        JobProcessor.process_job(job.id, db)
        db.refresh(job)

    return build_job_response(job)
