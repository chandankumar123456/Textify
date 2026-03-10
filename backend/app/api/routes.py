import uuid
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import Job, JobStatus as JobStatusEnum, JobMode, Concept
from ..schemas.schemas import (
    UploadResponse, JobStatus, JobResult, StartJobRequest, StartJobResponse, ErrorResponse
)
from ..services.storage import StorageService
from ..services.worker_client import start_processing_job
from ..config import settings

router = APIRouter()
storage = StorageService()

@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    mode: str = Form(...),
    model_provider: str = Form(...),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")
    
    if mode not in ("notes", "practice"):
        raise HTTPException(status_code=400, detail="Mode must be 'notes' or 'practice'")
    
    if model_provider not in ("gemini", "openai", "anthropic"):
        raise HTTPException(status_code=400, detail="Invalid model provider")
    
    job_id = uuid.uuid4()
    s3_key = f"uploads/{job_id}/{file.filename}"
    
    storage.upload_bytes(s3_key, content, content_type="application/pdf")
    
    job = Job(
        id=job_id,
        status=JobStatusEnum.QUEUED,
        mode=JobMode(mode),
        model_provider=model_provider,
        original_filename=file.filename,
        s3_input_key=s3_key,
    )
    db.add(job)
    db.commit()
    
    return UploadResponse(job_id=job_id, filename=file.filename, message="File uploaded successfully")

@router.post("/jobs/start", response_model=StartJobResponse)
async def start_job(request: StartJobRequest, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == request.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatusEnum.QUEUED:
        raise HTTPException(status_code=400, detail=f"Job is already {job.status.value}")
    
    job.status = JobStatusEnum.PROCESSING
    db.commit()
    
    start_processing_job(
        str(job.id),
        job.s3_input_key,
        job.mode.value,
        request.model_provider,
        request.api_key
    )
    
    return StartJobResponse(
        job_id=job.id,
        status="processing",
        message="Job processing started"
    )

@router.get("/jobs/{job_id}/status", response_model=JobStatus)
async def get_job_status(job_id: uuid.UUID, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/jobs/{job_id}/result", response_model=JobResult)
async def get_job_result(job_id: uuid.UUID, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatusEnum.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Job is not completed. Current status: {job.status.value}")
    
    concepts = db.query(Concept).filter(Concept.job_id == job_id).all()
    concept_list = [
        {"name": c.name, "related_concepts": c.related_concepts or [], "question_ids": c.question_ids or []}
        for c in concepts
    ]
    
    return JobResult(
        id=job.id,
        status=job.status.value,
        mode=job.mode.value,
        result_files=job.result_files or [],
        concepts=concept_list
    )

@router.get("/download/{file_path:path}")
async def download_file(file_path: str):
    try:
        data = storage.download_bytes(file_path)
        content_type = "application/pdf" if file_path.endswith(".pdf") else "application/octet-stream"
        filename = file_path.split("/")[-1]
        return StreamingResponse(
            iter([data]),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
