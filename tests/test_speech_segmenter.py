import pytest

from tradutor_talk.audio.segmenter import (
    SegmentState,
    SegmenterConfig,
    SpeechSegmenter,
    SpeechStartTimeout,
)


def test_segmenter_detects_start_and_end_without_hardware() -> None:
    segmenter = SpeechSegmenter(
        SegmenterConfig(
            block_ms=20,
            pre_roll_ms=40,
            start_speech_ms=40,
            end_silence_ms=40,
            wait_timeout_seconds=1,
            max_utterance_seconds=2,
        )
    )

    assert segmenter.feed(b"a", is_speech=False) is SegmentState.WAITING
    assert segmenter.feed(b"b", is_speech=False) is SegmentState.WAITING
    assert segmenter.feed(b"c", is_speech=True) is SegmentState.WAITING
    assert segmenter.feed(b"d", is_speech=True) is SegmentState.CAPTURING
    assert segmenter.feed(b"e", is_speech=True) is SegmentState.CAPTURING
    assert segmenter.feed(b"f", is_speech=False) is SegmentState.CAPTURING
    assert segmenter.feed(b"g", is_speech=False) is SegmentState.COMPLETE

    assert segmenter.pcm == b"cdefg"
    assert segmenter.ended_by_max_duration is False


def test_segmenter_times_out_when_nobody_speaks() -> None:
    segmenter = SpeechSegmenter(
        SegmenterConfig(
            block_ms=20,
            wait_timeout_seconds=0.04,
        )
    )

    assert segmenter.feed(b"a", is_speech=False) is SegmentState.WAITING
    with pytest.raises(SpeechStartTimeout):
        segmenter.feed(b"b", is_speech=False)


def test_segmenter_hard_caps_utterance_duration() -> None:
    segmenter = SpeechSegmenter(
        SegmenterConfig(
            block_ms=20,
            pre_roll_ms=20,
            start_speech_ms=20,
            end_silence_ms=200,
            wait_timeout_seconds=1,
            max_utterance_seconds=0.06,
        )
    )

    assert segmenter.feed(b"a", is_speech=True) is SegmentState.CAPTURING
    assert segmenter.feed(b"b", is_speech=True) is SegmentState.CAPTURING
    assert segmenter.feed(b"c", is_speech=True) is SegmentState.COMPLETE
    assert segmenter.ended_by_max_duration is True
