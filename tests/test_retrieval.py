import pytest
from fastapi import status

def test_certificate_retrieval_and_download(client):
    # Create job
    create_resp = client.post("/api/v1/jobs?async_process=false", json={
        "event_name": "DevOps Foundations",
        "recipients": [{"name": "Daniel Craig", "email": "daniel@example.com"}]
    })
    
    job_data = create_resp.json()
    cert_id = job_data["recipients"][0]["id"]

    # 1. Get Details
    details_resp = client.get(f"/api/v1/certificates/{cert_id}")
    assert details_resp.status_code == status.HTTP_200_OK
    assert details_resp.json()["recipient_name"] == "Daniel Craig"
    assert details_resp.json()["status"] == "SUCCESS"

    # 2. Download PDF
    pdf_resp = client.get(f"/api/v1/certificates/{cert_id}/download?format=pdf")
    assert pdf_resp.status_code == status.HTTP_200_OK
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 1000

    # 3. Download PNG
    png_resp = client.get(f"/api/v1/certificates/{cert_id}/download?format=png")
    assert png_resp.status_code == status.HTTP_200_OK
    assert png_resp.headers["content-type"] == "image/png"
    assert len(png_resp.content) > 1000

    # 4. Verify Certificate Seal
    verify_resp = client.get(f"/api/v1/certificates/verify/{cert_id}")
    assert verify_resp.status_code == status.HTTP_200_OK
    vdata = verify_resp.json()
    assert vdata["is_valid"] is True
    assert vdata["recipient_name"] == "Daniel Craig"
    assert vdata["event_name"] == "DevOps Foundations"

    # 5. Download All (ZIP Archive)
    job_id = job_data["id"]
    zip_resp = client.get(f"/api/v1/jobs/{job_id}/download-all?format=pdf")
    assert zip_resp.status_code == status.HTTP_200_OK
    assert zip_resp.headers["content-type"] == "application/zip"
    assert len(zip_resp.content) > 500

def test_verify_nonexistent_certificate(client):
    verify_resp = client.get("/api/v1/certificates/verify/nonexistent-id")
    assert verify_resp.status_code == status.HTTP_200_OK
    vdata = verify_resp.json()
    assert vdata["is_valid"] is False
    assert vdata["status"] == "NOT_FOUND"
