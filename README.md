# Textify

**AI-powered document intelligence system** that transforms handwritten study material into structured learning resources.

Textify converts handwritten notes PDFs into clean digital notes and generates practice-ready question sets — running entirely on your local machine with no cloud services required.

---

## Features

### Notes Conversion Mode
Upload handwritten PDF notes and Textify will:
- Convert handwriting into digital text using a vision AI model
- Detect headings, paragraphs, and document structure
- Detect and convert math expressions into LaTeX
- Generate a clean, well-formatted PDF of the notes

### Practice Mode
When practice mode is enabled, Textify will:
- Detect question blocks, multiple choice options, answers, and explanations
- Remove answers, check marks, and highlighted options
- Generate a practice PDF containing only questions and options

### Concept Extraction
Textify analyzes text and extracts key concepts (e.g., Linear Algebra, Vector Space, Eigenvalues), associates questions with detected concepts, and stores them in a concept graph structure.

---

## Local Architecture

```
User → Next.js Frontend → FastAPI Backend (background thread) → SQLite + Local Files → Generated PDFs
```

All processing happens in-process inside FastAPI using a background thread. No Redis, no Celery, no object storage service required.

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js (React, TypeScript) |
| Backend API | FastAPI (Python) |
| Background Processing | Python `threading.Thread` |
| Database | SQLite (default) or PostgreSQL |
| File Storage | Local filesystem (`data/`) |
| PDF Generation | WeasyPrint |

---

## Document Processing Pipeline

```
PDF Upload → Split to Page Images → Image Preprocessing → Handwriting Transcription (Vision AI)
→ Layout Detection → Document Classification → Question Extraction → Concept Extraction
→ Structured JSON → Document Reconstruction → PDF Generation
```

### Pipeline Modules

| Module | Responsibility |
|--------|---------------|
| `pdf_processor` | Splits PDF into individual page images |
| `image_preprocessor` | Normalizes images (orientation, size, color) |
| `layout_detector` | Organizes content into layout regions |
| `document_classifier` | Classifies pages as notes, questions, or mixed |
| `handwriting_engine` | Vision API integration (Gemini, OpenAI, Anthropic) |
| `math_parser` | Detects and formats LaTeX math expressions |
| `question_extractor` | Extracts and cleans question blocks |
| `concept_extractor` | Extracts key concepts and builds concept graph |
| `document_builder` | Builds HTML documents for PDF generation |

---

## Repository Structure

```
textify/
├── backend/
│   ├── app/
│   │   ├── api/routes.py              # API endpoints
│   │   ├── models/models.py           # SQLAlchemy ORM models
│   │   ├── schemas/schemas.py         # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── storage.py             # Local filesystem storage service
│   │   │   ├── processor.py           # Document processing pipeline (runs in thread)
│   │   │   └── worker_client.py       # Dispatches processing background thread
│   │   ├── pipeline/                  # PDF/AI processing modules
│   │   ├── config.py                  # Application configuration
│   │   ├── database.py                # SQLAlchemy engine (SQLite or PostgreSQL)
│   │   └── main.py                    # FastAPI application entry point
│   ├── templates/                     # HTML templates for PDF generation
│   ├── tests/
│   └── requirements.txt
├── frontend/                          # Next.js frontend
│   ├── app/
│   │   ├── page.tsx                   # Main UI component
│   │   └── globals.css
│   └── package.json
├── workers/
│   ├── celery_app.py                  # Legacy Celery config (not used locally)
│   └── tasks.py                       # Re-exports processor for optional Celery use
├── data/                              # Runtime data (git-ignored except .gitkeep)
│   ├── uploads/                       # Uploaded PDFs
│   ├── pages/                         # Per-page images extracted from PDFs
│   └── results/                       # Generated output PDFs
├── infra/                             # Dockerfiles (optional containerised setup)
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload a handwritten PDF |
| POST | `/api/jobs/start` | Start processing a job |
| GET | `/api/jobs/{id}/status` | Get job processing status |
| GET | `/api/jobs/{id}/result` | Get job results and file keys |
| GET | `/api/download/{file_path}` | Download a generated file |
| GET | `/health` | Health check |

---

## Supported AI Providers

Textify is **model-agnostic**. Users supply their own API key at processing time.

| Provider | Model |
|----------|-------|
| Google Gemini | gemini-1.5-flash |
| OpenAI | gpt-4o |
| Anthropic | claude-sonnet-4-20250514 |

API keys are **never stored** — they exist only in memory during processing.

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./data/textify.db` |
| `DATA_DIR` | Root directory for local file storage | `data` |
| `DEBUG` | Enable debug mode | `false` |
| `MAX_UPLOAD_SIZE_MB` | Max upload file size | `50` |
| `CORS_ORIGINS` | Allowed CORS origins (JSON list) | `["http://localhost:3000"]` |
| `NEXT_PUBLIC_API_URL` | Backend API URL (used by frontend) | `http://localhost:8000` |

