import asyncio
import logging
from datetime import datetime

from ...live.live_system import LiveSystem
from .manager import ConnectionManager

logger = logging.getLogger(__name__)


class SignalStreamer:
    """
    Real-time signal streaming engine with:
    - Non-blocking execution
    - Channel-based broadcasting
    - Safe lifecycle management
    """

    def __init__(
        self,
        live_system: LiveSystem,
        manager: ConnectionManager,
        interval: float = 2.5
    ):
        self.live_system = live_system
        self.manager = manager
        self.interval = interval

        self._running = False
        self._task: asyncio.Task | None = None

    async def _run_loop(self) -> None:
        logger.info("Signal streamer loop started")

        while self._running:
            try:
                # ⚡ Run in thread (non-blocking)
                signals = await asyncio.to_thread(self.live_system.run_cycle)

                payload = {
                    "type": "signals",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": signals if isinstance(signals, list) else [signals]
                }

                # ✅ Broadcast to "signals" channel only
                await self.manager.broadcast("signals", payload)

            except Exception as e:
                logger.error(f"Streaming error: {e}")

            await asyncio.sleep(self.interval)

        logger.info("Signal streamer loop stopped")

    async def start(self) -> None:
        """Start streaming (idempotent)."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        """Stop streaming safely."""
        self._running = False

        if self._task:
            await self._task
            self._task = None


# Singleton
_streamer: SignalStreamer | None = None


async def start_streaming(
    live_system: LiveSystem,
    manager: ConnectionManager
) -> SignalStreamer:
    """
    Initialize and start global streamer.
    """

    global _streamer

    if _streamer is None:
        _streamer = SignalStreamer(live_system, manager)

    await _streamer.start()
    return _streamer


async def stop_streaming() -> None:
    """Stop global streamer."""
    global _streamer

    if _streamer:
        await _streamer.stop()
        _streamer = None
