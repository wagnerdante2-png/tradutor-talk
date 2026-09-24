from collections import deque

from tradutor_talk.core.models import ConversationTurn


class ConversationContext:
    def __init__(self, max_turns: int = 8) -> None:
        if max_turns < 1:
            raise ValueError("max_turns must be >= 1")
        self._turns: deque[ConversationTurn] = deque(maxlen=max_turns)

    def add(self, turn: ConversationTurn) -> None:
        self._turns.append(turn)

    def snapshot(self) -> tuple[ConversationTurn, ...]:
        return tuple(self._turns)

    def clear(self) -> None:
        self._turns.clear()

    def __len__(self) -> int:
        return len(self._turns)
