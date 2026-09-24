from tradutor_talk.audio.buffer import AudioRingBuffer
from tradutor_talk.core.models import ConversationTurn, Direction
from tradutor_talk.translation.context import ConversationContext


def _turn(text: str) -> ConversationTurn:
    return ConversationTurn(
        direction=Direction.REMOTE_TO_LOCAL,
        source_language="en-US",
        target_language="pt-BR",
        original_text=text,
        translated_text=text,
    )


def test_context_is_bounded() -> None:
    context = ConversationContext(max_turns=2)
    context.add(_turn("one"))
    context.add(_turn("two"))
    context.add(_turn("three"))
    assert [turn.original_text for turn in context.snapshot()] == ["two", "three"]


def test_ring_buffer_keeps_only_recent_chunks() -> None:
    buffer = AudioRingBuffer(max_chunks=2)
    buffer.push(b"a")
    buffer.push(b"b")
    buffer.push(b"c")
    assert buffer.snapshot() == b"bc"
