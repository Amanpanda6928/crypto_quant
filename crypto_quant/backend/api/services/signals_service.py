from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from ...model.predict import Predictor
from ..database import Prediction


class SignalsService:
    def __init__(self, cache_ttl_seconds: int = 5):
        self._predictor: Predictor | None = None
        self._cache_ttl = cache_ttl_seconds
        self._cached_signals: list[dict[str, Any]] | None = None
        self._last_run_time: datetime | None = None
        self._lock = asyncio.Lock()
        self._inflight: asyncio.Task | None = None

    def _get_predictor(self) -> Predictor:
        if self._predictor is None:
            self._predictor = Predictor()
            self._predictor.load_latest_models()
        return self._predictor

    def reset_models(self) -> None:
        # Next request will reload latest models from disk.
        self._predictor = None

    async def get_signals(self, db: Session) -> dict[str, Any]:
        # Fast-path cache + singleflight control.
        async with self._lock:
            now = datetime.utcnow()
            if (
                self._cached_signals is not None
                and self._last_run_time is not None
                and (now - self._last_run_time) < timedelta(seconds=self._cache_ttl)
            ):
                return {
                    "status": "cached",
                    "timestamp": self._last_run_time.isoformat(),
                    "signals": self._cached_signals,
                }

            if self._inflight is None:
                self._inflight = asyncio.create_task(self._compute_and_store(db))
            task = self._inflight

        # Await outside lock so other requests can join.
        try:
            return await task
        finally:
            async with self._lock:
                if self._inflight is task:
                    self._inflight = None

    async def _compute_and_store(self, db: Session) -> dict[str, Any]:
        now = datetime.utcnow()
        predictor = self._get_predictor()
        preds = await asyncio.to_thread(predictor.predict_all)

        ts = now.isoformat()
        signals: list[dict[str, Any]] = []

        for symbol, horizon_map in preds.items():
            combined = predictor.combine_multi_horizon(horizon_map)
            confidence = abs(combined - 0.5) * 2
            signals.append(
                {
                    "symbol": symbol,
                    "prob_up": float(combined),
                    "confidence": float(confidence),
                    "timestamp": ts,
                    "horizons": {h: float(p[0]) for h, p in horizon_map.items()},
                }
            )

            for horizon, (prob,) in horizon_map.items():
                db.add(
                    Prediction(
                        symbol=symbol,
                        horizon=horizon,
                        probability=float(prob),
                        confidence=float(abs(prob - 0.5) * 2),
                    )
                )
        db.commit()

        async with self._lock:
            self._cached_signals = signals
            self._last_run_time = now

        return {"status": "fresh", "timestamp": ts, "signals": signals}


signals_service = SignalsService(cache_ttl_seconds=5)

