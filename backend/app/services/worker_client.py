import threading
import logging
from .processor import process_document

logger = logging.getLogger(__name__)


def start_processing_job(job_id: str, file_key: str, mode: str, model_provider: str, api_key: str):
    """Dispatch document processing in a background daemon thread."""
    thread = threading.Thread(
        target=process_document,
        args=(job_id, file_key, mode, model_provider, api_key),
        daemon=True,
        name=f"processor-{job_id}",
    )
    thread.start()
    logger.info("Started processing thread for job %s", job_id)
