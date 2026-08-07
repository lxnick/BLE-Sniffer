"""Capture lifecycle state machine independent of the transport adapter."""

from __future__ import annotations

from enum import Enum


class CaptureState(str, Enum):
    DISCONNECTED = "disconnected"
    OPENING = "opening"
    READY = "ready"
    CAPTURING = "capturing"
    STOPPING = "stopping"
    CLOSED = "closed"
    FAILED = "failed"


_ALLOWED_TRANSITIONS = {
    CaptureState.DISCONNECTED: {CaptureState.OPENING},
    CaptureState.OPENING: {CaptureState.READY, CaptureState.FAILED},
    CaptureState.READY: {CaptureState.CAPTURING, CaptureState.FAILED},
    CaptureState.CAPTURING: {CaptureState.STOPPING, CaptureState.FAILED},
    CaptureState.STOPPING: {CaptureState.CLOSED, CaptureState.FAILED},
    CaptureState.CLOSED: set(),
    CaptureState.FAILED: set(),
}


class CaptureSession:
    def __init__(self) -> None:
        self._state = CaptureState.DISCONNECTED
        self._failure: str | None = None
        self._partial = False

    @property
    def state(self) -> CaptureState:
        return self._state

    @property
    def failure(self) -> str | None:
        return self._failure

    @property
    def partial(self) -> bool:
        return self._partial

    def transition(self, target: CaptureState) -> None:
        if target not in _ALLOWED_TRANSITIONS[self._state]:
            raise ValueError(f"invalid capture transition: {self._state.value} -> {target.value}")
        self._state = target

    def fail(self, reason: str, *, partial: bool = False) -> None:
        if CaptureState.FAILED not in _ALLOWED_TRANSITIONS[self._state]:
            raise ValueError(f"cannot fail a session in state {self._state.value}")
        if not reason.strip():
            raise ValueError("failure reason must not be empty")
        self._failure = reason
        self._partial = partial
        self._state = CaptureState.FAILED

