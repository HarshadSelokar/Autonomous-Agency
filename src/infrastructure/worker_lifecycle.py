"""Worker Lifecycle Management Module.

Tracks worker states (STARTING -> READY -> RUNNING -> DRAINING -> STOPPED)
and manages signal registration for graceful draining during production shutdown.
"""

import asyncio
from enum import Enum
import logging
import signal
import sys
from typing import Any

logger = logging.getLogger(__name__)


class WorkerLifecycleState(str, Enum):
    STARTING = "STARTING"
    READY = "READY"
    RUNNING = "RUNNING"
    DRAINING = "DRAINING"
    STOPPED = "STOPPED"


class WorkerLifecycleManager:
    """Manages background worker state transitions and graceful shutdown signal handling."""

    def __init__(self, drain_timeout_seconds: float = 30.0) -> None:
        self.state = WorkerLifecycleState.STARTING
        self.drain_timeout_seconds = drain_timeout_seconds
        self._shutdown_event = asyncio.Event()

    @property
    def is_running(self) -> bool:
        return self.state in (WorkerLifecycleState.READY, WorkerLifecycleState.RUNNING)

    @property
    def is_draining(self) -> bool:
        return self.state == WorkerLifecycleState.DRAINING

    @property
    def is_stopped(self) -> bool:
        return self.state == WorkerLifecycleState.STOPPED

    def transition_to(self, new_state: WorkerLifecycleState) -> None:
        logger.info(f"Worker state transition: {self.state.value} -> {new_state.value}")
        self.state = new_state
        if new_state == WorkerLifecycleState.DRAINING:
            self._shutdown_event.set()

    def register_signal_handlers(self) -> None:
        """Register SIGTERM / SIGINT handlers for graceful shutdown."""
        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    loop.add_signal_handler(sig, self._handle_signal, sig)
                except NotImplementedError:
                    # Windows loop doesn't support add_signal_handler in all configurations
                    signal.signal(sig, lambda s, f: self._handle_signal(s))
            logger.info("Worker signal handlers registered (SIGTERM, SIGINT).")
        except Exception as err:
            logger.debug(f"Signal registration notice: {err}")

    def _handle_signal(self, sig: Any) -> None:
        logger.warning(f"Received signal {sig}. Initiating graceful worker drain...")
        self.transition_to(WorkerLifecycleState.DRAINING)

    async def wait_for_shutdown(self) -> None:
        """Block until shutdown signal is received."""
        await self._shutdown_event.wait()
