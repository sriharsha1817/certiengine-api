import pytest
from fastapi import status

def test_create_generation_job_sync(client):
    payload = {
        "event_name": "Python FastAPI Advanced Workshop",
        "issuer_name": "Tech Corp",
        "issuer_title": "Lead Instructor",
        "template_style": "classic",
        "recipients": [
            {"name": "Alice Smith", "email": "alice@example.com", "custom_attributes": {"score": "95%"}},
            {"name": "Bob Jones", "email": "bob@example.com", "custom_attributes": {"role": "Attendee"}}
        ]
    }
    
    response = client.post("/api/v1/jobs?async_process=false", json=payload)
    assert response.status_code == status.HTTP_202_ACCEPTED
    
    data = response.json()
    assert data["event_name"] == "Python FastAPI Advanced Workshop"
    assert data["total_count"] == 2
    assert data["success_count"] == 2
    assert data["failed_count"] == 0
    assert data["status"] == "COMPLETED"
    assert data["progress_percentage"] == 100.0
    assert len(data["recipients"]) == 2

def test_get_job_status(client):
    payload = {
        "event_name": "Machine Learning Bootcamp",
        "issuer_name": "AI Institute",
        "template_style": "modern",
        "recipients": [
            {"name": "Charlie Brown", "email": "charlie@example.com"}
        ]
    }
    
    create_resp = client.post("/api/v1/jobs?async_process=false", json=payload)
    job_id = create_resp.json()["id"]

    get_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert get_resp.status_code == status.HTTP_200_OK
    
    data = get_resp.json()
    assert data["id"] == job_id
    assert data["status"] == "COMPLETED"
    assert data["success_count"] == 1

def test_list_jobs(client):
    # Create 2 jobs
    for i in range(2):
        client.post("/api/v1/jobs?async_process=false", json={
            "event_name": f"Event {i}",
            "recipients": [{"name": f"User {i}", "email": f"user{i}@example.com"}]
        })
    
    list_resp = client.get("/api/v1/jobs")
    assert list_resp.status_code == status.HTTP_200_OK
    data = list_resp.json()
    assert len(data) == 2
