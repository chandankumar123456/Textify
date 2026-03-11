"""
workers/celery_app.py — legacy Celery configuration.

For local development no Celery or Redis broker is needed.
Processing runs in a background thread inside the FastAPI process.

This file is kept so a distributed Celery deployment can be restored
in the future by:
  1. Installing celery[redis] and redis packages
  2. Setting CELERY_BROKER_URL and CELERY_RESULT_BACKEND env vars
  3. Running: celery -A workers.celery_app worker --loglevel=info
"""
import os
from celery import Celery

BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

app = Celery(
    "textify",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["workers.tasks"],
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "workers.tasks.process_document": {"queue": "document_processing"},
    },
    task_default_retry_delay=30,
    task_max_retries=3,
)
