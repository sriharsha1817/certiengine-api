import io
import pytest
from fastapi import status

def test_upload_csv_bulk_job(client):
    csv_content = (
        "name,email,score,role\n"
        "Grace Hopper,grace@navy.mil,100%,Pioneer\n"
        "Ada Lovelace,ada@algorithm.org,99%,Inventor\n"
    )
    
    files = {
        "file": ("recipients.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")
    }
    data = {
        "event_name": "History of Computing Masterclass",
        "issuer_name": "ACM",
        "template_style": "elegant",
        "async_process": "false"
    }

    response = client.post("/api/v1/jobs/upload-csv", files=files, data=data)
    assert response.status_code == status.HTTP_202_ACCEPTED
    
    jdata = response.json()
    assert jdata["event_name"] == "History of Computing Masterclass"
    assert jdata["total_count"] == 2
    assert jdata["success_count"] == 2
    assert jdata["status"] == "COMPLETED"
    assert len(jdata["recipients"]) == 2
    assert jdata["recipients"][0]["custom_attributes"]["score"] == "100%"
