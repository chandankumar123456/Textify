import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import relationship
from ..database import Base
import enum


class GUID(TypeDecorator):
    """Cross-database UUID type. Stores as String(36); returns uuid.UUID objects."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return uuid.UUID(str(value))


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobMode(str, enum.Enum):
    NOTES = "notes"
    PRACTICE = "practice"

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    status = Column(SAEnum(JobStatus), default=JobStatus.QUEUED, nullable=False)
    mode = Column(SAEnum(JobMode), nullable=False)
    model_provider = Column(String(50), nullable=False)
    original_filename = Column(String(255), nullable=False)
    s3_input_key = Column(String(512), nullable=False)
    total_pages = Column(Integer, default=0)
    processed_pages = Column(Integer, default=0)
    result_files = Column(JSON, default=list)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    pages = relationship("Page", back_populates="job", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="job", cascade="all, delete-orphan")
    concepts = relationship("Concept", back_populates="job", cascade="all, delete-orphan")

class Page(Base):
    __tablename__ = "pages"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id = Column(GUID(), ForeignKey("jobs.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    s3_image_key = Column(String(512), nullable=True)
    raw_text = Column(Text, nullable=True)
    structured_content = Column(JSON, nullable=True)
    status = Column(String(50), default="pending")
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    job = relationship("Job", back_populates="pages")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id = Column(GUID(), ForeignKey("jobs.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)
    answer = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    concepts = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    job = relationship("Job", back_populates="questions")

class Concept(Base):
    __tablename__ = "concepts"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id = Column(GUID(), ForeignKey("jobs.id"), nullable=False)
    name = Column(String(255), nullable=False)
    related_concepts = Column(JSON, nullable=True)
    question_ids = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    job = relationship("Job", back_populates="concepts")
