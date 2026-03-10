from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class JobCreate(BaseModel):
    mode: str = Field(..., pattern="^(notes|practice)$")
    model_provider: str = Field(..., pattern="^(gemini|openai|anthropic)$")

class JobStatus(BaseModel):
    id: UUID
    status: str
    mode: str
    total_pages: int
    processed_pages: int
    result_files: List[str]
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class JobResult(BaseModel):
    id: UUID
    status: str
    mode: str
    result_files: List[str]
    concepts: List[dict] = []
    
    class Config:
        from_attributes = True

class UploadResponse(BaseModel):
    job_id: UUID
    filename: str
    message: str

class StartJobRequest(BaseModel):
    job_id: UUID
    api_key: str
    model_provider: str = Field(..., pattern="^(gemini|openai|anthropic)$")

class StartJobResponse(BaseModel):
    job_id: UUID
    status: str
    message: str

class PageContent(BaseModel):
    headings: List[str] = []
    paragraphs: List[str] = []
    questions: List[dict] = []
    formulas: List[str] = []

class ErrorResponse(BaseModel):
    detail: str
