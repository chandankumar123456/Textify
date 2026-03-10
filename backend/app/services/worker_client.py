from celery import Celery
from ..config import settings

celery_app = Celery(
    "textify",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

def start_processing_job(job_id: str, s3_input_key: str, mode: str, model_provider: str, api_key: str):
    celery_app.send_task(
        "workers.tasks.process_document",
        args=[job_id, s3_input_key, mode, model_provider, api_key],
        queue="document_processing",
    )
