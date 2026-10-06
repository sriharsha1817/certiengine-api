import pytest
from fastapi import status

def test_validation_empty_event_name(client):
    payload = {
        "event_name": "  ",
        "recipients": [{"name": "John Doe", "email": "john@example.com"}]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_validation_empty_recipient_name(client):
    payload = {
        "event_name": "Web Security 101",
        "recipients": [{"name": "   ", "email": "john@example.com"}]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_validation_invalid_email_schema(client):
    payload = {
        "event_name": "Web Security 101",
        "recipients": [{"name": "John Doe", "email": "not-an-email"}]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_validation_invalid_template_style(client):
    payload = {
        "event_name": "Design Systems",
        "template_style": "unknown_theme",
        "recipients": [{"name": "John Doe", "email": "john@example.com"}]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_validation_empty_recipients_list(client):
    payload = {
        "event_name": "Cloud Computing",
        "recipients": []
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
