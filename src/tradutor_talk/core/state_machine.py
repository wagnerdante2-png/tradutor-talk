from __future__ import annotations

from dataclasses import dataclass

from tradutor_talk.core.models import SessionState


class InvalidTransitionError(RuntimeError):
    pass


_MAIN = {
    SessionState.IDLE: {SessionState.LISTENING},
    SessionState.LISTENING: {SessionState.SPEECH_DETECTED, SessionState.IDLE},
    SessionState.SPEECH_DETECTED: {SessionState.CAPTURING},
    SessionState.CAPTURING: {SessionState.END_OF_TURN},
    SessionState.END_OF_TURN: {SessionState.TRANSCRIBING},
    SessionState.TRANSCRIBING: {SessionState.TRANSLATING},
    SessionState.TRANSLATING: {SessionState.SYNTHESIZING},
    SessionState.SYNTHESIZING: {SessionState.PLAYING},
    SessionState.PLAYING: {SessionState.COOLDOWN},
    SessionState.COOLDOWN: {SessionState.LISTENING},
    SessionState.RECOVERING_NETWORK: {SessionState.LISTENING, SessionState.SESSION_ERROR},
    SessionState.PROVIDER_UNAVAILABLE: {SessionState.LISTENING, SessionState.SESSION_ERROR},
    SessionState.AUDIO_DEVICE_LOST: {SessionState.LISTENING, SessionState.SESSION_ERROR},
    SessionState.RATE_LIMITED: {SessionState.LISTENING, SessionState.SESSION_ERROR},
    SessionState.SESSION_ERROR: {SessionState.IDLE, SessionState.LISTENING},
}

_EXCEPTION_STATES = {
    SessionState.RECOVERING_NETWORK,
    SessionState.PROVIDER_UNAVAILABLE,
    SessionState.AUDIO_DEVICE_LOST,
    SessionState.RATE_LIMITED,
    SessionState.SESSION_ERROR,
}


@dataclass(slots=True)
class SessionStateMachine:
    state: SessionState = SessionState.IDLE

    def can_transition(self, target: SessionState) -> bool:
        if target in _EXCEPTION_STATES and self.state is not SessionState.IDLE:
            return True
        return target in _MAIN.get(self.state, set())

    def transition(self, target: SessionState) -> SessionState:
        if not self.can_transition(target):
            raise InvalidTransitionError(f"invalid transition: {self.state.value} -> {target.value}")
        self.state = target
        return self.state

    def reset(self, target: SessionState = SessionState.IDLE) -> SessionState:
        if target not in {SessionState.IDLE, SessionState.LISTENING}:
            raise ValueError("reset target must be idle or listening")
        self.state = target
        return self.state
