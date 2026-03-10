import os
import io
import logging
import traceback
from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://textify:textify@localhost:5432/textify")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _ensure_backend_path():
    """Add backend directory to sys.path if not already present."""
    import sys
    backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)


def _get_storage():
    import boto3
    from botocore.config import Config as BotoConfig
    client = boto3.client(
        "s3",
        endpoint_url=os.environ.get("S3_ENDPOINT_URL", "http://localhost:9000"),
        aws_access_key_id=os.environ.get("S3_ACCESS_KEY", "minioadmin"),
        aws_secret_access_key=os.environ.get("S3_SECRET_KEY", "minioadmin"),
        region_name=os.environ.get("S3_REGION", "us-east-1"),
        config=BotoConfig(signature_version="s3v4"),
    )
    return client, os.environ.get("S3_BUCKET_NAME", "textify")


def _get_models():
    """Import DB models lazily."""
    _ensure_backend_path()
    from app.models.models import Job, Page, Question, Concept, JobStatus, JobMode
    return Job, Page, Question, Concept, JobStatus, JobMode


@shared_task(name="workers.tasks.process_document", bind=True, max_retries=3)
def process_document(self, job_id: str, s3_input_key: str, mode: str, model_provider: str, api_key: str):
    """Main document processing task."""
    Job, Page, Question, Concept, JobStatus, JobMode = _get_models()
    db = SessionLocal()
    
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        job.status = JobStatus.PROCESSING
        db.commit()
        
        # Download PDF from S3
        s3_client, bucket = _get_storage()
        response = s3_client.get_object(Bucket=bucket, Key=s3_input_key)
        pdf_bytes = response["Body"].read()
        
        # Import pipeline modules
        _ensure_backend_path()
        from app.pipeline.pdf_processor import PDFProcessor
        from app.pipeline.image_preprocessor import ImagePreprocessor
        from app.pipeline.handwriting_engine import HandwritingEngine
        from app.pipeline.layout_detector import LayoutDetector
        from app.pipeline.document_classifier import DocumentClassifier
        from app.pipeline.question_extractor import QuestionExtractor
        from app.pipeline.concept_extractor import ConceptExtractor
        from app.pipeline.document_builder import DocumentBuilder
        from app.pipeline.math_parser import MathParser
        
        # Step 1: Split PDF into page images
        processor = PDFProcessor()
        page_images = processor.split_to_images(pdf_bytes)
        job.total_pages = len(page_images)
        db.commit()
        
        # Create page records
        for i, img_bytes in enumerate(page_images):
            page_key = f"pages/{job_id}/page_{i+1}.png"
            s3_client.put_object(Bucket=bucket, Key=page_key, Body=img_bytes, ContentType="image/png")
            
            page = Page(
                job_id=job.id,
                page_number=i + 1,
                s3_image_key=page_key,
                status="pending",
            )
            db.add(page)
        db.commit()
        
        # Step 2: Process each page
        preprocessor = ImagePreprocessor()
        engine = HandwritingEngine(provider=model_provider, api_key=api_key)
        layout_detector = LayoutDetector()
        classifier = DocumentClassifier()
        question_extractor = QuestionExtractor()
        concept_extractor = ConceptExtractor()
        
        all_pages_content = []
        all_questions = []
        all_concepts = []
        
        pages = db.query(Page).filter(Page.job_id == job.id).order_by(Page.page_number).all()
        
        for page in pages:
            try:
                # Download page image
                resp = s3_client.get_object(Bucket=bucket, Key=page.s3_image_key)
                img_bytes = resp["Body"].read()
                
                # Preprocess
                processed_img = preprocessor.preprocess(img_bytes)
                
                # Transcribe with vision model
                structured = engine.transcribe(processed_img)
                
                page.structured_content = structured
                page.status = "completed"
                
                # Layout detection
                regions = layout_detector.detect_regions(structured)
                
                # Classification
                page_type = classifier.classify(structured)
                
                # Extract questions
                page_questions = question_extractor.extract_questions(structured)
                for q in page_questions:
                    q_record = Question(
                        job_id=job.id,
                        page_number=page.page_number,
                        question_text=q["question"],
                        options=q.get("options"),
                        answer=q.get("answer"),
                        explanation=q.get("explanation"),
                    )
                    db.add(q_record)
                    all_questions.append(q)
                
                # Extract concepts
                page_concepts = concept_extractor.extract_concepts(structured)
                all_concepts.extend(page_concepts)
                
                all_pages_content.append(structured)
                
                job.processed_pages = page.page_number
                db.commit()
                
            except Exception as e:
                page.status = "failed"
                page.error_message = str(e)
                page.retry_count += 1
                db.commit()
                logger.error(f"Failed to process page {page.page_number}: {e}")
                # Add empty content to maintain page order
                all_pages_content.append({
                    "headings": [],
                    "paragraphs": [f"[Page {page.page_number} processing failed]"],
                    "questions": [],
                    "formulas": [],
                })
        
        # Step 3: Build concept graph
        concept_graph = concept_extractor.build_concept_graph(all_concepts)
        for c in concept_graph:
            concept_record = Concept(
                job_id=job.id,
                name=c["name"],
                related_concepts=c.get("related_concepts"),
                question_ids=c.get("question_indices"),
            )
            db.add(concept_record)
        db.commit()
        
        # Step 4: Generate output PDFs
        builder = DocumentBuilder()
        result_files = []
        
        if mode == "notes":
            # Build notes PDF
            notes_html = builder.build_notes_html(all_pages_content, title=job.original_filename)
            notes_pdf = _generate_pdf(notes_html)
            notes_key = f"results/{job_id}/notes.pdf"
            s3_client.put_object(Bucket=bucket, Key=notes_key, Body=notes_pdf, ContentType="application/pdf")
            result_files.append(notes_key)
        
        elif mode == "practice":
            # Build notes PDF as well
            notes_html = builder.build_notes_html(all_pages_content, title=job.original_filename)
            notes_pdf = _generate_pdf(notes_html)
            notes_key = f"results/{job_id}/notes.pdf"
            s3_client.put_object(Bucket=bucket, Key=notes_key, Body=notes_pdf, ContentType="application/pdf")
            result_files.append(notes_key)
            
            # Build practice PDF
            if all_questions:
                practice_questions = question_extractor.create_practice_questions(all_questions)
                practice_html = builder.build_practice_html(practice_questions, title="Practice Questions")
                practice_pdf = _generate_pdf(practice_html)
                practice_key = f"results/{job_id}/practice.pdf"
                s3_client.put_object(Bucket=bucket, Key=practice_key, Body=practice_pdf, ContentType="application/pdf")
                result_files.append(practice_key)
        
        # Step 5: Update job as completed
        job.status = JobStatus.COMPLETED
        job.result_files = result_files
        db.commit()
        
        logger.info(f"Job {job_id} completed successfully with {len(result_files)} result files")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {traceback.format_exc()}")
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                db.commit()
        except Exception:
            pass
        
        # Retry if possible
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=30 * (self.request.retries + 1))
    
    finally:
        db.close()
        # API key is discarded here - not stored anywhere


def _generate_pdf(html_content: str) -> bytes:
    """Generate PDF from HTML using WeasyPrint."""
    from weasyprint import HTML
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes
