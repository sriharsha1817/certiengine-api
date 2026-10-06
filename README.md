# 📜 Bulk Certificate Generator API & Web Dashboard

A robust, production-grade **Bulk Certificate Generator Backend API** built with **Python**, **FastAPI**, **SQLAlchemy**, **ReportLab**, and **Pillow**.

The system accepts bulk certificate generation requests for large recipient lists via JSON payload or CSV upload, validates data per recipient, renders high-resolution PDF vector certificates and PNG previews with embedded verification QR codes, handles partial failures gracefully, tracks progress in real-time, and provides endpoints for individual certificate downloads, verification seals, and ZIP archive exports.

---

## 🌟 Key Features

- **Bulk Certificate Generation API**: Submit up to 1,000 recipients in a single request or via CSV file upload.
- **Resilient Error Isolation**: A failure during certificate generation for one recipient (e.g. malformed email or missing name) is isolated; it records the specific failure reason while allowing all other valid certificates in the job to generate cleanly.
- **Multiple Output Formats**: Generates both vector-quality **PDF** documents (via ReportLab) and crisp **PNG** preview images (via Pillow).
- **Embedded Verification QR Codes**: Each certificate features an embedded QR code linking directly to a public verification URL with SHA-256 cryptographic authenticity hashes.
- **Asynchronous & Synchronous Execution**: Supports background task processing (returning `202 Accepted` immediately for polling) as well as direct synchronous processing.
- **Bulk ZIP Archive Export**: Download all successful certificates in a job as a compressed `.zip` file in a single request.
- **Interactive Web Dashboard**: Glassmorphism UI dashboard built directly into FastAPI for live job creation, CSV drag-and-drop, progress tracking, certificate previews, and verification.
- **Comprehensive Test Suite**: Automated tests using `pytest` covering job creation, schema validation, PDF generation, failure isolation, download endpoints, CSV upload, and authenticity seals.

---

## 🏗️ Architecture & Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Language** | Python 3.12 |
| **Web Framework** | FastAPI (ASGI, Pydantic v2, OpenAPI/Swagger UI) |
| **Database & ORM** | Relational Database (SQLite by default, configurable to PostgreSQL via SQLAlchemy) |
| **PDF Generation** | ReportLab (Vector Canvas, Shapes, Typography, Page Layouts) |
| **PNG Rendering** | Pillow (PIL ImageDraw, High-Res 1600x1131 rendering) |
| **QR Code Generator** | `qrcode` |
| **Testing** | `pytest`, `httpx`, FastAPI `TestClient` |

---

## 🛠️ Project Setup Guide

### 1. Prerequisites
- Python 3.10+ installed on your system.

### 2. Clone / Setup Project Directory
Navigate to the project root directory:
```bash
cd c:\assessment
```

### 3. Create and Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Application

Start the FastAPI development server with Uvicorn:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Once started, access:
- **Interactive Web Dashboard**: [http://localhost:8000](http://localhost:8000)
- **Interactive OpenAPI (Swagger) Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Running Tests

Execute the complete automated test suite with `pytest`:

```bash
pytest
```

To view verbose test execution details:
```bash
pytest -v
```

All 13 integration & unit tests will run against an isolated SQLite test database and temporary file storage.

---

## 📖 How to Use the API

### 1. Submit a Bulk Generation Job (JSON API)

**Endpoint:** `POST /api/v1/jobs`

**Request Body Example:**
```json
{
  "event_name": "Full Stack Web Development Masterclass",
  "issuer_name": "Tech Academy",
  "issuer_title": "Director of Certification",
  "template_style": "classic",
  "issue_date": "October 6, 2026",
  "recipients": [
    {
      "name": "Alice Smith",
      "email": "alice@example.com",
      "custom_attributes": { "grade": "Distinction", "score": "98%" }
    },
    {
      "name": "Bob Johnson",
      "email": "bob@example.com",
      "custom_attributes": { "role": "Participant" }
    }
  ]
}
```

**cURL Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/jobs?async_process=true" \
     -H "Content-Type: application/json" \
     -d '{
       "event_name": "Full Stack Web Development Masterclass",
       "issuer_name": "Tech Academy",
       "template_style": "classic",
       "recipients": [
         {"name": "Alice Smith", "email": "alice@example.com"},
         {"name": "Bob Johnson", "email": "bob@example.com"}
       ]
     }'
```

**Response (HTTP 202 Accepted):**
```json
{
  "id": "e4b1a8d0-5623-4c9f-b3a1-778899aabbcc",
  "event_name": "Full Stack Web Development Masterclass",
  "issuer_name": "Tech Academy",
  "issuer_title": "Director of Certification",
  "template_style": "classic",
  "issue_date": "October 6, 2026",
  "status": "PENDING",
  "progress_percentage": 0.0,
  "total_count": 2,
  "success_count": 0,
  "failed_count": 0,
  "created_at": "2026-10-06T19:50:00Z",
  "recipients": [...]
}
```

---

### 2. Submit Bulk Job via CSV File Upload

**Endpoint:** `POST /api/v1/jobs/upload-csv`

**cURL Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/upload-csv" \
     -F "file=@recipients.csv" \
     -F "event_name=Cybersecurity Essentials" \
     -F "issuer_name=CyberSec Institute" \
     -F "template_style=modern"
```

