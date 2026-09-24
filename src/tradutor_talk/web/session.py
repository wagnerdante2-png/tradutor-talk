from __future__ import annotations

import asyncio
from collections.abc import Callable

from tradutor_talk.app.bootstrap import build_openai_app
from tradutor_talk.core.models import Direction, ProcessResult, SessionState, Utterance


class BrowserSessionBusyError(RuntimeError):
    pass


class BrowserPlaybackError(RuntimeError):
    pass


class BrowserConversationSession:
    """Bridge browser playback lifecycle to the existing SessionController."""

    def __init__(self, controller_factory: Callable = build_openai_app) -> None:
        self._controller_factory = controller_factory
        self._controller = None
        self._pending: Utterance | None = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> str:
        if self._controller is None:
            return SessionState.IDLE.value
        return self._controller.state.value

    @property
    def pending_utterance_id(self) -> str | None:
        return self._pending.id if self._pending else None

    @property
    def context_turns(self) -> int:
        if self._controller is None:
            return 0
        return len(self._controller.context)

    def _ensure_controller(self):
        if self._controller is None:
            self._controller = self._controller_factory()
            self._controller.start()
        elif self._controller.state is SessionState.IDLE:
            self._controller.start()
        elif self._controller.state is SessionState.SESSION_ERROR:
            self._controller.recover()
        return self._controller

    async def process_turn(
        self,
        *,
        audio: bytes,
        direction: Direction,
        source_language: str,
        target_language: str,
    ) -> ProcessResult:
        async with self._lock:
            if self._pending is not None:
                raise BrowserSessionBusyError(
                    "previous translated audio has not finished playback"
                )

            controller = self._ensure_controller()
            result = await controller.process_audio(
                audio=audio,
                direction=direction,
                source_language=source_language,
                target_language=target_language,
            )
            controller.begin_playback(result.utterance)
            self._pending = result.utterance
            return result

    async def finish_playback(self, utterance_id: str) -> None:
        async with self._lock:
            if self._pending is None:
                raise BrowserPlaybackError("there is no pending playback")
            if self._pending.id != utterance_id:
                raise BrowserPlaybackError("utterance does not own pending playback")

            controller = self._ensure_controller()
            controller.finish_playback(self._pending)
            self._pending = None

    async def fail_playback(self, utterance_id: str) -> None:
        async with self._lock:
            if self._pending is None:
                return
            if self._pending.id != utterance_id:
                raise BrowserPlaybackError("utterance does not own pending playback")

            controller = self._ensure_controller()
            controller.fail_playback(self._pending)
            self._pending = None
            controller.recover()

    async def reset(self, *, clear_context: bool = True) -> None:
        async with self._lock:
            if self._controller is None:
                self._pending = None
                return

            self._controller.stop()
            if clear_context:
                self._controller.context.clear()
            self._controller.start()
            self._pending = None

    async def hard_reset(self) -> None:
        async with self._lock:
            if self._controller is not None:
                self._controller.stop()
            self._controller = None
            self._pending = None
