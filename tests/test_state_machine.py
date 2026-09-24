import pytest

from tradutor_talk.core.models import SessionState
from tradutor_talk.core.state_machine import InvalidTransitionError, SessionStateMachine


def test_happy_path_state_cycle() -> None:
    sm = SessionStateMachine()
    path = [
        SessionState.LISTENING,
        SessionState.SPEECH_DETECTED,
        SessionState.CAPTURING,
        SessionState.END_OF_TURN,
        SessionState.TRANSCRIBING,
        SessionState.TRANSLATING,
        SessionState.SYNTHESIZING,
        SessionState.PLAYING,
        SessionState.COOLDOWN,
        SessionState.LISTENING,
    ]
    for state in path:
        sm.transition(state)
    assert sm.state is SessionState.LISTENING


def test_invalid_transition_is_rejected() -> None:
    sm = SessionStateMachine()
    with pytest.raises(InvalidTransitionError):
        sm.transition(SessionState.TRANSLATING)