*Note:* CSV file must contain column headers `name` and `email`. Any extra columns (e.g. `role`, `score`) are converted to recipient attributes.

---

### 3. Check Job Status & Progress

**Endpoint:** `GET /api/v1/jobs/{job_id}`

**cURL Request:**
```bash
curl "http://localhost:8000/api/v1/jobs/e4b1a8d0-5623-4c9f-b3a1-778899aabbcc"
```

**Response:**
```json
{
  "id": "e4b1a8d0-5623-4c9f-b3a1-778899aabbcc",
  "status": "COMPLETED",
  "progress_percentage": 100.0,
  "total_count": 2,
  "success_count": 2,
  "failed_count": 0,
  "recipients": [
    {
      "id": "cert-11223344",
      "recipient_name": "Alice Smith",
      "recipient_email": "alice@example.com",
      "status": "SUCCESS",
      "pdf_download_url": "http://localhost:8000/api/v1/certificates/cert-11223344/download?format=pdf",
      "png_download_url": "http://localhost:8000/api/v1/certificates/cert-11223344/download?format=png",
      "verification_url": "http://localhost:8000/api/v1/certificates/verify/cert-11223344"
    }
  ]
}
```

---

### 4. Retrieve / Download Generated Certificates

- **Download PDF File:**
  ```
  GET /api/v1/certificates/{certificate_id}/download?format=pdf
  ```
- **Download PNG File:**
  ```
  GET /api/v1/certificates/{certificate_id}/download?format=png
  ```
- **Download ALL Certificates in a Job as ZIP:**
  ```
  GET /api/v1/jobs/{job_id}/download-all?format=pdf
  ```
- **Verify Certificate Authenticity:**
  ```
  GET /api/v1/certificates/verify/{certificate_id}
  ```

---

## 📐 Important Implementation & Design Decisions

1. **Background Tasks vs Synchronous Execution**:
   - For bulk generation with large recipient lists (e.g. 500 recipients), synchronous HTTP requests would cause client timeouts.
   - We implemented asynchronous processing via FastAPI's `BackgroundTasks` so the API responds with `202 Accepted` immediately, allowing clients to poll `/api/v1/jobs/{job_id}` or monitor real-time progress.
   - A query parameter `async_process=false` is also provided for test suites and lightweight requests requiring immediate synchronous completion.

2. **Per-Recipient Error Isolation**:
   - In real-world bulk generation, a single bad email address or missing name shouldn't fail the entire job.
   - Each recipient is processed within an isolated `try/except` block. If validation or generation fails for recipient #3, its status is marked as `FAILED` with an explicit `error_message`, while recipients #1, #2, and #4 continue to generate cleanly.
   - Job final state is categorized as `COMPLETED`, `PARTIALLY_FAILED`, or `FAILED`.

3. **Dual Vector PDF & High-Res PNG Rendering**:
   - ReportLab was chosen for vector PDF output to ensure scalable, print-ready certificates.
   - Pillow (PIL) was integrated to render crisp PNG image previews (1600x1131 resolution) so web clients can instantly preview certificates in browser modals without needing external PDF viewer plugins.

4. **Cryptographic Verification & QR Code Embedding**:
   - Each certificate receives a unique UUID and a SHA-256 verification hash derived from certificate metadata.
   - A QR code linking to `/api/v1/certificates/verify/{cert_id}` is automatically rendered onto the certificate footer.

5. **Relational Database Design**:
   - Built with SQLAlchemy ORM using two primary models (`GenerationJob` and `RecipientCertificate`).
   - SQLite is used by default for zero-configuration setup, but the ORM abstraction allows seamless switching to PostgreSQL or MySQL simply by setting `DATABASE_URL` in environment variables.

---

## 📁 Project Directory Structure

```
c:\assessment\
├── app\
│   ├── api\
│   │   ├── jobs.py           # Job submission, status, & ZIP download
│   │   ├── certificates.py   # Certificate retrieval, download, & verification
│   │   ├── upload.py         # CSV file upload bulk creation
│   │   └── router.py         # Combined API router
│   ├── services\
│   │   ├── generator.py      # ReportLab PDF + Pillow PNG certificate engine
│   │   ├── job_processor.py  # Bulk processing worker & error isolation
│   │   └── zip_service.py    # Bulk ZIP archiving
│   ├── static\               # Web Dashboard UI (HTML/CSS/JS)
│   ├── config.py             # Settings & environment configuration
│   ├── database.py           # SQLAlchemy database engine & sessions
│   ├── main.py               # FastAPI app entrypoint
│   ├── models.py             # SQLAlchemy models (Jobs & RecipientCertificates)
│   └── schemas.py            # Pydantic schemas & validation
├── storage\                  # Generated certificate files storage (.pdf, .png)
├── tests\                    # Complete Pytest test suite (13 tests)
├── .env                      # Environment settings
├── pytest.ini                # Pytest configuration
├── requirements.txt          # Dependencies manifest
└── README.md                 # Documentation
```
