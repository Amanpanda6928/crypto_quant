from __future__ import annotations

import os
import threading
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from ...model.train import train_model

router = APIRouter(prefix="/train", tags=["train"])


_jobs_lock = threading.Lock()
_jobs: dict[str, dict[str, Any]] = {}


def _run_training(job_id: str, candles: int) -> None:
    started_at = datetime.utcnow()
    with _jobs_lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "status": "running",
            "candles": candles,
            "started_at": started_at.isoformat(),
            "ended_at": None,
            "error": None,
        }

    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        models_path = os.path.join(backend_dir, "models_store")
        train_model(limit=candles, models_path=models_path)
        # Force signals service to pick up new models.
        try:
            from ..services.signals_service import signals_service
            signals_service.reset_models()
        except Exception:
            pass
        ended_at = datetime.utcnow()
        with _jobs_lock:
            _jobs[job_id]["status"] = "succeeded"
            _jobs[job_id]["ended_at"] = ended_at.isoformat()
    except Exception as e:
        ended_at = datetime.utcnow()
        with _jobs_lock:
            _jobs[job_id]["status"] = "failed"
            _jobs[job_id]["ended_at"] = ended_at.isoformat()
            _jobs[job_id]["error"] = str(e)


@router.post("/")
async def start_training(candles: int = 2500) -> dict[str, Any]:
    """
    Start a background training job.
    """
    if candles < 1600:
        raise HTTPException(status_code=400, detail="candles must be >= 1600 for 1d horizon on 1m data")

    job_id = str(uuid.uuid4())
    t = threading.Thread(target=_run_training, args=(job_id, candles), daemon=True)
    t.start()
    return {"job_id": job_id, "status": "queued"}


@router.get("/{job_id}")
async def get_training_status(job_id: str) -> dict[str, Any]:
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job

