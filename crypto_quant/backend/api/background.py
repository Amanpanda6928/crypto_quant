from __future__ import annotations

import asyncio
import glob
import os
import threading
from typing import Optional

from .database import SessionLocal
from .services.signals_service import signals_service
from ..model.train import train_model


_task: Optional[asyncio.Task] = None
_train_thread_started = False


def _models_dir() -> str:
    backend_dir = os.path.dirname(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    return os.path.join(backend_dir, "models_store")


def _has_model(horizon: str) -> bool:
    return bool(glob.glob(os.path.join(_models_dir(), f"model_{horizon}_*.pkl")))


def _ensure_models_background() -> None:
    # If longer-horizon models are missing, train them once in background.
    required = ["1h", "4h", "1d"]
    if all(_has_model(h) for h in required):
        return

    # Train with enough candles for 1d on 1m data.
    train_model(limit=2500, models_path=_models_dir())
    signals_service.reset_models()


async def _loop(interval_seconds: int) -> None:
    # Periodically refresh cache + persist predictions.
    await asyncio.sleep(3)
    while True:
        db = SessionLocal()
        try:
            await signals_service.get_signals(db)
        finally:
            db.close()
        await asyncio.sleep(interval_seconds)


async def start_signal_updater(interval_seconds: int = 60) -> None:
    global _task
    if _task is not None:
        return
    _task = asyncio.create_task(_loop(interval_seconds))

    global _train_thread_started
    if not _train_thread_started:
        _train_thread_started = True
        threading.Thread(target=_ensure_models_background, daemon=True).start()

