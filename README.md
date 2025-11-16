# AI CV Screening Backend

This project is a Django-based backend service that automates the initial screening of job applications. It uses a RAG (Retrieval-Augmented Generation) pipeline to evaluate a candidate's CV and project report against a job description and a case study brief.

## Features

-   **RESTful API**: Endpoints for uploading documents, triggering evaluations, and retrieving results.
-   **Asynchronous Processing**: Uses Celery and Redis to handle long-running AI evaluation tasks without blocking API requests.
-   **RAG Pipeline**: Ingests reference documents into a ChromaDB vector store and retrieves them to provide context to an LLM for evaluation.
-   **LLM Chaining**: Uses Langchain to structure the evaluation process into multiple steps (CV evaluation, project report evaluation, final summary).
-   **Secure Endpoints**: API endpoints are protected using JWT authentication.

## Project Structure

-   `cv_screening`: The main Django project directory.
-   `api`: A Django app for the RESTful API (views, serializers, URLs).
-   `evaluations`: A Django app for the data models, Celery tasks, and AI pipeline logic.
-   `documents`: Contains the internal documents used for the RAG system and the ingestion script.
-   `chroma_db`: The directory where the ChromaDB vector store is persisted.
-   `media`: The directory where uploaded CVs and project reports are stored.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd cv-screening
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

# CV Screening — AI-powered CV & Project Report Evaluation

CV Screening adalah backend service berbasis Django yang otomatis melakukan screening awal terhadap pelamar kerja. Sistem ini menggunakan pendekatan RAG (Retrieval-Augmented Generation) yang mengombinasikan vector search (ChromaDB) dengan LLM untuk memberikan penilaian terstruktur terhadap CV dan laporan proyek.

Ringkasan singkat:
- Bahasa: Python 3.8+
- Framework: Django + Django REST Framework
- Asynchronous: Celery + Redis
- Vector store: ChromaDB
- LLM orchestration: LangChain (dengan dukungan model eksternal seperti Google Gemini / HuggingFace)

## Fitur Utama

- Endpoint REST untuk upload file, trigger evaluasi, dan mengambil hasil
- Evaluasi asinkron via Celery untuk menghindari blocking API
- RAG pipeline: referensi dokumen diindeks ke ChromaDB untuk retrieval konteks
- LangChain untuk menyusun proses evaluasi berlapis (CV -> Project -> Summary)
- Keamanan: autentikasi JWT dan rate limiting untuk proteksi sumber daya

## Struktur Proyek

- `cv_screening/` — Django project settings, WSGI, konfigurasi
- `api/` — Views, serializers, URL routing untuk publik API
- `core/` — Domain models, use-cases, dan infrastruktur (parser, LLM, persistence)
- `evaluations/` — Celery tasks dan orchestration untuk evaluasi
- `documents/` — Dokumen internal yang digunakan untuk RAG ingestion
- `chroma_db/` — Penyimpanan lokal ChromaDB
- `media/` — Upload file oleh pengguna

## Quickstart (Development)

1) Clone repo dan buat virtualenv

```bash
git clone <repository-url>
cd cv-screening
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2) Buat file `.env` di root (contoh sudah tersedia). Pastikan variabel penting seperti `SECRET_KEY`, `REDIS_URL`, `GOOGLE_API_KEY` di-set.

3) Migrasi dan buat superuser

```bash
python manage.py migrate
python manage.py createsuperuser
```

4) Jalankan Redis, Celery, dan Django

Terminal 1: Redis

```bash
redis-server
```

Terminal 2: Celery

```bash
celery -A cv_screening worker -l info --concurrency=4
```

Terminal 3: Django

```bash
python manage.py runserver
```

5) Ingest dokumen referensi ke ChromaDB (opsional)

```bash
python manage.py ingest
```

## Environment & Konfigurasi penting

- `.env`
  - `SECRET_KEY` — kunci Django
  - `REDIS_URL` — lokasi Redis (mis. `redis://127.0.0.1:6379/1`)
  - `THROTTLE_UPLOAD`, `THROTTLE_EVALUATE`, dsb — rate limits per endpoint
  - `JWT_ACCESS_TOKEN_LIFETIME`, `JWT_REFRESH_TOKEN_LIFETIME` — token lifetime

## API Endpoints (Ringkas)

- POST `/api/token/` — ambil JWT access & refresh
- POST `/api/upload/` — upload file (CV / project report)
- POST `/api/evaluate/` — trigger evaluasi (menghasilkan job ID)
- GET `/api/result/<job_id>/` — ambil status & hasil evaluasi

Contoh: upload file

```bash
curl -X POST http://localhost:8000/api/upload/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "file=@cv.pdf"
```

Contoh: trigger evaluasi

```bash
curl -X POST http://localhost:8000/api/evaluate/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"job_title":"Backend Developer","cv_id":"<cv-uuid>","project_report_id":"<proj-uuid>"}'
```

## Arsitektur & Alur Kerja

1. User meng-upload CV dan/atau report melalui `/api/upload/`.
2. User memanggil `/api/evaluate/` dengan `cv_id` dan `project_report_id`.
3. Sistem membuat `EvaluationJob` (status `queued`) dan men-trigger Celery task `evaluate_documents`.
4. Worker Celery membangun komposisi dependensi (repository, parser, LLM service, vector store).
5. Use case `EvaluateCandidateUseCase`:
   - parse teks CV & project
   - retrieve konteks via ChromaDB
   - panggil LLM untuk: evaluasi CV, evaluasi project, dan generate summary
   - parsing hasil, isi fields pada `EvaluationJob` dan set status `completed` atau `failed`

## Rate Limiting

Rate limiting dikonfigurasi via DRF throttle classes dan Redis backend. Default limits disimpan di `.env`.

Contoh default (di `.env`):
- `THROTTLE_UPLOAD=5/hour`
- `THROTTLE_EVALUATE=3/hour`
- `THROTTLE_RESULT=20/hour`
- `THROTTLE_TOKEN=5/min`

Jika limit tercapai, server mengembalikan HTTP 429 dengan header `Retry-After`.

## Pengujian & Debugging

- Lint/syntax check:

```bash
python -m py_compile api/throttles.py api/views.py cv_screening/settings.py
python manage.py check
```

- Test rate limiting: kirim banyak request cepat pada endpoint `/api/token/` dan perhatikan HTTP 429.

## Deployment (singkat)

- Gunakan PostgreSQL untuk production dan nonaktifkan `DEBUG`.
- Gunakan Gunicorn + Nginx sebagai reverse proxy.
- Gunakan Redis terkelola untuk reliability.
- Pastikan `SECRET_KEY` aman, `ALLOWED_HOSTS` di-set, dan HTTPS diaktifkan.

Contoh singkat menjalankan Gunicorn:

```bash
gunicorn --workers 4 --bind 0.0.0.0:8000 cv_screening.wsgi
```

## Kontribusi

1. Fork repo
2. Buat branch fitur: `git checkout -b feature/namafitur`
3. Commit perubahan, push, dan buat PR

## Troubleshooting

- Jika Redis tidak berjalan: `redis-server` atau periksa `REDIS_URL`.
- Jika Celery tidak memproses task: jalankan worker dengan logging dan periksa queue Redis.
- Jika rate limit dianggap terlalu ketat: sesuaikan nilai di `.env`.

## Lisensi

Lisensi proyek ini tidak disertakan — tambahkan `LICENSE` jika diperlukan.

---

Jika Anda ingin, saya bisa juga membuat contoh Postman collection, atau menambahkan dokumentasi OpenAPI/Swagger.
