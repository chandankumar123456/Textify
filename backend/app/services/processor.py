"""
backend/app/services/processor.py

Direct (in-process) document processing pipeline.
Called from a background thread by worker_client.py — no Celery or Redis needed.
"""
import logging
import traceback
from pathlib import Path

from ..database import SessionLocal
from .storage import StorageService

logger = logging.getLogger(__name__)


def _generate_pdf(html_content: str) -> bytes:
    from weasyprint import HTML
    return HTML(string=html_content).write_pdf()


def process_document(job_id: str, file_key: str, mode: str, model_provider: str, api_key: str):
    """
    Run the full document processing pipeline synchronously.
    Designed to be called in a background thread.
    """
    db = SessionLocal()
    storage = StorageService()

    try:
        from ..models.models import Job, Page, Question, Concept, JobStatus, JobMode

        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error("Job %s not found", job_id)
            return

        job.status = JobStatus.PROCESSING
        db.commit()

        # ── Step 1: Download PDF ──────────────────────────────────────────────
        pdf_bytes = storage.download_bytes(file_key)

        # ── Import pipeline modules ───────────────────────────────────────────
        from ..pipeline.pdf_processor import PDFProcessor
        from ..pipeline.image_preprocessor import ImagePreprocessor
        from ..pipeline.handwriting_engine import HandwritingEngine
        from ..pipeline.layout_detector import LayoutDetector
        from ..pipeline.document_classifier import DocumentClassifier
        from ..pipeline.question_extractor import QuestionExtractor
        from ..pipeline.concept_extractor import ConceptExtractor
        from ..pipeline.document_builder import DocumentBuilder

        # ── Step 2: Split PDF into page images ───────────────────────────────
        processor = PDFProcessor()
        page_images = processor.split_to_images(pdf_bytes)
        job.total_pages = len(page_images)
        db.commit()

        for i, img_bytes in enumerate(page_images):
            page_key = f"pages/{job_id}/page_{i + 1}.png"
            storage.upload_bytes(page_key, img_bytes, content_type="image/png")

            page = Page(
                job_id=job.id,
                page_number=i + 1,
                s3_image_key=page_key,
                status="pending",
            )
            db.add(page)
        db.commit()

        # ── Step 3: Process each page ─────────────────────────────────────────
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
                img_bytes = storage.download_bytes(page.s3_image_key)
                processed_img = preprocessor.preprocess(img_bytes)
                structured = engine.transcribe(processed_img)

                page.structured_content = structured
                page.status = "completed"

                layout_detector.detect_regions(structured)
                classifier.classify(structured)

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
                logger.error("Failed to process page %d: %s", page.page_number, e)
                all_pages_content.append({
                    "headings": [],
                    "paragraphs": [f"[Page {page.page_number} processing failed]"],
                    "questions": [],
                    "formulas": [],
                })

        # ── Step 4: Build concept graph ───────────────────────────────────────
        concept_graph = concept_extractor.build_concept_graph(all_concepts)
        for c in concept_graph:
            db.add(Concept(
                job_id=job.id,
                name=c["name"],
                related_concepts=c.get("related_concepts"),
                question_ids=c.get("question_indices"),
            ))
        db.commit()

        # ── Step 5: Generate output PDFs ──────────────────────────────────────
        builder = DocumentBuilder()
        result_files = []

        if mode in ("notes", "practice"):
            notes_html = builder.build_notes_html(all_pages_content, title=job.original_filename)
            notes_pdf = _generate_pdf(notes_html)
            notes_key = f"results/{job_id}/notes.pdf"
            storage.upload_bytes(notes_key, notes_pdf, content_type="application/pdf")
            result_files.append(notes_key)

        if mode == "practice" and all_questions:
            practice_questions = question_extractor.create_practice_questions(all_questions)
            practice_html = builder.build_practice_html(practice_questions, title="Practice Questions")
            practice_pdf = _generate_pdf(practice_html)
            practice_key = f"results/{job_id}/practice.pdf"
            storage.upload_bytes(practice_key, practice_pdf, content_type="application/pdf")
            result_files.append(practice_key)

        job.status = JobStatus.COMPLETED
        job.result_files = result_files
        db.commit()
        logger.info("Job %s completed with %d result file(s)", job_id, len(result_files))

    except Exception as e:
        logger.error("Job %s failed:\n%s", job_id, traceback.format_exc())
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                db.commit()
        except Exception:
            pass

    finally:
        db.close()
        # api_key is a local variable — discarded when this function returns