To use **PostgreSQL** instead of SQLite:
```
DATABASE_URL=postgresql://user:password@localhost:5432/textify
```
and uncomment `psycopg2-binary` in `backend/requirements.txt`.

---

## Local Setup

### Prerequisites

- **Python 3.11+**
- **Node.js 20+** (for the frontend)
- **poppler-utils** — required by `pdf2image` for PDF splitting
  - macOS: `brew install poppler`
  - Ubuntu/Debian: `sudo apt install poppler-utils`
  - Windows: download from [poppler releases](https://github.com/oschwartz10612/poppler-windows/releases) and add `bin/` to PATH

### 1. Clone the repository

```bash
git clone https://github.com/chandankumar123456/Textify.git
cd Textify
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env if you want to change any defaults (all have sensible local defaults)
```

### 3. Install backend dependencies

```bash
cd backend
python -m venv venv
# Activate the virtual environment:
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### 4. Start the backend

```bash
# From the backend/ directory with venv active:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will:
- Create the `data/uploads/`, `data/pages/`, and `data/results/` directories automatically
- Create `data/textify.db` (SQLite) on first startup
- Be available at [http://localhost:8000](http://localhost:8000)
- Show API docs at [http://localhost:8000/docs](http://localhost:8000/docs)

### 5. Install and start the frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

The frontend will be available at [http://localhost:3000](http://localhost:3000).

> **That's it.** No Redis, no Celery worker, no MinIO, no Docker required.

---

## How Documents Are Processed

1. **Upload** — The frontend POSTs the PDF to `/api/upload`. The backend saves it to `data/uploads/{job_id}/{filename}` and creates a `QUEUED` job record in the database.

2. **Start job** — The frontend POSTs to `/api/jobs/start`. The backend spawns a background daemon thread that runs the full pipeline:

   ```
   PDF → page images (data/pages/) → vision AI transcription → question/concept extraction → PDF generation (data/results/)
   ```

3. **Poll status** — The frontend polls `/api/jobs/{id}/status`. The background thread updates the job's `status`, `processed_pages`, and `total_pages` in the database as it progresses.

4. **Download results** — When status is `completed`, the frontend fetches `/api/jobs/{id}/result` to get the list of result file keys, then downloads each via `/api/download/{file_key}`.

---

## How to Use

1. Open [http://localhost:3000](http://localhost:3000)
2. Upload a handwritten PDF
3. Select the mode (Notes Conversion or Practice Mode)
4. Select your AI provider (Gemini, OpenAI, or Anthropic)
5. Enter your API key (used only during processing, never stored)
6. Click **Generate**
7. Monitor progress in real-time
8. Download the generated PDFs when complete

---

## Extending the System

### Adding a new AI provider
1. Add a new method in `backend/app/pipeline/handwriting_engine.py`
2. Update provider validation in `backend/app/api/routes.py`
3. Update the frontend dropdown in `frontend/app/page.tsx`

### Adding a new output format
1. Create a new HTML template in `backend/templates/`
2. Add a build method in `backend/app/pipeline/document_builder.py`
3. Use it in `backend/app/services/processor.py`

### Adding new pipeline modules
1. Create a new module in `backend/app/pipeline/`
2. Import and call it in `backend/app/services/processor.py`

### Switching to PostgreSQL
1. Uncomment `psycopg2-binary` in `backend/requirements.txt` and run `pip install psycopg2-binary`
2. Set `DATABASE_URL=postgresql://user:password@localhost:5432/textify` in `.env`

### Scaling with Celery (distributed deployment)
The `workers/` directory retains a Celery configuration for future distributed deployments:
1. Install `celery[redis]` and `redis` packages
2. Set `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` in `.env`
3. Run: `celery -A workers.celery_app worker --loglevel=info -Q document_processing`

---

## Docker Setup (optional)

To run with Docker (includes PostgreSQL and Redis):

```bash
docker compose up --build
```

To stop:
```bash
docker compose down
```

