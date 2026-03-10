# Textify

**AI-powered document intelligence system** that transforms handwritten study material into structured learning resources.

Textify converts handwritten notes PDFs into clean digital notes and generates practice-ready question sets.

---

## Features

### Notes Conversion Mode
Upload handwritten PDF notes and Textify will:
- Convert handwriting into digital text using vision AI models
- Detect headings, paragraphs, and document structure
- Detect and convert math expressions into LaTeX
- Generate a clean, well-formatted PDF of the notes

### Practice Mode
When practice mode is enabled, Textify will:
- Detect question blocks, multiple choice options, answers, and explanations
- Remove answers, check marks, circled answers, highlighted options, and solutions
- Generate a practice PDF containing only questions and options

### Concept Extraction
Textify analyzes text and extracts key concepts (e.g., Linear Algebra, Vector Space, Eigenvalues), associates questions with detected concepts, and stores them in a concept graph structure.

---

## Architecture

```
User → Next.js Frontend → FastAPI Backend → Redis Queue → Celery Workers → PostgreSQL + S3 Storage → Generated PDFs
```

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js (React, TypeScript) |
| Backend API | FastAPI (Python) |
| Task Queue | Celery + Redis |
| Database | PostgreSQL |
| Object Storage | S3-compatible (MinIO for local) |
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

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload a handwritten PDF |
| POST | `/api/jobs/start` | Start processing a job |
| GET | `/api/jobs/{id}/status` | Get job processing status |
| GET | `/api/jobs/{id}/result` | Get job results and download links |
| GET | `/api/download/{file}` | Download a generated file |
| GET | `/health` | Health check |

---

## Worker System

- Celery workers process documents asynchronously via Redis
- Pages are processed independently for parallel processing
- Workers are idempotent — safe to retry
- Failed page processing retries up to 3 times
- API keys exist only during processing and are discarded after job completion

---

## Supported AI Providers

Textify is **model-agnostic**. Users supply their own API key at processing time.

| Provider | Model |
|----------|-------|
| Google Gemini | gemini-1.5-flash |
| OpenAI | gpt-4o |
| Anthropic | claude-sonnet-4-20250514 |

API keys are **never stored permanently** — they exist only during processing and are discarded after job completion.

---

## Repository Structure

```
textify/
├── backend/
│   ├── app/
│   │   ├── api/routes.py          # API endpoints
│   │   ├── models/models.py       # SQLAlchemy ORM models
│   │   ├── schemas/schemas.py     # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── storage.py         # S3-compatible storage service
│   │   │   └── worker_client.py   # Celery task dispatch
│   │   ├── pipeline/
│   │   │   ├── pdf_processor.py
│   │   │   ├── image_preprocessor.py
│   │   │   ├── layout_detector.py
│   │   │   ├── document_classifier.py
│   │   │   ├── handwriting_engine.py
│   │   │   ├── math_parser.py
│   │   │   ├── question_extractor.py
│   │   │   ├── concept_extractor.py
│   │   │   └── document_builder.py
│   │   ├── config.py              # Application configuration
│   │   ├── database.py            # Database setup
│   │   └── main.py                # FastAPI application entry
│   ├── templates/
│   │   ├── notes_template.html    # Notes PDF template
│   │   └── practice_template.html # Practice PDF template
│   ├── tests/                     # Backend tests
│   └── requirements.txt
├── frontend/                      # Next.js frontend
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx               # Main UI component
│   │   └── globals.css
│   └── package.json
├── workers/
│   ├── celery_app.py              # Celery configuration
│   └── tasks.py                   # Document processing tasks
├── infra/
│   ├── Dockerfile.backend
│   ├── Dockerfile.worker
│   └── Dockerfile.frontend
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://textify:textify@localhost:5432/textify` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery result backend URL | `redis://localhost:6379/1` |
| `S3_ENDPOINT_URL` | S3-compatible storage endpoint | `http://localhost:9000` |
| `S3_ACCESS_KEY` | S3 access key | `minioadmin` |
| `S3_SECRET_KEY` | S3 secret key | `minioadmin` |
| `S3_BUCKET_NAME` | S3 bucket name | `textify` |
| `S3_REGION` | S3 region | `us-east-1` |
| `DEBUG` | Enable debug mode | `false` |
| `MAX_UPLOAD_SIZE_MB` | Max upload file size in MB | `50` |
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:3000"]` |
| `NEXT_PUBLIC_API_URL` | Backend API URL (frontend) | `http://localhost:8000` |

---

## Local Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 16
- Redis 7
- MinIO (or any S3-compatible storage)
- poppler-utils (for pdf2image)

### 1. Clone the repository
```bash
git clone https://github.com/chandankumar123456/Textify.git
cd Textify
```

### 2. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start infrastructure services
Start PostgreSQL, Redis, and MinIO. You can use Docker for these:
```bash
docker run -d --name textify-postgres -e POSTGRES_USER=textify -e POSTGRES_PASSWORD=textify -e POSTGRES_DB=textify -p 5432:5432 postgres:16-alpine
docker run -d --name textify-redis -p 6379:6379 redis:7-alpine
docker run -d --name textify-minio -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address ":9001"
```

### 4. Install backend dependencies
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 5. Start the backend
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Start the Celery worker
```bash
# From the project root, with backend venv activated
PYTHONPATH=backend celery -A workers.celery_app worker --loglevel=info -Q document_processing,page_processing --concurrency=2
```

### 7. Install and start the frontend
```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

### 8. Open the app
Navigate to [http://localhost:3000](http://localhost:3000) in your browser.

---

## Docker Setup Instructions

### Start all services
```bash
docker compose up --build
```

This starts:
- **Frontend** at [http://localhost:3000](http://localhost:3000)
- **Backend API** at [http://localhost:8000](http://localhost:8000)
- **Celery Worker** for background processing
- **PostgreSQL** database
- **Redis** queue
- **MinIO** object storage (console at [http://localhost:9001](http://localhost:9001))

### Stop all services
```bash
docker compose down
```

### Stop and remove data
```bash
docker compose down -v
```

---

## How to Use

1. Open the Textify frontend at [http://localhost:3000](http://localhost:3000)
2. Upload a handwritten PDF
3. Select the mode (Notes Conversion or Practice Mode)
4. Select your AI provider (Gemini, OpenAI, or Anthropic)
5. Enter your API key (it is used only during processing and never stored)
6. Click **Generate**
7. Monitor progress in real-time
8. Download the generated PDFs when processing completes

---

## Extending the System

### Adding a new AI provider
1. Add a new method in `backend/app/pipeline/handwriting_engine.py`
2. Update the provider validation in `backend/app/api/routes.py`
3. Update the frontend dropdown in `frontend/app/page.tsx`

### Adding a new output format
1. Create a new HTML template in `backend/templates/`
2. Add a build method in `backend/app/pipeline/document_builder.py`
3. Update the worker task in `workers/tasks.py` to use the new builder

### Adding new pipeline modules
1. Create a new module in `backend/app/pipeline/`
2. Import and use it in `workers/tasks.py`

### Database migrations
The project uses SQLAlchemy with auto-creation on startup. For production, use Alembic:
```bash
cd backend
alembic init migrations
alembic revision --autogenerate -m "initial"
alembic upgrade head
```
