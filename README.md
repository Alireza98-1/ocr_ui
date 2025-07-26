# Unified Persian OCR System

[![Python-Version](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![Celery](https://img.shields.io/badge/Async-Celery-orange.svg)](https://docs.celeryq.dev/en/stable/)

## ✨ Key Features

* **Asynchronous & Scalable**: FastAPI handles requests, Celery with RabbitMQ processes tasks in the background.
* **Multi-Format Support**: PDF (multi-page) and images (`.jpg`, `.png`, `.jpeg`).
* **Unified Pipeline**: Single optimized service for detection (YOLO) and recognition (Parseq).
* **High Accuracy**: Advanced deep-learning models for precise line/word detection and text extraction.
* **Webhook Notifications**: Results pushed to client-provided endpoint with retry logic.
* **Horizontal Scaling**: Increase Celery workers to match load.

---

## 🏗️ Architecture Overview

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant Queue as RabbitMQ
    participant Worker as Celery Worker
    participant Webhook

    Client->>+API: POST /api/v1/ocr (files + metadata + webhook_url)
    API->>API: Validate & queue tasks
    API->>Queue: enqueue process_task
    API-->>-Client: 200 OK (queued)

    Worker->>+Queue: dequeued process_task
    Worker->>Worker: OCR Pipeline Service
    Worker->>Queue: enqueue webhook_task

    Worker->>+Queue: dequeued webhook_task
    Worker->>+Webhook: POST results
    Webhook-->>-Worker: 200 OK
```

```mermaid
flowchart LR
    A[Client]
    B[FastAPI]
    C[RabbitMQ]
    D[Celery Worker]
    E[Webhook Endpoint]

    A -->|POST /api/v1/ocr| B
    B -->|enqueue| C
    C -->|dequeue| D
    D -->|process OCR| D
    D -->|enqueue| C
    C -->|dequeue| D
    D -->|POST results| E
```

---

## 🚀 Setup & Installation

1. **Clone** the repository:

   ```bash
   git clone <repo_url>
   cd <project_dir>
   ```

2. **Install** dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure** environment:

   * Create a `.env` in project root:

     ```env
     CELERY_BROKER_URL="amqp://guest:guest@localhost:5672//"
     CELERY_BACKEND_URL="redis://localhost:6379/0"
     ALLOW_INSECURE_WEBHOOKS=True
     ```
   * Place `master_config.json` alongside with model paths:

     ```json
     {
       "debug": false,
       "detection": { ... },
       "recognition": { ... },
       "pipeline": { ... },
       "valid_ocr_formats": [ ... ]
     }
     ```

4. **Start** services:

   * **Celery Workers**:

     ```bash
     celery -A app.worker.celery_app worker --loglevel=info -c 4
     ```
   * **FastAPI Server**:

     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port 8000
     ```

---

## 📦 API Usage

**Endpoint**: `POST /api/v1/ocr`

**Parameters** (multipart/form-data):

* `files`: PDF/image files (one or more).
* `metadata`: JSON array of objects `{ guid: string, file_type: string }`.
* `webhook_url`: URL to receive results.

**Example**:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/ocr \
  -F "files=@/path/doc.pdf" \
  -F 'metadata=[{"guid":"uuid-123","file_type":"application/pdf"}]' \
  -F "webhook_url=http://your-server.com/receive"
```

**Webhook Payload** (`application/json`):

```json
{
  "task_id": "...",
  "guid": "uuid-123",
  "text": "Base64-encoded text",
  "status": "completed",
  "confidence": 0.95,
  "error": ""
}
```

---

## 🧪 Stress Testing

Use `stress_test.py` to simulate load:

1. Place test files next to `stress_test.py`.
2. Install extras:

   ```bash
   pip install aiohttp aiofiles
   ```
3. Run:

   ```bash
   python stress_test.py
   ```
