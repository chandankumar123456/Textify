"""
workers/tasks.py — legacy Celery task module.

For local development the processing pipeline runs directly in the backend
via a background thread (backend/app/services/processor.py).

This file is kept as a thin re-export so a distributed Celery deployment can be
restored in the future without restructuring the codebase.
"""
import sys
import os

# Allow importing from the backend package when run as a standalone worker
_backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend")
if _backend_path not in sys.path:
    sys.path.insert(0, _backend_path)

from app.services.processor import process_document  # noqa: F401
