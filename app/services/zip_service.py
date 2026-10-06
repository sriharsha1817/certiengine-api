import io
import os
import zipfile
from pathlib import Path
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.models import RecipientCertificate, RecipientStatus

class ZipService:
    """
    Archives generated certificates for a bulk job into a downloadable ZIP stream.
    """

    @staticmethod
    def create_job_zip(job_id: str, db: Session, file_format: str = "pdf") -> Tuple[io.BytesIO, str]:
        recipients = db.query(RecipientCertificate).filter(
            RecipientCertificate.job_id == job_id,
            RecipientCertificate.status == RecipientStatus.SUCCESS.value
        ).all()

        zip_buffer = io.BytesIO()
        file_count = 0

        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for recipient in recipients:
                target_file_str = recipient.pdf_path if file_format.lower() == "pdf" else recipient.png_path
                if target_file_str and os.path.exists(target_file_str):
                    ext = "pdf" if file_format.lower() == "pdf" else "png"
                    # Clean filename e.g., "John_Doe_CERT-123.pdf"
                    safe_name = "".join(c for c in recipient.recipient_name if c.isalnum() or c in (" ", "_", "-")).strip()
                    arc_filename = f"{safe_name}_{recipient.id[:8]}.{ext}"
                    zf.write(target_file_str, arcname=arc_filename)
                    file_count += 1

        zip_buffer.seek(0)
        zip_name = f"certificates_job_{job_id[:8]}.zip"
        return zip_buffer, zip_name
