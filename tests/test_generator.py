import os
from pathlib import Path
from app.services.generator import CertificateGenerator

def test_certificate_generator_direct_creation():
    pdf_path, png_path, hash_val = CertificateGenerator.generate(
        cert_id="test-cert-12345",
        recipient_name="Emily Watson",
        recipient_email="emily@example.com",
        event_name="Fullstack Web Development",
        issuer_name="Code Academy",
        issuer_title="Head of Curriculum",
        issue_date="October 6, 2026",
        template_style="modern",
        custom_attributes={"grade": "A+", "score": "99%"}
    )

    assert os.path.exists(pdf_path)
    assert os.path.exists(png_path)
    assert len(hash_val) == 64  # SHA-256 length

    assert os.path.getsize(pdf_path) > 1000
    assert os.path.getsize(png_path) > 1000
